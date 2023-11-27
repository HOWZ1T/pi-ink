from dataclasses import dataclass
from typing import Any, Optional

from .edisplay_response import EDisplayResponse


@dataclass(kw_only=True, frozen=True)
class DisplayResult:
    response: EDisplayResponse
    value: Optional[Any] = None
