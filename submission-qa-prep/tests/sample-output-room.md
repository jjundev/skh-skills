## 약점 Top 3
1. README의 "동시 요청 충돌은 DB 제약으로 막습니다"는 근거가 없습니다(❌). 스키마에 겹침 관련 제약이 없고 겹침 검사는 INSERT 전에 Python에서 SELECT로 합니다. — `README.md:11`, `app/store.py:6-12`, `app/booking.py:1`, `app/booking.py:29-34`
2. "닫을 때 … 예약자에게 알림이 갑니다"를 뒷받침하는 코드가 없습니다(❌). `close_room`은 이후 예약을 DELETE로 지워서 누구에게 알릴지에 대한 기록도 남지 않습니다. — `README.md:13`, `app/booking.py:39-43`
3. 문서에 적힌 기능 중 함수가 없는 것이 있습니다(❌). 예약 취소, 관리자의 회의실 열기, 표시할 때의 타임존 변환입니다. — `README.md:3`, `README.md:7`, `AI_COLLABORATION.md:5`. `app/booking.py`에는 `to_utc`·`overlaps`·`create`·`close_room`만 있습니다.

## 제출 전에 직접 돌려볼 것
제출물 루트(`room-booking/`)에서 실행합니다. 아래 결과는 이번 점검에서 제출물을 복사한 사본으로 얻었습니다. 직접 돌려 같은 결과를 본 뒤에만 답안에서 "확인했습니다"라고 말하세요.

1. 테스트 전체 → 4개 통과(OK)
   ```
   python3 -m unittest discover -s tests -v
   ```
2. 동시 요청 재현(두 연결이 모두 검사를 마친 뒤 INSERT) → `False False` 다음 `(2,)`. 같은 시간대에 두 행이 들어갑니다.
   ```
   python3 - <<'EOF'
   import os, tempfile
   from datetime import datetime, timedelta, timezone
   from app import booking, store
   K = timezone(timedelta(hours=9)); p = os.path.join(tempfile.mkdtemp(), "db.sqlite")
   c1 = store.connect(p); c1.execute("INSERT INTO rooms(id) VALUES ('A')"); c1.commit(); c2 = store.connect(p)
   s, e = booking.to_utc(datetime(2026,1,5,10,tzinfo=K)), booking.to_utc(datetime(2026,1,5,11,tzinfo=K))
   print(booking.overlaps(c1, "A", s, e), booking.overlaps(c2, "A", s, e))
   for c in (c1, c2):
       c.execute("INSERT INTO bookings(room,owner,start_utc,end_utc) VALUES ('A','u',?,?)", (s, e)); c.commit()
   print(c1.execute("SELECT count(*) FROM bookings").fetchone())
   EOF
   ```
3. 규칙 경계 → `1`(정확히 4시간은 허용), `A invalid duration`(4시간 1분은 거절), `NOPE room closed`(없는 회의실도 "closed"로 응답), `[('u',)] (0,)`(10:00에 닫으면 08–12 진행 중 예약은 남고 13–14 예약은 삭제됨)
   ```
   python3 - <<'EOF'
   from datetime import datetime, timedelta, timezone
   from app import booking, store
   K = timezone(timedelta(hours=9)); d = lambda h, m=0: datetime(2026,1,5,h,m,tzinfo=K)
   c = store.connect(); c.execute("INSERT INTO rooms(id) VALUES ('A')")
   print(booking.create(c, "A", "u", d(8), d(12)))
   for args in [("A", d(13), d(17,1)), ("NOPE", d(13), d(14))]:
       try: booking.create(c, args[0], "u", args[1], args[2])
       except ValueError as x: print(args[0], x)
   booking.create(c, "A", "future", d(13), d(14)); booking.close_room(c, "A", d(10))
   print(c.execute("SELECT owner FROM bookings").fetchall(), c.execute("SELECT open FROM rooms").fetchone())
   EOF
   ```
