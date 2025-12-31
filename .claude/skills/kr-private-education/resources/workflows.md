# 주요 워크플로우

사교육 시스템의 핵심 업무 흐름을 정의합니다.

---

## 전체 업무 흐름

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ 상담/문의 │ → │ 레벨테스트 │ → │ 반편성  │ → │ 수강등록 │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
                                                │
┌─────────────────────────────────────────────────┘
│
▼
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  결제   │ → │ 수업진행 │ → │ 출결관리 │ → │ 성적관리 │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
                                                │
┌─────────────────────────────────────────────────┘
│
▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│ 정기상담 │ → │ 재등록  │ → │ 퇴원/졸업│
└─────────┘   └─────────┘   └─────────┘
```

---

## WF-001: 신규 상담 & 등록

### 흐름

```
상담문의 접수
    │
    ▼
┌──────────────────┐
│   상담 예약      │ ← 전화/온라인/방문
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   입학 상담      │ ← 학습 상태, 목표 파악
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   레벨테스트     │ ← 수준 진단
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   반 추천        │ ← 적합한 반 제안
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
[ 등록 ]   [ 미등록 ]
    │         │
    ▼         ▼
수강등록   Follow-up
프로세스   스케줄링
```

### 상태 흐름

```python
class ConsultationFlow:
    INQUIRY = "inquiry"           # 문의 접수
    SCHEDULED = "scheduled"       # 상담 예약
    IN_PROGRESS = "in_progress"   # 상담 중
    LEVEL_TEST = "level_test"     # 레벨테스트
    COMPLETED = "completed"       # 상담 완료
    ENROLLED = "enrolled"         # 등록 완료
    NOT_ENROLLED = "not_enrolled" # 미등록
    FOLLOW_UP = "follow_up"       # 재상담 필요
```

### 구현 예시

```python
class ConsultationService:
    async def process_inquiry(self, inquiry: InquiryDto) -> Consultation:
        """문의 접수 처리"""
        consultation = Consultation(
            consultation_type=ConsultationType.ADMISSION,
            status=ConsultationStatus.SCHEDULED,
            scheduled_at=inquiry.preferred_datetime,
            topic=inquiry.interest_subject
        )

        # 학부모 생성 (신규인 경우)
        parent = await self._create_or_get_parent(inquiry)

        # 상담 알림 발송
        await self._send_consultation_reminder(consultation, parent)

        return await self._repository.create(consultation)

    async def complete_level_test(
        self,
        consultation_id: str,
        test_result: LevelTestResult
    ) -> ClassRecommendation:
        """레벨테스트 완료 후 반 추천"""
        consultation = await self._repository.get(consultation_id)

        # 적합한 반 찾기
        recommended_classes = await self._find_suitable_classes(
            test_result.subject,
            test_result.level,
            test_result.target_grade
        )

        return ClassRecommendation(
            consultation_id=consultation_id,
            recommended_classes=recommended_classes,
            test_result=test_result
        )
```

---

## WF-002: 수강 등록 & 결제

### 흐름

```
반 선택
    │
    ▼
┌──────────────────┐
│  수강 정보 입력   │ ← 기간, 시작일
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  수강료 계산     │ ← 할인 적용
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  수강계약서 작성  │ ← 법적 필수
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  결제 처리       │ ← 카드/이체/현금
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
[ 성공 ]   [ 실패 ]
    │         │
    ▼         ▼
수강확정   재시도/취소
```

### 수강료 계산 로직

```python
class EnrollmentService:
    async def calculate_tuition(
        self,
        class_: Class,
        start_date: date,
        end_date: date,
        discount_codes: List[str] = []
    ) -> TuitionCalculation:
        """수강료 계산"""

        # 기본 수강료
        base_tuition = class_.tuition_monthly
        material_fee = class_.material_fee or 0

        # 기간 계산 (일할 계산)
        total_days = (end_date - start_date).days
        month_days = 30

        if start_date.day != 1:
            # 월 중간 등록 시 일할 계산
            remaining_days = month_days - start_date.day + 1
            first_month = int(base_tuition * remaining_days / month_days)
        else:
            first_month = base_tuition

        # 할인 적용
        discounts = await self._apply_discounts(
            base_tuition,
            discount_codes
        )

        return TuitionCalculation(
            base_tuition=base_tuition,
            material_fee=material_fee,
            prorated_amount=first_month,
            discounts=discounts,
            final_amount=first_month + material_fee - sum(discounts.values())
        )

    async def _apply_discounts(
        self,
        base: int,
        codes: List[str]
    ) -> Dict[str, int]:
        """할인 적용"""
        discounts = {}

        for code in codes:
            if code == "SIBLING":
                discounts["형제할인"] = int(base * 0.1)  # 10%
            elif code == "EARLY_BIRD":
                discounts["조기등록"] = int(base * 0.05)  # 5%
            elif code == "MULTI_SUBJECT":
                discounts["다과목할인"] = int(base * 0.1)  # 10%

        return discounts
