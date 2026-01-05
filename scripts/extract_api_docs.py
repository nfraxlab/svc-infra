#!/usr/bin/env python
"""Extract API documentation from Python source code using griffe.

This script automatically discovers all public classes exported from
svc_infra/__init__.py and extracts docstrings, signatures, parameters,
and methods into JSON format for rendering in nfrax-web.

Usage:
    python scripts/extract_api_docs.py [--output-dir docs/api]

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
from griffe import Alias, Class, Function, Module, Parameter


def resolve_alias_recursively(
    alias: Alias, loader: griffe.GriffeLoader, max_depth: int = 10
) -> Class | None:
    """Recursively resolve an alias to find the actual Class definition.

    Follows the alias chain through multiple modules until a Class is found.
    """
    if max_depth <= 0:
        return None

    if not hasattr(alias, "target_path"):
        return None

    target_path = str(alias.target_path)
    parts = target_path.rsplit(".", 1)
    if len(parts) != 2:
        return None

    module_path, class_name = parts

    try:
        target_module = loader.load(module_path)
    except Exception:
        return None

    # First check in classes dict
    if class_name in target_module.classes:
        cls = target_module.classes[class_name]
        # It might still be an alias, need to keep resolving
        if isinstance(cls, Alias):
            return resolve_alias_recursively(cls, loader, max_depth - 1)
        if isinstance(cls, Class):
            return cls

    # Then check in members
    if class_name in target_module.members:
        member = target_module.members[class_name]
        if isinstance(member, Class):
            return member
        if isinstance(member, Alias):
            return resolve_alias_recursively(member, loader, max_depth - 1)

    return None


def resolve_member(member: Any) -> Function | Class | None:
    """Resolve an alias to its actual definition."""
    if isinstance(member, Alias):
        try:
            return member.target
        except Exception:
            return None
    return member


def discover_classes_from_submodule(
    module: Module, loader: griffe.GriffeLoader, module_path: str
) -> list[tuple[str, Class, str]]:
    """Discover public classes from a submodule's __all__ or public members."""
    classes = []

    # Try to get __all__ list
    all_exports = []
    if "__all__" in module.members:
        try:
            all_member = module.members["__all__"]
            if hasattr(all_member, "value"):
                import ast

                try:
                    all_exports = ast.literal_eval(str(all_member.value))
                except (ValueError, SyntaxError):
                    all_exports = []
        except Exception:
            pass

    # If no __all__, use public members
    if not all_exports:
        all_exports = [n for n in module.members.keys() if not n.startswith("_")]

    for name in all_exports:
        if name.startswith("_"):
            continue

        member = module.members.get(name)
        if member is None:
            continue

        resolved = None
        full_path = f"{module_path}.{name}"

        if isinstance(member, Alias):
            resolved = resolve_alias_recursively(member, loader)
            if resolved and hasattr(member, "target_path"):
                full_path = str(member.target_path)
        elif isinstance(member, Class):
            resolved = member

        if isinstance(resolved, Class):
            classes.append((full_path, resolved, name))

    return classes


def discover_exported_classes(
    module: Module, loader: griffe.GriffeLoader, package_name: str
) -> list[tuple[str, Class, str]]:
    """Discover all public classes exported from a module.

    Uses __all__ from the module and resolves each class through griffe.
    Also recursively scans submodules for packages that export modules.
    Returns list of (fully_qualified_path, Class, export_name) tuples.
    """
    classes = []

    # First, try to get the __all__ list
    all_exports = []
    if "__all__" in module.members:
        try:
            all_member = module.members["__all__"]
            # __all__ is stored as an Attribute with value
            if hasattr(all_member, "value"):
                # Parse the value expression to get list items
                import ast

                try:
                    all_exports = ast.literal_eval(str(all_member.value))
                except (ValueError, SyntaxError):
                    all_exports = []
        except Exception:
            pass

    # If no __all__, fall back to module.members
    if not all_exports:
        all_exports = [n for n in module.members.keys() if not n.startswith("_")]

    for name in all_exports:
        if name.startswith("_"):
            continue

        resolved = None
        full_path = f"{package_name}.{name}"

        # Try to get from module.members first
        if name in module.members:
            member = module.members[name]

            # Check if this is a submodule - if so, scan it recursively
            if isinstance(member, Module):
                submodule_path = f"{package_name}.{name}"
                try:
                    submodule = loader.load(submodule_path)
                    subclasses = discover_classes_from_submodule(submodule, loader, submodule_path)
                    classes.extend(subclasses)
                except Exception:
                    pass
                continue

            if isinstance(member, Alias):
                # Check if alias points to a module
                if hasattr(member, "target_path"):
                    target_path = str(member.target_path)
                    try:
                        target = loader.load(target_path)
                        if isinstance(target, Module):
                            subclasses = discover_classes_from_submodule(
                                target, loader, target_path
                            )
                            classes.extend(subclasses)
                            continue
                    except Exception:
                        pass

                # Use recursive resolver for class aliases
                resolved = resolve_alias_recursively(member, loader)
                if resolved and hasattr(member, "target_path"):
                    full_path = str(member.target_path)
            elif isinstance(member, Class):
                resolved = member

        if isinstance(resolved, Class):
            classes.append((full_path, resolved, name))

    return classes


