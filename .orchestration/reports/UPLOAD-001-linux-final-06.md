# UPLOAD-001 final Linux synthetic evidence addendum

Date: 2026-09-25 KST. Task: `UPLOAD-001`. Contract: `P2-UPLOAD-v1`, document revision 2. This is a cross-platform validation addendum only; it changes no product source and does not replace `.orchestration/reports/UPLOAD-001-06.md`.

## Result

The final uploader source, including the five F26 restart-refusal parameter cases added after the earlier Linux snapshot, was executed from a clean bytecode-free copy in an ephemeral Linux container.

- Collection: **63 items**.
- Synthetic result: **62 passed**.
- Opt-in live result: **1 skipped**, exactly `tests/upload/integration/test_live_response_loss.py`; `--run-live-upload` was intentionally omitted.
- Duration reported by pytest: **1.16s**.
- Hash-locked dependency installation: **PASS**.
- `pip check`: **PASS**, `No broken requirements found.`
- Bytecode under the execution source root: **0 before**, **0 after**.
- Qualifying evidence interval: `2026-09-24T16:52:25Z` through `2026-09-24T16:52:37Z` (`2026-09-25 01:52:25` through `01:52:37` KST).

This closes the Reviewer 08 preflight gap that the previous Linux `57 passed, 1 skipped` evidence predated the final F26 matrix. It does not rerun or supersede the owner Windows `63 passed` live result and does not claim cross-service validation against Backend changes still in progress.

## Isolation and environment

- Host workspace: `C:\Dev\qa-visual-automation`, mounted at `/workspace` read-only.
- Input image: `qa-backend-upload-final:local`, recorded image ID `sha256:8bb295a1ec56`.
- Execution source root: `/tmp/upload-source-clean`, populated only with `agent/screenshot_upload`, `tests/upload`, and `pyproject.toml` from the read-only mount.
- Existing `__pycache__` directories and `*.pyc` files were removed from the temporary copy before execution.
- Virtual environment: new `/tmp/upload-linux-final-06-clean` inside the ephemeral container.
- OS: Debian GNU/Linux 13 (trixie), x86_64, kernel `6.18.33.2-microsoft-standard-WSL2`.
- Runtime: Python `3.12.14`, pytest `9.1.1`, pluggy `1.6.0`.
- Network: default bridge was used only to install hash-locked dependencies. No database, Backend, Web runtime, Docker socket, shared service, or user data was mounted or contacted.
- Container was removed by `docker run --rm` after the command.

## Exact command

Host invocation:

```powershell
docker run --rm --name qa-upload-linux-final-06-clean -v "C:\Dev\qa-visual-automation:/workspace:ro" -w /workspace qa-backend-upload-final:local sh -ec '<evidence script below>'
```

The evidence script copied only the declared source surface to `/tmp`, deleted bytecode, created a new venv, installed the checked lock with hashes, checked the environment, and ran this exact test command:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 \
  /tmp/upload-linux-final-06-clean/bin/python -m pytest tests/upload -ra \
  -p no:cacheprovider --basetemp=/tmp/upload-linux-final-06-clean-pytest
```

The dependency commands were:

```sh
python -m venv /tmp/upload-linux-final-06-clean
/tmp/upload-linux-final-06-clean/bin/python -m pip install \
  --disable-pip-version-check --quiet --require-hashes \
  -r /tmp/upload-source-clean/agent/screenshot_upload/requirements.lock
