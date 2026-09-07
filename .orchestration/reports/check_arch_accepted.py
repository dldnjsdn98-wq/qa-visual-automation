"""Read-only reviewer evidence for approved ARCH-001 revision 2, not product tests."""
import hashlib
import json
import re
from pathlib import Path
from uuid import UUID

import yaml

ROOT = Path(__file__).resolve().parents[2]
documents = [ROOT / 'docs/architecture' / name for name in (
    'overview.md', 'domain-model.md', 'api-contract.md', 'data-flow.md')]
examples = []
links = 0
for path in documents:
    content = path.read_text(encoding='utf-8-sig')
    assert 'Revision 2:' in content and content.count('```') % 2 == 0
    for target in re.findall(r'\]\(([^)]+)\)', content):
        if '://' not in target and not target.startswith('#'):
            assert (path.parent / target.split('#')[0]).is_file(), target
            links += 1
    examples.extend(json.loads(x) for x in re.findall(r'```json\s*\n(.*?)\n```', content, re.S))
assert len(examples) == 4
error, expected, upload, screenshot = examples
UUID(error['error']['request_id'])
assert expected['total'] == len(expected['items'])
missing = [x for x in expected['items'] if x['translation_status'] == 'missing']
assert expected['missing_count'] == len(missing)
assert all(x['text'] is None and x['entry_id'] is None for x in missing)
assert [x['position'] for x in expected['items']] == list(range(expected['total']))
for field in ('build_id', 'locale_id', 'situation_id'):
    assert expected[field] == upload[field] == screenshot[field]
for field in ('category_id', 'source'):
    assert upload[field] == screenshot[field]
assert re.fullmatch('[0-9a-f]{64}', screenshot['file_hash'])
assert screenshot['content_url'] == f"/api/v1/projects/{screenshot['project_id']}/screenshots/{screenshot['id']}/content"
assert 'storage_key' not in screenshot
def read_yaml(name):
    return yaml.safe_load((ROOT / '.orchestration' / name).read_text(encoding='utf-8-sig'))
tasks = read_yaml('TASKS.yaml')['tasks']
by_id = {t['id']: t for t in tasks}
assert len(tasks) == len(by_id)
task = by_id['ARCH-001']
assert task['status'] == task['review_result'] == 'ACCEPTED'
assert task['reviewed_revision'] == task['submission_revision'] == 2
assert not task['blockers'] and task['review_requested'] is False
assert any(x['id'] == 'R08-ARCH-001' and x['status'] == 'RESOLVED' for x in task['review_findings'])
assert any(x['result'] == 'CHANGES_REQUESTED' for x in task['review_history'])
assert any(x['submission'] == 2 and x['result'] == 'ACCEPTED' for x in task['review_history'])
acceptance = read_yaml('ACCEPTANCE.yaml')
assert next(x for x in acceptance['architecture'] if x['id'] == 'AC-ARCH-01')['status'] == 'PASS'
for key in ('review_evidence', 'reviewer_handoff', 'handoff'):
    assert (ROOT / task[key]).is_file()
assert read_yaml('PROJECT_STATE.yaml')['architecture_dispatch']['status'] == 'ACCEPTED'
print(f'PASS: {len(documents)} documents, {links} local links, {len(examples)} JSON examples and scope/missing/content consistency')
print('PASS: accepted revision 2, resolved finding, PASS acceptance and retained review history/evidence')
for path in documents:
    print(f'SHA256 {path.name}: {hashlib.sha256(path.read_bytes()).hexdigest()}')
print('NOT_RUN: production API/DB/storage/Frontend tests; no phase acceptance inferred')
