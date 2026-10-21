# 첫 착지 영상 테스트 진행 기록

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

다운로드가 허용되고 기록이 복구된 상태에서 `.venv/bin/python -m shorts.pilot --test 1 --execute`는 같은 작업을 조회·다운로드합니다. 차체 윤곽, 휠 수와 형태, 헤드라이트, 접지, 갑작스러운 변형을 검수한 뒤 테스트 2번과 3번을 각각 한 번씩 순서대로 진행합니다. 추가 재생성은 금지되어 있습니다.