/tmp/upload-linux-final-06-clean/bin/python -m pip check
```

## Source manifest

`agent/screenshot_upload/requirements.lock` SHA-256: `ff214596558d1af98ab54b54fd0271a4ef5e0059d5df4d7b520738aa52cf5344`.

The aggregate is SHA-256 over the exact sorted `sha256sum` lines below, including the final LF: `593e1925a36e55b667c752be7cc10ea944f14cf81f034f5d112d23358f7a563e`.

```text
3a1e99173d7efe67005b34ff02e85752199c5d4a093166e784e6a076b9a0d5d2  agent/screenshot_upload/__init__.py
fd5c536a58f94d9396efbe2e456addf06b85d5614f9817eb738c5bc293f705aa  agent/screenshot_upload/__main__.py
39d71c9aa3080e00e05bb1a20cc111b6d689ccb9f49450cb083d38be391d8868  agent/screenshot_upload/ack.py
e764bd620329881f4837e8040ac259b98d38e29c6a8134ff8cff9616106405cc  agent/screenshot_upload/canonical.py
9f9355a33f85d4b4af23fbc22be8302842cdf1c544cb4163aefe1b40e5334160  agent/screenshot_upload/client.py
5385fd90f751d9f5bc5c53e7fcdd7f166b83771ed775c6098e06bbbe70863b89  agent/screenshot_upload/config.py
762e1f6426f77a81191de5908b95a4f2347635b922eeb66224f1ea93e0eb2bf3  agent/screenshot_upload/durable_fs.py
32ca94bb5c6ff302ee17323d90c754ebbbef9608e7baf69c87c10bd48e6e0734  agent/screenshot_upload/faults.py
d1c60c9e448a68f204e57610ad9adaacbe47fef7c2f10f8cfd4bd45f9ae182e0  agent/screenshot_upload/image.py
f0fb85e62c62095d28e511d51506fcbe1f190e21463dd86f0b621338d9dcb955  agent/screenshot_upload/jsonio.py
bd1f9525504b03dc73958aaf9aad4da5b6cf484446f0aed08c458d815ca53113  agent/screenshot_upload/lock.py
5c0128c9fe74d86bbb6826bf8b1f4c4d520fbb31cf395fb80f906d98106b558d  agent/screenshot_upload/manifest.py
495043aa7aacdf61ee3bb2cca10d08cd6d417c8507132a41db1377c11d81bb5f  agent/screenshot_upload/marker.py
740a4453eabdee17ead080a4d6ca1586a2a68975d0e06980bdb2870ecb9bbdf8  agent/screenshot_upload/origin.py
a10789d1cf040fc4c9369638d0acf6855b64d9208e59acffbec26320e1d8fda1  agent/screenshot_upload/producer.py
8c922ced83b0522587c120bd609bbd63b14f6567e4a71a5a9c92b6686b84ba4c  agent/screenshot_upload/recovery.py
8573ac47bec35d32aac38d2dfb133b8e8c2cef8e49d5af2d864a85282a26240e  agent/screenshot_upload/requeue.py
8226fc52559541df5b9704183f659f079cc93baaa2ebc0179e87ac67f806c489  agent/screenshot_upload/requirements.in
ff214596558d1af98ab54b54fd0271a4ef5e0059d5df4d7b520738aa52cf5344  agent/screenshot_upload/requirements.lock
e95a6df87812cbfb3c657170a465a1a7528c7380bba3e67d4c2d15b20a946f57  agent/screenshot_upload/retry.py
988488d8198a018af7032350d91e27798c5f75cbed53338bb31cc292c09dc0a7  agent/screenshot_upload/runtime.py
76cf03138773aefac8ec510f597c09576a0558ab9624d4b0c0452d5545c2e8dc  agent/screenshot_upload/spool.py
72081aa1113c58bc148d85afb5e261c6666c3ce9bef82f20b37538ca218327b0  agent/screenshot_upload/state.py
0c6e3583201fd985c5e8f9f295fe8ab51843dcdc36304e4211c3f18ada058771  agent/screenshot_upload/state_store.py
4581595313ba3c340ceb9f148d0eeffc50f90d1e8ef8b8e3c06012597375b7aa  agent/screenshot_upload/worker.py
4994a233f7519fd6f6252810d58b73e4f655cd07ba7ff1b4226110409f9fe3f4  tests/upload/conftest.py
188d511f432820c58692a64a30ffac63fc86ed50eb5ca726005a0ceaa1f137d2  tests/upload/integration/response_loss_agent.py
049c715f42df62f0d9e0747bc20827911bb68afd6c1ae7453903ae3e46f34422  tests/upload/integration/test_live_response_loss.py
0b9df46bc337e0a81ede249f5c384ec401e56325ee62100dc71b0983ab5e94ba  tests/upload/support/fakes.py
c1cbce3c32f4bc30eca269dcb1c4a22eeac59a77a49355b31881a7741859a7cf  tests/upload/test_origin_binding.py
93f19c0e4f799f80580cfabc9591708d1fb38742d67cb77eb89280e3eb742e2f  tests/upload/test_producer_state.py
0ce5eaa7b62ce23a6fed89a4849aa9eeec2e5942173f327d99ba2bf5a0de536b  tests/upload/test_protocol_json.py
d7e8048c4586f1972540d4f4da9f557a1efadc6d7c8e5f1a57242c3fccc57926  tests/upload/test_worker_recovery.py
0024490e4faf1ca7bb21a25ec0c19fe72486229dd82f394fb157366de43bc003  pyproject.toml
```

## Installed environment manifest

```text
alembic==1.20.0
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.7.22
click==8.5.0
colorama==0.4.6
fastapi==0.141.1
greenlet==3.5.6
h11==0.16.0
httpcore==1.0.9
httptools==0.8.0
httpx==0.28.1
idna==3.20
iniconfig==2.3.0
Mako==1.4.3
MarkupSafe==3.0.3
packaging==26.3
pillow==12.3.0
pip==25.0.1
pluggy==1.6.0
psycopg==3.3.6
psycopg-binary==3.3.6
pydantic==2.13.5
pydantic_core==2.46.5
pydantic-settings==2.15.0
Pygments==2.21.0
pytest==9.1.1
python-dotenv==1.2.3
python-multipart==0.0.32
PyYAML==6.0.3
rfc8785==0.1.4
setuptools==84.0.0
SQLAlchemy==2.0.54
starlette==1.7.0
typing_extensions==4.16.0
typing-inspection==0.4.4
tzdata==2026.4
uvicorn==0.53.0
uvloop==0.22.1
watchfiles==1.3.0
websockets==17.1
```

## Pytest raw output

```text
============================= test session starts ==============================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0
rootdir: /tmp/upload-source-clean
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 63 items

tests/upload/integration/test_live_response_loss.py s                    [  1%]
tests/upload/test_origin_binding.py .................................... [ 58%]
..                                                                       [ 61%]
tests/upload/test_producer_state.py ......                               [ 71%]
tests/upload/test_protocol_json.py ..........                            [ 87%]
tests/upload/test_worker_recovery.py ........                            [100%]

=========================== short test summary info ============================
SKIPPED [1] tests/upload/integration/test_live_response_loss.py:144: pass --run-live-upload for disposable PostgreSQL/uvicorn integration
======================== 62 passed, 1 skipped in 1.16s =========================
```

## Non-qualifying setup attempts

The first diagnostic execution mounted the workspace read-only and passed, but its skip location printed a Windows path, showing that Python had read a pre-existing Windows `__pycache__` entry. It is not used as final source-execution evidence. A subsequent clean-copy setup command stopped before venv creation or test execution because it incorrectly expected `agent/__init__.py`; `agent` is a namespace package. The qualifying execution above removed that invalid manifest assumption, proved zero bytecode files before and after, and is the only clean-copy suite result claimed here.

## Boundary

No product source, original owner report, PM YAML/decisions, Backend, Frontend, Web runtime, shared service, database, commit, push, or IP check was changed or used. AC-P2-01 through AC-P2-04 remain PM/reviewer-controlled and are not inferred by this addendum.
