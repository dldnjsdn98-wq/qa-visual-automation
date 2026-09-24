# Quick Start

Game Multilingual QA Visual Automation System — **Phase 1 Web/Backend 구현, 전체 acceptance 대기 중**입니다.
현재 구현: FastAPI/Next.js 기반 Project·Build·Locale·Category·Situation CRUD,
String ID 기반 다국어 문자열, 수동 Screenshot 업로드·상세·Expected Strings·필터,
PostgreSQL 도메인 schema와 Alembic migration. OCR·게임 자동화는 후속 단계입니다.

설치·API·DB/storage·검증 상세는 [Backend owner runbook](backend/README.md),
화면 흐름·API origin 설정·Frontend 검증은 [Frontend owner runbook](frontend/README.md)을 따릅니다.
[독립 Web review](.orchestration/reports/REVIEW-WEB-001-08.md)의 실행 결과와 제한을 함께 확인합니다.
이후 [ENV-P1-DB-001 독립 closure](.orchestration/reports/ENV-P1-DB-001-08.md)는
환경 문제만 ACCEPTED로 판정했습니다. 이는 전체 Web review, 개별 AC-WEB 전체 기준 또는
Phase 1 acceptance 승인이 아니며, Phase 1 전체 acceptance는 여전히 대기 중입니다.

현재 열린 폴더가 프로젝트 루트입니다. 하위에 같은 프로젝트 폴더를 만들지 않습니다.
아래 명령은 루트의 PowerShell에서 실행합니다. Docker Desktop Engine이 실행되어 있어야 합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-env.ps1
docker compose up -d --build
docker compose ps
docker compose logs -f
```

setup-env.ps1은 .env가 없을 때만 임의의 로컬 DB 비밀번호를 생성합니다.
.env가 있으면 보존합니다. .env.example의 비밀번호는 placeholder입니다.
로그 보기는 Ctrl+C로 끝냅니다. 전체 종료는 다음과 같습니다.

```powershell
docker compose down
```

일반 down은 DB named volume을 보존합니다.

| 서비스 | 실제 호스트 주소 | 컨테이너 내부 포트 |
| --- | --- | --- |
| Frontend | http://localhost:3001 | 3000 |
| Backend liveness | http://localhost:8001/health | 8000 |
| Backend DB readiness | http://localhost:8001/ready | 8000 |
| FastAPI Docs | http://localhost:8001/docs | 8000 |
| PostgreSQL | 127.0.0.1:5433 | 5432 |

기존 서비스의 3000/8000/5432 점유 때문에 3001/8001/5433을 선택했습니다.
localhost 접속이 지연되면 HTTP 주소에도 127.0.0.1을 사용합니다.
Compose backend는 postgres:5432를, 로컬 Backend는 .env의 127.0.0.1:5433을 사용합니다.
Frontend는 Backend API에 연결된 CRUD·문자열 관리·업로드·Screenshot 검토 화면을 제공합니다.
API origin을 바꾸려면 Frontend runbook의 NEXT_PUBLIC_API_BASE_URL 설정과 재빌드 안내를 따릅니다.

## Local Development Quick Start

Python >=3.12,<3.13의 프로젝트 .venv를 사용합니다. 없으면 아래 생성 안내를 먼저 따릅니다.
활성화 없이 직접 실행할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install --require-hashes -r backend/requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
powershell -ExecutionPolicy Bypass -File .\scripts\setup-env.ps1
docker compose stop backend frontend
docker compose up -d postgres
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

첫 터미널을 유지하고 두 번째 터미널에서:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Frontend는 3001에서 실행됩니다. 각 개발 서버는 Ctrl+C로 종료합니다.
검증 이력과 실행 환경별 한계는 위 Web review 및 ENV closure 보고서에 기록되어 있습니다.
DB만 Compose를 사용하며, 별도 PostgreSQL을 사용하려면 .env의 DB 항목을 맞춥니다.

다른 PC에서 .venv가 없다면 Python >=3.12,<3.13을 준비한 후:

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
```

py가 없고 python --version이 3.12.x인 경우에만 python -m venv .venv를 사용합니다.
2026-09-05 Bootstrap 검증 당시에는 py/python이 PATH에 없어, 사용 가능한 Python 3.12 런타임으로 .venv를 생성했습니다.
시스템 Python 절대경로는 저장하지 않습니다. 가상환경은 다른 PC로 복사하지 말고 재생성합니다.
선택적으로 .\.venv\Scripts\Activate.ps1을 실행할 수 있지만 활성화는 필수가 아닙니다.

## Migration

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

