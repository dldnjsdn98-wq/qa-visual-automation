"""Hash only Backend03 native diagnostic artifacts; no tests or subprocesses."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
reports = root / '.orchestration/reports'
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
output = args.output.resolve()
if output.parent != reports or not output.name.startswith('BACKEND-OCR-001-native-diagnostic-artifact-index-'):
    parser.error('output must be a new own-role diagnostic index in reports')
if output.exists():
    parser.error('immutable index already exists')
files = set()
for entry in reports.glob('BACKEND-OCR-001-native-diagnostic*'):
    if 'artifact-index-' in entry.name:
        continue
    if entry.is_file():
        files.add(entry)
    elif entry.is_dir():
        files.update(p for p in entry.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
handoff = root / '.orchestration/handoffs/BACKEND-OCR-001-native-diagnostic-03.md'
if handoff.is_file():
    files.add(handoff)
entries = []
for path in sorted(files):
    data = path.read_bytes()
    entries.append({'path': path.relative_to(root).as_posix(), 'bytes': len(data),
                    'sha256': hashlib.sha256(data).hexdigest()})
data = {'kind': 'diagnostic-artifact-snapshot-not-qualification',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'count': len(entries), 'artifacts': entries}
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(data, stream, indent=2)
    stream.write('\n')
print(json.dumps({'count': len(entries), 'index_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
