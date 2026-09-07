"""Check handoff structure and phase gates without claiming Phase 1 acceptance."""
from pathlib import Path
import json
import yaml

root = Path(__file__).resolve().parents[1]
state = yaml.safe_load((root / '.orchestration/PROJECT_STATE.yaml').read_text(encoding='utf-8'))
tasks = yaml.safe_load((root / '.orchestration/TASKS.yaml').read_text(encoding='utf-8'))['tasks']
acceptance = yaml.safe_load((root / '.orchestration/ACCEPTANCE.yaml').read_text(encoding='utf-8'))
ids = {task['id'] for task in tasks}
assert len(ids) == len(tasks) == 10
assert state['active_roles'] == ['01', '02']
assert state['user_request_only_roles'] == ['10']
assert tasks[0]['id'] == 'ARCH-001' and tasks[0]['status'] == 'READY'
fields = {'id', 'phase', 'title', 'owner', 'status', 'priority', 'depends_on',
          'acceptance', 'branch', 'commit', 'tests', 'blockers', 'review_result'}
ac_ids = {item['id'] for item in acceptance['architecture']}
for phase in acceptance['phases']:
    assert phase['status'] == 'NOT_STARTED'
    for item in phase['criteria']:
        assert item['required'] and item['status'] == 'NOT_RUN'
        ac_ids.add(item['id'])
for task in tasks:
    assert fields <= task.keys()
    assert task['owner'] != '10'
    assert set(task['acceptance']) <= ac_ids
    for dependency in task['depends_on']:
        assert dependency in ids or dependency.endswith('ACCEPTED')
prompts = sorted((root / 'docs/prompts').glob('*.md'))
assert len(prompts) == 10
for prompt in prompts:
    content = prompt.read_text(encoding='utf-8')
    for section in ['역할', '책임 범위', '현재 활성 조건', 'WAITING 규칙',
                    '수정 가능 범위', '수정 금지 범위', 'Handoff 규칙', 'Review 규칙', 'Test 규칙']:
        assert section in content, (prompt.name, section)
for path in ['backend/app/main.py', 'frontend/package-lock.json', 'docker-compose.yml',
             'docs/architecture/overview.md', 'docs/architecture/domain-model.md',
             'docs/architecture/api-contract.md', 'docs/architecture/data-flow.md']:
    assert (root / path).is_file(), path
assert len(list((root / 'docs/phases').glob('phase-*.md'))) == 7
package = json.loads((root / 'frontend/package.json').read_text())
assert {'dev', 'build', 'start', 'typecheck'} <= package['scripts'].keys()
print('PASS: bootstrap structure, 10 role prompts, 10 tasks, 7 phase gates and references')
