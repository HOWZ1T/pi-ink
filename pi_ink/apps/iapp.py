from abc import ABC
from typing import Any


class IApp(ABC):
    def run(self, **kwargs) -> None:
        """
        Runs the app.
        """
        raise NotImplementedError("run() not implemented")
