## 약점 Top 3
1. ❌ README의 "워커 프로세스가 죽으면 작업은 자동으로 재시도됩니다"(README.md:24)를 뒷받침하는 코드가 없습니다. 워커도 큐도 없고 `post_plans`가 `jobs.run`을 동기로 호출하며(api.py:7), 작업·게시 상태는 프로세스 메모리 dict에만 있습니다(jobs.py:7-8). README 동작 2단계 "워커가 작업을 꺼내"(README.md:13)도 같은 문제입니다.
2. 🟡 "노선당 최대 탑승 시간은 60분"(README.md:19)은 보장되지 않습니다. `baseline`은 탑승 시간을 검사하지 않고(planner.py:14-23), `plan`·`jobs.run`도 결과를 검증하지 않은 채 DONE으로 게시합니다(planner.py:79-82, jobs.py:31-32). [이번 점검] 25분 구간 3개짜리 노선(75분)이 `validate_plan` 오류를 낸 채로 DONE 처리되고 게시됐습니다.
3. ❌ AI_COLLABORATION.md:6에는 "지역 탐색(swap/relocate)"이라고 적었지만 구현은 swap뿐입니다(planner.py:56, 70). 여기에 후보 상한 200(planner.py:55)까지 걸려서, 차량이 많으면 첫 번째 차량 쌍만 탐색하고 끝납니다.

## 제출 전에 직접 돌려볼 것
제출 폴더에 `__pycache__`가 생기지 않도록 `PYTHONDONTWRITEBYTECODE=1`을 붙입니다.
1. `cd .../shuttle-planner && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` → 테스트 4개 OK
2. `python3 -I -B /private/tmp/claude-501/-Users-hyunjun-macbook-pro-Documents-Private-skh-skills/ff81f0d0-ad55-4988-ae4d-b87800760d92/scratchpad/exp/probe.py /private/tmp/claude-501/-Users-hyunjun-macbook-pro-Documents-Private-skh-skills/ff81f0d0-ad55-4988-ae4d-b87800760d92/scratchpad/sp-copy` (제출물 복사본에 대해 실행합니다). 기대 출력은 아래와 같습니다.
   - `1 ride: ... validate: ['v1: ride over 60 min']` / `1 job: 200 {'status': 'DONE', ...} published m0: 200`: 60분을 넘는 계획이 그대로 게시됩니다.
   - `2 fail: ... 'FAILED' ... old route still: 200`: 실패해도 이전 게시 노선은 남습니다.
   - `3 same-version swap: ... 'DONE'`: 같은 version으로 데이터셋을 바꾸면 STALE로 잡히지 않습니다.
   - `4 n=2000: travel entries=4004001 ... improve=0.17s reason=time_or_candidate_limit`: 탐색이 200개 후보에서 멈춥니다.
   - `5 time_limit=0: time_or_candidate_limit`: 시간 제한 경로가 실제로 동작합니다.
   - `6 schedule: [('s1', 518), ('s2', 529), ('OFFICE', 540)]`: 출근 시각이 다른 두 사람(540, 600)이 함께 타면 가장 이른 시각 540에 맞춰 도착합니다.
3. `grep -rn "relocate\|retry" src/` → 결과 없음

## 예상 질문

### C1-1. 노선 계산에서 OR-Tools 같은 VRP 솔버 대신 "회사에서 가까운 구성원부터 채우는 기준선 + 시간·후보 수 제한이 있는 swap 지역 탐색" 구조를 택했습니다. 택한 이유, 솔버와의 차이, 이 선택으로 포기한 것은 무엇인가요?
- 출제 근거: AI_COLLABORATION.md:4-6 "OR-Tools VRP 솔버를 쓰자는 제안…받아들이지 않았다. 대신 가까운 구성원부터 채우는 기준선을 만들고"
- 모범 답안: 시험 환경에서 의존성 설치가 보장되지 않고 2초 안에 결과를 내야 해서, 표준 라이브러리만 쓰는 휴리스틱을 택했습니다. `baseline`은 회사까지 이동시간 순으로 정렬한 뒤 정원만큼 잘라 차량에 넣고, `improve`는 두 노선 사이에서 구성원을 맞바꿔 규칙을 지키면서 총 탑승 시간이 줄어드는 경우만 채택합니다. 시간 제한은 2초, 후보 상한은 200개입니다. 솔버라면 시간창과 정원 제약을 직접 모델링해 전역 최적에 가까운 해를 얻지만, 저는 최적성 보장과 제약 처리 능력을 포기했습니다. 문서에 적은 relocate는 구현하지 않았고 swap만 있습니다.
- 외울 키워드: 의존성·2초 제약 · baseline 후 swap · 최적성 포기, relocate 미구현
- 확인용 근거: [제출물] planner.py:14-23, planner.py:55-76, AI_COLLABORATION.md:4-6 / [이번 점검] `grep relocate src/` → 없음
- 꼬리 질문: "swap만 있으면 노선별 인원 수는 바뀌지 않나요?" → 네, 맞바꾸기만 하므로 노선별 인원이 baseline에서 고정된다고 인정하고, relocate를 추가하면 풀린다고 답합니다.
- ⚠ 본인 확인: 없음

