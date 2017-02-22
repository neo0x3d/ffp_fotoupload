#! /usr/bin/env python3
"""
Module to generate a html table of images fro a list of filenames.
Media source and colums can be adjusted.
"""
import logging
import os


# slice list in multiple lists with sublen as lengh
def row_major(slist, sublen):
    """
    Generate a list of lists (with sublen as lengh) from a simple list
    """
    return [slist[i:i + sublen] for i in range(0, len(slist), sublen)]


# create a simple html table with links to the content
def html_table(lists, img_weblink, job_dir):
    """
    Generate a html table with embedded images from an image list
    """
    table_text = "<table width=\"400px\"><tbody>\n"
    for sublist in lists:
        table_text += "<tr>\n"
        for img in sublist:
            logging.debug("adding to html table: " + img)

            # images are accessible via a weblink after remote_ftp upload
            #filelink = config["email"]["weblink"] + job_dir + "/" + nr
            filelink = img_weblink + job_dir + "/" + img
            table_text += "<td><a href=\"{}\">{}<br/><img style=\"max-width:40%;\" src=\"{}\" /></a></td>\n".format(
                filelink, img, filelink)
        table_text += "</tr>\n"
    table_text += "</tbody></table>\n"
    return table_text


def email_text_html(config, htmltext_header, htmltext_footer, img_weblink, img_path, job_dir):
    """
    Generate a full html file to be sent as email
    """
    # htmltext = config["email"]["header_html"]
    htmltext = htmltext_header
    htmltext += "Die Originalaufnahmen sind in wenigen Minuten <a href=\"{}/{}.zip\">hier</a> abrufbar.".format(
        img_weblink + job_dir, job_dir)
    # thumbnail images
    if config["image_thumbnail"]["enable"]:
        if os.path.exists(img_path):
            images = os.listdir(img_path)
            #htmltext.append("Image ZIP: %s")
            htmlret = html_table(row_major(images, 3), img_weblink, job_dir)
            htmltext += htmlret
    #htmltext += config["email"]["footer_html"]
    htmltext += htmltext_footer
    return htmltext
