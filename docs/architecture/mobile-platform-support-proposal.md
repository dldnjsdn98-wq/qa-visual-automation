# Android·iOS 블랙박스 UI 검사 플랫폼 지원 제안

초안 작성일: 2026-09-22. 재개·제출 검증일: 2026-09-25. 상태: **설계 제안 / 모바일 구현·기기 검증 NOT_RUN / 본 제안의 독립 acceptance 미획득**.
소유 파일: `docs/architecture/mobile-platform-support-proposal.md` 한 개. 작업 루트: `C:\Dev\qa-visual-automation`. Branch/commit: null/null; Commit/Push 없음.

## 1. 결론과 확인 범위

Windows에서 Android는 ADB 기반 원본 캡처·시각 좌표 입력을 확장하고, iOS는 실기기에서 촬영한 원본 파일의 수동 반입부터 지원하는 순서를 제안한다. iOS 자동화는 별도 macOS worker와 서명된 테스트 runner를 사용하는 후속 선택지다. 앱 소스 없이도 외부 화면 검사는 가능하지만, 설치 가능한 게임 빌드·계정·검사 화면 접근권한은 필요하다. 이 문서는 새 제품 기능이나 지원 인증을 의미하지 않는다.

저장소에서 직접 확인한 사실:

| 근거 | 확인 내용 | 해석 한계 |
| --- | --- | --- |
| `.orchestration/PROJECT_STATE.yaml`, `TASKS.yaml`, `ACCEPTANCE.yaml`, `DECISIONS.md` | 9/22 초안 당시 revision1 검토 단계. 9/25 재개 시 Phase 1 ACCEPTED 유지, Phase 2 revision2 계약 ACCEPTED 및 제품 CHANGES_REQUESTED; AC01/03 FAIL, AC02/04 NOT_RUN | 계약 승인과 제품 acceptance는 별개. 해당 기록을 읽었으며 제품 테스트를 다시 실행한 것은 아님 |
| `.orchestration/handoffs/PHASE-2-review-recovery-rework-01.md`, `.orchestration/reports/REVIEW-UPLOAD-001-08.md` | Backend005/009, uploader006/007, Web008 보완 및 독립 실행 증거 확보가 기존 담당 범위 | 본 모바일 제안은 해당 결함을 수정하거나 종료 판정하지 않음 |
| `.orchestration/handoffs/PHASE-1-acceptance-01.md` | 수동 업로드·다국어 관리 포함 13개 Web AC 완료 기록 | Android/iOS 기기별 캡처 지원을 검증한 기록은 아님 |
| `docs/prompts/01_pm.md`, `02_architect.md`, `06_screenshot_agent.md`, `07_visual_automation.md`, `08_reviewer.md` | PM gate/소유권, 원본 보존, ADB 입력 및 시각 인식 허용, 게임 내부 접근 금지 | iOS WDA 입력 허용이 명시되어 있지 않음 |
| `docs/architecture/overview.md`, `domain-model.md`, `api-contract.md`, `data-flow.md` | 캡처와 업로더 분리, bounded open CaptureMetadata, 원본 저장 | metadata 확장 공간이 있다는 사실과 전용 UI/검증 기능 구현 여부는 별개 |
| `docs/phases/phase-4-automation.md`, `phase-7-integration.md` | Phase 4 ADB 자동화 및 Phase 7 Android 흐름은 계획 상태 | 본 제안으로 기존 phase gate를 앞당기지 않음 |
| `docs/architecture/phase-2-upload-contract.md` §§1,2,7,8 및 `REVIEW-ARCH-UPLOAD-001-revision-2-08.md` | revision2 계약 승인 기록 확인; 원본·metadata 불변 의도, marker-last publication, immutable spool binding, 업로더 분리 | 계약은 이 작업에서 수정하거나 재심사하지 않으며 제품 승인으로 해석하지 않음 |