### C1-2. 소수 단위 이동시간을 구간마다 `math.ceil`로 올림하도록 정했습니다. "합계 후 한 번만 반올림"하는 방식 대신 이 방식을 택한 이유와 대안과의 차이, 그리고 이 선택의 비용은 무엇인가요?
- 출제 근거: AI_COLLABORATION.md:11-12 "구간마다 `math.ceil`로 올림하도록 바꿨다…정류장별 시각이 합계와 어긋나서 버렸다", planner.py:9-11
- 모범 답안: 정류장별 시각이 실제보다 앞서 표시되지 않게 하려고 구간마다 올림했습니다. `round()`를 쓰면 7.4분이 7분이 되고, 구간이 쌓일수록 도착 시각이 실제보다 이르게 나왔습니다. 합계를 낸 뒤 한 번만 반올림하면 전체 합은 정확해지지만 정류장별 시각을 합한 값과 맞지 않습니다. `test_minutes_are_rounded_up`에서 7.4분 구간 두 개가 14분이 아니라 16분이 되는지 검증했습니다. 비용은 구간이 많을수록 탑승 시간이 과대 추정되어 60분 제한에 더 빨리 걸리고, 출발 시각이 실제보다 이르게 잡힌다는 점입니다.
- 외울 키워드: 구간별 올림 · 정류장 시각 일관성 · 탑승 시간 과대 추정
- 확인용 근거: [제출물] planner.py:11, tests/test_planner.py:21-25 `test_minutes_are_rounded_up` / [이번 점검] unittest 4개 OK
- 꼬리 질문: "구간이 10개면 오차가 최대 얼마인가요?" → 구간마다 1분 미만이므로 최대 10분 미만으로 과대 추정됩니다.
- ⚠ 본인 확인: 없음

### C1-3. 작업 상태와 게시된 노선을 프로세스 메모리 dict(`JOBS`, `PUBLISHED`)에 두고, `POST /plans`에서 계산을 동기로 실행하는 구조를 택했습니다. 이유, DB·별도 워커 큐와의 차이, 포기한 것은 무엇인가요?
- 출제 근거: jobs.py:1 "In-memory job store", jobs.py:7-8, api.py:7 "synchronous in this submission"
- 모범 답안: 시험 범위 안에서 흐름을 단순하게 유지하려고 메모리 dict와 동기 실행을 택했습니다. `post_plans`가 `submit`으로 작업을 만들고 바로 `run`을 호출하므로 응답이 돌아올 때는 계산이 이미 끝나 있습니다. DB와 워커 큐를 쓰면 요청과 계산이 분리되고 재시작해도 상태가 남지만, 저는 영속성, 재시도, 비동기 응답을 포기했습니다. 그래서 README의 "워커가 작업을 꺼내"와 "자동 재시도"는 현재 코드와 맞지 않습니다. 정확히는 계획만 하고 구현하지 않은 부분입니다.
- 외울 키워드: 메모리 dict · 동기 run · 영속성·재시도 포기
- 확인용 근거: [제출물] api.py:5-8, jobs.py:7-8, README.md:13, README.md:24
- 꼬리 질문: "그럼 `job_id`를 반환하는 의미가 있나요?" → 지금은 사후 상태 조회용일 뿐이고, 비동기로 바꿀 때를 대비한 인터페이스라고 답합니다.
- ⚠ 본인 확인: [본인 기억으로 채우기: 동기 실행을 의도적으로 택했는지, 워커를 만들려다 시간이 부족했는지]

