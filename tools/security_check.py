"""Read-only, bounded local secret-pattern check. Never prints matched values."""
import argparse
import json
import os
from pathlib import Path
import re

SKIP = {'.git', 'node_modules', '.next', '.venv', 'venv', '__pycache__', '.lab-data', 'dist', 'build'}
LIMIT = 1024 * 1024
PATTERNS = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'aws-access-key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'credential-literal': re.compile(r'''(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*["']([^"'\r\n]{12,})["']'''),
}
PLACEHOLDERS = ('example', 'placeholder', 'your_', 'replace', 'dummy', 'test-', '<', '${', 'process.env')

def scan(root: Path):
    root = root.absolute()
    findings, skipped = [], []
    def visit_error(error):
        skipped.append({'path': str(Path(error.filename).relative_to(root)), 'reason': 'unreadable-directory'})
    if root.is_symlink():
        return [], [{'path': '.', 'reason': 'symlink'}]
    for parent, dirs, names in os.walk(root, followlinks=False, onerror=visit_error):
        for name in dirs[:]:
            path = Path(parent, name)
            if name in SKIP:
                dirs.remove(name)
            elif path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                dirs.remove(name); skipped.append({'path': str(path.relative_to(root)), 'reason': 'linked-directory'})
        for name in names:
            path = Path(parent, name); rel = str(path.relative_to(root))
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                skipped.append({'path': rel, 'reason': 'linked-file'}); continue
            if name == '.env' or (name.startswith('.env.') and name not in {'.env.example', '.env.sample', '.env.template'}):
                findings.append({'path': rel, 'line': 0, 'kind': 'environment-file'})
                continue
            try:
                with path.open('rb') as stream:
                    raw = stream.read(LIMIT + 1)
                if len(raw) > LIMIT:
                    skipped.append({'path': rel, 'reason': 'over-1MiB'}); continue
                if b'\0' in raw:
                    skipped.append({'path': rel, 'reason': 'binary'}); continue
                content = raw.decode('utf-8-sig')
            except (OSError, UnicodeError):
                skipped.append({'path': rel, 'reason': 'unreadable-or-non-utf8'}); continue
            for line, value in enumerate(content.splitlines(), 1):
                for kind, pattern in PATTERNS.items():
                    match = pattern.search(value)
                    if match:
                        if kind == 'credential-literal' and any(p in match.group(1).lower() for p in PLACEHOLDERS):
                            continue
                        findings.append({'path': rel, 'line': line, 'kind': kind})
    return findings, skipped

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error('root must be an existing directory')
    findings, skipped = scan(args.root)
    print(json.dumps({'findings': findings, 'skipped': skipped, 'excluded_directories': sorted(SKIP),
                      'scope': 'local UTF-8 files <=1MiB; patterns only; values redacted'}, ensure_ascii=True, indent=2))
    return int(bool(findings or skipped))

if __name__ == '__main__':
    raise SystemExit(main())