4. 슬롯 경계와 규모 → `1`(10:10–10:20 예약 하나로 10:00–10:30 슬롯 전체가 빠짐), `440 0.03 s` 안팎(30일 범위 1,440슬롯 × 예약 1,000건, 시간은 기기마다 다름)
   ```
   python3 - <<'EOF'
   import time
   from datetime import datetime, timedelta, timezone
   from app import booking, slots, store
   K = timezone(timedelta(hours=9)); d = lambda h, m=0: datetime(2026,1,5,h,m,tzinfo=K)
   c = store.connect(); c.execute("INSERT INTO rooms(id) VALUES ('A')")
   booking.create(c, "A", "u", d(10,10), d(10,20)); s = booking.to_utc(d(10))
   print(len(slots.free_slots(c, "A", s, s + 3600)))
   b = booking.to_utc(d(0))
   c.executemany("INSERT INTO bookings(room,owner,start_utc,end_utc) VALUES ('A','u',?,?)", [(b+i*2400, b+i*2400+600) for i in range(1000)])
   t = time.perf_counter(); n = len(slots.free_slots(c, "A", b, b + 30*86400)); print(n, round(time.perf_counter()-t, 3), "s")
   EOF
   ```

## 예상 질문

### C1-1. README에는 "같은 회의실의 예약은 시간이 겹칠 수 없습니다. 동시 요청 충돌은 DB 제약으로 막습니다"라고 적었지만, `booking.py`는 "Overlap is checked in Python before insert" 방식으로 `overlaps()`를 SELECT한 뒤 INSERT합니다. 이 방식을 택한 이유, DB 제약이나 트랜잭션 잠금 같은 대안과의 차이, 그리고 이 선택으로 포기한 것은 무엇인가요?
- 출제 근거: `README.md:11` "동시 요청 충돌은 DB 제약으로 막습니다." / `app/booking.py:1` "Overlap is checked in Python before insert."
- 모범 답안: 결론부터 말씀드리면 겹침 검사는 애플리케이션 코드에서 했고, README의 "DB 제약으로 막는다"는 문장은 구현과 맞지 않습니다. 시간 구간이 겹치는지는 UNIQUE 같은 단순 제약으로 표현할 수 없어서 `overlaps()`에서 반열린 구간 비교(`start_utc < end AND start < end_utc`)로 SELECT한 뒤 INSERT하게 했습니다. 단일 요청에서는 `test_overlap_rejected`와 `test_back_to_back_allowed`로 확인했습니다. 대안이었던 `BEGIN IMMEDIATE`로 검사와 삽입을 한 트랜잭션에 묶는 방식이나 트리거와 달리, 지금 구조는 두 요청이 동시에 검사를 통과하면 둘 다 들어갑니다. 그래서 포기한 것은 동시성 보장입니다.
- 외울 키워드: 반열린 구간 비교 · 검사 후 삽입(check-then-insert) · BEGIN IMMEDIATE
- 확인용 근거: [제출물] `app/booking.py:14-19`, `app/booking.py:29-35`, `app/store.py:6-12`(제약 없음), `tests/test_booking.py:26` `test_back_to_back_allowed`, `tests/test_booking.py:32` `test_overlap_rejected` / [이번 점검] 직접 돌려볼 것 2번 → `False False`, `(2,)`
- 꼬리 질문: "그럼 README 문장은 왜 그렇게 썼나요?" → 의도와 구현이 어긋났다고 인정하고, 고친다면 쓰기 트랜잭션으로 검사와 삽입을 묶겠다고 답합니다.
- ⚠ 본인 확인: [본인 기억으로 채우기: README의 "DB 제약" 문장을 누가(본인/AI) 언제 썼는지, 그때 DB 제약을 시도했는지]

