from __future__ import annotations

import importlib
from typing import Any


def resolve_target(path: str) -> Any:
    """Resolve a module:attribute(.nested) target string."""
    mod_name, attr_path = path.split(":", 1)
    obj: Any = importlib.import_module(mod_name)
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj
