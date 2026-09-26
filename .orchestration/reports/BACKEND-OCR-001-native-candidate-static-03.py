"""Validate proposed one-file unified diffs in memory; never apply or execute them."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    'windows': ('backend/app/workers/ocr_containment.py',
                'ef7d7ffe6dbc0b8f620ae9416818614cf9aa9dc5ceb822fdee11d4feca76bec5'),
    'linux': ('tests/backend/test_ocr_containment.py',
              '382257cfb9747b2fe9d7aa87fedd5d50d5f853745c483be5b1764c3c958ade1b'),
}
parser = argparse.ArgumentParser()
parser.add_argument('lane', choices=TARGETS)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
relative, expected = TARGETS[args.lane]
source = ROOT / relative
patch = ROOT / f'.orchestration/reports/BACKEND-OCR-001-native-candidate-{args.lane}-03.patch'
output = args.output.resolve()
assert output.parent == ROOT / '.orchestration/reports'
assert output.name.startswith('BACKEND-OCR-001-native-candidate-') and not output.exists()
before = source.read_bytes()
assert hashlib.sha256(before).hexdigest() == expected, 'frozen source mismatch'
original = before.decode('utf-8').replace('\r\n', '\n').splitlines(keepends=True)
raw_patch = patch.read_bytes()
lines = raw_patch.decode('utf-8').replace('\r\n', '\n').splitlines(keepends=True)
old_headers = [line[4:].strip().split('\t')[0] for line in lines if line.startswith('--- ')]
new_headers = [line[4:].strip().split('\t')[0] for line in lines if line.startswith('+++ ')]
assert old_headers in ([relative], ['a/' + relative]), 'unexpected old patch target'
assert new_headers in ([relative], ['b/' + relative]), 'unexpected new patch target'
result = []
cursor = 0
index = 0
hunks = 0
while index < len(lines):
    match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', lines[index])
    if not match:
        index += 1
        continue
    start, old_count, new_start, new_count = map(int, (
        match[1], match[2] or '1', match[3], match[4] or '1'))
    position = start - 1 if old_count else start
    assert cursor <= position <= len(original), 'overlapping/out-of-range hunk'
    result.extend(original[cursor:position])
    cursor = position
    assert len(result) == (new_start - 1 if new_count else new_start), 'new hunk offset mismatch'
    old_used = new_used = 0
    index += 1
    while index < len(lines) and (old_used < old_count or new_used < new_count):
        line = lines[index]
        assert line[:1] in (' ', '+', '-'), 'unsupported diff body'
        body = line[1:]
        if line[0] in (' ', '-'):
            assert cursor < len(original) and original[cursor] == body, 'exact context mismatch'
            cursor += 1
            old_used += 1
        if line[0] in (' ', '+'):
            result.append(body)
            new_used += 1
        index += 1
    assert (old_used, new_used) == (old_count, new_count), 'hunk count mismatch'
    hunks += 1
assert hunks > 0
result.extend(original[cursor:])
candidate = ''.join(result)
ast.parse(candidate, filename=relative)
assert source.read_bytes() == before, 'source changed during read-only validation'
record = {
    'lane': args.lane, 'source': relative, 'source_sha256': expected,
    'patch_sha256': hashlib.sha256(raw_patch).hexdigest(), 'hunks': hunks,
    'candidate_lf_utf8_sha256': hashlib.sha256(candidate.encode('utf-8')).hexdigest(),
    'exact_in_memory_context': 'PASS', 'candidate_ast_parse': 'PASS',
    'source_unchanged': True, 'patch_applied': False, 'candidate_executed': False,
    'pytest_native_build_model': 'NOT_RUN',
}
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps(record))