### C1-2. 시각을 `start_utc`/`end_utc` 정수(epoch 초)로 저장하고, `to_utc()`에서 타임존 없는(naive) datetime은 아예 거부하도록 만들었습니다. 이렇게 설계한 이유, ISO 문자열이나 로컬 시간 저장 같은 대안과의 차이, 그리고 이 선택으로 포기한 것은 무엇인가요?
- 출제 근거: `app/store.py:10` "start_utc INTEGER NOT NULL,  -- epoch seconds" / `app/booking.py:8` "Naive datetimes are rejected so local time never sneaks into storage."
- 모범 답안: UTC epoch 초로 저장해서 서버나 사용자의 타임존과 상관없이 시각을 하나의 기준으로 비교하려고 했습니다. 해외 지사 예약이 9시간 밀려 보인 문제가 계기였고, 타임존 없는 datetime은 `ValueError`로 거부해서 로컬 시간이 섞여 들어올 경로를 막았습니다. KST 10시 예약이 UTC 1시로 저장되는 것을 `test_stored_in_utc`로 확인했습니다. 정수로 저장하면 겹침 검사와 슬롯 계산이 단순한 정수 비교가 됩니다. ISO 문자열에 오프셋을 함께 저장하는 방식보다 사람이 DB를 읽기 어렵고, 예약한 사람의 원래 타임존 정보는 남지 않습니다. 표시할 때 변환하는 코드도 제출물에는 없습니다.
- 외울 키워드: UTC epoch 정수 · naive datetime 거부 · 원래 타임존 정보 소실
- 확인용 근거: [제출물] `app/booking.py:7-11`, `app/store.py:10-11`, `tests/test_booking.py:20` `test_stored_in_utc` / [이번 점검] 직접 돌려볼 것 1번 → 4개 통과
- 꼬리 질문: "서머타임이 있는 지역은요?" → 저장은 UTC라 영향이 없고, 표시 계층에서 `zoneinfo`로 변환해야 하는데 그 계층은 아직 없다고 답합니다.
- ⚠ 본인 확인: 없음

### C2-1. 구성원이 회의실 A의 빈 시간대를 조회한 뒤 하나를 골라 예약이 확정되기까지, 요청이 어떤 함수들을 거치고 회의실 상태(`rooms.open`)와 예약 데이터는 어디에 저장되며 누가 쓰고 읽는지 흐름을 설명해 주세요.
- 출제 근거: `README.md:3` "구성원은 빈 시간대를 조회하고 예약하며" / `app/slots.py:5`, `app/booking.py:22`
- 모범 답안: 조회는 `slots.free_slots()`가 처리합니다. 해당 회의실에서 범위와 겹치는 예약을 SELECT한 뒤 30분씩 걸으며 빈 슬롯의 UTC 시작 시각 목록을 돌려줍니다. 예약은 `booking.create()`가 처리하는데, `to_utc()`로 변환하고 길이를 검사한 뒤 `rooms.open`을 읽고 `overlaps()`를 거쳐 INSERT하고 commit합니다. 상태는 모두 SQLite의 `rooms`와 `bookings` 테이블에 있고, 연결은 호출자가 `store.connect()`로 만들어 넘깁니다. 기본 경로가 `:memory:`라서 프로세스가 끝나면 사라집니다. HTTP 계층이나 사용자 인증은 구현하지 않았고, `free_slots`는 회의실이 닫혔는지 확인하지 않습니다.
- 외울 키워드: free_slots → create · SQLite 두 테이블 · 연결은 호출자 소유
- 확인용 근거: [제출물] `app/slots.py:5-16`, `app/booking.py:22-36`, `app/store.py:16-19`, `tests/test_booking.py:39` `test_free_slots_skip_booked`
- 꼬리 질문: "조회와 예약 사이에 다른 사람이 먼저 잡으면?" → `create`의 `overlaps`가 거절하지만, 완전히 동시에 들어오면 둘 다 통과할 수 있다(C1-1)고 답합니다.
- ⚠ 본인 확인: 없음

### C2-2. 관리자가 회의실을 닫는 순간부터, 그 회의실에 이후 예약을 갖고 있던 구성원이 그 사실을 알게 되기까지 어떤 일이 일어나나요? README의 "이후 예약은 자동 취소되고 예약자에게 알림이 갑니다"를 기준으로, 상태가 어디서 어떻게 바뀌고 누가 그 결과를 읽는지 설명해 주세요.
- 출제 근거: `README.md:13` "닫을 때 이후 예약은 자동 취소되고 예약자에게 알림이 갑니다." / `app/booking.py:39-43`
- 모범 답안: `close_room()`은 `rooms.open`을 0으로 바꾸고, 시작 시각이 지금 이후인 예약 행을 DELETE한 다음 commit합니다. 여기서 끝이고, README에 적은 알림은 구현하지 않았습니다. 행을 지우기 때문에 누구의 예약이 취소됐는지 기록도 남지 않아서, 나중에 알림을 붙이려면 삭제 대신 상태 컬럼을 두거나 지우기 전에 owner를 먼저 SELECT해야 합니다. 이미 시작해서 진행 중인 예약은 지워지지 않고 남습니다. 회의실을 다시 여는 함수도 없습니다. 이 동작은 테스트가 없어서 코드로만 설명드릴 수 있습니다.
- 외울 키워드: open=0 + DELETE · 알림 미구현 · 진행 중 예약은 남음
- 확인용 근거: [제출물] `app/booking.py:39-43`(알림 코드 없음, 해당 테스트 없음) / [이번 점검] 직접 돌려볼 것 3번 → `[('u',)] (0,)`
- 꼬리 질문: "구성원 화면에는 뭐가 보이나요?" → 예약이 조용히 사라지고, `free_slots`는 닫힌 회의실의 빈 슬롯도 그대로 보여 준다고 답합니다.
- ⚠ 본인 확인: [본인 기억으로 채우기: 알림을 구현하려다 뺐는지, 처음부터 README에만 적었는지]