지침 탐색: 9/22 초안 당시 루트 및 적용 상위/하위 경로에서 AGENTS.md를 찾지 못했으나, 9/25 재개 시 생성된 루트 `AGENTS.md`를 직접 읽고 적용했다. 기존 파일 소유권·독립 gate를 유지하며 차단 작업 반복/우회, push/배포/사용자 데이터 삭제/DB 초기화/계정 보안 변경은 하지 않는다. 기존 임시 테스트 디렉터리 하나의 접근 거부는 당시 탐색 한계이며 재탐색하지 않았다. 외부 공식 문서의 최신 내용을 이번 작업에서 조회하지 않았으며, 아래 플랫폼 설명은 일반적인 도구 전제에 기반한 제안이다. 실제 설치 버전·실기기 조합에서 후속 검증한다.

## 2. 지원 경로와 전제

| 경로 | 호스트·기기·설치 전제 | 지원 제안 및 제외 |
| --- | --- | --- |
| Android 수동 파일 | Windows, 설치·실행 가능한 게임, 기기 screenshot 원본 전송 | 현재 수동 PNG/JPEG 업로드 경로 이용 가능성 검증; 플랫폼별 제품 PASS는 별도 |
| Android 자동 캡처 | Windows Platform Tools/ADB, USB 데이터 연결, 필요한 OEM 드라이버, USB debugging·기기 RSA 승인, 선택한 serial이 `device` 상태 | 캡처 + 허용 ADB 입력 + 시각 상태 확인; 소스/루팅 불필요. emulator는 APK ABI·GPU·로그인·게임 정책 호환 확인 후 보조 |
| iOS 수동 파일 | iPhone/iPad에 실행 가능한 게임, OS screenshot, Windows로 원본 파일 반입 | Xcode/WDA·개발용 서명 없이 촬영 가능. USB 전송은 잠금 해제/Trust 및 Apple 장치 지원 환경에 따라 검증; 원본 다운로드도 가능 |
| iOS 자동 캡처·좌표 입력 | 호환 macOS/Xcode host 또는 관리 Mac worker, 실기기 연결·Trust, 버전에 필요한 Developer Mode, WDA/XCTest runner 빌드·서명·provisioning | 게임 소스와 별개로 runner 준비 필요. Appium XCUITest 등 선택 도구/OS/Xcode 조합을 고정하고 실제 게임에서 검증 |
| iOS Simulator 보조 | macOS/Xcode와 simulator용 게임 build | 실기기용 IPA를 임의 실행할 수 없음. 소스·simulator build 미제공 조건에서는 확보되었다고 가정하지 않음 |

Windows만으로 Xcode 기반 iOS 자동화 환경을 완결했다고 주장하지 않는다. 이미 서명·설치된 runner나 제3자 Windows 도구가 일부 기능을 제공할 수 있어도 이를 기본 지원 경로로 약속하지 않는다. Mac worker 또는 device farm은 기기·OS 제공 범위, 앱 설치/계정 정책, 원본 반출, 네트워크 및 서명 수명 관리까지 별도 검증 후 선택한다. 현재 서버는 loopback 단일 운영자 설계이므로 Mac 연결 때문에 공개 바인딩/CORS를 자동 확대하지 않는다. 초기에는 원본과 sidecar를 Windows로 전달해 기존 업로더가 처리하고, 원격 제어/전송 보안 설계는 별도 승인 범위로 둔다.

iOS의 WDA는 외부 테스트 runner이며 게임 소스가 없어도 사용 후보가 될 수 있다. 그러나 현재 프로젝트의 ADB-only 허용 정책을 자동으로 확장하지 않는다. PM/Architect가 screenshot + 시각 좌표 tap/swipe만 허용하는 후속 정책을 검토해야 한다. 게임 accessibility hierarchy, resource-id, GameObject/Widget, debug API, 메모리, 내부 이벤트/스크립트, 주입·개발자 hook은 사용하지 않는다. 해당 정책 결정 전 iOS 자동화 acceptance는 BLOCKED 대상으로 두고 수동 검사는 독립 진행한다.

