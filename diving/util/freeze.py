#!/usr/bin/python3
"""Utilities for creating deeply immutable data structures."""

from collections.abc import Mapping
from typing import Any

from frozendict import frozendict


def deep_freeze(obj: Any) -> Any:
    """Recursively convert mutable structures to immutable equivalents.

    - dict -> frozendict
    - list -> tuple
    - set -> frozenset
    - Nested structures are recursively frozen
    """
    if isinstance(obj, frozendict):
        return obj
    if isinstance(obj, Mapping):
        return frozendict({k: deep_freeze(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple)):
        return tuple(deep_freeze(item) for item in obj)
    if isinstance(obj, (set, frozenset)):
        return frozenset(deep_freeze(item) for item in obj)
    # Primitive types (str, int, float, bool, None) are already immutable
    return obj


def unfreeze(obj: Any) -> Any:
    """Recursively convert frozen structures to mutable equivalents.

    - frozendict -> dict
    - tuple -> list
    - frozenset -> set
    - Nested structures are recursively unfrozen
    """
    if isinstance(obj, Mapping):
        return {k: unfreeze(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return [unfreeze(item) for item in obj]
    if isinstance(obj, frozenset):
        return {unfreeze(item) for item in obj}
    # Primitive types and other objects remain unchanged
    return obj
