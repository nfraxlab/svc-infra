from __future__ import annotations

import importlib


def resolve_target(path: str) -> object:
    """Resolve a module:attribute(.nested) target string."""
    mod_name, attr_path = path.split(":", 1)
    obj: object = importlib.import_module(mod_name)
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj
