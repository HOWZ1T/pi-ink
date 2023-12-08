from abc import ABC
from typing import Any

from PIL import Image

from pi_ink.spotify import Spotify


class IRenderer(ABC):
    def render_frame(self, spotify: Spotify) -> Any:
        """
        Using spotify data, renders a frame and returns it.

        Args:
            spotify (Spotify): spotify client

        Returns:
            Any: rendered frame
        """
        raise NotImplementedError("render_frame() not implemented")

    def render_picture_frame(self, picture: Image) -> Any:
        """
        Renders a frame from a picture and returns it.

        Args:
            picture (Image): picture to render

        Returns:
            Any: rendered frame
        """
        raise NotImplementedError("render_picture_frame() not implemented")
