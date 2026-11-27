#!/usr/bin/env python3
"""Validate a scientific-pdf-evidence-reader result and optional case contract."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


REQUIRED = {
    "schema_version",
    "case_id",
    "status",
    "document",
    "evidence",
    "uncertainties",
    "change_records",
    "contract_output",
}
VALID_STATUS = {"success", "partial", "failure"}


def contract_keys(contract: Any) -> list[str]:
    if isinstance(contract, dict):
        if isinstance(contract.get("properties"), dict):
            keys = list(contract["properties"])
            required = contract.get("required", [])
            if isinstance(required, list):
                keys.extend(required)
            return list(dict.fromkeys(str(key) for key in keys))
        return [str(key) for key in contract.keys()]
    if isinstance(contract, list):
        result: list[str] = []
        for item in contract:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                for key in ("name", "field", "key", "id"):
                    if item.get(key):
                        result.append(str(item[key]))
                        break
        return result
    return []


def validate_bbox(index: int, value: Any, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list) or len(value) != 4:
        errors.append(f"evidence[{index}].bbox must contain four numbers")
        return
    if not all(isinstance(number, (int, float)) and math.isfinite(number) for number in value):
        errors.append(f"evidence[{index}].bbox contains a non-finite value")
        return
    x0, y0, x1, y1 = value
    if x1 < x0 or y1 < y0:
        errors.append(f"evidence[{index}].bbox has reversed coordinates")


def validate_contract_schema(
    data: dict[str, Any], contract: Any, errors: list[str]
) -> None:
    if not isinstance(contract, dict):
        return
    if isinstance(contract.get("properties"), dict):
        schema = contract
    else:
        properties = {
            key: value
            for key, value in contract.items()
            if isinstance(value, (dict, bool))
        }
        if not properties:
            return
        schema = {
            "type": "object",
            "properties": properties,
            "required": contract_keys(contract),
        }
    try:
        from jsonschema.validators import validator_for

        validator_type = validator_for(schema)
        validator_type.check_schema(schema)
        validator = validator_type(schema)
        for error in validator.iter_errors(data):
            location = "/".join(map(str, error.absolute_path)) or "<root>"
            errors.append(f"contract schema {location}: {error.message}")
    except ImportError:
        inferred = {}
        for key in contract_keys(schema):
            if key in data:
                inferred[key] = type(data[key]).__name__
        errors.append(
            "jsonschema is required for full contract validation; inferred types: "
            + json.dumps(inferred, ensure_ascii=False)
        )
    except Exception as exc:
        errors.append(f"cannot validate contract schema: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument(
        "--case",
        required=True,
        help="Original case.json for output_contract validation",
    )
    args = parser.parse_args()

    path = Path(args.result)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot load JSON: {exc}")
        return 2
    if not isinstance(data, dict):
        print("FAIL: result JSON must be an object")
        return 1

    errors: list[str] = []
    missing = REQUIRED - set(data)
    if missing:
        errors.append(f"missing required fields: {sorted(missing)}")
    if (
        not isinstance(data.get("status"), str)
        or data.get("status") not in VALID_STATUS
    ):
        errors.append(f"invalid status: {data.get('status')!r}")
    if data.get("status") != "failure" and (
        not isinstance(data.get("case_id"), str) or not data.get("case_id")
    ):
        errors.append("case_id must be a non-empty string")

    document = data.get("document")
    if not isinstance(document, dict):
        errors.append("document must be an object")
    else:
        if not isinstance(document.get("pages"), list):
            errors.append("document.pages must be a list")
        if not isinstance(document.get("full_markdown"), str):
            errors.append("document.full_markdown must be a string")
        if not isinstance(document.get("metadata"), dict):
            errors.append("document.metadata must be an object")

    evidence = data.get("evidence")
    evidence_ids: set[str] = set()
    if not isinstance(evidence, list):
        errors.append("evidence must be a list")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"evidence[{index}] must be an object")
                continue
            evidence_id = item.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                errors.append(f"evidence[{index}] missing evidence_id")
            elif evidence_id in evidence_ids:
                errors.append(f"duplicate evidence_id: {evidence_id}")
            else:
                evidence_ids.add(evidence_id)
            page = item.get("page")
            if not isinstance(page, int) or page < 1:
                errors.append(f"evidence[{index}] missing positive integer page")
            validate_bbox(index, item.get("bbox"), errors)

    if not isinstance(data.get("uncertainties"), list):
        errors.append("uncertainties must be a list")
    if not isinstance(data.get("change_records"), list):
        errors.append("change_records must be a list")
    contract_output = data.get("contract_output")
    if not isinstance(contract_output, dict):
        errors.append("contract_output must be an object")

    if isinstance(document, dict) and isinstance(document.get("pages"), list):
        for page_index, page in enumerate(document["pages"]):
            if not isinstance(page, dict):
                errors.append(f"document.pages[{page_index}] must be an object")
                continue
            page_number = page.get("page")
            if not isinstance(page_number, int) or page_number < 1:
                errors.append(f"document.pages[{page_index}] has invalid page number")

    case_checked = False
    if args.case:
        case_path = Path(args.case)
        try:
            case_data = json.loads(case_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"cannot load case file: {exc}")
            case_data = {}
        if isinstance(case_data, dict):
            case_checked = True
            expected_case_id = (
                case_data.get("case_id")
                or case_data.get("caseId")
                or case_data.get("id")
            )
            if expected_case_id is None:
                errors.append("case.json has no case identifier")
            if (
                expected_case_id is not None
                and data.get("case_id") != expected_case_id
            ):
                errors.append(
                    f"case_id mismatch: result={data.get('case_id')!r}, case={expected_case_id!r}"
                )
            contract = (
                case_data.get("output_contract")
                or case_data.get("outputContract")
                or case_data.get("output")
                or {}
            )
            for key in contract_keys(contract):
                if key not in data:
                    errors.append(f"top-level output contract field missing: {key}")
                if isinstance(contract_output, dict) and key not in contract_output:
                    errors.append(f"contract_output field missing: {key}")
                if (
                    isinstance(contract_output, dict)
                    and key in data
                    and key in contract_output
                    and data[key] != contract_output[key]
                ):
                    errors.append(
                        f"contract_output differs from top-level field: {key}"
                    )
            validate_contract_schema(data, contract, errors)
        else:
            errors.append("case JSON must be an object")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(
        json.dumps(
            {
                "status": "valid",
                "path": str(path),
                "case_checked": case_checked,
                "pages": len(document["pages"]),
                "evidence": len(evidence),
                "uncertainties": len(data["uncertainties"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