### C3-1. 이 서비스에서 실제로 구현해 검증한 부분과 구현하지 않았거나 가정으로 남긴 부분을 구분해 설명해 주세요. 그리고 다른 평가자가 README의 "같은 회의실의 예약은 시간이 겹칠 수 없습니다"라는 주장을 확인하려면 어떤 경로(테스트·명령·파일)를 보면 되나요?
- 출제 근거: `README.md:11` "같은 회의실의 예약은 시간이 겹칠 수 없습니다." / `tests/test_booking.py:20-45`
- 모범 답안: 세 묶음으로 나누겠습니다. 테스트까지 있는 것은 UTC 저장, 연속 예약 허용, 겹침 거절, 빈 슬롯 계산입니다. 코드만 있고 테스트가 없는 것은 최대 4시간, 닫힌 회의실 거절, 회의실 닫기와 이후 예약 삭제입니다. 구현하지 않은 것은 동시 요청을 막는 DB 제약, 알림, 예약 취소, 회의실 열기, 표시할 때 타임존 변환입니다. 겹침 주장은 `tests/test_booking.py`의 `test_overlap_rejected`와 `test_back_to_back_allowed`, `booking.py`의 `overlaps()`를 보고 `python -m unittest discover -s tests`로 돌리면 확인할 수 있습니다. 다만 이 경로는 단일 요청만 검증하고, 동시 요청은 검증하지 않습니다.
- 외울 키워드: 테스트 4개 · 코드만 3개 · 미구현 5개
- 확인용 근거: [제출물] `tests/test_booking.py:20,26,32,39`, `app/booking.py:14-19`, `README.md:17` / [이번 점검] 직접 돌려볼 것 1번 → 4개 통과
- 꼬리 질문: "동시 요청은 어떻게 테스트하겠어요?" → 파일 DB에 연결 두 개를 열어 검사 후 INSERT를 교차시키는 테스트를 만들고, 지금은 두 행이 들어간다는 것을 보이겠다고 답합니다.
- ⚠ 본인 확인: 없음

### C3-2. README "규칙"의 "예약은 최대 4시간입니다"와 "닫힌 회의실에는 예약할 수 없고"는 테스트로 검증되었나요? 검증되지 않았다면 제3자가 이 두 주장을 확인할 수 있는 경로는 무엇이고, 경계값(정확히 4시간, 존재하지 않는 회의실)에서는 어떻게 동작하나요?
- 출제 근거: `README.md:12` "예약은 최대 4시간입니다." / `README.md:13` "닫힌 회의실에는 예약할 수 없고" / `app/booking.py:24-28`
- 모범 답안: 두 규칙 모두 코드는 있지만 테스트는 없습니다. `create()`에서 `end - start > MAX_SECONDS`이면 거절하므로, 코드상 정확히 4시간은 허용되고 4시간 1분부터 거절됩니다. 닫힘은 `rooms.open`을 읽어 0이거나 행이 없으면 "room closed"로 거절합니다. 그래서 존재하지 않는 회의실 ID도 같은 "room closed" 메시지가 나오는데, 사용자에게는 오해를 줄 수 있습니다. 제3자는 `booking.py`의 해당 줄을 보거나 경계값 스크립트를 돌리면 확인할 수 있습니다. 테스트 파일에 4시간 경계와 닫힌 회의실 예약을 추가하는 것이 남은 일입니다.
- 외울 키워드: MAX_SECONDS 4×3600 · 정확히 4시간 허용 · 없는 회의실도 room closed
- 확인용 근거: [제출물] `app/booking.py:4`, `app/booking.py:24-28`(해당 테스트 없음) / [이번 점검] 직접 돌려볼 것 3번 → `1`, `A invalid duration`, `NOPE room closed`
- 꼬리 질문: "end가 start보다 앞이면요?" → `end <= start` 조건으로 같은 "invalid duration"으로 거절된다고 답합니다(`app/booking.py:24`).
- ⚠ 본인 확인: 없음

