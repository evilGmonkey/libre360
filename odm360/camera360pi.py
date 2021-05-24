import os
import time
import logging
import json
import requests
import psycopg2
import uuid
import subprocess

logger = logging.getLogger(__name__)
from datetime import datetime

# import odm360 methods and functions
from odm360.timer import RepeatedTimer
from odm360 import dbase

# connect to child database
db = "dbname=odm360 user=odm360 host=localhost password=zanzibar"
conn = psycopg2.connect(db)
cur = conn.cursor()

# get the uuid of the device
try:
    cur.execute("SELECT * FROM device")
    device_uuid, device_name = cur.fetchone()
except:
    device_uuid, device_name = str(uuid.uuid4()), "dummy"
try:
    from picamera import PiCamera
except:

    class PiCamera:
        def __init__(self):
            pass


class Camera360Pi(PiCamera):
    """
    This class is for increasing the functionalities of the Camera class of PiCamera specifically for
    the 360 camera use case.
    """

    def __init__(
        self,
        state,
        logger=logger,
        debug=False,
        host=None,
        port=None,
        project_id=None,
        project_name=None,
        n_cams=None,
        dt=None,
    ):
        self.debug = debug
        self.state = state
        self.timer = None
        self._device_uuid = device_uuid
        self._device_name = device_name
        self._root = "photos"
        self._project_id = project_id  # project_id for the entire project from parent
        self._project_name = project_name  # human-readable name
        self._n_cams = n_cams  # total amount of cameras related to this project
        self._dt = dt  # time intervals requested by parent
        self.src_fn = None  # path to currently made photo (source) inside the camera
        self.dst_fn = ""  # path to photo (destination) on drive
        self.logger = logger
        self.host = host
        self.port = port
        if not (os.path.isdir(self._root)):
            os.makedirs(self._root)
        super().__init__()
        # now set the resolution explicitly. If you do not set it, the camera will fail after first photo is taken
        self.resolution = (2028, 1520)

    def init(self):
        try:
            if not (self.debug):
                self.start_preview()
                # camera may need time to warm up
                time.sleep(2)
            msg = "Raspi camera initialized"
            self.logger.info(msg)
            self.state["status"] = "ready"
        except:
            msg = "Raspi camera could not be initialized"
            self.state["status"] = "broken"
            self.logger.error(msg)
        return {"msg": msg, "level": "info"}

    def wait(self):
        """
        Basically do not do anything, just let the server know you understood the msg
        """
        msg = "Raspi camera will wait for further instructions"
        self.logger.debug(msg)  # better only show this in debug mode
        return {"msg": msg, "level": "debug"}

    def exit(self):
        self.stop_preview()
        self.state["status"] = "idle"
        msg = "Raspi camera shutdown"
        self.logger.info(msg)
        return {"msg": msg, "level": "info"}

    def stop(self):
        if self.timer is not None:
            try:
                self.timer.stop()
            except:
                pass
            self.state["status"] = "ready"
            msg = "Camera capture stopped"
        else:
            msg = "No capturing taking place, do nothing"
        self.logger.info(msg)
        return {"msg": msg, "level": "info"}

    def capture(self, timeout=1.0, cur=cur):
        # FIXME: store photos file based in minio bucket
        root_dir = "/home/pi/piimages"
        photo_uuid = uuid.uuid4()
        photo_prefix = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        photo_filename = f"{self._device_uuid}/{self._project_id}/{self._survey_run}/{photo_prefix}.jpg"
        target = os.path.join(root_dir, "tmp.jpg")
        # capture to local file
        self.logger.info(f"Writing to {target}")
        # prepare kwargs for database insertion
        tic = time.time()
        kwargs = {
            "photo_uuid": photo_uuid,
            "project_id": self._project_id,
            "survey_run": self._survey_run,
            "device_uuid": self._device_uuid,
            "device_name": self._device_name,
            "photo_filename": photo_filename,
            "timestamp": datetime.utcfromtimestamp(time.time()),
            "fn": target,
        }
        if not (self.debug):
            super().capture(target, "jpeg")
        # # store details about photo in database
        dbase.insert_photo(cur, **kwargs)

        # Update the last time of request
        self.state["req_time"] = time.time()
        toc = time.time()
        # self.state['last_photo'] = target
        self.logger.debug(f"Photo took {toc-tic} seconds to take")
        # FIXME: Change the message information posted to parent, so that  photo can be logged entirely to database
        post_capture = {
            "kwargs": {"msg": f"Taken photo {photo_filename}", "level": "info"},
            "req": "LOG",
            "state": self.state,
        }
        self.post(
            post_capture
        )  # this just logs on parent side what happened on child side

    def capture_continuous(self, start_time=None, survey_run=None, project=None):
        # FIXME alter to new model: receiving a serialized survey object of following example:
        # {
        #     "kwargs": {
        #         "id": 5,
        #         "project": {
        #             "dt": 4,
        #             "id": 1,
        #             "n_cams": 1,
        #             "name": "dar",
        #             "status": 1
        #         },
        #         "project_id": 1,
        #         "timestamp": "2021-05-24 16:41:32"
        #     },
        #     "task": "capture_continuous"
        # }
        self._project_id = int(project["project_id"])
        self._project_name = project["project_name"]
        self._dt = int(project["dt"])
        self._n_cams = int(project["n_cams"])
        self._survey_run = survey_run
        # import pdb;pdb.set_trace()
        self.logger.info(
            f"Starting capture for project - id: {self._project_id} name: {self._project_name} interval: {self._dt} secs survey run {self._survey_run}."
        )
        try:
            self.timer = RepeatedTimer(
                int(project["dt"]), self.capture, start_time=start_time
            )
            self.state["status"] = "capture"
        except:
            msg = "Camera not responding or disconnected"
            logger.error(msg)
        msg = f"Camera is now capturing every {self._dt} seconds"
        logger.info(msg)
        return {"msg": msg, "level": "info"}

    def capture_stream(self):
        """
        Done with a raspivid command so the camera has to be stopped first, and then a cvlc command has to be opened and streamed
        :return:
        """
        # stop any preview and change resolution to HD
        self.stop_preview()
        self.resolution = (1920, 1080)

        # self.recording = Thread(target=self._video, args=()).start()
        vlc_cmd = "cvlc -vvv stream:///dev/stdin --sout #standard{access=http,mux=ts,dst=:8554/stream} :demux=h264"
        cmdline = vlc_cmd.split()

        # open pipe to vlc
        self.myvlc = subprocess.Popen(cmdline, stdin=subprocess.PIPE)
        self.start_recording(self.myvlc.stdin, format="h264", bitrate=3000000)
        # give camera 2 seconds to start up
        time.sleep(2)
        self.state["status"] = "stream"
        self.logger.info("Camera is streaming")
        msg = "Camera streaming started"
        self.logger.info(msg)
        return {"msg": msg, "level": "info"}

    def stop_stream(self):
        try:
            # first stop the camera
            self.stop_recording()
            # then stop the stream
            self.myvlc.stdin.close()
            # finally kill the vlc process
            self.myvlc.terminate()
            # get ready for capturing
            self.resolution = (2028, 1520)
            # start warming up again
            self.start_preview()
            time.sleep(2)
        except:
            pass
        self.state["status"] = "ready"
        msg = "Camera streaming stopped"
        self.logger.info(msg)
        return {"msg": msg, "level": "info"}

    def post(self, msg):
        """

        :param msg: dict
        :return:
        """
        headers = {"Content-type": "application/json"}
        r = requests.post(
            f"http://{self.host}:{self.port}/picam",
            data=json.dumps(msg),
            headers=headers,
        )
