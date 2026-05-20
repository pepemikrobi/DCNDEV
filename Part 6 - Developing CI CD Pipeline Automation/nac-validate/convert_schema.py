#!/usr/bin/env python3
"""Convert JSON Schema to Yamale YAML schema for nac-validate."""

import json
import re
from pathlib import Path


def to_pascal_case(name: str) -> str:
    return "".join(word.capitalize() for word in re.split(r"[_\-\s]+", name))


def type_validator(json_type: str, schema_obj: dict, required: bool) -> str:
    """Return a yamale validator string for a simple (non-object, non-array) type."""
    opt = "" if required else "required=False"
    if "enum" in schema_obj:
        vals = ", ".join(f"'{v}'" for v in schema_obj["enum"])
        args = f"{vals}, {opt}" if opt else vals
        return f"enum({args})"
    elif json_type == "string":
        return f"str({opt})"
    elif json_type == "integer":
        return f"int({opt})"
    elif json_type in ("number", "float"):
        return f"num({opt})"
    elif json_type == "boolean":
        return f"bool({opt})"
    else:
        return f"any({opt})"


class SchemaConverter:
    def __init__(self):
        self.includes: dict[str, list[tuple[str, str, bool]]] = {}  # name -> [(field, validator, required)]

    def include_name(self, path: list[str]) -> str:
        return "".join(to_pascal_case(p) for p in path)

    def resolve_type(self, field_schema: dict) -> tuple[str, dict]:
        """Resolve the effective type from a schema, handling anyOf/oneOf."""
        if "anyOf" in field_schema:
            # Pick the first entry with a concrete type
            for sub in field_schema["anyOf"]:
                if "type" in sub:
                    merged = {**field_schema, **sub}
                    merged.pop("anyOf", None)
                    return sub["type"], merged
        if "oneOf" in field_schema:
            for sub in field_schema["oneOf"]:
                if "type" in sub:
                    merged = {**field_schema, **sub}
                    merged.pop("oneOf", None)
                    return sub["type"], merged
        return field_schema.get("type", "object"), field_schema

    def process_object(self, schema_obj: dict, path: list[str]) -> str | None:
        """Process an object schema node, register an include, return include name.
        Returns None if the object has no properties (use map() instead)."""
        props = schema_obj.get("properties", {})
        if not props:
            return None  # Empty object — caller should use map()

        name = self.include_name(path)
        if name in self.includes:
            return name  # Already processed

        required_fields = set(schema_obj.get("required", []))
        fields = []
        for field_name, field_schema in props.items():
            is_required = field_name in required_fields
            validator = self.process_field(field_schema, path + [field_name], is_required)
            fields.append((field_name, validator, is_required))

        self.includes[name] = fields
        return name

    def process_field(self, field_schema: dict, path: list[str], required: bool) -> str:
        """Return the yamale validator string for a field."""
        opt = "" if required else ", required=False"

        json_type, resolved = self.resolve_type(field_schema)

        if json_type == "object":
            inc_name = self.process_object(resolved, path)
            if inc_name is None:
                opt_kw = "required=False" if not required else ""
                return f"map({opt_kw})"
            return f"include('{inc_name}'{opt})"

        elif json_type == "array":
            items = resolved.get("items", {})
            item_type, item_resolved = self.resolve_type(items) if isinstance(items, dict) else ("object", {})

            if isinstance(items, dict) and item_type == "object":
                inc_name = self.process_object(item_resolved, path + ["item"])
                if inc_name is None:
                    return f"list(map(){opt})"
                return f"list(include('{inc_name}'){opt})"
            elif isinstance(items, dict) and item_type == "string":
                return f"list(str(){opt})"
            elif isinstance(items, dict) and item_type == "integer":
                return f"list(int(){opt})"
            elif isinstance(items, dict) and item_type == "boolean":
                return f"list(bool(){opt})"
            else:
                return f"list(any(){opt})"

        else:
            return type_validator(json_type, resolved, required)

    def convert(self, json_schema: dict) -> str:
        """Convert the top-level JSON Schema to yamale YAML string."""
        top_props = json_schema.get("properties", {})
        top_required = set(json_schema.get("required", []))

        root_lines = []
        for field_name, field_schema in top_props.items():
            is_required = field_name in top_required
            validator = self.process_field(field_schema, [field_name], is_required)
            root_lines.append(f"{field_name}: {validator}")

        # All includes go in ONE second YAML document (single --- separator)
        include_lines = []
        for inc_name, fields in self.includes.items():
            include_lines.append(f"{inc_name}:")
            for field_name, validator, _req in fields:
                include_lines.append(f"  {field_name}: {validator}")

        parts = ["\n".join(root_lines)]
        if include_lines:
            parts.append("---\n" + "\n".join(include_lines))

        return "\n".join(parts) + "\n"


def main():
    schema_path = Path("/home/pod5/catalyst_center_schema.json")
    output_path = Path("/home/pod5/DCNDEV/TF_NETASCODE/.schema.yaml")

    with open(schema_path, encoding="utf-8-sig") as f:
        json_schema = json.load(f)

    converter = SchemaConverter()
    yaml_schema = converter.convert(json_schema)

    with open(output_path, "w") as f:
        f.write(yaml_schema)

    print(f"Schema written to {output_path}")
    print(f"Total include types defined: {len(converter.includes)}")


if __name__ == "__main__":
    main()
