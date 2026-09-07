r"""Executable architecture boundary examples; not production/API/DB validation.

Run: .\.venv\Scripts\python.exe docs/architecture/check_unicode_contract.py
This checks reference Unicode semantics and local driver adaptation only.
"""

import json
from pathlib import Path

from psycopg import DataError
from psycopg.types.string import StrDumper


def invalid_string(value):
    return any(ord(char) == 0 or 0xD800 <= ord(char) <= 0xDFFF for char in value)


def invalid_path(value, path):
    if isinstance(value, str):
        return path if invalid_string(value) else None
    if isinstance(value, dict):
        for key, item in value.items():
            if invalid_string(key):
                return path
            # ASCII-escaped bracket paths for unusual but valid keys.
            child = f"{path}.{key}" if key.isascii() and key.isidentifier() else f"{path}[{json.dumps(key)}]"
            found = invalid_path(item, child)
            if found:
                return found
    if isinstance(value, list):
        for index, item in enumerate(value):
            found = invalid_path(item, f"{path}[{index}]")
            if found:
                return found
    return None


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def main():
    cases = json.loads(Path(__file__).with_name("unicode-cases.json").read_text(encoding="utf-8"))
    assert len({case["id"] for case in cases}) == len(cases)
    accepted = 0
    for case in cases:
        value = json.loads(case["json_text"])
        found = invalid_path(value, case["field"])
        assert (found is None) == case["accepted"], case["id"]
        if found is not None:
            assert found == case["error_field"], case["id"]
            assert not invalid_string(found), "Unsafe error path"
            continue
        accepted += 1
        assert value == case["expected"], case["id"]
        if "scalar_length" in case:
            assert len(value) == case["scalar_length"], case["id"]
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8", errors="strict")
        assert json.loads(encoded) == value, case["id"]
        for item in strings(value):
            assert bytes(StrDumper(str).dump(item)) == item.encode("utf-8"), case["id"]
    try:
        StrDumper(str).dump("hello\x00world")
    except DataError:
        pass
    else:
        raise AssertionError("Original NUL driver failure not reproduced")
    for malformed in (b'"\xff"', b'"\xed\xa0\x80"'):
        try:
            malformed.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            pass
        else:
            raise AssertionError("Invalid UTF-8 was accepted")
    print(f"PASS: {len(cases)} Unicode fixtures ({accepted} accepted, {len(cases)-accepted} rejected); safe error paths")
    print("PASS: accepted scalar preservation/driver adaptation; NUL rejection reproduced; 2 malformed UTF-8 cases")
    print("NOT_RUN: production validators, HTTP status/side-effect tests, PostgreSQL text/JSONB round trips")


if __name__ == "__main__":
    main()