현재 migration head는 0002_phase1_domain입니다. 빈 0001_bootstrap baseline 다음에
9개 도메인 테이블과 scoped FK·삭제 제한·고유성/check 제약·인덱스를 생성합니다.
독립 Web review에서 fresh PostgreSQL migration/downgrade/re-upgrade 및 model parity를
격리된 테스트 DB로 검증했습니다. ENV closure에는 설정된 DB의 현재 head 독립 확인과
owner의 additive migration 실행 증거가 구분되어 있습니다. 이 결과만으로 AC-WEB-11 전체나
Phase 1을 승인하지 않습니다. downgrade/roundtrip은 폐기 가능한 테스트 DB에서만 수행하며,
기존 사용자 DB·volume·storage를 reset하지 않습니다.
Backend 컨테이너는 시작 시 upgrade head 후 Uvicorn을 실행합니다.
서비스 확대 시 migration을 단일 실행 작업으로 분리하는 것은 Architect의 후속 결정입니다.

## Tests and Build

의존성 설치 후 루트에서 (격리 PostgreSQL runner는 Docker Engine 필요):

```powershell
.\.venv\Scripts\python.exe backend/tools/run_postgres_tests.py -q --tb=short
.\.venv\Scripts\python.exe tests/frontend/run_integration.py --isolated-postgres
.\.venv\Scripts\python.exe -m pip check
docker compose config --quiet
```

frontend/에서 (npm.cmd ci로 의존성 설치 후):

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run typecheck
```

실제 npm scripts: dev, build, start, typecheck, test, test:integration.
npm.cmd test는 Vitest unit/component 테스트이며, 실제 API 통합 검증은 위 Python runner가
FastAPI·Alembic·임시 PostgreSQL DB/storage를 준비한 뒤 test:integration을 실행합니다.
두 격리 runner는 자체 테스트 자원을 정리하며 기존 설정 DB를 migration/reset하지 않습니다.
Backend 테스트는 tests/backend/에 CRUD·Unicode·업로드/storage·동시성·migration 검증을 포함합니다.
설정된 PostgreSQL을 사용하는 pytest 실행 조건과 Linux/clean-install 검증은 Backend runbook을 따릅니다.

2026-09-08~09 독립 Web review의 기록: Windows Backend 54 PASS, Frontend 23 PASS,
typecheck/build PASS, 실제 TypeScript client 통합 2 PASS. 이는 해당 시점과 환경의 실행 증거이며,
현재 checkout의 재실행 결과나 전체 Phase 1 acceptance PASS를 뜻하지 않습니다.
scripts/check_bootstrap.py는 초기 역할/작업/phase 상태를 assert하는 역사적 Bootstrap 전용 검사입니다.
현재 상태 검증 명령으로 사용하지 않으며, 검사에 맞추어 orchestration 상태를 되돌리지 않습니다.

## Historical Bootstrap Environment / Verification — 2026-09-05

아래는 초기 Bootstrap 시점의 기록입니다. 현재 기능·테스트 수·migration head·진행 상태를 나타내지 않습니다.

| 항목 | 실제 결과 |
| --- | --- |
| Python / .venv | 3.12.14 / 3.12.14 PASS |
| py / python PATH | 사용 불가, 사용 가능한 3.12 런타임으로 .venv 생성 |
| Node / npm | v24.19.0 / 11.17.0 PASS |
| Git | 2.55.0.windows.3, 기존 저장소 main, 커밋 없음 |
| Docker CLI / Engine | 29.7.2 / 29.7.2 PASS |
| Docker Compose | v5.5.0 PASS |
| PostgreSQL | 17.11, 빈 DB 초기화와 baseline 적용 PASS |
| Python 설치 / pip check | PASS |
| Backend tests | 3 PASS, 라이브러리 deprecation 경고 2개 |
| Next.js | 16.3.4로 resolve, npm lockfile 생성 |
| Frontend | Windows build/typecheck PASS; Docker build 및 HTTP 200 PASS |
| Compose | config PASS; 전체 기동 PASS (포트 충돌 수정 후) |
| Migration | 컨테이너와 로컬 .venv에서 head 확인 PASS |
| HTTP | Frontend /health /ready /docs 응답 PASS |
| Orchestration | 10 prompts / 10 tasks / 7 phase gates 구조 검사 PASS |

초기 제한된 실행에서는 npm 네트워크와 Docker 접근이 거부됐고,
허용된 실행 권한으로 재실행해 성공했습니다. 초기 Compose 기동은 기존 포트 충돌로 실패했으며
프로젝트 포트를 변경해 해결했습니다. localhost DB 연결이 지연되어 127.0.0.1 및 5초 연결 제한을 적용했습니다.
한 권한 확장 테스트 실행에서 pytest 캐시 쓰기 경고가 추가로 발생했으나 테스트 3개는 통과했습니다.
실행하지 않은 확인을 Verified로 표기하지 않습니다.
상세 기록: [.orchestration/reports/bootstrap-report.md](.orchestration/reports/bootstrap-report.md).

## Directory Structure

```text
backend/                 FastAPI app, Dockerfile, migrations
frontend/                Next.js App Router, Dockerfile, npm lockfile
worker/{ocr,verification}/
agent/{screenshot_upload,visual_automation}/
shared/{schemas,models}/
captures/{pending,uploaded,failed,debug,recordings}/
storage/local/
docs/{prompts,architecture,api,phases}/
.orchestration/
  PROJECT_STATE.yaml
  TASKS.yaml
  ACCEPTANCE.yaml
  DECISIONS.md
  handoffs/
  reports/