서명 전제는 게임 배포 서명과 runner 서명을 구분한다. App Store/TestFlight 등 정상 배포 게임을 다시 서명해야 한다고 단정하지 않는다. 별도 IPA는 정상 설치 자격·provisioning·만료 상태가 필요하다. runner는 서명 identity/team과 기기용 profile, trust, OS 요구사항을 확인한다. 개인 무료 provisioning의 제약/만료 및 유료 계정 필요 여부는 실제 배포 방식으로 결정하며 모든 수동 검사에 유료 개발자 계정이 필요하다고 하지 않는다.

## 3. 수집·입력·복구 흐름

1. 실행 프로필을 고정한다: 게임 build와 배포 출처, 플랫폼/기기/OS, 언어, orientation, display 설정, 시나리오와 checkpoint. 실기기 보유 여부와 지원 OS 범위는 아직 미확정이다.
2. Android는 `adb devices -l`로 대상 상태를 확인하고 모든 명령에 `-s <serial>`을 지정한다. `getprop ro.product.model`, `getprop ro.build.version.release`, `getprop ro.build.version.sdk`, `wm size`, `wm density`는 후속 probe 후보다. 명령 출력은 OEM/OS별로 달라 raw 증거와 parser 실패를 보존한다. 실제 serial은 공개 metadata 대신 로컬 매핑의 별칭으로 연결한다.
3. 캡처 후보는 `adb -s <serial> exec-out screencap -p`의 binary stdout 직접 저장이다. PowerShell 버전별 텍스트 리다이렉션으로 PNG가 변형되지 않도록 binary subprocess 저장을 구현·검증한다. 대안은 기기 임시 PNG 생성 후 `adb pull`이다. 명령 exit code뿐 아니라 PNG 완전 decode·크기·hash를 확인한다. 이 문서의 명령은 실행하지 않았다.
4. 수동 iOS는 OS screenshot 원본을 USB 또는 원본 다운로드로 반입한다. 메신저 압축본, 브라우저 화면 재촬영, 녹화 추출본을 OS screenshot 원본으로 분류하지 않는다. Photos의 편집/변환 여부와 실제 PNG/JPEG 형식을 확인한다. 기기 측 hash 확보가 불가능하면 Windows 최초 수신 hash부터 보존하며 전송 전후 동일성은 미검증으로 남긴다.
5. locale는 OS 언어, per-app 언어, 게임 내 언어를 별개로 기록한다. 게임 화면에서 실제 적용 언어를 확인하고 필요한 재시작·재진입을 수행한다. `adb input text`가 임의 Unicode/CJK를 정상 입력한다고 가정하지 않는다. 설정 UI의 수동 변경을 허용하며 game locale API는 쓰지 않는다.
6. 화면 안정화와 required/optional/forbidden 시각 anchor를 확인하고 checkpoint를 촬영한다. 애니메이션·네트워크 지연에는 bounded polling과 timeout을 사용한다. 불명확한 상태에서 좌표 입력을 반복하지 않고 원본·마지막 상태·진단을 남긴다. 보호 화면의 검은 캡처, USB 끊김, 권한 실패는 성공으로 처리하지 않는다.
7. Phase 1 경로는 기존 `source=manual` 업로드를 유지한다. 미래 agent import는 `source=agent`, 시각 시나리오 producer는 `source=automation`을 제안하되 Phase 2 승인 계약의 의미를 따른다. 사람 촬영 여부는 별도 capture_method로 기록한다. 플랫폼을 source enum에 추가하지 않는다.
8. 미래 producer는 승인된 06 helper로 original/manifest/ready를 발행하고 기존 업로더에 넘긴다. 임의 파일 복사만으로 `captures/pending`을 ready로 만들지 않는다. 재전송 중 metadata를 보완하거나 UUID를 바꾸지 않는다. 수정된 context는 명시적인 새 capture intent이며 이전 원본을 보존한다.