```

### 결제 처리

```python
class PaymentService:
    async def process_payment(
        self,
        enrollment_id: str,
        payment_request: PaymentRequest
    ) -> Payment:
        """결제 처리"""

        enrollment = await self._enrollment_repo.get(enrollment_id)

        # 결제 생성
        payment = Payment(
            enrollment_id=enrollment_id,
            parent_id=enrollment.student.parent_id,
            amount=enrollment.final_amount,
            payment_type=PaymentType.TUITION,
            payment_method=payment_request.method,
            status=PaymentStatus.PENDING,
            due_date=date.today()
        )

        # PG 결제 처리
        if payment_request.method in [PaymentMethod.CARD]:
            pg_result = await self._pg_service.process(payment_request)
            payment.pg_tid = pg_result.tid
            payment.pg_response = pg_result.raw_response

            if pg_result.success:
                payment.status = PaymentStatus.COMPLETED
                payment.paid_at = datetime.now()
            else:
                payment.status = PaymentStatus.FAILED

        # 현금/이체는 수동 확인 필요
        elif payment_request.method in [PaymentMethod.CASH, PaymentMethod.BANK_TRANSFER]:
            payment.status = PaymentStatus.PENDING

        await self._payment_repo.create(payment)

        # 결제 완료 시 수강 활성화
        if payment.status == PaymentStatus.COMPLETED:
            await self._activate_enrollment(enrollment)

        return payment
```

---

## WF-003: 출결 관리

### 일일 출결 흐름

```
수업 시작
    │
    ▼
┌──────────────────┐
│  출석 체크 시작   │ ← 수업 시작 시간
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  학생별 출결 입력 │ ← 출석/결석/지각
└────────┬─────────┘
         │
    ┌────┼────┬────┐
    ▼    ▼    ▼    ▼
 출석  결석  지각  조퇴
         │    │
         ▼    ▼
     ┌────────────┐
     │ 학부모 알림 │
     └────────────┘
         │
         ▼
┌──────────────────┐
│  보강 여부 확인   │
└──────────────────┘
```

### 구현 예시

```python
class AttendanceService:
    async def record_attendance(
        self,
        enrollment_id: str,
        schedule_id: str,
        date_: date,
        status: AttendanceStatus,
        check_in_time: Optional[time] = None,
        reason: Optional[str] = None
    ) -> Attendance:
        """출결 기록"""

        attendance = Attendance(
            enrollment_id=enrollment_id,
            schedule_id=schedule_id,
            date=date_,
            status=status,
            check_in_time=check_in_time,
            reason=reason
        )

        await self._attendance_repo.create(attendance)

        # 결석/지각 시 학부모 알림
        if status in [AttendanceStatus.ABSENT, AttendanceStatus.LATE]:
            await self._notify_parent(attendance)

        return attendance

    async def get_attendance_summary(
        self,
        student_id: str,
        start_date: date,
        end_date: date
    ) -> AttendanceSummary:
        """출결 요약"""

        attendances = await self._attendance_repo.find_by_student_and_period(
            student_id, start_date, end_date
        )

        return AttendanceSummary(
            total=len(attendances),
            present=len([a for a in attendances if a.status == AttendanceStatus.PRESENT]),
            absent=len([a for a in attendances if a.status == AttendanceStatus.ABSENT]),
            late=len([a for a in attendances if a.status == AttendanceStatus.LATE]),
            early_leave=len([a for a in attendances if a.status == AttendanceStatus.EARLY_LEAVE]),
            attendance_rate=self._calculate_rate(attendances)
        )

    async def _notify_parent(self, attendance: Attendance):
        """학부모 알림 발송"""
        enrollment = await self._enrollment_repo.get(attendance.enrollment_id)
        parent = enrollment.student.parent

        message = self._build_attendance_message(attendance)

        for channel in parent.notification_channels:
            if channel == "SMS":
                await self._sms_service.send(parent.phone, message)
            elif channel == "KAKAO":
                await self._kakao_service.send_alimtalk(parent.phone, message)

        attendance.notification_sent = True
        await self._attendance_repo.update(attendance)
```

---

## WF-004: 환불 처리

### 흐름

```
환불 요청
    │
    ▼