tests/{backend,frontend,upload,ocr,automation,integration}/
scripts/
pyproject.toml
alembic.ini
docker-compose.yml
.env.example
.gitignore
```

## Orchestration and Next Tasks

.orchestration/이 진행 상태의 Single Source of Truth입니다.
역할 활성화 및 Task/AC/Phase 상태 변경은 PM이 해당 상태 파일과 handoff/review 증거를 대조하여 관리합니다.
2026-09-05 Bootstrap 당시에는 01/02 ACTIVE, ARCH-001 READY였으며 역할별 Codex task를 생성하지 않았습니다.
이 초기 기록은 현재 상태가 아닙니다. 독립 Web review는 ARCH-001 revision 2의 기존 승인을 유지하며,
ENV closure 이후에도 전체 Phase 1 acceptance는 대기 중입니다.
08은 READY_FOR_REVIEW 발생 시, 10은 사용자 Commit/Push 요청 때만 동작합니다.
역할별 task를 새로 만들고 docs/prompts/의 해당 파일을 읽도록 지시합니다.
이 Bootstrap task를 특정 역할 task로 재사용하지 않습니다.

[Architecture](docs/architecture/overview.md)와 관련 승인 기록을 함께 확인합니다.
모든 required acceptance PASS와 Reviewer 승인 없이 다음 Phase를 완료 처리하지 않습니다.

## Phase 1 Scope / Later-Phase Plans

Phase 1 구현 범위: Project/Build/Locale/Category/Situation CRUD, string_id 기반 다국어 문자열,
수동 Screenshot 업로드, 상세/Expected Strings 및 필터. 구현·검증 증거와 전체 acceptance 승인은 별개입니다.
아래는 후속 단계의 계획이며 현재 제공되는 CLI/기능이 아닙니다.
Phase 2: 재시도/오프라인 큐/중복방지/idempotency Upload Agent.
Phase 3: PaddleOCR/OpenCV/RapidFuzz와 PASS/REVIEW/FAIL.
Phase 4: ADB와 시각 Anchor 기반 자동화. Phase 5: Record & Replay.
Phase 6: State Graph / goto_state. Phase 7: E2E 통합.
이후 단계용 라이브러리와 Worker 서비스를 Bootstrap에서 설치·실행하지 않습니다.

Planned CLI (현재 실행 불가):
- python -m agent screenshot-upload
- python -m agent devices
- python -m agent screenshot
- python -m agent detect-state
- python -m agent run-scenario scenarios/example.yaml
- python -m agent goto-state reward

## Rules / Troubleshooting

게임 내부 API, memory, Unity/Unreal Object, resource-id, 내부 이벤트/script/hook 사용 금지.
스크린샷·ADB 입력·OpenCV·visual template·OCR 보조만 사용합니다.
오프라인에서 스크린샷 원본을 삭제하지 않습니다.
.env, 실제 QA 데이터, captures 이미지, storage, .venv는 Git 제외입니다.
명시적 요청 전에는 commit/push하지 않으며, push는 역할 10만 담당합니다.

PowerShell npm.ps1 정책 오류가 있으면 문서처럼 npm.cmd를 사용합니다.
가상환경 활성화 정책 오류가 있어도 .venv Python 직접 실행은 가능합니다.
Docker 접근 오류는 Engine 실행 및 현재 계정의 접근 권한을 확인합니다.
.env 변경 시 기존 DB volume의 비밀번호가 자동 변경되지 않으므로 기존 값을 보존합니다.

공식 참고 문서:
[Next.js 설치](https://nextjs.org/docs/app/getting-started/installation),
[FastAPI 가상환경](https://fastapi.tiangolo.com/virtual-environments/).