# Classes to skip (base classes, internal types, dataclasses without methods)
SKIP_CLASSES = {
    # Error classes (standard exception pattern)
    "SvcInfraError",
    "ConfigurationError",
    "ValidationError",
    "DatabaseError",
    "AuthError",
    "LoaderError",
    # Simple dataclasses/types
    "LoadedContent",
    "ServiceInfo",
    "AuthConfig",
    # Base classes (abstract, not directly used)
    "BaseLoader",
    "BaseRepository",
    "BaseService",
}

# Additional submodules to scan for classes (for packages with nested structure)
ADDITIONAL_SUBMODULES = [
    "svc_infra.api.fastapi",
    "svc_infra.api.fastapi.auth",
    "svc_infra.db.sql",
    "svc_infra.db.nosql",
    "svc_infra.cache",
    "svc_infra.webhooks",
    "svc_infra.billing",
]


# Minimum methods to be considered worth documenting
MIN_METHODS = 1


def extract_parameter(param: Parameter) -> dict[str, Any]:
    """Extract parameter information."""
    return {
        "name": param.name,
        "type": str(param.annotation) if param.annotation else None,
        "default": str(param.default) if param.default else None,
        "description": None,  # Will be filled from docstring Args section
        "required": param.default is None and param.name not in ("self", "cls"),
    }


def parse_docstring_args(docstring: str | None) -> dict[str, str]:
    """Parse Args section from Google-style docstring.

    Returns a dict mapping parameter names to descriptions.
    """
    if not docstring:
        return {}

    args_map: dict[str, str] = {}
    in_args = False
    current_param = ""
    current_desc_lines: list[str] = []

    for line in docstring.split("\n"):
        stripped = line.strip()

        # Check for Args: section start
        if stripped == "Args:":
            in_args = True
            continue

        # Check for section end (new section or empty line after content)
        if in_args and stripped and not stripped.startswith(" ") and stripped.endswith(":"):
            if stripped in ("Returns:", "Raises:", "Yields:", "Example:", "Note:", "Attributes:"):
                in_args = False
                if current_param:
                    args_map[current_param] = " ".join(current_desc_lines).strip()
                continue

        if in_args:
            # New parameter line: "param_name: description" or "param_name (type): description"
            if ": " in stripped and not stripped.startswith(" "):
                # Handle "param_name: description" or "param_name (type): description"
                colon_idx = stripped.index(": ")
                param_part = stripped[:colon_idx]
                desc_part = stripped[colon_idx + 2 :]

                # Remove type annotation if present: "param_name (type)"
                if " (" in param_part and param_part.endswith(")"):
                    param_name = param_part.split(" (")[0]
                else:
                    param_name = param_part

                # Save previous param
                if current_param:
                    args_map[current_param] = " ".join(current_desc_lines).strip()

                current_param = param_name
                current_desc_lines = [desc_part] if desc_part else []
            elif stripped and current_param:
                # Continuation of previous parameter description
                current_desc_lines.append(stripped)

    # Save last param
    if current_param:
        args_map[current_param] = " ".join(current_desc_lines).strip()

    return args_map


def parse_docstring_raises(docstring: str | None) -> list[dict[str, str]]:
    """Parse Raises section from Google-style docstring."""
    if not docstring:
        return []

    raises_list: list[dict[str, str]] = []
    in_raises = False
    current_exc = ""
    current_desc_lines: list[str] = []

    for line in docstring.split("\n"):
        stripped = line.strip()

        if stripped == "Raises:":
            in_raises = True
            continue

        if in_raises and stripped and not stripped.startswith(" ") and stripped.endswith(":"):
            if stripped in ("Returns:", "Args:", "Yields:", "Example:", "Note:", "Attributes:"):
                in_raises = False
                if current_exc:
                    raises_list.append(
                        {"type": current_exc, "description": " ".join(current_desc_lines).strip()}
                    )
                continue

        if in_raises:
            if ": " in stripped and not stripped.startswith(" "):
                if current_exc:
                    raises_list.append(
                        {"type": current_exc, "description": " ".join(current_desc_lines).strip()}
                    )
                colon_idx = stripped.index(": ")
                current_exc = stripped[:colon_idx]
                current_desc_lines = [stripped[colon_idx + 2 :]]
            elif stripped and current_exc:
                current_desc_lines.append(stripped)

    if current_exc:
        raises_list.append(
            {"type": current_exc, "description": " ".join(current_desc_lines).strip()}
        )

    return raises_list


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

    # Parse docstring for parameter descriptions
    docstring_text = str(func.docstring.value) if func.docstring else None
    args_map = parse_docstring_args(docstring_text)
    raises_list = parse_docstring_raises(docstring_text)

    # Extract parameters with descriptions
    extracted_params = []
    for p in func.parameters:
        param_data = extract_parameter(p)
        if p.name in args_map:
            param_data["description"] = args_map[p.name]
        extracted_params.append(param_data)

    # Check decorators for classmethod/staticmethod/property
    decorators = []
    is_classmethod = False
    is_staticmethod = False
    is_property = False

    if hasattr(func, "decorators"):
        for dec in func.decorators:
            dec_name = str(dec.value) if hasattr(dec, "value") else str(dec)
            decorators.append(dec_name)
            if "classmethod" in dec_name:
                is_classmethod = True
            elif "staticmethod" in dec_name:
                is_staticmethod = True
            elif "property" in dec_name:
                is_property = True

    return {
        "name": func.name,
        "signature": signature,
        "docstring": docstring_text,
        "parameters": extracted_params,
        "returns": return_type,
        "is_async": "async" in (func.labels if hasattr(func, "labels") else set()),
        "is_classmethod": is_classmethod,
        "is_staticmethod": is_staticmethod,
        "is_property": is_property,
        "raises": raises_list if raises_list else None,
    }


