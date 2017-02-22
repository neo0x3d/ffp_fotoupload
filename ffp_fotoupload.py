#! /usr/bin/env python3
"""
FFP_Fotoupload

Receive media (images & videos) from various sources (email, mmc reader, local folder),
process them (image rotation, rescaling) and upload them to various ftps servers.
"""
# Author: Marius Pfeffer (neo0x3d)
# License: MIT

import argparse
import json
import logging
import multiprocessing
import os
import threading
import time
from datetime import datetime

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
from mutagen.mp3 import MP3

from libmultiupload import analyze_source, upload_routine

################################################################################
# global config
################################################################################

if __name__ == "__main__":
    # set json config file (use full path !)
    with open("ffp_fotoupload_config.json") as config_fh:
        config = json.load(config_fh)

    # set timestamp format
    timestamp = datetime.now().strftime(config["timestamp"])

    # set logging
    logfile = config["log"]["path"] + timestamp + ".log"
    loggerinstance = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG,
                        filename=logfile,
                        format='%(asctime)s %(levelname)s: %(message)s')  # include timestamp
    # https://docs.python.org/2/library/logging.html?highlight=logging#integration-with-the-warnings-module
    logging.captureWarnings(True)
    # needs warning module?

    loggerinstance = logging.getLogger(__name__)
    loggerinstance.info("Start of logfile: " + timestamp)


################################################################################
# set possible cli arguments
################################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Source path for upload")  # directory
    parser.add_argument("--daemon", action='store_true', help="Run as a daemon with http server")
    args = args = parser.parse_args()


################################################################################
# daemon processes
################################################################################

def analyzer_proc(analyze_q, job_q, status_q):
    """
    Analyzer routine (analyze source, copy to local machine)

    Args:
        analyze_q: queue for elements to be analyzed
        job_q: queue for elements to be treated by the uploader process pool
        status_q: status queue for the webui
    """
    logging.debug("process working: " + str(os.getpid()))
    while True:
        to_analyze = analyze_q.get(True)
        #print (os.getpid(), "analyzer: ", str(to_analyze))
        logging.debug(str(os.getpid()) + " got from analyze_queue: " + str(to_analyze))
        joblist = analyze_source.analyze_move_userfeedback(to_analyze, status_q, config)
        for job in joblist:
            job_q.put(job)
            logging.debug("analyzed, put into job queue: " + str(job))


def upload_proc(job_q):
    """
    Uploader routine (take data from lokal folder, process it and upload it)

    Args:
        job_q: queue for the jobs to work on
    """
    logging.debug("process working: " + str(os.getpid()))
    while True:
        job = job_q.get(True)  # wait until an element is present
        #print (os.getpid(), " uploader: ", str(job))
        logging.debug(str(os.getpid()) + " received job: " + str(job))
        ret = upload_routine.upload_routine(job, config)
        if ret == 0:
            logging.info("processing job: " + str(job) + "was successfull")
        else:
            logging.warning("processing job: " + str(job) + "returned != 0")


# start job queue and pool of workers
if __name__ == '__main__':
    analyze_queue = multiprocessing.Queue()  # analyzing queue for incomming jobs
    job_queue = multiprocessing.Queue()  # job queue for working and uploading
    status_queue = multiprocessing.Queue()  # statur for the webui
    proc_pool = multiprocessing.Pool(1, analyzer_proc, (analyze_queue, job_queue, status_queue,))
    upload_pool = multiprocessing.Pool(1, upload_proc, (job_queue,))


################################################################################
# process cli arguments
################################################################################

if __name__ == "__main__":
    if args.source and not args.daemon:
        logging.info("sarting in single upload mode")
        analyze_queue.put(args.source)

    elif args.daemon and not args.source:
        logging.info("starting in daemon mode")
    else:
        logging.error("Invalid startup mode defined")
        exit(1)


################################################################################
# http server for daemon
################################################################################

async_mode = 'threading'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    main GET/POST handler to deliver html page and receive upload commands
    """
    if request.method == "GET":
        return render_template('webui.html', async_mode=socketio.async_mode)
    elif request.method == "POST":
        # POST request, used to queue an upload
        # print(str(request.form["upload"]))
        analyze_queue.put(request.form["upload"])
        return '', 204
    else:
        logging.warning("Bad Request: " + str(request.form))
        return '', 400


@app.route('/audio/<path:filename>')
def upload_file(filename):
    """
    deliver audio files from folder
    """
    return send_from_directory(config["audio"]["path"],
                               filename, as_attachment=True)


@socketio.on('uploadcmd')
def proc_upload_cmd(message):
    """
    receive upload command from html site, add it to the analyzer queue,
    """
    analyze_queue.put(message['upload'])
    logging.debug("uploadcmd received: " + message['upload'])


def update_webui():
    """
    Get updates for the user from a queue and send them to the webui.
    Wait until the audio file has played before playing the next.
    """
    while True:
        status = status_queue.get(True)
        logging.debug("status: " + str(status))

        if status.startswith("start"):
            socketio.emit('status_text', {'data': 'gestartet', 'color': 'orange'}, broadcast=True)
            socketio.emit('play_audio', {'audiofile': 'audio/' + config['audio']['started']}, broadcast=True)
            socketio.emit('server_log', {'data': 'Job(s) angenommen: ' +
                                         status.split('#')[1]}, broadcast=True)
            audio_mp3 = MP3(os.path.join(config['audio']['path'], config['audio']['started']))
            time.sleep(audio_mp3.info.length + 1)

        elif status.startswith("end"):
            socketio.emit('status_text', {'data': 'Fertig', 'color': 'limegreen'}, broadcast=True)
            socketio.emit('play_audio', {'audiofile': 'audio/' +
                                         config['audio']['finished']}, broadcast=True)
            socketio.emit('server_log', {'data': 'Letzten Job bendet: ' +
                                         status.split('#')[1]}, broadcast=True)
            audio_mp3 = MP3(os.path.join(config['audio']['path'], config['audio']['finished']))
            time.sleep(audio_mp3.info.length + 1)

        elif status == "error_source":
            socketio.emit('play_audio', {'audiofile': 'audio/' + config['audio']['error']}, broadcast=True)
            socketio.emit('server_log', {'data': 'Fehler bei: ' + status}, broadcast=True)
            audio_mp3 = MP3(os.path.join(config['audio']['path'], config['audio']['error']))
            time.sleep(audio_mp3.info.length + 1)
        else:
            logging.error("internal status code not known")


# start webui update thread and flask socketio server
if __name__ == "__main__" and args.daemon:
    logging.debug("starting http daemon")
    update_webui_thread = threading.Thread(target=update_webui)
    update_webui_thread.start()
    socketio.run(app, host=config["http_server"]["host"], port=config["http_server"]["port"])