revision2 연결 원칙: Windows local spool의 기존 `binding.json` 목적지 권위와 검증 순서를 따른다. Mac에서 네트워크 공유 spool을 직접 조작하거나 기존 ACK를 다른 Backend로 옮기지 않는다. 별도 수신 staging에서 원본을 확인한 뒤 Windows producer가 로컬에 발행하는 경로를 제안한다. 플랫폼 수집기 연결은 현재 06의 파일시스템/origin 수정 및 독립 검증을 대체하지 않는다.

## 4. 해상도와 좌표계

| 개념 | 의미 | QA 증거로 인정하는 범위 |
| --- | --- | --- |
| 물리 패널 해상도 | 실기기 display mode의 실제 pixel 격자 | 다른 panel/aspect/cutout을 검사하려면 해당 실기기 또는 명시적인 별도 display mode에서 재실행·재캡처 |
| OS 논리 display/밀도 | Android display size/density, iOS point 크기·Display Zoom 등 | 앱이 실제 재배치한 화면을 촬영해야 해당 설정 검사. panel 자체가 바뀌었다고 표기하지 않음 |
| 게임 render target | 엔진 내부 렌더링 크기/dynamic resolution | 블랙박스 screenshot만으로 확정 불가; `unknown` 유지 |
| 캡처 bitmap | 디코딩한 width/height 및 방향 | 서버 width/height 및 기존 `metadata.resolution`의 유일한 의미 |
| 사후 이미지 resize/crop | 원본에 대한 분석용 파생물 | OCR/정규화 보조만 가능. 다른 기기에서 layout을 재실행한 증거가 아님 |

Android `wm size`/`wm density` override는 compositor/논리 화면 조건에 영향을 줄 수 있지만 패널·실제 notch·OS·GPU를 다른 기기로 바꾸지 않는다. 크기만 변경하면 dp 영역·밀도·letterbox가 함께 달라질 수 있어 size/density 쌍과 전후 상태를 기록한다. 변경 전 현재 override를 저장하고 종료/오류 시 그 값으로 복구한다. 원래 override가 없었던 항목만 reset한다. 매번 무조건 reset해서 운영자의 기존 설정을 지우지 않는다. game 재시작 후 변화가 없으면 해당 셀을 대체 검증 성공으로 세지 않는다.

`wm size` 출력의 `Physical size` 라벨도 제조사 panel/native mode의 증명은 아니다. base display 값과 panel 사양을 별도 보존한다. baseline은 override 없이 실행하고, override 지원을 선언할 때만 size-only/density-only/both를 추가 검증한다. 회전·display 상태를 캡처 직전/직후 관찰해 바뀐 샘플로 입력하지 않으며 bounded retry한다. 알려진 crop/scale의 모서리·중앙점 역변환 오차는 원본 1 pixel 이하를 제안하고 실제 입력 변환은 별도 calibration으로 검증한다.

iOS 실기기에는 Android `wm size`와 동등한 일반 해상도 override를 기본 전제로 두지 않는다. 제공되는 Display Zoom/접근성 설정은 해당 설정의 검사이며 임의 pixel 해상도 보장이 아니다. simulator preset도 실기기 인증을 대신하지 않는다.

iOS OS screenshot과 WDA screenshot의 crop/orientation/색공간/보호 콘텐츠 처리가 같다고 가정하지 않는다. capture_method별 baseline을 분리하고 같은 실기기 비교 후에만 공통 기준 사용 여부를 결정한다. Mac worker는 runner 서명 자산을 Keychain 등 호스트 자격증명 저장소에 두고 metadata에 넣지 않는다. 재부팅 후 잠금 해제, trust prompt, 자동 잠금, USB 단절, runner 만료·재설치의 운영 복구를 검사하며 제어 endpoint는 loopback 또는 검토된 격리망에 제한한다.

좌표의 기준은 **현재 orientation의 전체 캡처 bitmap 좌상단 (0,0), 단위 px**다. portrait native panel 크기와 rotated screenshot 크기를 분리한다. 검출용 resize/crop을 사용하면 scale, crop origin, rotation을 함께 저장해 원본 좌표로 역변환한다. 입력 대상은 Android display 좌표 또는 iOS runner point 좌표일 수 있으므로 별도 calibration을 거친다. 예를 들어 축 정렬 crop의 검출 좌표는 `x_original = crop_left + x_analysis / scale_x`로 되돌리며, 이후 원본→입력 변환을 적용한다. 회전·letterbox가 있으면 단순 width 비율만 사용하지 않는다. 회전/설정 변경 후 calibration을 폐기하고 재측정한다.

