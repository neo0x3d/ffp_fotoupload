# FFP_Fotoupload

# This project has been moved to Gitlab: <https://gitlab.com/users/neo0x3d/projects>

[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://img.shields.io/badge/License-GPL%20v2-blue.svg)

Note: This is under heavy development and currently not all necessary files are released!

This is an upload script/toolkit, used to process and upload images from removable media with minimal user interaction.

**Abstract**

- accept a folder or block device partition as source
- copy files of matching file type to local folder, empty removable device
- generate thumbnails from the raw data
- send email via SMTP server containing links to thumbnails
- upload thumbnails and archive of original images to remote servers
- upload everything to local archive server

Besides that

- audio output for user information (over webpage)
- write log
- send error email in the event of a failure (e.g. bug or FTP server offline)

## File/Folder architecture:

bootstrap/ --> methods to start the script<br>
libmultiupload/ --> custom modules<br>
webui/ --> webui to display information via webbrowser and audio output (can run under different user)<br>
ffp_fotoupload.py --> main script<br>
ffp_fotoupload_config.json --> main config file

## Installation and Setup

### Underlying OS

Designed and tested with Fedora 24 and CentOS 7\. Other Linux distributions may work but have not been tested (some packages might be differently named e.g. Python3 PIL and Pillow).

Basic CentOS 7 example setup can be found in another repo: [CentOS7_setup.md]([a link](https://github.com/neo0x3d/ffp_infoscreen/blob/master/CentOS7_setup.md)

### Setup: user account (if needed)

**IMPORTANT NOTE:** The script will contain some sensitive data (ftp/imap user and password e.g) across the config files. Access to these files should be controlled (set owner and group, set permissions to 700) and no auto login should be performed. If this computer is also used as multimonitor infoscreen, use a separate user with auto login, which has no access to these files.

(e.g. FTP user with a chroot jail and write only permissions)

Add a user and log in afterwards

```
$ sudo useradd fotoupload
```

Do not use the user account as automatic log in! use separate for script set permissions to 700

### Clone repository from Github

Clone github repo to /home/$USER/ffp_fotoupload

```
$ git clone https://github.com/neo0x3d/ffp_fotoupload /home/fotoupload/
```

Modify permissions:

```
$ chmod 700 -R /home/$USER/ffp_fotoupload
```

### Install Dependencies: (Fedora 25 / CentOS 7)

Following packages need to be installed (and running if they are a daemon):

1. SMTP server (e.g. postfix)
2. Python3
3. python3-pillow
4. udiskie

```
$ sudo pip3 install requirements.txt
```

### Configure main script

- ffp_fotoupload.py: Set config file path in to the ffp_fotoupload_config.py (use full path, this is the only modification required in this file)

- ffp_fotoupload_config.json: Needs to be configured before start, it will hold all mandatory information required for running.

### Setup starting method

The program can either run once (and work on one job) or as daemon in the background (and receive jobs over a http server).

If running as daemon, jobs can be accepted the following ways:

1. upon SD card plugging via udev [bootstrap/udev](/boostrap/udev/UDEV.md)
2. automatic email downloader script, see [bootstrap/email_scraper](/bootstrap/email_scraper/EMAIL_SCRAPER.md)
3. Physical Arduino button + DE Application Shortcut [bootstrap/arduino_button](/bootstrap/arduino_button/ARDUINO_SETUP.md)
4. over a raw POSt request (e.g. via curl: $curl --data "&enable=true&source=/dir/to/folder/")
