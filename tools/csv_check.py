"""Inspect a UTF-8 CSV without printing cell values or choosing business rules."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

def inspect(path: Path, keys=(), numbers=()):
    issues, seen, count = [], set(), 0
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if not header or len(set(header)) != len(header) or any(not h.strip() for h in header):
            raise ValueError('missing, duplicate or blank header')
        requested = list(keys) + list(numbers)
        if any(name not in header for name in requested):
            raise ValueError('requested column does not exist')
        for row in reader:
            count += 1
            line = reader.line_num
            if len(row) != len(header):
                issues.append({'line': line, 'kind': 'column-count'}); continue
            item = dict(zip(header, row))
            if keys:
                key = tuple(item[name] for name in keys)
                if any(not value.strip() for value in key):
                    issues.append({'line': line, 'kind': 'blank-key'})
                elif key in seen:
                    issues.append({'line': line, 'kind': 'duplicate-key'})
                seen.add(key)
            for name in numbers:
                try:
                    number = Decimal(item[name])
                    if not number.is_finite():
                        raise InvalidOperation
                except InvalidOperation:
                    issues.append({'line': line, 'kind': 'invalid-number', 'column': name})
    return {'rows': count, 'columns': header, 'issues': issues,
            'note': 'No correction/deduplication applied; duplicates may be legitimate revisions. Keys compared exactly.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--key', action='append', default=[])
    parser.add_argument('--number', action='append', default=[])
    args = parser.parse_args()
    try:
        result = inspect(args.file, args.key, args.number)
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        # No cell content from library exceptions is printed.
        parser.error(type(error).__name__ + ': cannot inspect file/header/options')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return int(bool(result['issues']))

if __name__ == '__main__':
    raise SystemExit(main())
