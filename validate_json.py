#!/usr/bin/env python3
import json, sys
from jsonschema import Draft7Validator

def main(schema_path, json_path):
    with open(schema_path,'r') as f: schema = json.load(f)
    with open(json_path,'r') as f: data = json.load(f)
    v = Draft7Validator(schema)
    errors = sorted(v.iter_errors(data), key=lambda e: e.path)
    if errors:
        print("Validation FAILED:")
        for e in errors:
            loc = ".".join([str(x) for x in e.path]) or "<root>"
            print(f" - {loc}: {e.message}")
        raise SystemExit(1)
    print("Validation OK.")

if __name__ == "__main__":
    if len(sys.argv)<2:
        print("Usage: python validate_json.py params.json")
        raise SystemExit(2)
    main("params.schema.json", sys.argv[1])