┌──────────────────┐
│  환불 사유 확인   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  환불금액 계산   │ ← 학원법 기준
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  환불 승인       │ ← 관리자 승인
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  환불 처리       │ ← PG/현금
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  수강 종료 처리   │
└──────────────────┘
```

### 구현 예시

```python
class RefundService:
    async def calculate_refund(
        self,
        enrollment_id: str,
        cancel_date: date
    ) -> RefundCalculation:
        """환불 금액 계산 (학원법 시행령 기준)"""

        enrollment = await self._enrollment_repo.get(enrollment_id)

        # 수업 시작 전
        if cancel_date < enrollment.start_date:
            refund_amount = enrollment.final_amount
            refund_ratio = Decimal("1.0")
            reason = "수업 시작 전 전액 환불"
        else:
            # 경과 비율 계산
            total_days = (enrollment.end_date - enrollment.start_date).days
            elapsed_days = (cancel_date - enrollment.start_date).days
            progress = Decimal(elapsed_days) / Decimal(total_days)

            if progress < Decimal("0.333"):
                refund_ratio = Decimal("0.667")
                reason = "1/3 경과 전 2/3 환불"
            elif progress < Decimal("0.5"):
                refund_ratio = Decimal("0.5")
                reason = "1/2 경과 전 1/2 환불"
            else:
                refund_ratio = Decimal("0")
                reason = "1/2 경과 후 환불 불가"

            refund_amount = int(enrollment.final_amount * refund_ratio)

        # 교재비는 환불 불가 (사용 시)
        if enrollment.material_used:
            refund_amount -= enrollment.material_fee

        return RefundCalculation(
            enrollment_id=enrollment_id,
            original_amount=enrollment.final_amount,
            refund_amount=max(0, refund_amount),
            refund_ratio=refund_ratio,
            reason=reason,
            progress_percentage=float(progress) * 100 if cancel_date >= enrollment.start_date else 0
        )

    async def process_refund(
        self,
        enrollment_id: str,
        approved_amount: int,
        reason: str
    ) -> Payment:
        """환불 처리"""

        enrollment = await self._enrollment_repo.get(enrollment_id)
        original_payment = await self._payment_repo.find_by_enrollment(enrollment_id)

        # PG 환불 처리
        if original_payment.payment_method == PaymentMethod.CARD:
            refund_result = await self._pg_service.refund(
                original_payment.pg_tid,
                approved_amount
            )

        # 결제 정보 업데이트
        original_payment.refund_amount = approved_amount
        original_payment.refunded_at = datetime.now()
        original_payment.refund_reason = reason
        original_payment.status = PaymentStatus.REFUNDED

        await self._payment_repo.update(original_payment)

        # 수강 상태 변경
        enrollment.status = EnrollmentStatus.REFUNDED
        enrollment.cancelled_at = datetime.now()
        await self._enrollment_repo.update(enrollment)

        return original_payment
```

---

## WF-005: 정기 상담

### 월간 상담 흐름

```
월말 접근
    │
    ▼
┌──────────────────┐
│ 상담 대상 추출    │ ← 월 1회 이상
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  상담 일정 배정   │ ← 강사별 배분
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  상담 알림 발송   │ ← 학부모 안내
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  상담 진행       │ ← 성적/태도/계획
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  상담 기록 저장   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  후속조치 등록    │
└──────────────────┘
```

### 구현 예시

```python
class ConsultationScheduler:
    async def generate_monthly_schedule(
        self,
        academy_id: str,
        target_month: date
    ) -> List[Consultation]:
        """월간 상담 스케줄 생성"""

        # 활성 수강생 조회
        active_students = await self._student_repo.find_active_by_academy(academy_id)

        # 강사별 상담 가능 시간 조회
        instructors = await self._instructor_repo.find_by_academy(academy_id)

        consultations = []

        for student in active_students:
            # 담당 강사 찾기
            instructor = await self._find_primary_instructor(student)

            # 상담 시간 배정
            available_slot = await self._find_available_slot(
                instructor,
                target_month
            )

            consultation = Consultation(
                student_id=student.id,
                parent_id=student.parent_id,
                instructor_id=instructor.id,
                consultation_type=ConsultationType.REGULAR,
                scheduled_at=available_slot,
                method=ConsultationMethod.PHONE,
                topic=f"{target_month.strftime('%Y년 %m월')} 정기 상담",
                status=ConsultationStatus.SCHEDULED
            )

            consultations.append(consultation)

            # 학부모 알림
            await self._notify_consultation_schedule(consultation)

        return await self._consultation_repo.bulk_create(consultations)
```

---

## 워크플로우 상태 다이어그램

### 수강 상태

```
                    ┌─────────┐
         ┌──────────│ PENDING │──────────┐
         │          └────┬────┘          │
         │               │               │
         │          결제완료              │결제실패
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ EXPIRED │    │ ACTIVE  │    │CANCELLED│
    └─────────┘    └────┬────┘    └─────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
      환불요청       기간만료        중도퇴원
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │REFUNDED │    │COMPLETED│    │WITHDRAWN│
    └─────────┘    └─────────┘    └─────────┘
```

### 상담 상태

```
    ┌────────────┐
    │ SCHEDULED  │ ──────┬──────────────────┐
    └─────┬──────┘       │                  │
          │              │                  │
     상담시작         노쇼              취소요청
          │              │                  │
          ▼              ▼                  ▼
    ┌────────────┐  ┌────────────┐   ┌────────────┐
    │IN_PROGRESS │  │  NO_SHOW   │   │ CANCELLED  │
    └─────┬──────┘  └────────────┘   └────────────┘
          │
      상담완료
          │
          ▼
    ┌────────────┐
    │ COMPLETED  │
    └────────────┘
```
