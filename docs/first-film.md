# 첫 완성본: 안전한 착지는 어떻게 만들까?

> 이 문서는 v1 이력입니다. 최신 YouTube Shorts 수정본은 [v2 안내](revision-v2.md)를 확인하세요. 남성 내레이션·기술 중심 대본·사용자 선택 이미지를 적용했으며 화면의 고정 AI 문구는 제거했습니다.

2026-10-21 (한국 시간). 세로 720×1280, 24fps, 30초. 파일은 `outputs/first-film/roadster_landing_v1.mp4`, 자막은 같은 폴더의 `captions.srt`입니다. 생성 클립·설명용 도식·한국어 합성 음성·번인 자막을 결합합니다. 음악은 넣지 않았습니다. 계정에는 게시하지 않습니다.

## 편집과 대본

| 시간 | 내레이션 | 화면 |
| --- | --- | --- |
| 0–3.1초 | 차가 날아오르면, 어떻게 안전하게 착지할까요? | 체공 테스트 2, 질문 |
| 3.1–6.8초 | 이건 인공 지능으로 만든 가상 자동차입니다. | 테스트 1의 앞 1.25초 + 황혼 원본 이미지 |
| 6.8–10.6초 | 땅에 닿기 전에, 하강 속도를 줄입니다. | 테스트 3 하강 일부 + 속도 화살표 도식 |
| 10.6–15.6초 | 같은 조건이면, 멈추는 시간이 길수록 평균 충격력은 작아집니다. | 같은 질량·속도 변화에서 멈추는 시간 비교 |
| 15.6–21.2초 | 스프링은 눌리고, 댐퍼는 에너지를 흡수해 반동을 줄입니다. | 스프링과 댐퍼 설명용 도식 |
| 21.2–25.1초 | 차체의 자세와 지면 상태도 중요합니다. | 자세·접지·지면 도식 |
| 25.1–30초 | 충격과 균형이 핵심입니다. 여러분은 타고 싶나요? | 황혼 이미지와 결론·질문 |

전체에 `AI 콘셉트 · 실제 양산 사양 아님`을 표시합니다. 하강 클립에는 접지 미확인을 알리고, 도식에는 실제 차량 구조가 아님을 표시합니다. 실제 양산 로드스터 사진·실제 비행 기능·물리 시뮬레이션 결과로 소개하지 않습니다. 도약과 착지의 난이도를 보편적으로 비교하지 않습니다.

## 설명 근거와 한계

- [OpenStax, Linear Momentum, Force, and Impulse](https://openstax.org/books/physics/pages/8-1-linear-momentum-force-and-impulse): 같은 질량과 속도 변화에서 정지 시간을 늘리면 평균 알짜힘은 작아집니다. 화면의 삼각형은 같은 충격량을 설명하는 개념도이며 실측 힘 곡선이 아닙니다. 실제 접촉력에는 중력과 자세 등도 작용하며 최대 힘을 정량 예측하지 않습니다.
- [NASA, Keeping Our Feet Firmly on the Ground](https://science.nasa.gov/blog/keeping-our-feet-firmly-on-the-ground/): Ingenuity의 스프링·댐퍼 사례에서 에너지 흡수와 반발·전도 문제가 설명됩니다. 이 사례의 구조·수치가 콘셉트 자동차에 적용된다고 주장하지 않습니다. 영상의 자동차식 스프링·댐퍼는 일반 원리를 설명하는 별도 도식입니다.
- [NASA JPL, Touchdown](https://www.jpl.nasa.gov/edu/resources/lesson-plan/touchdown/): 충격 흡수와 균형을 함께 고려하고 시험으로 개선하는 설계 접근을 확인했습니다. 낮은 하강 속도 하나만으로 안전을 보장하지 않습니다.

## 비용과 제작 기록

첫 테스트 25 + 이번 두 테스트 50 = 75크레딧. 실제 잔액 925. [Runway 공식 단가](https://docs.dev.runwayml.com/guides/pricing/) 기준 $0.75 상당(세금 제외). 음성·도식·편집은 로컬 처리해 별도 서비스 과금이 없습니다. 세대별 작업 ID·원본 해시·요청·잔액은 `production-state.json`에 보존합니다.

생성 실패나 부족한 연출은 재생성 대신 편집·도식으로 처리했습니다. 클립 3에서 명확한 착지·서스펜션 압축은 확인하지 못했으므로 착지 성공을 주장하지 않습니다. 클립 검수 상세는 `pilot-review.md`에 있습니다.

## 음성과 재현

한국어 음성은 sherpa-onnx 1.13.8과 Mimic3 KSS 한국어 로컬 모델로 생성합니다. 별도 음성 API·결제·실존 인물 음성 복제는 사용하지 않습니다. 모델 원본의 [CC0 라이선스](https://github.com/MycroftAI/mimic3-voices/blob/master/voices/ko_KO/kss_low/LICENSE), [변환 모델 출처](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models)를 기록합니다. KSS low 모델이므로 전문 성우 수준의 자연스러움을 보장하지 않습니다.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-production.txt
# 허용된 GitHub 릴리스에서 모델 파일만 다운로드. 합성 자체는 오프라인.
mkdir -p outputs/models
curl --fail --location https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-mimic3-ko_KO-kss_low.tar.bz2 -o outputs/models/korean-tts.tar.bz2
tar -xjf outputs/models/korean-tts.tar.bz2 -C outputs/models
# 다른 환경에서는 먼저 pilot_session download로 기존 클립을 복원합니다.
.venv/bin/python -m shorts.narrate
.venv/bin/python -m shorts.first_film
```

FFmpeg/libx264와 Noto Sans CJK 글꼴이 필요합니다. 현재 렌더러 글꼴 경로는 Linux 기본 설치 경로입니다. `config/first-film.json`에 대본·자막·편집 구간을 보존합니다. 생성과 최종 편집 명령은 분리돼 있어 렌더·음성을 반복해도 Runway 생성 요청을 보내지 않습니다. 모델은 `outputs/models/`에 두며 Git에 올리지 않습니다.

## 이후 운영

최종 기술 검사는 `final-quality.json`에 기록합니다. 30.000초·720프레임, H.264/AAC, 전체 디코딩, 각 구간의 자막·도식·공개 표시를 확인했습니다. 합성 음성은 문장별 길이와 음량을 검사했고 로컬 자동 받아쓰기로 보완했습니다. 자동 인식에 불확실한 단어가 남아 있으므로 발음·자연스러움의 완전 통과나 사람의 전체 청취 검수를 주장하지 않습니다. 재생 가능한 첫 완성본으로 제공하며 전문 음성 서비스나 추가 결제는 사용하지 않았습니다.

[플랫폼별 게시 문안](publishing-copy.md)을 검토해 사용자가 직접 업로드합니다. 게시 성과는 `tracking/performance.csv`에 24시간·7일 기준으로 기록합니다. 아직 게시 전이므로 조회수·성과는 미측정입니다. 채널 운영 기준은 [channel-production.md](channel-production.md)에 보존합니다.
