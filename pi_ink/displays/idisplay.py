from abc import ABC
from typing import Any

from .display_result import DisplayResult


class IDisplay(ABC):
    def set_frame(
        self, frame: Any, saturation: float = 0.5, dynamic_saturation: bool = False
    ) -> None:
        """
        Sets the frame to be displayed.

        Args:
            frame (Any): frame to be displayed
            saturation (float): the saturation of the frame. Defaults to 0.5
            dynamic_saturation (bool): whether to dynamically adjust the saturation of the frame. Defaults to False
        """
        raise NotImplementedError("set_frame() not implemented")

    def display_frame(self) -> DisplayResult:
        """
        Displays the frame.
        """
        raise NotImplementedError("display_frame() not implemented")

    def clear_frame(self) -> None:
        """
        Clears the frame.
        """
        raise NotImplementedError("clear_frame() not implemented")
