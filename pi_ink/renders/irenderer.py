from abc import ABC
from typing import Any

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
