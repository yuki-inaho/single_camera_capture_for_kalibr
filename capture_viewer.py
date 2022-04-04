import os
import cvui
import cv2
import click
import numpy as np
import time
import datetime
from threading import Thread, RLock
from pathlib import Path
import pdb


SCRIPT_DIR = str(Path(__file__).parent)


def get_date():
    now = datetime.datetime.today()
    date = str(now.year) + "-" + str(now.month) + "-" + str(now.day) \
        + "-" + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
    return date


class Viewer(object):
    def __init__(self, camera_id, dir_name, image_width, image_height, fps, mjpg_capturing_mode):
        self._rgb_img = None
        self._stopped = False

        self._rgb_dir = os.path.join(dir_name, "cam0")
        self._setting(camera_id, image_width, image_height, fps, mjpg_capturing_mode)

    def _setting(self, camera_id, image_width, image_height, fps, mjpg_capturing_mode):
        if camera_id == '':
            self._cam = cv2.VideoCapture(0)
        elif camera_id.isdigit():
            self._cam = cv2.VideoCapture(int(camera_id))
        else:
            self._cam = cv2.VideoCapture(camera_id)
        if mjpg_capturing_mode:
            self._cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._cam.set(cv2.CAP_PROP_FPS, fps)
        self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, image_width)
        self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, image_height)

        os.makedirs(self._rgb_dir)
        self._file_count = len(os.listdir(self._rgb_dir))
        self._lock = RLock()
        self._status = False

    def _start(self):
        self._thread_ = Thread(target=self._update, args=())
        self._thread_.daemon = True
        self._thread_.start()

    def _update(self):
        while True:
            if self._stopped:
                return
            with self._lock:
                (self._status, self._rgb_img) = self._cam.read()

    def _save_image(self):
        timestamp = time.time_ns()
        save_name = str(timestamp) + ".png"
        with self._lock:
            cv2.imwrite(os.path.join(self._rgb_dir, save_name), self._rgb_img)
        print("captured")
        self._file_count += 1

    def _cvui_gui(self, frame):
        if self._status:
            rgb_resize = cv2.resize(self._rgb_img.copy(), (1280, 720))
            frame[:720, :1280, :] = rgb_resize
        if cvui.button(frame, 10, 800, 200, 50, "capture image") and self._status:
            self._save_image()
        cvui.text(frame, 300, 800, 'Image Num = {}'.format(self._file_count), 0.5)

    def run(self):
        WINDOW_NAME = "viewer"
        self._start()
        cvui.init(WINDOW_NAME)

        frame = np.zeros((960, 1280, 3), np.uint8)
        while True:
            frame[:] = (49, 52, 49)
            cvui.text(frame, 10, 10, 'See3CAM', 0.5)
            k = cv2.waitKey(10)
            if k == 27 or k == ord('q'):
                self._stopped = True
                break
            elif k == ord('s'):
                self._save_image()
            self._cvui_gui(frame)
            cvui.imshow(WINDOW_NAME, frame)
        cv2.destroyAllWindows()


@click.command()
@click.option('--save-dir', '-s', default='{}/images'.format(SCRIPT_DIR))
@click.option('--camera-id', '-c', default='')
@click.option('--image-width', '-w', default=1920)
@click.option('--image-height', '-h', default=1080)
@click.option('--fps', '-f', default=30)
@click.option('--mjpg-capturing-mode', '-m', is_flag=True)
def main(save_dir, camera_id, image_width, image_height, fps, mjpg_capturing_mode):
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    date = get_date()
    print(date)
    dir_name = os.path.join(save_dir, date)

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    viewer = Viewer(camera_id,
                    dir_name,
                    image_width=image_width,
                    image_height=image_height,
                    fps=fps,
                    mjpg_capturing_mode=mjpg_capturing_mode)
    viewer.run()


if __name__ == '__main__':
    main()
