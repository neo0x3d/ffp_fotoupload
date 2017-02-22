#!/usr/bin/env python3
"""
Analyze a given source and copy specific files to the local machine. Inform the user over a queue.
    1. analyze source (mount if blkdev partition)
    2. copy files of matching type to local timestamped folder
    3. delete copied files (if specified)
"""

import logging
import os
import stat
from datetime import datetime

from libmultiupload import emailmod, move_files, udiskie_mounthelper


def analyze_move_userfeedback(media_source, userstatus_queue, config):
    """
    Determine the source type (folder, block device partition)
    Copy the files to a local timestamped folder
    Inform the user about the status
    Return a list of folders to process
    Args:
        media_source: source object to be analyzed
        userstatus_queue: user information
        config: parsed json config file
    Returns:
        joblist: list of paths to jobs, which are ready for processing
    """
    ############################################################################
    # init content
    ############################################################################

    joblist = []

    # set timestamp format
    timestamp = datetime.now().strftime(config["timestamp"])

    ############################################################################
    # determine source type and mount if necessary
    ############################################################################

    needto_unmount = False

    if os.path.isdir(media_source):
        logging.info("source is directory")
        source = media_source
    else:
        if stat.S_ISBLK(os.stat(media_source).st_mode):

            logging.info(
                "Block device partition defined as source: " + media_source)

            # check if partition is mounted
            is_mounted = udiskie_mounthelper.check_if_mounted(media_source)

            # partition is not mounted -> mount it
            if is_mounted == 0:
                ret = udiskie_mounthelper.mount_partition(media_source)
                needto_unmount = True

                if ret == -1:
                    logging.error("mount_part() returned with -1")

                    emailmod.send_err("error in multiupload.py",
                                      "mount_part() returned -1", config)
                    logging.info("End of job: " + str(media_source))
                    exit()
                else:
                    logging.info("Sucessfully mounted, mountpoint: " + ret)
                    source = ret

            # error while checking if mounted
            elif is_mounted == -1:
                logging.error("check_if_mounted() returned with -1")
                emailmod.send_err("error in multiupload.py",
                                  "check_if_mounted() returned -1", config)
                logging.info("End of logfile: " + timestamp)
                exit()

            # partition is mounted -> get mountpoint
            else:
                # make sure return value ends with "/", required later on
                logging.debug("mountpoint: " + is_mounted)
                source = is_mounted

        # source folder and device given
        else:
            userstatus_queue.put("error_source")
            logging.error("Source is neither blkdev nor dir")
            emailmod.send_err("error in upload_routine.py",
                              "Source is neither blkdev nor dir", config)
            logging.info("End of logfile: " + timestamp)
            return -1

    ############################################################################
    # check against subfolders
    ############################################################################

    sourcelist = [source]

    def scantree(root_path):
        """
        (recoursive) scan for folders
        """
        for entry in os.scandir(root_path):
            if entry.is_dir():
                sourcelist.append(os.path.join(root_path, entry.name))
                scantree(os.path.join(root_path, entry.name))

    scantree(source)

    #############################################################################
    # local copy & delete source
    #############################################################################

    #  inform user after valid medium has been detected
    userstatus_queue.put("start#" + str(sourcelist))

    # def check_free_space():

    for folder in sourcelist:

        # main job folder name (time when analyze_move_userfeedback() has been called)
        job_dir = timestamp

        # make sure folder does not exist
        if os.path.exists(os.path.join(config["temp_path"], job_dir)):
            folder_counter = 1
            while os.path.exists(os.path.join(config["temp_path"], job_dir) + "_" + str(folder_counter)):
                folder_counter += 1
            job_dir += "_" + str(folder_counter)
        logging.debug("current job_dir is: " + job_dir)

        image_path = os.path.join(config["temp_path"], job_dir, "image")
        video_path = os.path.join(config["temp_path"], job_dir, "video")

        # copy image files
        if config["image"]["enable"]:
            logging.debug("start copying images")
            image_count = move_files.move_files(folder, image_path,
                                                config["image"]["type"], config["delete_source"])

        # copy video files
        if config["video"]["enable"]:
            logging.debug("start copying videos")
            video_count = move_files.move_files(folder, video_path,
                                                config["video"]["type"], config["delete_source"])

        # quit if no files were copied
        if image_count <= 0 and video_count <= 0:
            logging.warning("No image or video files found")
            logging.info("End of job: " + str(media_source))
        else:
            joblist.append(os.path.join(config["temp_path"], job_dir))
            logging.debug("appended to job list: " +
                          str(os.path.join(config["temp_path"])) + job_dir)

    ############################################################################
    # unmount via udiskie_mounthelper
    ############################################################################

    # try to unmount if mounted (same condition as for mounting)
    # so that sd card can be physically removed
    if needto_unmount:
        ret = udiskie_mounthelper.umount(source)
        if ret == 0:
            logging.debug("umount returned successfully")
        else:
            logging.warning("umount() returned non zero: " + ret)
            emailmod.send_err("error in multiupload.py",
                              "umount() returned non zero: " + ret, config)

    else:
        logging.debug("No need to unmount, skip")

    ############################################################################
    # end
    ############################################################################

    userstatus_queue.put("end#" + str(job_dir))
    logging.debug("analyze source returns with jobs: " + str(joblist))
    return joblist
