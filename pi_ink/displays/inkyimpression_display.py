import logging
import time

from inky.auto import auto
from PIL import Image

from .display_result import DisplayResult
from .edisplay_response import EDisplayResponse
from .idisplay import IDisplay

logger = logging.getLogger(__name__)


class InkyImpressionDisplay(IDisplay):
    _last_update: float = 0
    _screen_refresh_time: float = 15  # in seconds
    _frame: Image = None
    _display = None

    def __init__(self):
        self._display = auto()

    @staticmethod
    def _normalize_rgb(r: int, g: int, b: int) -> (float, float, float):
        assert (
            0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255
        ), "r, g, b must be in standard range [0, 255]"
        return float(r) / 255.0, float(g) / 255.0, float(b) / 255.0

    @staticmethod
    def _get_luminosity(r: float, g: float, b: float) -> float:
        assert (
            0 <= r <= 1 and 0 <= g <= 1 and 0 <= b <= 1
        ), "r, g, b must be in normalized [0, 1]"
        return 0.5 * (max(r, g, b) + min(r, g, b))

    @staticmethod
    def _get_saturation(r: float, g: float, b: float) -> float:
        assert (
            0 <= r <= 1 and 0 <= g <= 1 and 0 <= b <= 1
        ), "r, g, b must be in normalized [0, 1]"
        l = InkyImpressionDisplay._get_luminosity(r, g, b)
        if l == 0 or l == 1:
            return 0

        return (max(r, g, b) - min(r, g, b)) / (1 - abs(2 * l - 1))

    def set_frame(
        self, frame: Image, saturation: float = 0.5, dynamic_saturation: bool = False
    ) -> None:
        if self._frame is not None:
            del self._frame  # del previous frame's image resource
        self._frame = frame

        if dynamic_saturation:
            # TODO
            pass

        self._display.set_image(self._frame, saturation=saturation)

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
