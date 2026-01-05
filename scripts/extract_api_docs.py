#!/usr/bin/env python
"""Extract API documentation from Python source code using griffe.

This script parses Python modules and extracts docstrings, signatures,
parameters, and methods into JSON format for rendering in nfrax-web.

Usage:
    python scripts/extract_api_docs.py [--output-dir docs/api] [--classes Class1,Class2]

Output:
    docs/api/<classname>.json for each extracted class
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import griffe
from griffe import Alias, Class, Function, Parameter


def resolve_member(member: Any) -> Function | Class | None:
    """Resolve an alias to its actual definition."""
    if isinstance(member, Alias):
        try:
            return member.target
        except Exception:
            return None
    return member


# Core classes to extract (public API)
DEFAULT_CLASSES = [
    # Loaders (top-level exports)
    "svc_infra.loaders.base.BaseLoader",
    "svc_infra.loaders.github.GitHubLoader",
    "svc_infra.loaders.url.URLLoader",
    "svc_infra.loaders.models.LoadedContent",
    # API/FastAPI
    "svc_infra.api.fastapi.dual.DualAPIRouter",
    "svc_infra.api.fastapi.openapi.models.ServiceInfo",
    # Database
    "svc_infra.db.sql.service.SqlService",
    "svc_infra.db.sql.resource.SqlResource",
    "svc_infra.db.nosql.service.NoSqlService",
    "svc_infra.db.nosql.repository.NoSqlRepository",
    # Cache
    "svc_infra.cache.recache.RecachePlan",
    "svc_infra.cache.resources.Resource",
    # Jobs
    "svc_infra.jobs.queue.JobQueue",
    "svc_infra.jobs.runner.WorkerRunner",
    # Webhooks
    "svc_infra.webhooks.service.WebhookSubscription",
    "svc_infra.webhooks.service.WebhookService",
    # Health
    "svc_infra.health.HealthCheck",
    "svc_infra.health.HealthRegistry",
    # WebSocket
    "svc_infra.websocket.manager.ConnectionManager",
    "svc_infra.websocket.client.WebSocketClient",
]


def extract_parameter(param: Parameter) -> dict[str, Any]:
    """Extract parameter information."""
    return {
        "name": param.name,
        "type": str(param.annotation) if param.annotation else None,
        "default": str(param.default) if param.default else None,
        "description": None,  # Will be extracted from docstring if available
        "required": param.default is None and param.name not in ("self", "cls"),
    }


def extract_function(func: Function) -> dict[str, Any]:
    """Extract function/method information."""
    # Build signature string
    params = []
    for param in func.parameters:
        if param.name in ("self", "cls"):
            continue
        param_str = param.name
        if param.annotation:
            param_str += f": {param.annotation}"
        if param.default:
            param_str += f" = {param.default}"
        params.append(param_str)

    return_type = str(func.returns) if func.returns else None
    signature = f"({', '.join(params)})"
    if return_type:
        signature += f" -> {return_type}"

    return {
        "name": func.name,
        "signature": signature,
        "docstring": str(func.docstring.value) if func.docstring else None,
        "parameters": [extract_parameter(p) for p in func.parameters],
        "returns": return_type,
        "is_async": func.is_async if hasattr(func, "is_async") else False,
    }


def extract_class(cls: Class, module_path: str) -> dict[str, Any]:
    """Extract class information including methods and attributes."""
    # If cls is an Alias, resolve it
    if isinstance(cls, Alias):
        try:
            cls = cls.target
        except Exception:
            pass

    # Get __init__ parameters
    init_params = []
    if "__init__" in cls.members:
        init_member = cls.members["__init__"]
        init_func = resolve_member(init_member)
        if isinstance(init_func, Function):
            init_params = [
                extract_parameter(p) for p in init_func.parameters if p.name not in ("self", "cls")
            ]

    # Extract public methods (exclude private/dunder except __init__)
    methods = []
    for name, member in cls.members.items():
        resolved = resolve_member(member)
        if isinstance(resolved, Function):
            if name.startswith("_") and name != "__init__":
                continue
            methods.append(extract_function(resolved))

    # Sort methods: __init__ first, then alphabetically
    methods.sort(key=lambda m: (m["name"] != "__init__", m["name"]))

    return {
        "name": cls.name,
        "module": module_path,
        "docstring": str(cls.docstring.value) if cls.docstring else None,
        "parameters": init_params,
        "methods": methods,
        "bases": [str(base) for base in cls.bases] if cls.bases else [],
    }


def load_class(class_path: str, search_paths: list[Path]) -> Class | None:
    """Load a class from a module path like 'svc_infra.loaders.BaseLoader'."""
    parts = class_path.rsplit(".", 1)
    if len(parts) != 2:
        print(f"Invalid class path: {class_path}", file=sys.stderr)
        return None

    module_path, class_name = parts

    try:
        loader = griffe.GriffeLoader(search_paths=search_paths)
        module = loader.load(module_path)

        if class_name in module.classes:
            return module.classes[class_name]

        # Check if it's in a submodule
        for submodule in module.modules.values():
            if class_name in submodule.classes:
                return submodule.classes[class_name]

        print(f"Class {class_name} not found in {module_path}", file=sys.stderr)
        return None

    except Exception as e:
        print(f"Error loading {class_path}: {e}", file=sys.stderr)
        return None


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Extract API documentation from Python source")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/api"),
        help="Output directory for JSON files",
    )
    parser.add_argument(
        "--classes",
        type=str,
        default=None,
        help="Comma-separated list of classes to extract (e.g., svc_infra.loaders.BaseLoader)",
    )
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=Path("src"),
        help="Source directory to search for modules",
    )

    args = parser.parse_args()

    # Determine which classes to extract
    if args.classes:
        class_paths = [c.strip() for c in args.classes.split(",")]
    else:
        class_paths = DEFAULT_CLASSES

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Search paths for griffe
    search_paths = [args.src_dir]

    extracted_count = 0
    for class_path in class_paths:
        cls = load_class(class_path, search_paths)
        if cls is None:
            continue

        module_path = class_path.rsplit(".", 1)[0]
        data = extract_class(cls, module_path)

        # Write to JSON file
        output_file = args.output_dir / f"{cls.name.lower()}.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Extracted {class_path} -> {output_file}")
        extracted_count += 1

    print(f"\nExtracted {extracted_count}/{len(class_paths)} classes")
    return 0 if extracted_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