### C4-1. 두 구성원이 같은 회의실의 같은 시간대를 거의 동시에 예약하거나, 서비스 프로세스가 재시작되거나, `create()`가 INSERT 직전에 예외로 중단되면 각각 시스템은 어떻게 동작하고 기존 예약과 구성원 화면은 어떤 상태가 되나요?
- 출제 근거: `README.md:11` "동시 요청 충돌은 DB 제약으로 막습니다." / `app/store.py:16` `def connect(path=":memory:")`
- 모범 답안: 동시 예약은 막지 못합니다. 검사와 삽입이 한 트랜잭션으로 묶이지 않아서, 두 요청이 모두 검사를 통과하면 같은 시간대에 두 행이 생기고 두 사람 모두 예약 성공으로 보게 됩니다. 재시작은 연결 경로에 달려 있습니다. 기본값인 `:memory:`를 쓰면 모든 예약과 회의실이 사라지고, 파일 경로를 주면 남습니다. 서비스 진입점이 없어서 운영에서 어느 쪽을 쓸지는 정하지 않았습니다. INSERT 전 예외는 쓴 것이 없으니 기존 데이터에 영향이 없고, 호출자가 `ValueError`를 받습니다. 동시성 처리는 미구현입니다.
- 외울 키워드: 중복 예약 두 행 · :memory: 유실 · 쓰기 전 예외는 무해
- 확인용 근거: [제출물] `app/booking.py:29-35`, `app/store.py:16-19` / [이번 점검] 직접 돌려볼 것 2번 → `(2,)`
- 꼬리 질문: "중복이 이미 생긴 뒤에는 어떻게 찾나요?" → 같은 room에서 구간이 겹치는 행 쌍을 self-join으로 찾는 점검 쿼리를 제안합니다.
- ⚠ 본인 확인: 없음

### C4-2. 관리자가 진행 중인 예약이 있는 회의실을 닫거나, 클라이언트가 타임존 없는 시각을 보내거나, 존재하지 않는 회의실 ID로 예약을 시도하면 각각 어떻게 동작하나요? 저장된 데이터와 사용자가 보는 결과를 함께 설명해 주세요.
- 출제 근거: `app/booking.py:39-43`, `app/booking.py:8-10`, `app/booking.py:26-28`
- 모범 답안: 진행 중인 예약은 시작 시각이 닫는 시각보다 앞이라 DELETE 조건(`start_utc >= now`)에 걸리지 않습니다. 코드상 그대로 남고, 이후 예약만 지워지며 회의실은 닫힘 상태가 됩니다. 타임존 없는 시각은 `to_utc()`가 "timezone-aware datetime required"로 거절하므로 저장되지 않습니다. 없는 회의실은 `rooms` 조회 결과가 없어서 "room closed"로 거절되는데, 메시지가 원인과 달라 사용자가 헷갈릴 수 있습니다. 세 경우 모두 테스트는 없고 코드로 설명드리는 것입니다. 거절은 전부 `ValueError` 하나라서 호출자가 원인을 메시지 문자열로만 구분할 수 있다는 한계도 있습니다.
- 외울 키워드: start_utc >= now · naive 거절 · 오류 종류가 ValueError 하나
- 확인용 근거: [제출물] `app/booking.py:9-10`, `app/booking.py:26-28`, `app/booking.py:42` / [이번 점검] 직접 돌려볼 것 3번 → `NOPE room closed`, `[('u',)] (0,)`
- 꼬리 질문: "진행 중 예약을 남긴 건 의도였나요?" → 코드 조건이 그렇게 되어 있다는 사실과 의도 여부를 구분해서 답합니다.
- ⚠ 본인 확인: [본인 기억으로 채우기: 진행 중 예약을 남기는 것이 의도한 정책이었는지]

