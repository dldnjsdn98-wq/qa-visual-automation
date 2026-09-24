"""Reviewer read-only configured DB/object/API check; no seed, migration or restart."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import httpx
from sqlalchemy import text
from backend.app.config import get_settings
from backend.app.db import engine
from backend.app.storage.local import LocalStorage, ROOT as ADAPTER_ROOT


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    baseline = ROOT / '.orchestration/reports/ENV-P1-DB-001-records.json'
    before = baseline.read_bytes()
    fixture = json.loads(before)
    expected_root = ROOT / 'storage/local'
    assert ADAPTER_ROOT == ROOT and expected_root.is_dir()
    settings = get_settings()
    assert settings.storage_root == 'storage/local'
    adapter = LocalStorage(settings.storage_root)
    assert adapter.root == expected_root
    with engine.connect() as connection:
        connection.exec_driver_sql('SET TRANSACTION READ ONLY')
        identity = tuple(connection.execute(text('SELECT 1,current_database(),current_user')).one())
        revision = connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        rows = connection.execute(text('SELECT id,project_id,build_id,locale_id,category_id,situation_id,storage_key,file_hash,size_bytes FROM screenshots')).mappings().all()
    by_id = {str(row['id']): row for row in rows}
    old_id = fixture['screenshot_id']
    new_id = 'b55d0ba3-90d7-4e9b-b1d7-b30f5d50f77d'
    assert old_id in by_id and new_id in by_id
    for row in rows:
        stream, length = adapter.open_read(row['storage_key'])
        with stream:
            data = stream.read()
        assert length == row['size_bytes'] == len(data)
        assert digest(data) == row['file_hash']
    old = by_id[old_id]
    new = by_id[new_id]
    legacy_root = ROOT.parent / 'storage/local'
    assert digest((legacy_root / old['storage_key']).read_bytes()) == fixture['fixture_sha256']
    assert old['file_hash'] == new['file_hash'] == fixture['fixture_sha256']
    assert not (legacy_root / new['storage_key']).exists()
    assert str(new['build_id']) == '661e4f6c-b9e2-41c4-a878-edf54d290395'
    for key in ('project_id','build_id','locale_id','category_id','situation_id'):
        assert str(old[key]) == fixture[key]
    with httpx.Client(base_url='http://127.0.0.1:8001', timeout=15) as client:
        assert client.get('/ready').status_code == 200
        for row in (old, new):
            base = f"/api/v1/projects/{row['project_id']}/screenshots/{row['id']}"
            response = client.get(base)
            response.raise_for_status()
            detail = response.json()
            assert detail['id'] == str(row['id'])
            for key in ('project_id','build_id','locale_id','category_id','situation_id'):
                assert detail[key] == str(row[key])
            assert (detail['width'],detail['height'],detail['size_bytes'],detail['source']) == (128,72,243,'manual')
            image = client.get(detail['content_url'])
            image.raise_for_status()
            assert digest(image.content) == row['file_hash'] == detail['file_hash']
            expected = client.get(base + '/expected-strings')
            expected.raise_for_status()
            result = expected.json()
            if str(row['id']) == old_id:
                assert result['items'][0]['text'] == '한국어 日本語 中文 العربية 😀 e\u0301'
                assert result['missing_count'] == 0
            else:
                assert result['items'] == []
    assert baseline.read_bytes() == before
    print(json.dumps({'checked_at_utc':datetime.now(timezone.utc).isoformat(),
        'result':'PASS','actual_adapter_root':str(adapter.root),
        'authenticated_identity':identity,'migration':revision,
        'db_reference_count':len(rows),'all_reference_hashes':'PASS',
        'legacy_original_retained':'PASS','new_object_absent_at_legacy_root':'PASS',
        'original_and_new_api_readback':'PASS','baseline_sha256':digest(before),
        'original_id':old_id,'new_id':new_id,'image_sha256':fixture['fixture_sha256']},ensure_ascii=True))


if __name__ == '__main__':
    main()
