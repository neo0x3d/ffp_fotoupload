#!/usr/bin/env python3
"""
Udiskie helper functions (check if mounted, mount, unmount ...)
"""
import logging
import os
import stat
import subprocess


def check_if_mounted(device):
    """
    Check if a device partition is already mounted.

    Args:
        device: path to the partition (e.g. "/dev/sdb1")

    Retuns:
        mountpoint if mounted
        0 if not mounted
        -1 in the event of an error
    """

    logging.debug("Entered check_if_mounted()")
    try:

        with open("/proc/mounts", "r") as mountfile:  # specific to Linux
            mounted_partitions = mountfile.read()

            for item in mounted_partitions.split("\n"):
                if device in item:
                    logging.debug("Found partition mounted: " + item)
                    snip = item.split()

                    # return mountpoint if it is mounted
                    return snip[1]

            # return 0 if not mounted (not present in /proc/mounts)
            logging.debug("Partition is not mounted: " + device)
            return 0

    except Exception:
        logging.exception("Fatal error in check_if_mounted()")
        return -1


def mount_partition(partition):
    """
    Mount a block device partition and return the mountpoint.
    Check if partition exist before

    Args:
        partition: path to the partition to be mounted (e.g. "/dev/sdb1")

    Retuns:
        mountpoint if successfull
        -1 in the event of an error (or partition does not exist)
    """

    logging.debug("Entered mount_partition()")
    try:
        # check if path exists
        if os.path.exists(partition):
            # check if partition is an existing block device
            if not stat.S_ISBLK(os.stat(partition).st_mode):
                logging.error("partition is not a block device: " + partition)
                return -1
            else:
                logging.debug(
                    "partition is a block device, trying to mount via udiskie-mount")

                # mount at automatic folder (accourding to the label)
                ret = subprocess.check_output(["udiskie-mount", partition],
                                              stderr=subprocess.STDOUT).decode()
                snip = ret.split()
                return snip[3]  # return the mountpoint
        else:
            return -1

    except Exception:
        logging.exception("Fatal error in mount_part()")
        return -1


def umount(mountpoint):
    """
    Unmount a mountpoint and return

    Args:
        mountpoint: mountpoint
    Returns:
        0 if completed successfully
        -1 if an error occoured
    """

    logging.debug("Entered umount()")
    try:
        ret = subprocess.check_output(
            ["udiskie-umount", mountpoint], stderr=subprocess.STDOUT).decode()
        if ret.startswith("unmounted"):
            logging.debug("udiskie-umount returned: " + ret)
        else:
            logging.warning(
                "umount(), udiskie-umount returned without unmounted")
        # return in any case with 0, filesystem corruption may occour
        return 0

    except Exception:
        logging.exception("Fatal error in umount()")
        return -1