### C5-1. 회의실과 예약이 크게 늘어나 30일 범위의 빈 시간대를 조회하고 한 회의실에 예약이 수천 건 쌓이면 어떤 부분이 병목이나 위험이 되나요? 이를 어떻게 확인했고, 결과를 신뢰하기 위해 앞으로 추가로 해볼 검증이나 개선은 무엇인가요?
- 출제 근거: `app/slots.py:12-13` `while t + SLOT <= day_end_utc:` / `if not any(s < t + SLOT and t < e for s, e in busy):`
- 모범 답안: 가장 큰 병목은 `free_slots()`입니다. 슬롯마다 범위 안의 예약 전체를 `any()`로 훑기 때문에 슬롯 수와 예약 수의 곱만큼 비교합니다. 30일이면 1,440슬롯입니다. 또 `bookings`에 `(room, start_utc)` 인덱스가 없어서 `overlaps()`와 조회 SELECT가 예약이 늘수록 느려질 수 있습니다. 제출 시점에는 성능을 측정하지 않았습니다. 30일·1,000건 정도는 스크립트로 시간을 재 볼 수 있고, 더 키운 측정과 인덱스 추가 전후 비교, 예약을 시작 시각 순으로 정렬해 한 번만 훑는 방식으로 바꾸는 것이 다음 개선입니다.
- 외울 키워드: 슬롯×예약 이중 순회 · 인덱스 없음 · 정렬 후 한 번 훑기
- 확인용 근거: [제출물] `app/slots.py:6-15`, `app/store.py:6-12`(인덱스 없음) / [이번 점검] 직접 돌려볼 것 4번 → `440 0.03 s` 안팎
- 꼬리 질문: "회의실이 100개면요?" → `free_slots`가 회의실 하나 단위라서 호출이 100번 반복되고, 회의실별로 묶어 조회하는 API가 필요하다고 답합니다.
- ⚠ 본인 확인: 없음

### C5-2. 예약이 10:10–10:20처럼 30분 경계에 맞지 않거나, 길이가 0이거나, 정확히 4시간처럼 극단적인 값이면 `create()`와 `free_slots()`는 각각 어떻게 동작하나요? 위험한 부분은 무엇이고 어떻게 확인할 수 있나요?
- 출제 근거: `README.md:8` "빈 시간대 계산 (30분 단위)" / `app/booking.py:24` / `app/slots.py:13`
- 모범 답안: `create()`는 30분 정렬을 강제하지 않아서 10:10–10:20 같은 예약도 받습니다. 그러면 `free_slots()`는 그 예약과 겹치는 10:00–10:30 슬롯 전체를 비어 있지 않다고 보므로, 10분 예약 하나가 30분을 막습니다. 길이 0이나 음수는 `end <= start` 조건으로, 4시간 초과는 `MAX_SECONDS` 조건으로 거절하고, 정확히 4시간은 허용합니다. 또 조회 시작 시각이 30분 경계가 아니면 슬롯도 어긋난 시각부터 만들어집니다. 이 경계값들은 테스트가 없고, 스크립트로 확인할 수 있습니다. 예약 시각을 30분 단위로 강제할지 정하는 것이 남은 일입니다.
- 외울 키워드: 30분 정렬 미강제 · 10분 예약이 슬롯 통째로 막음 · 4시간 정확히 허용
- 확인용 근거: [제출물] `app/booking.py:24-25`, `app/slots.py:11-15`(경계 테스트 없음) / [이번 점검] 직접 돌려볼 것 4번 → `1`, 3번 → `1`, `A invalid duration`
- 꼬리 질문: "정렬을 강제한다면 어디서 하나요?" → `create()`에서 `start % SLOT == 0`과 `end % SLOT == 0`을 검사하는 것이 가장 단순하다고 답합니다.
- ⚠ 본인 확인: 없음

