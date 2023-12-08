import logging
import random
import time
from pathlib import Path
from typing import List

from PIL import Image
from RPi import GPIO

from pi_ink.apps.iapp import IApp
from pi_ink.displays import EDisplayResponse, InkyImpressionDisplay
from pi_ink.renderers import ImageRenderer

logger = logging.getLogger(__name__)


class PictureFrame(IApp):
    _btns: List[int] = [
        5,
        6,
        16,
        24,
    ]  # gpio pins for each button (from top btn to bottom btn)
    _btn_names: List[str] = ["A", "B", "C", "D"]  # names for each button
    _pic_dir: Path
    _all_pic_fps: List[Path]
    _cur_pic_fp: Path = None
    _cur_pic_img: Path = None
    _history: List[Path] = []
    _history_cursor: int = 0
    _history_limit: int = 1000
    _t0: float = 0.0
    _t1: float = 0.0
    _do_update: bool = True
    _timer_paused: bool = False
    _display_busy: bool = False

    def btn_busy_ignore(fn):
        """
        Decorator that ignores button presses if the display is busy.
        """

        def wrapper(self, *args, **kwargs):
            if self._display_busy:
                logger.info("display busy, ignoring button press")
                return
            fn(self, *args, **kwargs)

        return wrapper

    @btn_busy_ignore
    def __handle_btn_a(self):
        logger.info("btn a -> requesting next picture")
        self._cur_pic_fp, self._cur_pic_img = self.__next_picture()
        self._do_update = True
        self.__reset_timer()

    @btn_busy_ignore
    def __handle_btn_b(self):
        logger.info("btn b -> requesting prev picture")
        self._cur_pic_fp, self._cur_pic_img = self.__prev_picture()
        self._do_update = True
        self.__reset_timer()

    @btn_busy_ignore
    def __handle_btn_c(self):
        logger.info("btn c -> clearing history")
        self._history = [self._cur_pic_fp]
        self._history_cursor = 0

    @btn_busy_ignore
    def __handle_btn_d(self):
        logger.info("btn d -> toggle timer")
        self._timer_paused = not self._timer_paused
        if self._timer_paused:
            logger.info("timer paused")
        else:
            logger.info("timer unpaused")
            self.__reset_timer()

    _btn_fns = {
        "A": __handle_btn_a,
        "B": __handle_btn_b,
        "C": __handle_btn_c,
        "D": __handle_btn_d,
    }

    def __btn_callback(self, pin):
        btn_name = self._btn_names[self._btns.index(pin)]
        self._btn_fns[btn_name](self)

    def __init__(self, **kwargs):
        GPIO.setmode(GPIO.BCM)  # setups RPI.GPIO to use the BCM pin numbering scheme

        # btns connect to ground, set them as inputs with pull-up resistors
        GPIO.setup(self._btns, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # setup callbacks for each button
        for btn, btn_name in zip(self._btns, self._btn_names):
            GPIO.add_event_detect(
                btn, GPIO.FALLING, callback=self.__btn_callback, bouncetime=250
            )
            logger.info(f"added callback for button {btn_name} on pin {btn}")

        # create path relative to this file and one level up
        self._pic_dir = Path(__file__).parent.parent / "photos"
        self._all_pic_fps = [
            fp
            for fp in self._pic_dir.iterdir()
            if fp.is_file() and fp.suffix in [".JPG", ".jpg", ".png"]
        ]

    def __next_picture(self) -> (Path, Image):
        # check if cursor is at the end of the history
        if len(self._history) == 0 or self._history_cursor == len(self._history) - 1:
            logger.info("getting random picture")
            # get a random picture
            fp, img = self.__get_random_picture()
            self._history.append(fp)

            # if this is the first picture in the history, set the cursor to 0
            # otherwise, increment the cursor
            #
            # only need to do this check for the next picture, and not the previous picture, method
            if len(self._history) == 1:
                self._history_cursor = 0
            else:
                self._history_cursor += 1

            # if the history is longer than history limit, remove the oldest picture
            if len(self._history) > self._history_limit:
                self._history.pop(0)

            return fp, img

        # otherwise, get the next picture in the history
        logger.info(
            "getting next picture from history",
            extra={
                "history_cursor": self._history_cursor,
                "history_cursor_next": self._history_cursor + 1,
                "current_cursor_fname": self._history[self._history_cursor].name,
                "next_cursor_fname": self._history[self._history_cursor + 1].name,
            },
        )
        self._history_cursor += 1
        fp = self._history[self._history_cursor]
        img = Image.open(fp)
        return fp, img

    def __prev_picture(self) -> (Path, Image):
        # check if cursor is at the beginning of the history
        if len(self._history) == 0 or self._history_cursor == 0:
            logger.info("getting random picture")

            # if the history is longer than history limit, remove the oldest picture
            #
            # important [for prev only] that this is done before to ensure that we don't remove the previous picture we
            # are adding at the begging of the history
            if (len(self._history) + 1) > self._history_limit:
                self._history.pop(0)

            # get a random picture
            fp, img = self.__get_random_picture()
            self._history.insert(0, fp)
            return fp, img

        # otherwise, get the previous picture in the history
        logger.info(
            "getting next picture from history",
            extra={
                "history_cursor": self._history_cursor,
                "history_cursor_prev": self._history_cursor - 1,
                "current_cursor_fname": self._history[self._history_cursor].name,
                "prev_cursor_fname": self._history[self._history_cursor - 1].name,
            },
        )
        self._history_cursor -= 1
        fp = self._history[self._history_cursor]
        img = Image.open(fp)
        return fp, img

    def __get_random_picture(self) -> (Path, Image):
        fp = random.choice(self._all_pic_fps)

        if self._cur_pic_fp is not None:
            while (
                fp == self._cur_pic_fp
            ):  # make sure we don't get the same picture twice in a row
                fp = random.choice(self._all_pic_fps)

                # attempt to get a picture that is not in the history only if the history is smaller than
                # the total number of pictures
                if 0 < len(self._history) < len(self._all_pic_fps):
                    logger.info(
                        "attempting to get a picture that is not in the history"
                    )
                    new_attempt = 0
                    shrinking_all_pic_fps = self._all_pic_fps
                    while (
                        fp in self._history
                        and new_attempt < 10
                        and len(shrinking_all_pic_fps) > 0
                    ):
                        fp = random.choice(self._all_pic_fps)
                        # not the most efficient, but works
                        shrinking_all_pic_fps = [
                            fp for fp in shrinking_all_pic_fps if fp != fp
                        ]
                        new_attempt += 1
                    logger.info(
                        f"attempted {new_attempt} times to get a picture that is not in the history"
                    )

        img = Image.open(fp)
        return fp, img

    def __reset_timer(self):
        self._t0 = time.time()
        self._t1 = self._t0

    def run(self, **kwargs):
        img_renderer = ImageRenderer()
        display = InkyImpressionDisplay()
        change_picture_interval = 60 * 3  # in seconds

        while True:
            if not self._timer_paused:
                self._t1 = time.time()

            if self._t1 - self._t0 >= change_picture_interval:
                self._do_update = True

                # not necessary but will ensure we don't get stuck in a loop continually trying to update the display

                logger.info("changing picture")
                self._cur_pic_fp, self._cur_pic_img = self.__next_picture()
                self.__reset_timer()

            if not self._do_update:
                continue

            logger.info(
                f"displaying picture {self._cur_pic_fp.name}",
                extra={
                    "history_cursor": self._history_cursor,
                    "history_size": len(self._history),
                    "timer_paused?": self._timer_paused,
                },
            )

            self._display_busy = True
            frame = img_renderer.render_picture_frame(self._cur_pic_img)
            sat = kwargs.get("saturation", 0.5)
            dynamic_saturation = kwargs.get("dynamic_saturation", False)
            logger.info(
                f"displaying frame [saturation={sat}, dynamic_saturation={dynamic_saturation}]"
            )
            display.set_frame(
                frame, saturation=sat, dynamic_saturation=dynamic_saturation
            )
            res = display.display_frame()

            if res.response == EDisplayResponse.ERROR:
                logger.error(f"error displaying frame: {res.value}")
                break

            if res.response == EDisplayResponse.NOT_READY:
                logger.info(f"display not ready, waiting {res.value}s")
                time.sleep(res.value)
                continue

            self._do_update = False
            self._display_busy = False
            self.__reset_timer()  # reset timer
