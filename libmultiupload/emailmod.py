#!/usr/bin/env python3
"""
Collection of different email functions (generic and error email)
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send(sender, recipient, recipient_cc, recipient_bcc, subject, text, text_html):
    """
    Send email

    Args:
        sender:
        recipient:
        recipient_cc:
        recipient_bcc:
        email_subject: subject for the email
        email_text: text for the email to send

    Depends:
        local mail transfer agent (e.g. postfix) is required
    """

    logging.debug("Entered send_mail()")

    message = MIMEMultipart('alternative')
    message['From'] = sender
    message['To'] = ",".join(recipient)
    message['Cc'] = 'RecipientCc ' + ",".join(recipient_cc)
    message['Bcc'] = 'RecipientBcc ' + ",".join(recipient_bcc)
    message['Subject'] = str(subject)

    textpart = MIMEText(str(text), 'plain')
    message.attach(textpart)

    if text_html != "":
        htmlpart = MIMEText(str(text_html), 'html')
        message.attach(htmlpart)
    msg_full = message.as_string()

    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, recipient + recipient_cc + recipient_bcc, msg_full)
        logging.info("Sent email to: " + str(recipient) + "subject: " + subject)
        return 0

    except Exception as exceptmsg:
        logging.exception("Error sending mail :(, " + str(exceptmsg))
        return -1


def send_err(subject, text, config):
    """
    Send error email
    """
    if config["err_email"]["enable"]:
        logging.info("Sending error email with subject: " + subject)
        send(config["err_email"]["sender"], config["err_email"]["recipient"], [], [], subject, text, "")
    else:
        logging.info("Sending error email is disabled in config file")
