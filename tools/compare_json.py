"""Strict JSON comparison. Shows differing locations, never payload values."""
import argparse
import json
import math
from pathlib import Path

def reject_constant(_value):
    raise ValueError('non-finite number')

def finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('non-finite number')
    return parsed

def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate object key')
        result[key] = value
    return result

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=reject_constant, parse_float=finite_float, object_pairs_hook=object_pairs)

def differences(expected, actual, path='$'):
    if type(expected) is not type(actual):
        return [{'path': path, 'kind': 'type'}]
    if isinstance(expected, dict):
        result = []
        for index, key in enumerate(expected):
            # Use key ordinal instead of keys: object keys can also contain personal data.
            child = f'{path}/key#{index}'
            result += [{'path': child, 'kind': 'missing-key'}] if key not in actual else differences(expected[key], actual[key], child)
        if actual.keys() - expected.keys():
            result.append({'path': path, 'kind': 'extra-keys'})
        return result
    if isinstance(expected, list):
        result = [] if len(expected) == len(actual) else [{'path': path, 'kind': 'length'}]
        for index, (left, right) in enumerate(zip(expected, actual)):
            result += differences(left, right, f'{path}/{index}')
        return result
    return [] if expected == actual else [{'path': path, 'kind': 'value'}]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('expected'); parser.add_argument('actual'); args = parser.parse_args()
    try:
        result = differences(read(args.expected), read(args.actual))
    except (OSError, ValueError, RecursionError):
        parser.error('cannot read strict JSON inputs')
    print(json.dumps({'equal': not result, 'differences': result}, indent=2))
    return int(bool(result))

if __name__ == '__main__':
    raise SystemExit(main())
