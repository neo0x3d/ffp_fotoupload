#!/usr/bin/env python3
"""
FTPS upload module for uploading specific files (recoursively) via FTP SSL/TLS
Uploads the files (of matching type if enabled) of a folder to a remte server. Recourive upload possible.
"""
import ftplib
import logging
import os


# TODO
# redo eror mail


def ftpsupload(config, localpath, filetype, remote_basedir, remotefoldername, enable_recursive, ftps_usr, ftps_passwd, ftps_ip):
    """
    Upload recursive/non-recursive files matching type from a folder to a target
    directory on a FTP server

    Args:
        localpath: path which holds elements to upload
        filetype: type of files to upload (leave empty to disable)
        remote_basedir: remote folder on FTP server
        remotefoldername: job folder name
        enable_recursive: enable or disable resoursive upload
        FTPusername: FTP username
        FTPpasswd: FTP password
        FTPIP: IP adress of the ftps server

    Returns:
        0: everything ok
        -1: some error occoured
    """

    logging.debug("Entered ftpsupload_recoursive()")
    try:
        ftps = ftplib.FTP_TLS(ftps_ip)
        ftps.login(ftps_usr, ftps_passwd)
        ftps.prot_p()          # switch to secure data connection
        logging.info("Logged into FTPS Server: %s, username: %s", ftps_ip, ftps_usr)

        # remote_basedir on server must already exist!
        # for security reasons the ftps account should only have writing
        # permissions to the remote folder name, no other directory, no other permissions,
        # create job specific folder in remote_basedir if not already exists
        logging.info("cwd: " + remote_basedir)
        ftps.cwd(remote_basedir)

        # if ftps server supports mlsd, use it, nlst is maked as deprecated in Python3/ftplib
        # check if remotefoldername exists
        use_mlsd = False
        logging.debug("use mlsd instead nlst: " + str(use_mlsd))

        if use_mlsd:
            remotefoldername_exists = False
            for name, facts in ftps.mlsd(".", ["type"]):
                if facts["type"] == "dir" and name == remotefoldername:
                    logging.debug("isdir: " + name)
                    remotefoldername_exists = True
                    break
            logging.debug("remote state" + str(remotefoldername_exists))
            if remotefoldername_exists:
                logging.debug("folder did exist: " + remotefoldername)
            else:
                ftps.mkd(remotefoldername)
                logging.debug("folder does not exitst, ftps.mkd: " + remotefoldername)
        else:
            # nlst legacy support for ftps servers that do not support mlsd
            # e.g. vsftp
            items = []
            ftps.retrlines('LIST', items.append)
            items = map(str.split, items)
            dirlist = [item.pop() for item in items if item[0][0] == 'd']

            if not remotefoldername in dirlist:
                ftps.mkd(remotefoldername)
                logging.debug("folder does not exitst, ftps.mkd: " + remotefoldername)
            else:
                logging.debug("folder did exist: " + remotefoldername)

        # cwd into job dir
        logging.info("cwd: " + remotefoldername)
        ftps.cwd(remotefoldername)

        def STOR_dir(ftps, path):
            """
            Upload a directory
            """
            logging.debug("Entered STOR_dir: " + path)

            filelist = os.listdir(path)
            logging.debug("filelist in path: " + str(filelist))

            for f_name in filelist:
                f_path = os.path.join(path, f_name)

                # check if f_path is file or dir
                logging.debug("analyzing: " + f_path)

                if os.path.isfile(f_path):
                    logging.debug("is a file: " + f_path)
                    # check if f_path is accepted filetype
                    if not filetype:
                        logging.debug("filetype list empty, disabled type checking")
                        ftps.storbinary('STOR ' + f_name, open(f_path, 'rb'))
                        logging.info("STOR: " + f_name)
                    elif f_path.lower().endswith(tuple(filetype)):
                        logging.debug("file has correct extension: " + f_path)
                        ftps.storbinary('STOR ' + f_name, open(f_path, 'rb'))
                        logging.info("STOR: " + f_name)
                    else:
                        logging.debug("Not correct file extension: " + f_path)

                # check if f_path is dir
                elif os.path.isdir(f_path):
                    logging.debug("is a path: " + f_path)
                    # check if recursive upload is desired
                    if enable_recursive:
                        logging.debug("recursive upload enabled")
                        logging.debug("mkd " + f_name)
                        ftps.mkd(f_name)

                        logging.debug("cwd" + f_name)
                        ftps.cwd(f_name)

                        logging.info("starting recursive call on: " + f_path)
                        STOR_dir(ftps, f_path)

                        logging.debug("cwd ..")
                        ftps.cwd("..")
                    else:
                        logging.debug("recursive disabled")
                else:
                    logging.debug(
                        "recursive upload, element is neither file nor folder")

        logging.info("Starting upload of dir: " + localpath)
        STOR_dir(ftps, localpath)
        ftps.quit()
        logging.info("FTP logout")
        return 0, "success"

    except OSError as exceptmsg:
        if str(exceptmsg) == "[Errno 113] No route to host":
            return -1, "error in ftpsupload_recoursive():\n" + str(exceptmsg) + "\nFTP offline?"
        else:
            return -1, "error in ftpsupload_recoursive():\n" + str(exceptmsg)

    except Exception as exceptmsg:
        return -1, "error in ftpsupload_recoursive():\n" + str(exceptmsg)
