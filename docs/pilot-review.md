# 첫 착지 영상 테스트 진행 기록

> 최신 상태 (2026-10-21, 한국 시간): 이 채팅의 새 승인에 따라 2·3번을 각각 1회 생성·다운로드했습니다. 총 75크레딧 사용, 실제 잔액 925. 아래 과거의 다운로드 전용 제한은 당시 이력이며 현재는 추가 생성 예산이 모두 소진됐습니다. **이제 모든 테스트는 기존 ID 조회·다운로드만 허용하며 재생성하지 않습니다.** 현재 작업 ID와 설정은 `docs/production-state.json`, 완성본 안내는 `docs/first-film.md`를 확인하세요.

2026-10-21 (한국 시간). 기준 코드: `ac2fa46dfcf97f8f0789f4b06e34bdb5d5228832`.

- `docs/first-video.md`의 30초 기획을 확인했습니다.
- 키 값을 출력하지 않고 Runway 조직 조회가 HTTP 200으로 성공했습니다. 시작 잔액은 1,000크레딧입니다.
- 환경 상태 도구의 비밀값/네트워크 준비 표시는 `unknown`이었지만, 실제 인증 API 조회와 첫 생성은 성공했습니다.
- Gen-4 Turbo, 720×1280, 5초 테스트 1번을 한 번 제출했고 `SUCCEEDED`를 확인했습니다.
- 작업 ID: `17de86aa-604d-43dc-a307-21f98ae79580`.
- 생성 후 잔액은 975크레딧입니다. 잔액 차이로 확인한 사용량은 25크레딧, 첫 세 테스트 예산의 남은 금액은 50크레딧입니다.
- 실제 결과 호스트 `dnznrvs05pmza.cloudfront.net` 다운로드가 프록시에서 `403 Forbidden`으로 거부됐습니다. 다운로드·시각 검수는 미완료입니다.
- 테스트 2·3번은 미제출입니다. 추가 재생성도 하지 않았습니다.

## 재개

클라우드 환경의 네트워크 허용 호스트에 `dnznrvs05pmza.cloudfront.net`을 추가해야 합니다. API 키 허용 도메인은 기존 `api.dev.runwayml.com`을 유지합니다. 결과 호스트에 API 인증 헤더를 보내지 않습니다.

로컬 `outputs/pilot-tests/jobs/scene_01.json`은 Git에서 제외된 파일입니다. 환경을 새로 만들거나 다른 컴퓨터에서 재개할 경우, 아래 기록을 먼저 같은 경로에 복구해야 합니다. 기록 없이 테스트 1번 생성 명령을 실행하면 중복 과금될 수 있습니다. 요청 설정을 바꾸거나 새 작업을 제출하지 말고 위 작업 ID로 조회·다운로드를 이어갑니다.

```json
{
  "fingerprint": "968faf4ed5be3f8146c2afcaa02da80dfd805769ac88404a218dfdbc2a9bbd93",
  "status": "SUCCEEDED",
  "request": {
    "scene_id": 1,
    "model": "gen4_turbo",
    "ratio": "720:1280",
    "duration": 5,
    "edit_duration": 5,
    "image": "황혼의 해안도로를 달리는 미래형 슈퍼카.png",
    "image_sha256": "4b8b4fb62f96b980d0eab82981d628487df55736ae2230eae35d827995970990",
    "prompt_text": "The reference car moves slowly forward on the empty coastal road. The camera tracks smoothly beside the front quarter, keeping the entire car visible. Wheels roll naturally, subtle suspension motion, stable body proportions. Preserve the original dusk lighting and coastline. Vertical 9:16, photorealistic cinematic automotive footage. Preserve the exact pearl-white body shape, black wheels, headlights and windows from the reference. No text, no watermark."
  },
  "id": "17de86aa-604d-43dc-a307-21f98ae79580"
}
```

현재 재개 범위는 **기존 1번 결과의 다운로드·검수만**입니다. `shorts.pilot --execute` 등 생성 가능한 명령은 실행하지 않습니다. 테스트 2·3번 및 재생성도 실행하지 않습니다. 아래 새 채팅용 조회·다운로드 절차를 사용합니다.


## 다운로드 정책 재확인 (2026-10-21, 한국 시간)

사용자가 다운로드 도메인 허용 후 재게시했다고 알려 재확인했습니다. 현재 작업에 연결된 환경의 `observations_current`는 `true`, `spec_revision`과 `observed_spec_revision`은 모두 `3`, 네트워크 정책 상태는 `enforced`입니다. 그러나 해당 환경의 `allowed_hosts`에는 `api.dev.runwayml.com`만 있으며 `dnznrvs05pmza.cloudfront.net`은 없습니다. 실행 환경의 `/etc/codex/network-policy.json`에도 다운로드 호스트가 없습니다. 따라서 현재 작업에서 다운로드 도메인 허용은 확인되지 않았습니다.