safe area는 bitmap에서 보이는 안전영역과 앱이 실제 적용한 inset을 구분한다. 블랙박스에서 UIKit/엔진의 내부 safe-area 값은 확정하지 못한다. 기기 사양 기반 추정, OS 외부 관찰, 사람 annotation의 출처·확신도를 기록한다. unknown을 0으로 채우지 않는다. cutout/rounded corner/home indicator/gesture bar, game viewport·letterbox, 일시적 keyboard/permission overlay를 별도로 기록한다. 가로 양방향에서 비대칭 notch 위치와 중요한 버튼·문구 가림을 검사한다.

## 5. CaptureMetadata 확장 제안

기존 reserved key 의미·형식을 유지한다: `device`는 200자 이하 문자열, `resolution`은 decoded bitmap과 동일한 양의 정수 width/height, `run_id` UUID, scenario/checkpoint/screen_state 128자 이하. 기존 metadata_version=1을 DB나 플랫폼 schema 버전으로 재사용하지 않는다. 추가 이름공간 `mobile`과 `profile_version:1`은 **소비자 간 의미를 합의할 제안**이며 서버 전용 validation/UI가 구현되었다는 뜻이 아니다.

| 필드(제안) | 값·출처 규칙 |
| --- | --- |
| mobile.platform, device_alias, model, device_kind | android/ios, 비식별 별칭, 관찰 모델, physical/emulator/simulator |
| mobile.os_version, os_build, api_level | 기기 관찰값; Android API level만 해당 시 포함 |
| mobile.game_version, distribution | 외부 표시 version 및 store/testflight/package 등; relational build_id가 기준, 동일 build가 두 OS artifact를 묶으면 별도 artifact 식별자 기록 |
| mobile.os_locale, app_locale, game_locale, locale_evidence | 원문 보존, 가능하면 BCP 47; OS locale 추정만으로 game_locale 확정 금지; relational locale_id와 교차 검토 |
| mobile.orientation, display_mode | portrait/landscape_left/landscape_right 및 native/override/zoom 등 |
| mobile.panel_px, logical_size, density_dpi, pixel_scale | 측정 가능한 항목만, logical_size는 unit=dp/pt/display_px를 명시; screenshot만으로 panel 크기/scale 추정 금지 |
| mobile.override_size_px, override_density_dpi | Android override 실제 관찰값; 설정 유무도 기록 |
| mobile.aspect_ratio, viewport_px | aspect는 캡처 w:h에서 계산; viewport는 x/y/width/height와 annotation 출처 |
| mobile.safe_area | status=unknown/estimated/observed, source, 알려진 경우 top/right/bottom/left를 bitmap px 단위로 기록 |
| mobile.cutout_class, navigation_mode, text_scale | 관찰된 screen 위험조건; 앱이 text scale을 반영하는지 별도로 확인 |
| mobile.capture_method, captured_at, clock_source | os_screenshot/adb_screencap/wda, timezone 포함 시각, device/host/import_time; uploaded_at 대체 금지 |
| mobile.original_status, provenance | received_original/derived/unknown, 전송 경로·변환 유무; 원본 hash의 기준 지점 기록 |

unknown은 위 확장 profile에서 null 또는 생략으로 표현하되 reserved key는 null 금지다. 어떤 값도 모른다는 이유로 필수 관계 ID를 추정하지 않는다. raw ADB dump, 인증정보, UDID/serial, 계정명은 metadata에 넣지 않는다. 증거 파일 참조가 필요하면 검토 가능한 별칭만 사용한다.

아래는 실제 기기 증거가 아닌 **합성 예시**이며 `ScreenshotUpload.metadata`에 들어가는 객체만 나타낸다. 해상도는 가정한 원본 이미지와 반드시 일치해야 한다.