### C2-1. HR 운영자가 `POST /plans`를 호출한 순간부터 구성원이 `GET /me/route`로 자기 노선을 볼 수 있게 되기까지, 요청이 거치는 함수와 각 상태(작업·계획·활성 데이터셋·게시 노선)가 어디에 저장되고 누가 쓰고 읽는지 설명해 주세요.
- 출제 근거: README.md:12-14, api.py:5-8, jobs.py:13-41
- 모범 답안: `api.post_plans`가 `jobs.submit`을 호출해 `JOBS`에 QUEUED 작업을 만들고, 이어서 `jobs.run`을 동기로 실행합니다. `run`은 `dataset.active()`로 활성 데이터셋을 받아 RUNNING과 version을 기록하고, `planner.plan`으로 계산합니다. 끝나면 version을 다시 비교해 같으면 DONE과 계획을 `JOBS`에 쓰고, `publish`가 `PUBLISHED`를 비운 뒤 구성원별 (차량, 시간표)로 채웁니다. `get_my_route`는 `PUBLISHED`를 읽기만 합니다. 활성 데이터셋은 dataset 모듈의 `_active`에 있고 `activate`만 씁니다. 세 상태 모두 한 프로세스의 메모리에 있습니다. README는 워커라고 적었지만 실제로는 API가 직접 실행합니다.
- 외울 키워드: submit→run→plan→publish · JOBS/PUBLISHED/_active · 워커 없음
- 확인용 근거: [제출물] api.py:5-8, jobs.py:20-41, dataset.py:14-25, api.py:18-23
- 꼬리 질문: "계획은 `JOBS`와 `PUBLISHED` 두 곳에 있는데 무엇이 원본인가요?" → `JOBS[jid]["plan"]`이 작업 결과이고, `PUBLISHED`는 조회용으로 펼친 사본입니다.
- ⚠ 본인 확인: 없음

### C2-2. 활성 데이터셋은 누가 소유하고 어떻게 교체되나요? 계획 생성 중 "스냅샷"으로 계산한다고 했는데, 무엇이 스냅샷을 보장하고 교체 감지는 무엇에 의존하나요?
- 출제 근거: README.md:13 "활성 데이터셋 스냅샷으로 노선을 계산합니다", dataset.py:1 "Swapped atomically by operators"
- 모범 답안: 활성 데이터셋은 dataset 모듈의 전역 `_active`가 소유하고, 운영자는 `activate`로 객체 참조를 통째로 바꿉니다. `jobs.run`이 시작할 때 `active()`로 받은 참조를 끝까지 쓰고, `Dataset`이 frozen dataclass라서 이 참조가 사실상 스냅샷 역할을 합니다. 다만 안쪽 dict는 불변이 아니어서, 누군가 그 dict를 직접 고치면 스냅샷이 깨집니다. 교체 감지는 계산 후 `version` 비교 하나에 의존합니다. 그래서 운영자가 같은 version 번호로 새 데이터셋을 넣으면 STALE로 잡히지 않습니다. 코드상 그렇게 되고, 직접 실험해 확인할 수 있습니다.
- 외울 키워드: 전역 `_active` 참조 교체 · frozen이지만 dict는 가변 · version 비교 의존
- 확인용 근거: [제출물] dataset.py:5-25, jobs.py:21, jobs.py:28 / [이번 점검] probe `3 same-version swap` → DONE
- 꼬리 질문: "version은 누가 올리나요?" → 호출자가 `Dataset(version, …)`으로 넣어 주는 값이고 자동 증가는 없습니다. `activate`에서 증가를 강제하는 것이 개선안입니다.
- ⚠ 본인 확인: 없음

### C2-3. `publish`는 `PUBLISHED`를 비운 뒤 다시 채웁니다. 새 계획이 게시될 때, 그리고 FAILED나 STALE일 때 구성원 화면에 보이는 노선은 각각 어떤 상태인가요?
- 출제 근거: jobs.py:35-41, api.py:18-23
- 모범 답안: DONE이면 `publish`가 락을 잡고 `PUBLISHED`를 `clear`한 뒤 새 계획의 구성원으로 다시 채웁니다. 새 데이터셋에서 빠진 구성원은 404 "no published route"를 받습니다. FAILED나 STALE이면 `run`이 `publish` 전에 반환하므로 이전 게시 노선이 그대로 남아, 구성원은 예전 데이터셋 기준 노선을 계속 봅니다. `get_my_route`는 락 없이 읽기 때문에, 다른 스레드에서 게시가 일어나면 clear와 재채움 사이에 잠깐 404가 보일 여지가 있습니다. 지금은 동기 실행이라 드물지만, 이 부분은 테스트하지 않았습니다.
- 외울 키워드: clear 후 재채움 · 실패·STALE은 이전 노선 유지 · 읽기에 락 없음
- 확인용 근거: [제출물] jobs.py:26-32, jobs.py:36-41, api.py:19 / [이번 점검] probe `2 fail ... old route still: 200`
- 꼬리 질문: "원자적으로 바꾸려면?" → 새 dict를 다 만든 뒤 참조 하나로 교체하면 됩니다.
- ⚠ 본인 확인: 없음

