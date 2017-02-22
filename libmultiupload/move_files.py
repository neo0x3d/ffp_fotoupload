#! /usr/bin/env python3
"""
Copy files of specific type, delete if successfull if enabled
"""
import logging
import os
import shutil


def move_files(sourcepath, destpath, filetype, del_src):
    """
    Copy files of matching type from sourcepath to destpath, delete files from source

    Args:
        sourcepath: original path to the sd card, where files will be deleted
        destpath: local path where the copied files reside
        filetype: target file types/endings
        del_src: delete files from source after copying (uses move())

    Returns:
        number of files which were copied if successfull
        -1 in the event of an error
    """

    logging.debug("Entered move_files()")
    logging.debug("parameter: " + str(sourcepath) + " " + str(destpath) + " " + str(filetype) + " ")

    try:
        if not os.path.exists(sourcepath):
            logging.error("Sourcepath does not exist: %s", sourcepath)
            return -1
        else:
            src_lst = os.listdir(sourcepath)
            logging.debug("Source dir contains: " + str(src_lst))

            copied_files = []
            for file_to_copy in src_lst:
                logging.debug("analyzing: " + file_to_copy)
                # check also against lowercase version
                if os.path.isfile(os.path.join(sourcepath, file_to_copy)) and file_to_copy.lower().endswith(tuple(filetype)):
                    logging.debug("is file of matching type: " + file_to_copy)
                    # makedirs (jobfolder and image/video folder) if at least
                    # one file of matching type exists
                    if not os.path.exists(destpath):
                        os.makedirs(destpath)
                        logging.debug("makedirs destpath: %s", destpath)

                    shutil.copy2(os.path.join(sourcepath, file_to_copy), destpath)
                    copied_files.append(os.path.join(sourcepath, file_to_copy))
                    logging.debug("copied: %s -> %s", os.path.join(sourcepath, file_to_copy), destpath)
                else:
                    logging.debug("file does not match: " + str(os.path.join(sourcepath, file_to_copy)))

            # delete files from source if no exception occoured while copying
            if del_src:
                for file_to_del in copied_files:
                    os.remove(file_to_del)

    except Exception as exceptmsg:
        logging.exception("Fatal Error in move_files(): " + str(exceptmsg))
        return -1
    if len(copied_files) > 0:
        return len(copied_files)
    else:
        return 0