```json
{
  "device": "android-lab-a",
  "resolution": {"width": 2400, "height": 1080},
  "scenario": "settings-language",
  "checkpoint": "language-applied",
  "mobile": {
    "profile_version": 1,
    "platform": "android",
    "device_alias": "android-lab-a",
    "device_kind": "physical",
    "os_locale": "ko-KR",
    "game_locale": "ja-JP",
    "locale_evidence": "operator-checked-visible-menu",
    "orientation": "landscape_left",
    "display_mode": "native",
    "aspect_ratio": "20:9",
    "safe_area": {"status": "unknown", "source": "not-measured"},
    "capture_method": "adb_screencap",
    "original_status": "received_original"
  }
}
```

전체 CaptureMetadata는 compact literal-Unicode UTF-8 16 KiB, container depth 5, 모든 object key 총 100개 이하, 유한 숫자 및 기존 Unicode 제약을 지킨다. 완전한 request metadata part 32 KiB, 원본 20 MiB, whole request 21 MiB, PNG/JPEG 단일 frame, 각 dimension 16384 이하/총 4천만 pixel 제한도 유지한다. 초과 이미지를 몰래 resize해 원본으로 제출하지 않는다. 별도 보관 후 명시적 파생물 정책을 검토한다. Phase 2 fingerprint는 unknown metadata도 포함하므로 발행 후 mobile 값의 자동 보정/추가를 금지한다.

## 6. 최소 검증 매트릭스

특정 모델 구매를 전제하지 않는다. 먼저 게임의 실제 지원 OS 하한/상한과 전화기·태블릿·회전 지원, 출시 locale 목록을 확보한 뒤 다음 위험군에 보유/대여 기기를 배정한다. 없으면 해당 셀은 BLOCKED이며 비슷한 resize 이미지로 채우지 않는다.

| 프로필 | 최소 대표 조건 | 목적 |
| --- | --- | --- |
| A1 | Android 지원 하한 OS, 가장 작은 지원 논리 viewport, 가능하면 16:9 계열 | 좁은 UI, 기본 밀도 및 오래된 OS |
| A2 | Android 지원 상한 OS, 긴 화면비(예: 19.5:9/20:9), cutout·gesture 영역, 다른 density | edge/letterbox·배율 위험 |
| I1 | iOS 지원 하한 OS, 작은 지원 논리 viewport 실기기 | 작은 화면·기존 OS |
| I2 | iOS 지원 상한 OS, notch/Dynamic Island 등 비대칭 안전영역 실기기 | 가로 방향·home indicator 침범 |

이는 **최소 4개 실행 프로필**이지 반드시 실물 4대로 모든 조건이 충족된다는 뜻은 아니다. 하한 OS와 작은 화면을 한 기기에서 만족하지 못하면 셀을 분리한다. 태블릿 지원 시 Android tablet·iPad 각 1개 이상 추가하며 foldable을 지원하면 접힘/펼침 전환도 추가한다. 실제 native bitmap 크기·dp/pt viewport·density·OS build·orientation으로 profile을 고정한다.

언어는 최소 L0=기준 언어, L1=지원 언어 중 긴 라틴 문구(예: 독일어), L2=CJK(예: 일본어/한국어) 세 범주를 선택한다. 지원하지 않는 언어를 필수로 만들지 않는다. RTL 출시 언어가 있으면 L3=RTL을 필수 추가한다. 각 출시 locale는 적어도 OS별 대표 프로필 하나에서 별도 smoke를 수행한다. 세 범주의 통과를 모든 번역의 검증으로 해석하지 않는다.

기본 실행량: 4 프로필 × 3 locale 범주 × 게임의 기본 orientation 1개 × 5 checkpoint = **60 checkpoint 관찰**. 추가로 A2/I2 × 3 locale × 지원하는 반대 landscape 방향 × 동일 5 checkpoint = **30 관찰**. 회전 고정 게임이면 반대 방향은 N/A 근거를 기록한다. portrait도 지원하면 같은 위험군으로 전환·재배치 검사를 추가한다. RTL 필수이면 기본 20 및 반대 방향 10 관찰이 추가된다. OS×geometry 전수 조합은 아니므로 실패가 나온 OS/언어/화면군의 인접 조합을 확대한다.