def extract_class(cls: Class, module_path: str) -> dict[str, Any]:
    """Extract class information including methods and attributes."""
    # If cls is an Alias, resolve it
    if isinstance(cls, Alias):
        try:
            cls = cls.target
        except Exception:
            pass

    # Get source file and line
    source_file = None
    source_line = None
    if hasattr(cls, "filepath") and cls.filepath:
        # Convert to relative path from src/
        filepath = Path(cls.filepath)
        try:
            # Find "src" in the path and get relative path from there
            parts = filepath.parts
            if "src" in parts:
                src_idx = parts.index("src")
                source_file = str(Path(*parts[src_idx:]))
            else:
                source_file = str(filepath)
        except Exception:
            source_file = str(filepath)
    if hasattr(cls, "lineno") and cls.lineno:
        source_line = cls.lineno

    # Get __init__ parameters with descriptions
    init_params = []
    init_docstring = None
    if "__init__" in cls.members:
        init_member = cls.members["__init__"]
        init_func = resolve_member(init_member)
        if isinstance(init_func, Function):
            init_docstring = str(init_func.docstring.value) if init_func.docstring else None
            args_map = parse_docstring_args(init_docstring)
            for p in init_func.parameters:
                if p.name not in ("self", "cls"):
                    param_data = extract_parameter(p)
                    if p.name in args_map:
                        param_data["description"] = args_map[p.name]
                    init_params.append(param_data)

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
        "source_file": source_file,
        "source_line": source_line,
    }


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
        "--src-dir",
        type=Path,
        default=Path("src"),
        help="Source directory to search for modules",
    )
    parser.add_argument(
        "--package",
        type=str,
        default="svc_infra",
        help="Package to discover classes from (default: svc_infra)",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Search paths for griffe
    search_paths = [args.src_dir]

    # Load the main package module to discover exports
    try:
        loader = griffe.GriffeLoader(search_paths=search_paths)
        package = loader.load(args.package)
    except Exception as e:
        print(f"Error loading package {args.package}: {e}", file=sys.stderr)
        return 1

    # Discover all exported classes from main package
    discovered = discover_exported_classes(package, loader, args.package)

    # Also scan additional submodules for packages with nested structure
    for submodule_path in ADDITIONAL_SUBMODULES:
        try:
            submodule = loader.load(submodule_path)
            subclasses = discover_classes_from_submodule(submodule, loader, submodule_path)
            discovered.extend(subclasses)
        except Exception:
            pass  # Submodule may not exist

    # Deduplicate by class name (same class may be exported from multiple places)
    seen_names = set()
    unique_discovered = []
    for item in discovered:
        if item[2] not in seen_names:  # item[2] is export_name
            seen_names.add(item[2])
            unique_discovered.append(item)
    discovered = unique_discovered

    print(f"Discovered {len(discovered)} exported classes from {args.package}")

    extracted_count = 0
    skipped_count = 0

    for full_path, cls, export_name in discovered:
        # Skip classes in the skip list
        if export_name in SKIP_CLASSES:
            skipped_count += 1
            continue

        # Extract class info
        module_path = full_path.rsplit(".", 1)[0] if "." in full_path else args.package
        data = extract_class(cls, module_path)

        # Skip classes with too few methods (likely just dataclasses)
        public_methods = [m for m in data["methods"] if m["name"] != "__init__"]
        if len(public_methods) < MIN_METHODS:
            skipped_count += 1
            continue

        # Write to JSON file (with trailing newline for pre-commit compatibility)
        output_file = args.output_dir / f"{cls.name.lower()}.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        print(f"  Extracted {export_name} ({len(public_methods)} methods) -> {output_file}")
        extracted_count += 1

    print(f"\nExtracted {extracted_count} classes, skipped {skipped_count}")
    return 0 if extracted_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
