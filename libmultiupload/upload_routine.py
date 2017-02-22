#!/usr/bin/env python3
"""
Main processing and upload routine:
    1. check source against valid filetypes
    2. generate thumbnails
    3. zip original files
    4. generate html file/table and send via email
    5. ftps upload to remote and local server
    6. move to archive folder
"""

import logging
import os
import shutil
from datetime import datetime

# import local modules
from libmultiupload import emailmod, ftps_mod, html_email, img_thumbnail


# TODO
# remove all job_dir
# if possible
# switch away from os.listdir to scandir
# rework check if images have been uploaded (server remaining space check)


def upload_routine(job_path, config):
    """
    Args:
        media_source: source folder or partition
        config: parsed config file
    returns:
        non zero on failure
    """

    ##########################################################################
    # init content
    ##########################################################################

    # move folder from temp dir to archive if finished without errors
    moveto_archive = True

    ####################
    # parse input data
    ###################

    job_dir = os.path.basename(os.path.normpath(job_path))
    image_path = os.path.join(job_path, "image")

    # check if valid files are present
    data_valid = False
    filelist = os.listdir(image_path)
    for entry in filelist:
        if entry.lower().endswith(tuple(config["image"]["type"])):
            data_valid = True
            break

    if not data_valid:
        logging.error("No valid files found in: " + str(image_path))
        logging.debug("content of dir: " + str(filelist))
        return -1

    ############################
    # image and video webversion
    ############################

    # thumbnail path
    image_thumb_path = os.path.join(job_path, "image_thumb")

    # create thumbnails
    if config["image_thumbnail"]["enable"]:
        logging.debug("starting image thumb creation")

        img_list = os.listdir(image_path)
        for image in img_list:
            src_path = os.path.join(image_path, image)
            dest_path = os.path.join(image_thumb_path, image)
            retval = img_thumbnail.make_thumbnail(src_path, dest_path,
                                                  config["image"]["type"],
                                                  config["image_thumbnail"]["size_px"])

            if retval != 0:
                moveto_archive = False
                logging.error("make_thumbnail returned an error")
                emailmod.send_err(
                    "make_thumbnail returned error", "see logfile", config)
            else:
                logging.debug("processed successfull: " + dest_path)

    ##########################################################################
    # create archive
    ##########################################################################

    def makezip(sourcepath, destarchive):
        """
        Create ZIP archive from original images

        Args:
            sourcepath: path to the original files (local, not SD card!)
            destpath: dest path and name of the ZIP archive

        Returns:
            0 if everything is ok
            -1 in the event of an error
        """

        logging.debug("Entered makezip()")
        try:
            if os.path.exists(sourcepath):
                shutil.make_archive(destarchive, format="zip",
                                    root_dir=sourcepath, logger=logging)
                logging.info("Created archive: %s", destarchive)
            else:
                logging.error(
                    "Cannot make compressed archive, path does not exist: %s", sourcepath)
                return -1

        except Exception:
            logging.exception("Fatal error in makezip()")
        return 0

    # create archive of the original images
    #
    #
    # check if zip name already exists

    if config["image"]["enable"]:
        image_archive_name = job_dir
        # image_archive_path = os.path.join(
        #    config["temp_path"], job_dir, image_archive_name)
        image_archive_path = os.path.join(job_path, image_archive_name)
        logging.debug("creating archive of original images")
        makezip(image_path, image_archive_path)

    ############
    # send email
    ############

    if config["email"]["enable"]:
        logging.debug("Start sending email")
        try:
            # generate and save html text
            html_text = html_email.email_text_html(config, config["email"]["header_html"],
                                                   config["email"][
                                                       "footer_html"],
                                                   config["email"]["weblink"],
                                                   image_thumb_path, job_dir)
            htmlfile = config["temp_path"] + job_dir + "/" + job_dir + "_email.html"

            with open(htmlfile, "w+") as fh:
                fh.write(html_text)

            email_ret = emailmod.send(config["email"]["sender"],
                                      config["email"]["recipient"],
                                      config["email"]["recipient_cc"],
                                      config["email"]["recipient_bcc"],
                                      'Fotoupload ' + job_dir, "", html_text)
            if email_ret != 0:
                emailmod.send_err("fatal error while sending html email", str(email_ret), config)

        except Exception:
            logging.exception("Error creating and saving HTML email file")

    else:
        logging.info("Email disabled")

    ############
    # ftps upload
    ############

    # upload thumbnail images and archive of original images to remote ftps server
    if config["remote_ftp"]["enable"]:

        # upload webversion images
        if config["image_thumbnail"]["enable"]:
            logging.info("Starting thumbnails upload")

            ret_code, ret_msg = ftps_mod.ftpsupload(config, image_thumb_path,
                                                    config["image"]["type"],
                                                    config["remote_ftp"]["target_dir"],
                                                    job_dir, False,
                                                    config["remote_ftp"]["username"],
                                                    config["remote_ftp"]["password"],
                                                    config["remote_ftp"]["ftp"])

            # disable moving folder into archive dir if error occoured
            if ret_code != 0:
                logging.error(
                    "ftpsupload_recoursive returned with: " + ret_msg)
                emailmod.send_err("fatal error in ftps_module",
                                  str(ret_msg), config)
                moveto_archive = False
        else:
            logging.info(
                "Can not upload thumbnails, thumbnails creation disabled")

        # upload zip archive of original images
        ret_code, ret_msg = ftps_mod.ftpsupload(config,
                                                config["temp_path"] + job_dir, ".zip",
                                                config["remote_ftp"]["target_dir"],
                                                job_dir, False,
                                                config["remote_ftp"]["username"],
                                                config["remote_ftp"]["password"],
                                                config["remote_ftp"]["ftp"])

        # disable moving folder into archive dir if error occoured
        if ret_code != 0:
            logging.error("ftpsupload_recoursive returned with: " + ret_msg)
            emailmod.send_err("fatal error in ftp_module", str(ret_msg), config)
            moveto_archive = False

    # upload complete job folder recursively to local FTP server
    if config["local_ftp"]["enable"]:
        ret_code, ret_msg = ftps_mod.ftpsupload(config, config["temp_path"] + job_dir,
                                                config["local_ftp"]["type"],
                                                config["local_ftp"]["target_dir"],
                                                job_dir, True,
                                                config["local_ftp"]["username"],
                                                config["local_ftp"]["password"],
                                                config["local_ftp"]["ftp"])

        # disable moving folder into archive dir if error occoured
        if ret_code != 0:
            logging.error(
                "ftpsupload_recoursive returned with: " + str(ret_msg))
            logging.error("ftp returned with an ERROR")
            moveto_archive = False

    #################
    # move to archive
    #################

    # move to archive if not fatal error have occoured
    # if fatal error(s) have occoured, folder should remain in tempdir (clean
    # up manually with this script)

    if moveto_archive:
        logging.info("moving to archive")
        try:
            shutil.move(config["temp_path"] + job_dir, config["archive_path"] + job_dir)
        except Exception:
            logging.exception("Fatal Error moving job folder to archive")
    else:
        logging.info("Folder was not moved to archive! Clean up folder: " + config["temp_path"] + job_dir)
        emailmod.send_err("Error while processing job: " + job_dir, str(email_ret), config)

    return 0