### C6-1. AI_COLLABORATION.md에 적은 "시간대(타임존) 처리 기준" 항목을 실제로 어떻게 진행하셨나요? 해외 지사 구성원 예약이 9시간 밀려 보이는 문제를 처음 어떻게 알게 되었고, AI가 제안한 해결 방식 중 받아들인 것과 고치거나 버린 것은 무엇이며, 각각 어떤 근거로 판단하셨는지 구체적으로 설명해 주세요.
- 출제 근거: `AI_COLLABORATION.md:3` "## 1. 시간대(타임존) 처리 기준" / `AI_COLLABORATION.md:4-5` "UTC로 저장하고 표시할 때만 변환하도록 바꿨다. `test_stored_in_utc`로 확인했다."
- 모범 답안: AI가 처음 만든 코드는 모든 시각을 서버 로컬 시간으로 저장했습니다. [본인 기억으로 채우기: 9시간 밀림을 발견한 계기]로 문제를 알게 됐고, 저장은 UTC로 하도록 바꿨습니다. 지금 코드는 `to_utc()`에서 타임존 없는 datetime을 거부하고 UTC epoch 초로 저장합니다. KST 10시 예약이 UTC 1시로 저장되는 것을 `test_stored_in_utc`로 확인했습니다. AI 제안 중 [본인 기억으로 채우기: 받아들인 것과 고치거나 버린 것]. 다만 문서에 쓴 "표시할 때만 변환"하는 부분은 제출물에 코드가 없습니다. 저장 기준만 고쳤고 표시 쪽은 구현하지 않았습니다.
- 외울 키워드: 로컬 시간 → UTC · naive 거부 · 표시 변환 미구현
- 확인용 근거: [제출물] `app/booking.py:7-11`, `tests/test_booking.py:20-24` `test_stored_in_utc` / [이번 점검] 직접 돌려볼 것 1번 → `test_stored_in_utc ... ok`
- 꼬리 질문: "naive datetime 거부는 누구 아이디어였나요?" → 본인 기억에 따라 답하고, 그 줄의 주석(`app/booking.py:8`)이 의도를 설명한다고 덧붙입니다.
- ⚠ 본인 확인: [본인 기억으로 채우기: 9시간 밀림을 처음 본 계기(화면, 테스트, 동료 제보 등)] · [본인 기억으로 채우기: AI가 낸 수정안의 구체적 내용, 받아들인 것과 고치거나 버린 것] · [본인 기억으로 채우기: naive datetime 거부를 누가 제안했는지]

### C6-2. AI_COLLABORATION.md의 "겹침 검사 경계 조건" 항목에서, 10:00–11:00 예약 뒤 11:00–12:00 예약이 거절되는 버그를 처음 어떻게 알게 되었나요? AI가 제안한 `<=`→`<` 수정은 받아들이고 "1분 여유 두기"는 "슬롯 계산과 어긋나서" 버렸다고 적었는데, 각각 어떤 근거(테스트나 확인 결과)로 판단하셨는지 설명해 주세요.
- 출제 근거: `AI_COLLABORATION.md:7` "## 2. 겹침 검사 경계 조건" / `AI_COLLABORATION.md:8-9` "AI가 함께 제안한 \"1분 여유 두기\"는 슬롯 계산과 어긋나서 버렸다."
- 모범 답안: [본인 기억으로 채우기: 버그를 처음 본 계기]로, 끝나는 시각과 시작 시각이 같은 연속 예약이 거절되는 것을 알게 됐습니다. 끝 시각을 포함하는 `<=` 비교를 `<`로 바꿔 구간을 반열린 구간으로 보게 했고, `test_back_to_back_allowed`로 10–11시 뒤 11–12시 예약이 통과하는 것을 확인했습니다. "1분 여유 두기"를 버린 이유는 `free_slots()`도 같은 반열린 비교를 쓰기 때문입니다. 예약 쪽에만 1분 여유를 두면 두 함수의 겹침 기준이 서로 달라집니다. [본인 기억으로 채우기: 어긋남을 확인한 방법]. 이 판단을 직접 검증하는 테스트는 제출물에 없습니다.
- 외울 키워드: 반열린 구간 · test_back_to_back_allowed · 예약과 슬롯이 같은 기준
- 확인용 근거: [제출물] `app/booking.py:16`, `app/slots.py:13`, `tests/test_booking.py:26-30` `test_back_to_back_allowed` / [이번 점검] 직접 돌려볼 것 1번 → `test_back_to_back_allowed ... ok`
- 꼬리 질문: "1분 여유를 두면 구체적으로 어떤 화면 문제가 생기나요?" → 슬롯 목록에는 빈 칸으로 보이는데 예약하면 거절되는 불일치가 생긴다는 방향으로 답합니다.
- ⚠ 본인 확인: [본인 기억으로 채우기: 버그를 발견한 계기] · [본인 기억으로 채우기: "1분 여유" 제안의 정확한 형태(시작에 더하기, 끝에서 빼기 등)와 어긋남을 확인한 방법]