5개 checkpoint는 (1) 로그인/최초진입·권한 복귀, (2) 메인 HUD·화면 가장자리, (3) 가장 긴 목록/상점·스크롤, (4) 확인/오류 modal 및 CTA, (5) 언어 변경 후 동일 화면 재진입으로 제안한다. 실제 게임에 없는 상황은 동등한 UI 위험을 가진 상황으로 매핑하고 근거를 남긴다. 글자 잘림·겹침·폰트 누락·줄바꿈·번역 fallback·RTL 방향·버튼 접근성·notch 침범을 관찰한다. 언어별 reference와 기대 문구를 고정하고 동적 영역 mask를 문서화한다. 단순 pixel diff/OCR confidence만으로 번역 정확성 PASS를 주지 않는다.

## 7. Acceptance 제안과 증거

아래 `MOB-*`는 본 문서에서만 사용하는 제안 ID이며 PM ACCEPTANCE.yaml을 변경하지 않았다. 현재 모두 **NOT_RUN**이다. 실행 시 PASS/FAIL/BLOCKED/N/A와 근거를 셀별로 기록하고, N/A는 게임 지원 범위 근거가 있어야 한다. 환경 미확보는 제품 FAIL과 분리한다.

| ID | 제안 수용 조건 | 필요한 증거 |
| --- | --- | --- |
| MOB-01 Android capture | 실기기 원본 완전 decode, correct serial·orientation·profile, 재캡처 3회 성공; unauthorized/offline/다중기기 오선택 시 안전 중단 | 명령/tool version·종료코드, 원본 hash/크기, 대상 별칭, 실패 진단 |
| MOB-02 iOS manual | 실기기 OS screenshot을 Windows로 원본 반입, provenance·locale·기기·OS 기록, 수동 업로드 후 동일 바이트 readback | 최초 수신 hash와 서버 content hash 동일, Web 관계 context 일치; 기기 측 동일성 미측정이면 명시 |
| MOB-03 geometry | native/override/resize를 구별, 알려진 inset·viewport의 단위/출처 일치, 회전 후 입력 calibration 검증 및 Android 원설정 복구 | 전후 screenshot/profile, 좌표 변환 검산, 원래 override 복구 기록; 미지원 override는 별도 BLOCKED/N/A |
| MOB-04 language/UI | 선택한 최소 matrix 모든 필수 셀 관찰, 중요 텍스트/CTA 잘림·가림·누락 0, 기대 locale/문구 확인 | 원본 screenshot ID, build/locale/situation, reference·사람 판정; 미해결 결함과 확장 검사 기록 |
| MOB-05 metadata | 합의된 mobile profile 저장/readback, reserved resolution 일치, unknown≠0, Unicode 보존, 경계 초과·불일치 거절 | 합성 경계 fixture 결과 및 실제 capture 1건/플랫폼 readback; 서버 validator 추가 여부 별도 표시 |
| MOB-06 delivery | 승인된 Phase 2 구현 이후 offline/restart/lost-response에도 원본·같은 intent 보존, metadata 완전 표시 | 기존 AC-P2-01..04 증거 재사용/추적; 모바일 producer 연결 증거 추가. 새로운 큐 구현 금지 |
| MOB-07 iOS automation (조건부) | 별도 black-box 확장 승인, Mac/Xcode/OS/runner 버전·서명 확인, screenshot·좌표 입력 및 재연결 성공, 서명 만료/Trust 실패 안전 진단 | 실제 기기 3회 checkpoint 재현, 연결 끊김·runner 재시작 기록; 정책/환경 미충족이면 BLOCKED |

