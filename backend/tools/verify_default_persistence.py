"""Explicit default-environment synthetic seed/readback; preserves all records.

Run seed once, upload env-p1-db-001.png in the Web UI, capture baseline once,
then run verify before/after restart. Verification never modifies the baseline.
"""
import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4
import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / '.orchestration/reports/ENV-P1-DB-001-records.json'
TEXT = '한국어 日本語 中文 العربية 😀 e\u0301'

def main():
    mode = sys.argv[1]
    if mode not in ('seed', 'baseline', 'verify'):
        raise SystemExit('Use seed, baseline, or verify')
    with httpx.Client(base_url='http://127.0.0.1:8001', timeout=30) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        assert request('GET', '/ready') == {'status': 'ready'}
        if mode == 'seed':
            if MANIFEST.exists():
                raise SystemExit('Manifest exists; use verify. No duplicate seed created.')
            name = 'env-p1-db-' + uuid4().hex[:8]
            project = request('POST', '/api/v1/projects', json={'slug': name, 'name': name})
            base = '/api/v1/projects/' + project['id']
            build = request('POST', base + '/builds', json={'label': 'persistent-001'})
            locale = request('POST', base + '/locales', json={'code': 'ko-KR', 'name': '한국어'})
            category = request('POST', base + '/categories', json={'slug': 'menu', 'name': '메뉴'})
            situation = request('POST', base + '/situations', json={'slug': 'title', 'name': '타이틀', 'category_id': category['id']})
            request('POST', base + '/string-keys', json={'string_id': 'TITLE_GREETING'})
            request('POST', base + '/strings', json={'build_id': build['id'], 'locale_id': locale['id'], 'string_id': 'TITLE_GREETING', 'text': TEXT})
            request('PUT', base + '/situations/' + situation['id'] + '/expected-string-keys', params={'build_id': build['id']}, json={'string_ids': ['TITLE_GREETING']})
            data = {'project_id': project['id'], 'project_name': name, 'build_id': build['id'], 'locale_id': locale['id'], 'category_id': category['id'], 'situation_id': situation['id']}
            fixture = ROOT / '.pytest_cache/env-p1-db-001.png'
            Image.new('RGB', (128, 72), (20, 80, 130)).save(fixture)
            data['fixture_sha256'] = hashlib.sha256(fixture.read_bytes()).hexdigest()
            MANIFEST.write_text(json.dumps(data, indent=2), encoding='utf-8')
            print(json.dumps({'seed': 'PASS', **data}))
            return
        data = json.loads(MANIFEST.read_text(encoding='utf-8'))
        base = '/api/v1/projects/' + data['project_id']
        filters = {key: data[key] for key in ('build_id', 'locale_id', 'situation_id')}
        listing = request('GET', base + '/screenshots', params=filters)
        assert listing['total'] == 1, listing
        shot = listing['items'][0]
        detail = request('GET', base + '/screenshots/' + shot['id'])
        if mode == 'verify':
            assert shot['id'] == detail['id'] == data['screenshot_id'], 'Screenshot identity changed'
        assert all(detail[key] == data[key] for key in ('project_id', 'build_id', 'locale_id', 'category_id', 'situation_id'))
        image = client.get(detail['content_url']); image.raise_for_status()
        assert hashlib.sha256(image.content).hexdigest() == data['fixture_sha256'] == detail['file_hash']
        for path, params in [(base + '/screenshots/' + shot['id'] + '/expected-strings', {}), (base + '/situations/' + data['situation_id'] + '/expected-strings', {'build_id': data['build_id'], 'locale_id': data['locale_id']})]:
            expected = request('GET', path, params=params)
            assert expected['items'][0]['text'] == TEXT
            assert expected['missing_count'] == 0
        cors = client.options(base + '/screenshots', headers={'Origin': 'http://127.0.0.1:3001', 'Access-Control-Request-Method': 'POST'})
        assert cors.status_code == 200 and cors.headers['access-control-allow-origin'] == 'http://127.0.0.1:3001'
        if mode == 'baseline':
            if 'screenshot_id' in data:
                raise SystemExit('Baseline already exists; use verify')
            data['screenshot_id'] = shot['id']
            MANIFEST.write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(json.dumps({'mode': mode, 'ready': 'PASS', 'filtered_list_detail_content_unicode_expected_cors': 'PASS', 'screenshot_id': shot['id'], 'sha256': data['fixture_sha256']}))

if __name__ == '__main__':
    main()