### C3-1. 이 서비스에서 실제로 구현해 테스트로 검증한 부분, 코드만 있는 부분, 구현하지 않은 부분을 나눠 주세요. 그리고 다른 평가자가 "생성된 계획이 운영 규칙을 지킨다"는 주장을 확인하려면 어떤 테스트, 명령, 파일을 보면 되나요?
- 출제 근거: README.md:16-19 운영 규칙, README.md:26-29 테스트
- 모범 답안: 테스트로 검증한 것은 구간별 올림, 작은 예제에서 정원과 탑승 시간 준수, 좌석 부족 시 예외, 데이터셋 교체 시 STALE, 이렇게 네 가지입니다. 코드만 있고 테스트가 없는 것은 2초 시간 제한, 출근 시각 준수, API 핸들러와 게시입니다. 자동 재시도와 relocate는 구현하지 않았습니다. 규칙 준수는 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`로 `test_plan_respects_capacity_and_ride_limit`을 돌리고 `planner.validate_plan`을 보면 됩니다. 다만 이 테스트는 16분짜리 작은 예제뿐이고, 출근 시각은 `validate_plan`이 검사하지 않습니다.
- 외울 키워드: 테스트 4개 · validate_plan · 출근 시각 미검사
- 확인용 근거: [제출물] tests/test_planner.py:21-54, planner.py:45-52 / [이번 점검] unittest 4개 OK
- 꼬리 질문: "그 테스트가 60분 위반을 잡을 수 있나요?" → 예제 노선이 16분이라 위반 상황 자체를 만들지 않습니다. 위반 사례 테스트가 필요합니다.
- ⚠ 본인 확인: 없음

### C3-2. README에 "모든 구성원은 출근 시각 이전에 도착합니다"라고 적었습니다. 이 규칙은 코드 어디에서 보장되고, 어떻게 검증했나요? 같은 차에 출근 시각이 다른 사람이 타면 어떻게 되나요?
- 출제 근거: README.md:18, planner.py:29
- 모범 답안: 이 규칙은 검사가 아니라 시간표를 만드는 방식으로 보장됩니다. `schedule`이 노선 구성원 중 가장 이른 `arrive_by`를 회사 도착 시각으로 잡고, 거꾸로 구간 시간을 빼며 정류장 시각을 계산합니다. 그래서 모두 자기 출근 시각에 맞거나 그보다 일찍 도착합니다. 하지만 `validate_plan`에는 도착 시각 검사가 없고, 이 규칙만 따로 본 테스트도 없습니다. 출근 시각이 540분과 600분인 두 사람이 같이 타면 540분에 도착하므로, 뒤쪽 사람은 60분 일찍 도착합니다. 코드상 그렇게 되고, 직접 실험해 확인할 수 있습니다.
- 외울 키워드: 가장 이른 arrive_by 역산 · 구조상 보장, 검사·테스트 없음 · 늦은 사람은 조기 도착
- 확인용 근거: [제출물] planner.py:26-33, planner.py:45-52 / [이번 점검] probe `6 schedule` → `[('s1', 518), ('s2', 529), ('OFFICE', 540)]`
- 꼬리 질문: "왜 검사 함수에 넣지 않았나요?" → 구조상 깨질 수 없다고 판단했지만, 회귀를 막으려면 `validate_plan`에 넣는 편이 맞다고 답합니다.
- ⚠ 본인 확인: 없음

### C3-3. README "신뢰성" 절의 세 주장(2초 시간 제한 시 최선해 반환, 데이터셋 변경 시 STALE, 워커 사망 시 자동 재시도)은 각각 어디까지 구현되고 검증됐나요?
- 출제 근거: README.md:21-24
- 모범 답안: STALE은 구현하고 테스트했습니다. `test_dataset_swap_marks_stale`이 계산 도중 version 2 데이터셋을 활성화해서 상태가 STALE이 되는지 확인합니다. 시간 제한은 `improve`가 매 후보마다 `time.monotonic()`을 확인해 그때까지의 최선해를 반환하도록 구현했지만 테스트는 없습니다. 반환 이유가 `time_or_candidate_limit` 하나라서 시간 초과인지 후보 상한인지도 구분되지 않습니다. 자동 재시도는 구현하지 않았습니다. 워커가 없고 재시도 코드도 없으므로 이 문장은 README에서 빼거나 고쳐야 합니다.
- 외울 키워드: STALE ✅ · 시간 제한 코드만 · 재시도 ❌
- 확인용 근거: [제출물] tests/test_planner.py:40-54, planner.py:59-67, README.md:24 / [이번 점검] probe `5 time_limit=0` → `time_or_candidate_limit`
- 꼬리 질문: "시간 제한을 테스트하려면?" → `time_limit_sec=0`으로 호출해 이유 값과 baseline 유지를 확인하면 됩니다.
- ⚠ 본인 확인: 없음

### C4-1. 계획 생성 중 최적화가 시간 제한에 걸리거나, 실행 중인 프로세스가 죽거나, 생성 중에 운영자가 데이터셋을 바꾸면 각각 시스템은 어떻게 동작하고, 기존 계획과 구성원 화면은 어떤 상태가 되나요?
- 출제 근거: README.md:21-24, jobs.py:20-32
- 모범 답안: 시간 제한에 걸리면 `improve`가 그때까지의 최선해와 `time_or_candidate_limit`을 반환합니다. 작업은 DONE이 되고 새 노선이 게시됩니다. 프로세스가 죽는 경우는 처리하지 않았습니다. `JOBS`, `PUBLISHED`, `_active`가 모두 메모리에 있어 전부 사라지고, 재시작 후 구성원은 404를 받습니다. 재시작 직후 데이터셋 없이 `POST /plans`를 보내면 `dataset.active()`가 try 밖에서 예외를 던져 작업이 QUEUED로 남습니다. 데이터셋이 바뀌면 STALE이 되어 게시하지 않고 이전 노선이 유지됩니다. 다만 같은 version으로 바꾸면 이를 감지하지 못합니다.
- 외울 키워드: 제한→DONE 게시 · 사망→전부 유실, 재시도 없음 · 변경→STALE, 이전 노선 유지
- 확인용 근거: [제출물] planner.py:66-67, jobs.py:7-8, jobs.py:21-23, jobs.py:28-30, test_dataset_swap_marks_stale / [이번 점검] probe `3`, `5`
- 꼬리 질문: "QUEUED로 남은 작업은 누가 정리하나요?" → 아무도 정리하지 않습니다. run 전체를 try로 감싸 FAILED로 남겨야 합니다.
- ⚠ 본인 확인: 없음

### C4-2. 기준선이 이미 60분 탑승 제한을 넘는 노선을 만들면 지역 탐색이 이를 고칠 수 있나요? 그런 계획은 최종적으로 어떤 상태로 저장되고 구성원에게 보이나요?
- 출제 근거: README.md:19 "노선당 최대 탑승 시간은 60분입니다", planner.py:71, planner.py:79-82
- 모범 답안: 대부분 고치지 못하고, 위반 계획이 그대로 게시됩니다. `baseline`은 정원만 보고 탑승 시간은 검사하지 않습니다. `improve`는 `validate_plan`을 통과한 후보만 받아들이므로, 한 번의 swap으로 모든 위반이 풀리지 않으면 기준선이 그대로 남습니다. `plan`과 `jobs.run`은 결과를 다시 검증하지 않아서 상태는 DONE, 이유는 converged로 저장되고 게시됩니다. 25분 구간 3개짜리 노선이라면 75분짜리 노선이 게시되는 것을 확인할 수 있습니다. 게시 전에 `validate_plan`을 호출해 실패로 처리하는 것이 필요합니다.
- 외울 키워드: baseline 탑승 미검사 · 위반 후보는 거부만 · DONE으로 게시
- 확인용 근거: [제출물] planner.py:14-23, planner.py:71-72, jobs.py:31-32 / [이번 점검] probe `1 ride ... validate: ['v1: ride over 60 min']`, `1 job ... DONE`
- 꼬리 질문: "검증 실패 시 상태는 무엇이 좋나요?" → FAILED나 별도의 INVALID로 두고 게시하지 않으며, 위반 목록을 reason에 담습니다.
- ⚠ 본인 확인: 없음

### C4-3. 좌석이 부족하거나 이동시간 데이터에 정류장 쌍이 빠져 있어 planner가 예외를 던지면, 작업 상태, 운영자가 보는 정보, 구성원 화면은 어떻게 되나요?
- 출제 근거: planner.py:21-22, jobs.py:23-27
- 모범 답안: `jobs.run`이 planner 예외를 모두 잡아 작업을 FAILED로 두고, 예외 메시지를 reason에 담습니다. 좌석이 부족하면 "not enough seats for N members"가 남고, 정류장 쌍이 없으면 `KeyError` 메시지가 남습니다. 운영자는 `GET` 작업 조회로 status와 reason을 봅니다. `publish`가 호출되지 않으므로 구성원은 이전 게시 노선을 계속 봅니다. 좌석 부족은 `test_not_enough_seats_raises`에서 `baseline` 수준으로만 테스트했고, 작업 상태가 FAILED가 되는 경로는 테스트하지 않았습니다.
- 외울 키워드: 예외→FAILED+reason · 게시 안 함, 이전 노선 유지 · 좌석 부족만 테스트
- 확인용 근거: [제출물] jobs.py:23-27, api.py:11-15, tests/test_planner.py:32-36 / [이번 점검] probe `2 fail` → FAILED, 이전 노선 200
- 꼬리 질문: "KeyError 메시지가 운영자에게 유용한가요?" → 아닙니다. 입력 검증 단계에서 빠진 쌍을 명시하는 편이 좋습니다.
- ⚠ 본인 확인: 없음

### C5-1. 구성원이 2000명으로 늘고 30일치 계획이 필요하다면 어디가 병목이나 위험이 되나요? 이를 어떻게 확인했고, 결과를 신뢰하려면 앞으로 무엇을 검증해야 하나요?
- 출제 근거: planner.py:55 `max_candidates=200`, planner.py:62-73, dataset.py:11
- 모범 답안: 제출 시점에는 규모를 측정하지 않았습니다. 코드상 위험은 세 가지입니다. 첫째, 이동시간이 모든 정류장 쌍의 dict라서 2000명이면 약 400만 항목이 됩니다. 둘째, `improve`는 후보 200개에서 멈추는데 첫 차량 쌍만 20×20=400개라서, 나머지 차량은 탐색하지 못하고 사실상 기준선이 그대로 나옵니다. 셋째, 후보마다 계획 전체를 복사하고 비용을 다시 계산합니다. 30일은 모델에 날짜 개념이 없어서 데이터셋마다 한 번씩 돌려야 합니다. 앞으로 규모별 실행 시간과 baseline 대비 개선율을 측정하고, 후보 순서를 무작위로 바꿔 볼 계획입니다.
- 외울 키워드: 이동시간 N² · 후보 200 상한, 첫 쌍만 · 날짜 개념 없음
- 확인용 근거: [제출물] planner.py:55, planner.py:62-69, dataset.py:11 / [이번 점검] probe `4 n=2000: travel entries=4004001 ... improve=0.17s reason=time_or_candidate_limit`
- 꼬리 질문: "그럼 2초 제한은 의미가 있나요?" → 이 규모에서는 후보 상한이 먼저 걸리므로, 상한을 규모에 비례해 늘려야 합니다.
- ⚠ 본인 확인: 없음

### C5-2. 차량 정원이 1석이거나, 구성원이 0명이거나, 정원이 0이나 음수처럼 잘못 들어오는 극단 입력에서 시스템은 어떻게 동작하나요? 무엇을 검증했고 무엇이 비어 있나요?
- 출제 근거: planner.py:18-22, planner.py:29, tests/test_planner.py:32-36
- 모범 답안: 총 좌석이 구성원보다 적으면 `baseline`이 ValueError를 던지고, 이것은 `test_not_enough_seats_raises`로 검증했습니다. 정원이 1이고 좌석이 충분하면 1인 노선만 생기므로 swap을 해도 비용이 바뀌지 않습니다. 구성원이 0명이면 `schedule`이 빈 노선을 처리하지만, `publish`가 `PUBLISHED`를 비워서 모두 404를 받습니다. 정원 입력은 검증하지 않습니다. 음수 정원이면 슬라이싱 때문에 엉뚱하게 배정되고, 위반 계획도 게시될 수 있습니다. 이 부분은 코드상 그렇다는 것이고, 앞으로 입력 검증과 테스트를 추가해야 합니다.
- 외울 키워드: 좌석 부족만 테스트 · 0명이면 전원 404 · 정원 입력 검증 없음
- 확인용 근거: [제출물] planner.py:18-22, planner.py:29, jobs.py:37, tests/test_planner.py:32-36
- 꼬리 질문: "입력 검증은 어디에 두나요?" → `activate` 시점에 정원 1 이상, 이동시간 쌍 완비, version 증가를 검사합니다.
- ⚠ 본인 확인: 없음

### C5-3. 기준선은 "회사까지 이동시간" 순으로 정렬해 정원만큼 자릅니다. 구성원이 넓게 퍼져 있거나 출근 시각이 제각각이면 어떤 위험이 있고, 결과 품질을 어떻게 확인하겠습니까?
- 출제 근거: planner.py:16, AI_COLLABORATION.md:5 "가까운 구성원부터 채우는 기준선"
- 모범 답안: 여기서 "가까운"은 서로 가까운 것이 아니라 회사까지의 거리가 비슷하다는 뜻입니다. 그래서 회사에서 같은 거리지만 반대 방향에 사는 사람들이 한 차에 묶일 수 있습니다. 그러면 구간 사이 이동이 길어져 60분 제한을 넘기 쉽고, 앞에서 말한 대로 그런 계획도 그대로 게시됩니다. 출근 시각도 고려하지 않아서, 가장 이른 사람 기준으로 다른 사람이 일찍 도착합니다. 제출 시점에는 균일한 이동시간 예제만 테스트했습니다. 앞으로 지역을 나눈 합성 데이터로 위반 수, 총 탑승 시간, 조기 도착 시간을 측정해야 합니다.
- 외울 키워드: 회사 거리 정렬, 방향 무시 · 60분 위반 위험 · 출근 시각 미고려
- 확인용 근거: [제출물] planner.py:16, planner.py:29, tests/test_planner.py:11-17
- 꼬리 질문: "개선안 하나만?" → 각도(방향)로 구역을 나누는 sweep 기준선이나 출근 시각별 그룹핑을 제안합니다.
- ⚠ 본인 확인: 없음

### C6-1. AI_COLLABORATION.md의 "노선 계산 방식 선택" 과정을 실제로 어떻게 진행하셨나요? OR-Tools 제안을 처음 어떻게 검토했고, AI 제안 중 받아들인 것과 버린 것은 무엇이며, 각각 무엇을 근거로 판단했나요? 문서의 "swap/relocate" 중 relocate가 코드에 없는 이유도 설명해 주세요.
- 출제 근거: AI_COLLABORATION.md:3-6
- 모범 답안: AI에게 처음 물었을 때 OR-Tools VRP 솔버를 쓰자는 제안을 받았습니다. 시험 환경에서 의존성 설치가 보장되지 않고 2초 안에 결과를 내야 해서 받아들이지 않았습니다. 대신 기준선을 만든 뒤 시간과 후보 수를 제한한 지역 탐색으로 개선하는 구조를 택했습니다. 판단 근거는 [본인 기억으로 채우기: 설치를 시도했는지, 2초 요구가 어디서 왔는지]입니다. 문서에는 swap/relocate라고 적었지만 실제 코드에는 swap만 있습니다. relocate가 빠진 이유는 [본인 기억으로 채우기]이고, 문서를 코드에 맞게 고쳐야 합니다.
- 외울 키워드: OR-Tools 거절 · 의존성·2초 · relocate 미구현 인정
- 확인용 근거: [제출물] AI_COLLABORATION.md:4-6, planner.py:56, planner.py:70
- 꼬리 질문: "기준선과 지역 탐색 구조는 누가 제안했나요?" → [본인 기억으로 채우기]
- ⚠ 본인 확인: [본인 기억으로 채우기: OR-Tools 거절 당시 설치 시도나 실행 여부] · [본인 기억으로 채우기: 2초 요구의 출처] · [본인 기억으로 채우기: relocate를 뺀 이유(시간 부족, AI 코드 누락 등)] · [본인 기억으로 채우기: 대체 구조를 AI가 냈는지 본인이 냈는지]

### C6-2. AI_COLLABORATION.md의 "소수 단위 이동시간을 분 단위 시간표로 변환할 때 생기는 계산 기준 문제" 처리 과정을 실제로 어떻게 진행하셨나요? 이 문제를 처음 어떻게 알게 되었고, AI 제안 중 받아들인 것과 버린 것은 무엇이며, 각각 어떤 근거로 판단했나요?
- 출제 근거: AI_COLLABORATION.md:8-12
- 모범 답안: 이동시간이 7.4분처럼 소수로 들어오는데, AI가 처음 작성한 코드는 `round()`로 7분으로 내렸습니다. 구간이 쌓이면 실제보다 이른 도착 시각이 표시됐습니다. 이 문제를 처음 알아챈 계기는 [본인 기억으로 채우기]입니다. 저는 `test_minutes_are_rounded_up`을 추가해 7.4분 두 구간이 16분이어야 한다는 실패를 재현한 뒤, 구간마다 `math.ceil`로 올림하도록 바꿨습니다. AI가 제안한 "합계를 낸 뒤 마지막에 한 번만 반올림" 방식은 정류장별 시각이 합계와 어긋나서 버렸습니다. 이 테스트는 지금 통과합니다.
- 외울 키워드: round→이른 도착 · 실패 테스트 먼저 · 구간별 ceil, 합계 반올림 기각
- 확인용 근거: [제출물] AI_COLLABORATION.md:9-12, planner.py:11, tests/test_planner.py:21-25 / [이번 점검] unittest 4개 OK
- 꼬리 질문: "합계 반올림 방식이 어긋난다는 것은 어떻게 확인했나요?" → [본인 기억으로 채우기: 예시 계산이나 실행 결과]
- ⚠ 본인 확인: [본인 기억으로 채우기: 문제를 처음 발견한 계기(화면 확인, 수작업 계산 등)] · [본인 기억으로 채우기: 합계 반올림안이 어긋남을 확인한 구체 사례]

### C6-3. README에는 "워커가 작업을 꺼내"와 "워커 프로세스가 죽으면 자동 재시도"라고 적혀 있지만, 코드는 동기 실행이고 재시도가 없습니다. AI가 만든 문서와 코드가 일치하는지 어떻게 검토하셨고, 이 불일치는 어떻게 생겼나요?
- 출제 근거: README.md:13, README.md:24, api.py:7 "synchronous in this submission; see README"
- 모범 답안: 이 부분은 제가 검토하지 못한 불일치입니다. 코드상 `post_plans`가 `jobs.run`을 직접 호출하고, 워커 루프나 재시도 코드는 없습니다. api.py 주석은 README를 참조하라고 하지만, README에는 동기 실행에 대한 설명이 없습니다. 불일치가 생긴 경위는 [본인 기억으로 채우기]입니다. 제가 검증한 것은 README의 테스트 명령으로 돌린 네 개 테스트이고, 신뢰성 절에서 테스트로 뒷받침되는 것은 STALE 하나뿐입니다. 제출 전에 재시도 문장은 미구현이라고 고치고, 워커 대신 동기 실행이라고 명시하는 것이 맞습니다.
- 외울 키워드: 문서·코드 불일치 인정 · STALE만 테스트 · 미구현 명시
- 확인용 근거: [제출물] README.md:13, README.md:24, api.py:7, jobs.py:1 / [이번 점검] `grep -rn "retry" src/` → 없음
- 꼬리 질문: "AI 산출물을 검증하는 본인 절차가 있나요?" → [본인 기억으로 채우기], 앞으로는 주장마다 테스트나 파일을 대응시키는 원장을 만들겠다고 답합니다.
- ⚠ 본인 확인: [본인 기억으로 채우기: README를 AI가 썼는지, 원래 워커를 계획했는지] · [본인 기억으로 채우기: 문서 검토를 어떻게 했는지]

## 주장 원장
| 주장 | 문서 위치 | 상태 | 코드·테스트 위치 |
|---|---|---|---|
| `POST /plans` 시 작업 생성, `job_id` 반환 | README.md:12 | 🟡 | api.py:5-8 (API 테스트 없음) |
| 워커가 작업을 꺼내 처리 | README.md:13 | ❌ | 워커·큐 없음, api.py:7 동기 호출 |
| 활성 데이터셋 스냅샷으로 계산 | README.md:13 | 🟡 | jobs.py:21, dataset.py:5-6 (내부 dict는 가변) |
| 계획 저장, `GET /me/route`로 조회 | README.md:14 | 🟡 | jobs.py:31-41, api.py:18-23 (테스트 없음) |
| 차량 정원 초과 배정 안 함 | README.md:17 | ✅ | planner.py:18-22, 48-49 / test_plan_respects_capacity_and_ride_limit, test_not_enough_seats_raises |
| 모든 구성원 출근 시각 이전 도착 | README.md:18 | 🟡 | planner.py:29-32 구조상 보장, validate_plan 검사·테스트 없음 |
| 노선당 최대 탑승 60분 | README.md:19 | 🟡 (위반 게시 가능) | planner.py:6, 50-51 검사만 있음. baseline·게시 경로 미검증, 테스트는 16분 예제뿐 |
| 시간 제한(기본 2초) 시 최선해 반환 | README.md:22 | 🟡 | planner.py:55, 59, 66-67 (테스트 없음) |
| 데이터셋 변경 시 STALE, 미게시 | README.md:23 | ✅ | jobs.py:28-30 / test_dataset_swap_marks_stale (같은 version은 미감지) |
| 워커 사망 시 자동 재시도 | README.md:24 | ❌ | 없음, jobs.py:7-8 메모리 저장 |
| 테스트 명령 `python -m unittest discover -s tests` | README.md:28 | ✅ | [이번 점검] 4개 OK |
| OR-Tools 거절, 표준 라이브러리 휴리스틱 | AI_COLLABORATION.md:4-6 | 🟡 | planner.py:2-3 (math, time만 import) |
| 가까운 구성원부터 채우는 기준선 | AI_COLLABORATION.md:5 | 🟡 | planner.py:14-23 (회사까지 거리 기준) |
| 시간·후보 수 제한 지역 탐색 | AI_COLLABORATION.md:5-6 | 🟡 | planner.py:55, 66-67 |
| swap | AI_COLLABORATION.md:6 | 🟡 | planner.py:70 |
| relocate | AI_COLLABORATION.md:6 | ❌ | 없음 |
| `round()`가 이른 도착 시각을 냄 → 구간별 `math.ceil` | AI_COLLABORATION.md:9-11 | ✅ | planner.py:11 / test_minutes_are_rounded_up (tests/test_planner.py:21-25) |
| 합계 후 한 번 반올림 방식 기각 | AI_COLLABORATION.md:12 | ❌ (문서 진술뿐, 비교 근거 없음) | 없음 (본인 기억) |
