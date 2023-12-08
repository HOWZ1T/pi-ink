import logging
import time
from tkinter import Label, Tk

from PIL import Image, ImageTk

from .display_result import DisplayResult
from .edisplay_response import EDisplayResponse
from .idisplay import IDisplay

logger = logging.getLogger(__name__)


class TkinterEinkMockDisplay(IDisplay):
    _last_update: float = 0
    _screen_refresh_time: float = 15  # in seconds
    _frame: Image = None
    _root: Tk = None
    _label: Label = None

    def __init__(self):
        self._root = Tk()
        self._root.title("[MOCK] E-Ink Display")
        self._root.geometry("600x448")
        self._root.configure(background="pink")

        # add label
        self._label = Label(self._root)
        self._label.place(x=0, y=0, width=600, height=448)

    def set_frame(
        self, frame: Image, saturation: float = 0.5, dynamic_saturation: bool = False
    ) -> None:
        if self._frame is not None:
            del self._frame  # del previous frame's image resource

        self._frame = frame

    def display_frame(self) -> DisplayResult:
        now = time.time()
        delta = now - self._last_update
        if delta < self._screen_refresh_time:
            return DisplayResult(
                response=EDisplayResponse.NOT_READY,
                value=self._screen_refresh_time
                - delta,  # remaining wait time until screen is ready
            )  # cannot update screen yet

        logger.info(f"displaying frame")
        self._last_update = now

        if self._frame is None:
            return DisplayResult(
                response=EDisplayResponse.ERROR, value="no frame to display"
            )

        # draw image onto Tk Window
        img_tk = ImageTk.PhotoImage(self._frame)
        self._label.configure(image=img_tk)
        self._root.update_idletasks()
        self._root.update()

        return DisplayResult(
            response=EDisplayResponse.SUCCESS,
            value=None,
        )

    def clear_frame(self) -> None:
        del self._frame
        self._frame = None