## 주장 원장
| 주장 | 문서 위치 | 상태 | 코드·테스트 위치 |
|---|---|---|---|
| 구성원이 빈 시간대를 조회하고 예약 | `README.md:3` | ✅ | `app/slots.py:5-16`, `app/booking.py:22-36`; `test_free_slots_skip_booked`, `test_back_to_back_allowed` |
| 관리자가 회의실을 연다 | `README.md:3` | ❌ | 여는 함수 없음(`rooms.open` 기본값 1만 있음, `app/store.py:5`) |
| 관리자가 회의실을 닫는다 | `README.md:3` | 🟡 | `app/booking.py:39-43`, 테스트 없음 |
| 예약 저장소는 SQLite | `README.md:6` | ✅ | `app/store.py:2`, `app/store.py:16-19`; 모든 테스트가 `store.connect()` 사용 |
| 예약 생성 | `README.md:7` | ✅ | `app/booking.py:22-36`; 테스트 4개 |
| 예약 취소 | `README.md:7` | ❌ | 취소 함수 없음(`app/booking.py:1` docstring에만 "cancel") |
| 겹침 검사 | `README.md:7` | ✅ | `app/booking.py:14-19`, `app/booking.py:29-30`; `test_overlap_rejected` |
| 빈 시간대 30분 단위 계산 | `README.md:8` | ✅ | `app/slots.py:2`, `app/slots.py:12-15`; `test_free_slots_skip_booked` |
| 같은 회의실 예약은 겹칠 수 없음 | `README.md:11` | ✅ (단일 요청 기준) | `app/booking.py:29-30`; `test_overlap_rejected`, `test_back_to_back_allowed` |
| 동시 요청 충돌은 DB 제약으로 막음 | `README.md:11` | ❌ | `app/store.py:6-12` 제약 없음, `app/booking.py:1` "checked in Python"; [이번 점검] 중복 2행 |
| 예약은 최대 4시간 | `README.md:12` | 🟡 | `app/booking.py:4`, `app/booking.py:24-25`, 테스트 없음 |
| 닫힌 회의실에는 예약 불가 | `README.md:13` | 🟡 | `app/booking.py:26-28`, 테스트 없음 |
| 닫을 때 이후 예약 자동 취소 | `README.md:13` | 🟡 | `app/booking.py:42`(DELETE, 기록 남지 않음), 테스트 없음 |
| 예약자에게 알림 | `README.md:13` | ❌ | 알림 코드 없음 |
| 테스트 명령 `python -m unittest discover -s tests` | `README.md:17` | ✅ | [이번 점검] 4개 통과 |
| AI가 처음에 서버 로컬 시간으로 저장하는 코드를 만듦 | `AI_COLLABORATION.md:4` | ❌ | 저장소에 이력 없음(git 저장소 아님), 본인 기억 |
| 시각을 UTC로 저장 | `AI_COLLABORATION.md:5` | ✅ | `app/booking.py:7-11`, `app/store.py:10-11`; `test_stored_in_utc` |
| 표시할 때만 변환 | `AI_COLLABORATION.md:5` | ❌ | 표시·변환 코드 없음(`free_slots`는 UTC epoch 반환, `app/slots.py:14`) |
| 겹침 비교를 `<=`에서 `<`로 수정 | `AI_COLLABORATION.md:8` | ✅ | `app/booking.py:16`; `test_back_to_back_allowed` |
| "1분 여유 두기"는 슬롯 계산과 어긋나서 버림 | `AI_COLLABORATION.md:9` | 🟡 | 코드에 여유 없음, `app/booking.py:16`과 `app/slots.py:13`이 같은 반열린 비교; 이유를 검증하는 테스트 없음 |