생성 함수나 생성 명령을 실행하지 않고, 저장된 작업 ID `17de86aa-604d-43dc-a307-21f98ae79580`로 조회 API만 호출했습니다. 기존 결과는 여전히 `SUCCEEDED`이며 결과 호스트는 `dnznrvs05pmza.cloudfront.net`입니다. 인증 헤더 없이 기존 결과 다운로드를 시도했으나 프록시 CONNECT 단계에서 `403 Forbidden`이 발생했습니다. 다운로드와 시각 검수는 여전히 미완료입니다.

잔액은 975크레딧으로 유지됐습니다. 새 생성·재생성은 없으며 테스트 2·3번도 실행하지 않았습니다. 기존 작업 ID 및 위 복구용 작업 기록을 유지합니다. 현재 채팅에 연결된 환경에서 다운로드 호스트의 허용을 적용한 후, 동일 작업 ID로 기존 결과 조회·다운로드만 재개해야 합니다. 이번 사용자 지시에 따라 추가 영상 생성은 진행하지 않습니다.


## 새 채팅 인계: 기존 결과만 다운로드

- 저장소: `Ssungmin-Park/AI-shorts`
- PR: https://github.com/Ssungmin-Park/AI-shorts/pull/1
- 브랜치: `codex/roadster-video-pipeline`
- 작업 ID: `17de86aa-604d-43dc-a307-21f98ae79580`
- 마지막 확인 상태: `SUCCEEDED`, 5초, Gen-4 Turbo, 720×1280.
- 마지막 확인 잔액: 975크레딧. 기존 사용량 25크레딧이며, 이번 재개에 신규 생성 예산을 사용하지 않습니다.
- 결과 파일 목표 경로: 저장소 아래 `outputs/pilot-tests/clips/scene_01.mp4`.
- 새 채팅은 이전 로컬 파일을 공유한다고 가정하지 않습니다. 위 JSON은 작업 기록 복구용이며, 아래 조회·다운로드 코드는 작업 기록 파일이 없어도 같은 ID만 조회합니다.

### 환경 확인 및 준비

1. 새 채팅에 연결된 환경에서 클라우드 상태와 `/etc/codex/network-policy.json`을 확인합니다. 이전 채팅의 정책 적용 상태를 재사용하지 않습니다.
2. API 호스트 `api.dev.runwayml.com`과 결과 호스트 `dnznrvs05pmza.cloudfront.net`의 허용을 확인합니다. 최신 결과 조회가 다른 호스트를 반환하면 해당 호스트와 실제 오류를 기록하고 중단합니다. 정책을 우회하지 않습니다.
3. `RUNWAYML_API_SECRET`은 새 채팅의 클라우드 비밀값으로 연결되어 있어야 합니다. 키 값, 환경변수 전체, 인증 헤더, 비밀 파일 내용은 출력하거나 GitHub에 저장하지 않습니다. API 키는 API 호스트에만 전송합니다.
4. 위 브랜치를 체크아웃한 저장소에서 `python -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`로 준비합니다. Windows는 `.venv\Scripts\python.exe`를 사용합니다.

### 생성 경로 없는 다운로드 예시 (Linux/macOS)

저장소 루트에서 실행합니다. Runway 작업 조회와 파일 다운로드만 하며 생성 API는 호출하지 않습니다. 서명된 결과 URL은 만료될 수 있으므로 GitHub에 고정 URL을 저장하지 않고 작업 ID로 다시 조회합니다.

```bash
.venv/bin/python - <<'PYTHON'
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from runwayml import RunwayML

TASK_ID = "17de86aa-604d-43dc-a307-21f98ae79580"
client = RunwayML(max_retries=0, timeout=30)
try:
    task = client.tasks.retrieve(TASK_ID)
except Exception as error:
    raise SystemExit(f"작업 조회 중단: {type(error).__name__}. 새 생성 금지.") from None
print(json.dumps({"task_id": task.id, "status": task.status}))
if task.status != "SUCCEEDED" or not task.output:
    raise SystemExit("기존 결과를 사용할 수 없습니다. 작업 ID를 보존하고 중단합니다.")
url = task.output[0]
parts = urlsplit(url)
print(json.dumps({"output_host": parts.hostname}))
if parts.scheme != "https" or parts.hostname != "dnznrvs05pmza.cloudfront.net":
    raise SystemExit("결과 호스트가 변경되었습니다. 네트워크 정책 확인 후 재개하세요.")
clip = Path("outputs/pilot-tests/clips/scene_01.mp4")
clip.parent.mkdir(parents=True, exist_ok=True)
partial = clip.with_suffix(".part")
try:
    # Runway 클라이언트 인증 헤더를 결과 다운로드에 전달하지 않습니다.
    with urlopen(url, timeout=60) as response, partial.open("wb") as target:
        while block := response.read(1024 * 1024):
            target.write(block)
    if partial.stat().st_size == 0:
        raise ValueError("Empty download")
    partial.replace(clip)
except Exception as error:
    partial.unlink(missing_ok=True)
    raise SystemExit(f"다운로드 중단: {type(error).__name__}. 작업 ID 보존, 새 생성 금지.") from None
print(json.dumps({"saved": str(clip), "bytes": clip.stat().st_size,
                  "sha256": hashlib.sha256(clip.read_bytes()).hexdigest()}))
PYTHON
```