수동 전용 iOS 지원 선언에는 MOB-02/04/05의 해당 iOS 셀을 요구한다. MOB-07을 제외했다면 반드시 “iOS 수동 수집만”으로 지원 범위를 표시한다. Android 자동화 선언은 MOB-01/03/04/05와 기존 Phase 4 gate를, 자동 업로드 선언은 MOB-06과 Phase 2 gate를 만족해야 한다. 최종 판정은 지정 Reviewer 08과 PM이 맡는다.

## 8. 역할·통합·검증 기록

부모는 기존 계약·PM 상태와 metadata 의미/검사 matrix를 통합하고 유일한 파일 편집자로 검증한다. Android 독립 검토는 중 난이도 `gpt-5.6-sol/medium`으로 배정했다(한정된 ADB 명령·좌표 의미 분석). iOS 독립 검토는 상 난이도 `gpt-5.6-sol/high`로 배정했다(호스트·runner 서명·정책 전제가 복합). 최초 상속 모델 iOS 검토는 요청된 등급 설정을 명시하지 않아 중단 후 올바른 설정으로 재배정했다. 서브에이전트는 보고만 수행하며 파일을 수정하지 않는다. tool 설정은 요청값이며 별도 런타임 attestation을 주장하지 않는다. 기존 구현 담당 task를 새로 만들지 않았다.

실행한 검증은 저장소 상태/문서 읽기, 적용 지침 탐색, git 변경 목록 및 보호 대상 hash 확인, 이 제안의 metadata 예시·참조·형식 검산이다. Android/iOS 연결, ADB 실행, Xcode/WDA 설치·서명, 실제 캡처, 해상도/locale 변경, 제품/API/DB/Web 테스트는 모두 NOT_RUN이다. 기기·지원 OS·게임 artifact·Mac 접근권은 확보 여부 미확인이다.

독립 검토 통합: Android 검토의 wm base≠panel, rotation 경쟁 상태, override 복원·변환 오차 권고를 반영했다. iOS 검토의 현재 ADB-only 정책, 게임/runner 서명 분리, 수동/WDA baseline 차이와 무인 복구 전제를 반영했다. 이는 지정 Reviewer 08의 독립 acceptance를 대체하지 않는다.

PM 반영 제안: (1) 승인된 Phase 2 revision2 계약 4파일을 유지하고 기존 제품 재작업/독립 검토를 우선한다. (2) 이 문서를 플랫폼 범위 검토 입력으로 받고 기기/지원 OS/locale inventory만 수집한다. (3) Phase 2 제품 승인 및 별도 파일 claim 후 06의 기존 producer 경계에 Android/iOS import provenance를 연결한다. (4) Phase 3/4 기존 gate 아래 07과 Architect가 Android geometry/시각 검사를 구체화한다. (5) iOS 자동화는 Mac/서명 전제 및 black-box 허용 범위 결정을 별도로 받아 기존 담당자에게 배정한다. 공통 파일 claim과 acceptance 등록은 PM, metadata 의미 합의는 Architect, 독립 판정은 Reviewer 08 소유다.

재개 기록: Android/iOS 서브에이전트의 완료 보고와 초안에 통합된 권고를 복구했다. 현재 실행 중인 하위 에이전트가 없어 중복 작업을 생성하지 않았다. 9/22의 revision1 검증 결과는 과거 기록이며 revision2 보존 검증과 혼동하지 않는다. 문서 작성 완료는 모바일 지원 구현 완료나 Phase 2 제품 승인과 다르다.

다음 검토 시 참고할 공식 문서 위치(이번 작업에서 최신 페이지 내용 검증 안 함):

- Android ADB: https://developer.android.com/tools/adb
- Android pixel/dp: https://developer.android.com/training/multiscreen/screendensities
- Apple Developer Mode: https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device
- Apple 기기 실행: https://developer.apple.com/documentation/xcode/running-your-app-in-simulator-or-on-a-device
- Appium XCUITest 준비/실기기: https://appium.github.io/appium-xcuitest-driver/latest/installation/ 및 https://appium.github.io/appium-xcuitest-driver/latest/preparation/real-device-config/
