#!/usr/bin/env python3
"""
Create thumbnails from images with autotation and EXIF stripping
"""
import logging
import os
import shutil

from PIL import ExifTags, Image


def make_thumbnail(src, dest, filetype, size_px):
    """
    Create thumbnails from image with rotating.
    Strip EXIF date.

    Args:
        src: strig, path to the original file
        dest: path to the not yet existent thumbnail file
        filetype: accepted type (file ending)
        size_px: size of the thumbnail (aspec ration is kept, image is fitted inside this area)

    Returns:
        0 if completed successfull
        -1 in the event of an error
    """

    logging.debug("Entered make_thumbnail()")
    logging.debug("process " + str(os.getpid()) + " arguments: " + str(src) +
                  " " + str(dest) + " " + str(filetype) + " " + str(size_px))

    try:
        logging.debug("checking if path exists: " + os.path.dirname(dest))

        if not os.path.exists(os.path.dirname(dest)):
            logging.debug("dest folder does not exist, creating: " + os.path.dirname(dest))
            os.makedirs(os.path.dirname(dest))
        else:
            logging.debug("dest path exists " + os.path.dirname(dest))

        shutil.copy2(src, dest)

        # also check against lowercase
        if os.path.isfile(dest) and dest.lower().endswith(tuple(filetype)):

            # PIL/pillow will not save EXIF data after modifying image
            # (desired since those images might be shared with press or third party
            # and EXIF data might contain sensitive information (GPS location))
            with Image.open(src) as img:

                logging.debug("opening for thumb creation: " + dest)

                # try:
                logging.debug("process " + str(os.getpid()) + "trying EXIF rotation")


#
#
# I would use orientation = exif.get(orientation, None) and then if orientation is None: return and add some logs that image exif possibly invalid. I am not saying it may cause error to everybody but it happened to me and it may be very rare.
#
##
                #image=Image.open(os.path.join(path, fileName))
                if hasattr(img, '_getexif'):  # only present in JPEGs
                    for orientation in ExifTags.TAGS.keys():
                        if ExifTags.TAGS[orientation] == 'Orientation':
                            break
                    e = img._getexif()       # returns None if no EXIF data
                    if e is not None:
                        exif = dict(e.items())
                        orientation = exif[orientation]

                        if orientation == 3:
                            img = img.transpose(Image.ROTATE_180)
                        elif orientation == 6:
                            img = img.transpose(Image.ROTATE_270)
                        elif orientation == 8:
                            img = img.transpose(Image.ROTATE_90)

                img.thumbnail(size_px, Image.ANTIALIAS)
                img.save(dest)

                # except AttributeError:
                #    logging.info("image without EXIF data or non jpeg image")
                # except Exception as e:
                #     logging.warning(
                #         "some other error while trying to rotate thumbnail ???" + str(e))
        logging.info("Created thumbnail: " + dest)
        return 0

    except Exception as exceptmsg:
        logging.exception("Fatal Error in image_thumbnails(): " + str(exceptmsg))
        return -1

        # for orientation in ExifTags.TAGS.keys():
        #     if ExifTags.TAGS[orientation] == 'Orientation':
        #         break
        # exif = dict(img._getexif().items())
        # logging.debug(
        #     "process " + str(os.getpid()) + " got EXIF data")
        # if exif[orientation] == 3:
        #     logging.debug("rotating 180")
        #     img = img.rotate(180, expand=True)
        # elif exif[orientation] == 6:
        #     logging.debug("rotating 270")
        #     img = img.rotate(270, expand=True)
        # elif exif[orientation] == 8:
        #     logging.debug("rotating 90")
        #     img = img.rotate(90, expand=True)
        # logging.debug("process " + str(os.getpid()) + " rotated")
        # img.thumbnail(size_px, Image.ANTIALIAS)
        # logging.debug("resized")
        # img.save(dest)
        # logging.debug("saved")