다운로드 후 디코딩 가능 여부, 해상도·길이를 확인하고 시간 순서대로 프레임을 검수합니다. 차체 윤곽, 휠 수·형태, 헤드라이트, 접지, 갑작스러운 변형과 전진·추적 움직임을 평가합니다. 검수 결과와 다운로드 파일 경로를 기록합니다. 차단·만료·작업 조회 실패 시 작업 ID와 오류를 보존하고 사용자에게 알리며, 새 생성이나 재생성으로 대체하지 않습니다.

### 새 채팅에 전달할 요청

> `Ssungmin-Park/AI-shorts`의 PR #1, `codex/roadster-video-pipeline` 브랜치에서 `docs/pilot-review.md`를 읽고 이어서 진행해 줘. 먼저 현재 채팅에 다운로드 도메인 정책이 적용됐는지 확인하고, 작업 ID `17de86aa-604d-43dc-a307-21f98ae79580`의 기존 결과만 다운로드·검수해 줘. 새 영상 생성, 테스트 2·3번, 재생성은 하지 마. API 키를 출력하거나 기록하지 마. 차단되면 작업 ID와 진행 기록을 보존하고 알려줘.


## 이번 제작: 2·3번 생성 완료 및 편집 판단 (2026-10-21, 한국 시간)

현재 환경은 observations_current=true, 비밀값 ready, 네트워크 enforced이며 API·다운로드 호스트 모두 허용됩니다. 실제 인증 조회 및 인증 헤더 없는 다운로드로 확인했습니다. 신규 생성은 Gen-4 Turbo, 720:1280, 5초를 각각 한 번만 제출했습니다. 아래 ID는 재사용하며 자동 재생성하지 않습니다.

| 테스트 | 작업 ID | 상태 | 크레딧 | 편집 판단 |
| --- | --- | --- | --- | --- |
| 1 | `17de86aa-604d-43dc-a307-21f98ae79580` | SUCCEEDED | 25 | 0–1.25초만 사용. 휠 형태 변화는 보이지만 실제 회전과 생성 왜곡 구분은 불확실. 후반 범퍼 잘림 제외. |
| 2 | `82809632-8631-4f42-8b0a-8e6b65cd01d2` | SUCCEEDED | 25 | 0–3.1초 사용. 차체와 체공 구도 대체로 유지. 분사·연기는 가상 연출이며 실제 추진 기술의 증거가 아님. |
| 3 | `cedccc44-f84c-477e-a302-17264defa8a4` | SUCCEEDED | 25 | 1.25–3.25초 하강 연출만 사용. 최종 프레임에서도 지면 접촉·단일 압축·정착 확인 불가. 성공한 착지 장면으로 제시하지 않고 도식으로 설명. |

잔액: 975 → 950 → 925크레딧. 이번 사용 50, 기존 포함 총 75크레딧. 공식 API 단가 1크레딧=$0.01 기준 이번 $0.50, 총 $0.75 상당(구매·세금 별도). 추가 생성 예산은 0입니다.

세 클립은 각 720×1280, 24fps, 약 5.041667초입니다. 순차 프레임과 시작·중간·끝을 확인했습니다. 가려진 바퀴와 실제 물리적 안전성은 검증할 수 없습니다. 검수·편집은 실제 기능의 성능 평가가 아닙니다.

### 현재 재개 방법

`docs/production-state.json`이 비밀값 없는 기준 기록입니다. 생성 작업 ID, 요청 설정, 예산 예약 상태를 Git에 보관합니다. 로컬 파일은 `outputs/pilot-tests/`에 있습니다. 새 환경에서도 저널을 지우거나 재초기화하지 않습니다.

```bash
# 조회·다운로드는 생성 경로와 분리되어 있습니다.
python -m shorts.pilot_session status --test 2
python -m shorts.pilot_session download --test 2
python -m shorts.pilot_session status --test 3
python -m shorts.pilot_session download --test 3
```

결과 URL 만료 시 download를 다시 실행하면 같은 작업 ID를 재조회합니다. URL·인증 헤더는 저장하지 않습니다. 다른 결과 호스트가 반환되면 정책을 확인하고 중단합니다. `SUBMITTING`인데 ID가 없으면 대시보드에서 ID를 복구해야 하며 재전송하지 않습니다. 추가 예산이 소진됐으므로 submit 및 기존 `shorts.pilot --execute`는 실행하지 않습니다.
