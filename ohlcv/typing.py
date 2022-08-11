"""Module containing custom typings."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Union


__all__ = [
    # Variable exports
    "JSONLike",
    "Number",
]


# Basic JSON-like typing, includes an empty JSON
JSONLike = Union[Dict, Dict[str, Any]]

Number = Union[int, float]
