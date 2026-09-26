"""Write a new source checkpoint without changing product or prior evidence."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[2]
output = root / '.orchestration/reports/BACKEND-OCR-001-runtime-conformance-source-manifest.txt'
paths = []
for directory in ('backend', 'tests/backend'):
    for path in (root / directory).rglob('*'):
        if (path.is_file() and not {'__pycache__', '.pytest_cache'} & set(path.parts)
                and path.suffix not in {'.pyc', '.pyo'}):
            paths.append(path.relative_to(root).as_posix())
paths.append('pyproject.toml')
payload = ''.join(f'{path} {hashlib.sha256((root/path).read_bytes()).hexdigest()}\n'
                  for path in sorted(paths))
aggregate = hashlib.sha256(payload.encode('utf-8')).hexdigest()
header = '\n'.join((
    'BACKEND-OCR-001 runtime-conformance checkpoint; not qualification',
    'generated_utc=' + datetime.now(timezone.utc).isoformat(),
    'sorting=ordinal; path_separator=/',
    'line_format=<relative-path><space><lowercase-sha256>',
    'scope=backend/** + tests/backend/** + pyproject.toml',
    f'count={len(paths)}', f'aggregate_sha256={aggregate}',
    'status=BLOCKED_NATIVE_QUALIFICATION_NOT_READY_FOR_REVIEW', '',
)) + '\n'
with output.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(header + payload)
print(f'count={len(paths)} aggregate={aggregate}')
print(f'manifest_sha256={hashlib.sha256(output.read_bytes()).hexdigest()}')
