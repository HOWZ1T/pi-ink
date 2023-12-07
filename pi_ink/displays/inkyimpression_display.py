import logging
import time
from PIL import Image
from .display_result import DisplayResult
from .edisplay_response import EDisplayResponse
from .idisplay import IDisplay
from inky.auto import auto

logger = logging.getLogger(__name__)


class InkyImpressionDisplay(IDisplay):
    _last_update: float = 0
    _screen_refresh_time: float = 15  # in seconds
    _frame: Image = None
    _display = None

    def __init__(self):
        self._display = auto()

    def set_frame(self, frame: Image) -> None:
        if self._frame is not None:
            del self._frame  # del previous frame's image resource

        self._frame = frame
        self._display.set_image(self._frame)

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

        # draw frame
        self._display.show()

        return DisplayResult(
            response=EDisplayResponse.SUCCESS,
            value=None,
        )

    def clear_frame(self) -> None:
        del self._frame
        self._frame = None
