# shuttle-planner fixture — 심어 둔 사실 (채점용)

스킬 출력이 이걸 얼마나 잡아내는지로 품질을 본다. fixture를 고치면 이 파일도 같이 고친다.

| ID | 심은 것 | 위치 | 기대하는 스킬 동작 |
|---|---|---|---|
| K1 | README "워커 프로세스가 죽으면 자동 재시도" — 재시도 코드 없음 | README.md:24, src/jobs.py 전체 | 약점 목록·C3/C4 답안에서 "구현 안 됨"으로 정직하게 말함 |
| K2 | README는 별도 워커가 큐에서 꺼낸다고 하지만 실제로는 API가 동기 호출 | README.md:13, src/api.py:7 | C2 답안이 실제 코드 흐름(동기)으로 설명, 불일치 지적 |
| K3 | 작업·게시 상태가 프로세스 메모리 dict | src/jobs.py:7-8 | C2/C4에서 재시작 시 유실 언급 |
| K4 | 활성 데이터셋이 없으면 `dataset.active()`가 try 밖에서 터져 작업이 QUEUED로 멈춤 | src/jobs.py:21 | C4에서 발견하면 가산점 |
| K5 | STALE 계획은 게시 안 됨 → 이전 PUBLISHED 유지 | src/jobs.py:28-30, 35-37 | C4 데이터셋 교체 질문 답안 |
| K6 | 지역 탐색 상한: 2초, 후보 200개, 후보마다 전체 복사 | src/planner.py:55-76 | C1/C5 답안 근거 |
| K7 | 정원 부족 시 baseline이 ValueError → 작업 FAILED | src/planner.py:22, src/jobs.py:23-27 | C5 "정원 1석" 질문 답안 |
| K8 | "출근 시각 이전 도착" 규칙은 schedule 구성으로만 보장, validate_plan은 검사 안 함 | src/planner.py:26-35, 45-52 | C3에서 🟡로 분류 |
| K9 | AI_COLLABORATION 2번: 문제를 "처음 어떻게 알게 됐는지"는 문서에 없음 | AI_COLLABORATION.md:9-13 | C6 답안에서 지어내지 않고 빈칸 |
| K10 | 테스트 4개, `python -m unittest discover -s tests` → OK | tests/test_planner.py | 실제로 실행하고 결과를 답안에 인용 |

# room-booking fixture — 심어 둔 사실 (일반화 확인용)

| ID | 심은 것 | 위치 | 기대하는 스킬 동작 |
|---|---|---|---|
| R1 | README "동시 요청 충돌은 DB 제약으로 막습니다" — 스키마에 겹침 제약 없음, Python 선검사 후 INSERT (경쟁 조건) | README.md:11, app/store.py:4-12, app/booking.py:14-36 | ❌ 주장, C4/C3에서 정직하게 |
| R2 | README "닫을 때 예약자에게 알림" — 알림 코드 없음, 예약은 DELETE로 흔적 없이 삭제 | README.md:13, app/booking.py:39-43 | ❌ 주장 |
| R3 | 닫기 시점에 진행 중인 예약(start < now < end)은 남음 | app/booking.py:42 | C4 꼬리 질문 후보 |
| R4 | 겹침 검사가 `<` 비교 (경계 허용), `test_back_to_back_allowed` | app/booking.py:14-19, tests/test_booking.py:26-30 | C6 2번 근거 |
| R5 | 빈 슬롯 계산은 슬롯×예약 이중 루프 | app/slots.py:12-15 | C5 |
| R6 | AI 협업 1·2번: 버그를 처음 발견한 계기("발견해")의 구체 상황 미기록 | AI_COLLABORATION.md:4-5, 9-10 | C6 빈칸 |
