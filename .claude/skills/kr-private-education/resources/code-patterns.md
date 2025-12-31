# 코드 패턴

사교육 도메인에 맞는 코드 패턴과 모범 예시를 제공합니다.

---

## 디렉토리 구조 (권장)

```
backend/
├── domain/
│   ├── academy/               # 학원 도메인
│   │   ├── model.py
│   │   ├── repository.py
│   │   └── service.py
│   ├── student/               # 학생 도메인
│   ├── enrollment/            # 수강 도메인
│   ├── attendance/            # 출결 도메인
│   ├── payment/               # 결제 도메인
│   ├── consultation/          # 상담 도메인
│   └── notification/          # 알림 도메인
├── api/v1/routers/
│   ├── academy.py
│   ├── student.py
│   ├── enrollment.py
│   ├── attendance.py
│   └── ...
├── dtos/
│   ├── academy.py
│   ├── student.py
│   └── ...
└── services/
    ├── sms_service.py         # SMS 발송
    ├── kakao_service.py       # 알림톡
    └── pg_service.py          # PG 연동
```

---

## 학생 관리 패턴

### 학생 등록

```python
# domain/student/service.py
class StudentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repository = StudentRepository(session)
        self._parent_repo = ParentRepository(session)

    async def register_student(
        self,
        dto: StudentRegistrationDto
    ) -> Student:
        """학생 등록 (학부모 연결 포함)"""

        # 1. 학부모 확인 또는 생성
        parent = await self._get_or_create_parent(dto.parent_info)

        # 2. 개인정보 동의 확인
        if not parent.privacy_consent:
            raise BusinessError("개인정보 동의가 필요합니다")

        # 3. 만 14세 미만 확인
        age = self._calculate_age(dto.birth_date)
        if age < 14 and not parent.privacy_consent:
            raise BusinessError("만 14세 미만은 법정대리인 동의 필수")

        # 4. 학생 생성
        student = Student(
            name=dto.name,
            phone=dto.phone,
            birth_date=dto.birth_date,
            school_name=dto.school_name,
            school_type=dto.school_type,
            grade=dto.grade,
            academy_id=dto.academy_id,
            parent_id=parent.id,
            enrollment_date=date.today(),
            status=StudentStatus.ACTIVE
        )

        await self._repository.create(student)

        # 5. 등록 알림 발송
        await self._send_welcome_notification(student, parent)

        return student
```

### 학생 검색

```python
# domain/student/repository.py
class StudentRepository(BaseRepository[Student]):
    async def search(
        self,
        academy_id: str,
        search_params: StudentSearchParams
    ) -> List[Student]:
        """학생 검색"""

        stmt = select(Student).where(Student.academy_id == academy_id)

        # 이름 검색
        if search_params.name:
            stmt = stmt.where(Student.name.contains(search_params.name))

        # 학년 필터
        if search_params.grade:
            stmt = stmt.where(Student.grade == search_params.grade)

        # 학교 타입 필터
        if search_params.school_type:
            stmt = stmt.where(Student.school_type == search_params.school_type)

        # 상태 필터 (기본: 재원생)
        if search_params.status:
            stmt = stmt.where(Student.status == search_params.status)
        else:
            stmt = stmt.where(Student.status == StudentStatus.ACTIVE)

        # 페이징
        stmt = stmt.offset(search_params.offset).limit(search_params.limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()
```

---

## 수강 관리 패턴

### 수강 등록 (트랜잭션)

```python
# domain/enrollment/service.py
class EnrollmentService:
    async def enroll(
        self,
        dto: EnrollmentCreateDto
    ) -> Enrollment:
        """수강 등록 (결제 포함)"""

        async with self.session.begin():
            # 1. 반 정원 확인
            class_ = await self._class_repo.get(dto.class_id)
            if class_.current_count >= class_.capacity:
                raise BusinessError("정원이 초과되었습니다")

            # 2. 수강료 계산
            tuition = await self._calculate_tuition(
                class_,
                dto.start_date,
                dto.discount_codes
            )

            # 3. 수강 등록 생성
            enrollment = Enrollment(
                student_id=dto.student_id,
                class_id=dto.class_id,
                start_date=dto.start_date,
                end_date=dto.end_date,
                tuition_amount=tuition.base_tuition,
                discount_amount=tuition.total_discount,
                final_amount=tuition.final_amount,
                status=EnrollmentStatus.PENDING
            )

            await self._enrollment_repo.create(enrollment)

            # 4. 반 인원 증가
            class_.current_count += 1
            await self._class_repo.update(class_)

            # 5. 수강계약서 생성
            await self._create_contract(enrollment)

            return enrollment
```

### 환불 처리

```python
# domain/enrollment/refund_service.py
class RefundService:
    async def process_refund(
        self,
        enrollment_id: str,
        reason: str
    ) -> RefundResult:
        """환불 처리 (학원법 기준 적용)"""

        enrollment = await self._enrollment_repo.get(enrollment_id)

        # 1. 환불 금액 계산 (학원법 시행령)
        refund_calc = self._calculate_refund_by_law(enrollment)

        # 2. 환불 승인 요청 생성
        refund_request = RefundRequest(
            enrollment_id=enrollment_id,
            original_amount=enrollment.final_amount,
            refund_amount=refund_calc.amount,
            refund_ratio=refund_calc.ratio,
            reason=reason,
            legal_basis=refund_calc.legal_basis  # "학원법 시행령 별표4"
        )

        # 3. 결제 취소 처리
        payment = await self._payment_repo.find_by_enrollment(enrollment_id)

        if payment.payment_method == PaymentMethod.CARD:
            # PG 환불 (부분환불 지원)
            await self._pg_service.partial_refund(
                payment.pg_tid,
                refund_calc.amount
            )

        # 4. 상태 업데이트
        enrollment.status = EnrollmentStatus.REFUNDED
        enrollment.cancelled_at = datetime.now()
        enrollment.refund_amount = refund_calc.amount

        # 5. 반 인원 감소
        class_ = await self._class_repo.get(enrollment.class_id)
        class_.current_count -= 1
        await self._class_repo.update(class_)

        return RefundResult(
            enrollment_id=enrollment_id,
            refund_amount=refund_calc.amount,
            message=f"환불 완료: {refund_calc.legal_basis}"
        )

    def _calculate_refund_by_law(self, enrollment: Enrollment) -> RefundCalculation:
        """학원법 시행령 별표4 기준 환불 계산"""

        cancel_date = date.today()

        # 수업 시작 전
        if cancel_date < enrollment.start_date:
            return RefundCalculation(
                amount=enrollment.final_amount,
                ratio=Decimal("1.0"),
                legal_basis="수업시작 전 전액환불"
            )

        # 경과 비율 계산
        total = (enrollment.end_date - enrollment.start_date).days
        elapsed = (cancel_date - enrollment.start_date).days
        ratio = Decimal(elapsed) / Decimal(total)

        if ratio < Decimal("0.333"):
            return RefundCalculation(
                amount=int(enrollment.final_amount * Decimal("0.667")),
                ratio=Decimal("0.667"),
                legal_basis="1/3 경과 전 2/3 환불"
            )
        elif ratio < Decimal("0.5"):
            return RefundCalculation(
                amount=int(enrollment.final_amount * Decimal("0.5")),
                ratio=Decimal("0.5"),
                legal_basis="1/2 경과 전 1/2 환불"
            )
        else:
            return RefundCalculation(
                amount=0,
                ratio=Decimal("0"),
                legal_basis="1/2 경과 후 환불불가"
            )
```

---

## 출결 관리 패턴

### 일일 출결 처리

```python
# domain/attendance/service.py
class AttendanceService:
    async def check_in(
        self,
        student_id: str,
        class_id: str
    ) -> Attendance:
        """출석 체크"""

        now = datetime.now()
        today = now.date()
        current_time = now.time()

        # 오늘 스케줄 확인
        schedule = await self._get_today_schedule(class_id)
        if not schedule:
            raise BusinessError("오늘은 수업이 없습니다")

        # 수강 정보 확인
        enrollment = await self._enrollment_repo.find_active(student_id, class_id)
        if not enrollment:
            raise BusinessError("수강 정보를 찾을 수 없습니다")

        # 출결 상태 결정
        status = self._determine_status(current_time, schedule)

        attendance = Attendance(
            enrollment_id=enrollment.id,
            schedule_id=schedule.id,
            date=today,
            status=status,
            check_in_time=current_time
        )

        await self._attendance_repo.create(attendance)

        # 지각/결석 시 알림
        if status != AttendanceStatus.PRESENT:
            await self._notify_parent(attendance)

        return attendance

    def _determine_status(
        self,
        check_in: time,
        schedule: Schedule
    ) -> AttendanceStatus:
        """출결 상태 판정"""

        # 수업 시작 시간 기준
        start = schedule.start_time
        grace_period = timedelta(minutes=10)
        half_class = timedelta(minutes=30)  # 1시간 수업 기준

        check_in_dt = datetime.combine(date.today(), check_in)
        start_dt = datetime.combine(date.today(), start)

        diff = check_in_dt - start_dt

        if diff <= grace_period:
            return AttendanceStatus.PRESENT  # 정시 (10분 이내)
        elif diff <= half_class:
            return AttendanceStatus.LATE     # 지각
        else:
            return AttendanceStatus.ABSENT   # 결석 처리

    async def bulk_attendance(
        self,
        class_id: str,
        date_: date,
        records: List[AttendanceRecordDto]
    ) -> List[Attendance]:
        """일괄 출결 처리 (강사용)"""

        schedule = await self._schedule_repo.find_by_class_and_day(
            class_id,
            date_.weekday()
        )

        attendances = []

        for record in records:
            enrollment = await self._enrollment_repo.find_active(
                record.student_id,
                class_id
            )

            attendance = Attendance(
                enrollment_id=enrollment.id,
                schedule_id=schedule.id,
                date=date_,
                status=record.status,
                reason=record.reason
            )

            attendances.append(attendance)

            # 결석 시 학부모 알림
            if record.status == AttendanceStatus.ABSENT:
                await self._notify_parent(attendance)

        return await self._attendance_repo.bulk_create(attendances)
```

---

## 알림 패턴

### 통합 알림 서비스

```python
# services/notification_service.py
class NotificationService:
    def __init__(
        self,
        sms_service: SMSService,
        kakao_service: KakaoService,
        push_service: PushService
    ):
        self._sms = sms_service
        self._kakao = kakao_service
        self._push = push_service

    async def send_to_parent(
        self,
        parent: Parent,
        template: NotificationTemplate,
        data: dict
    ):
        """학부모에게 알림 발송 (멀티채널)"""

        message = self._render_template(template, data)

        for channel in parent.notification_channels:
            try:
                if channel == "SMS":
                    await self._sms.send(parent.phone, message)

                elif channel == "KAKAO":
                    await self._kakao.send_alimtalk(
                        parent.phone,
                        template.kakao_template_code,
                        data
                    )

                elif channel == "APP_PUSH":
                    await self._push.send(
                        parent.device_token,
                        template.title,
                        message
                    )

            except Exception as e:
                # 실패 로깅 (다른 채널 계속 시도)
                logger.error(f"알림 발송 실패: {channel}, {e}")

    def _render_template(
        self,
        template: NotificationTemplate,
        data: dict
    ) -> str:
        """템플릿 렌더링"""
        return template.content.format(**data)


# 알림 템플릿 예시
ATTENDANCE_ABSENT_TEMPLATE = NotificationTemplate(
    code="ATT_ABSENT",
    title="결석 안내",
    content="{student_name} 학생이 {class_name} 수업에 결석하였습니다. ({date})",
    kakao_template_code="ATT001"
)

PAYMENT_DUE_TEMPLATE = NotificationTemplate(
    code="PAY_DUE",
    title="수강료 납부 안내",
    content="{student_name} 학생의 {month}월 수강료 {amount}원 납부 기한이 {due_date}입니다.",
    kakao_template_code="PAY001"
)
```

---

## API 라우터 패턴

### 학생 라우터 예시

```python
# api/v1/routers/student.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

router = APIRouter(prefix="/api/v1/students", tags=["학생"])


@router.get("", response_model=PagedResponse[StudentListDto])
async def list_students(
    academy_id: str,
    name: Optional[str] = Query(None, description="학생 이름 검색"),
    grade: Optional[int] = Query(None, ge=1, le=12, description="학년"),
    school_type: Optional[SchoolType] = Query(None, description="학교 타입"),
    status: Optional[StudentStatus] = Query(StudentStatus.ACTIVE),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_read_session_dependency)
):
    """학생 목록 조회"""
    service = StudentService(session)
    return await service.list_students(
        academy_id=academy_id,
        search_params=StudentSearchParams(
            name=name,
            grade=grade,
            school_type=school_type,
            status=status,
            offset=(page - 1) * size,
            limit=size
        )
    )


@router.post("", response_model=StudentDetailDto, status_code=201)
async def register_student(
    dto: StudentRegistrationDto,
    session: AsyncSession = Depends(get_write_session_dependency)
):
    """학생 등록"""
    service = StudentService(session)
    student = await service.register_student(dto)
    return StudentDetailDto.from_model(student)


@router.get("/{student_id}", response_model=StudentDetailDto)
async def get_student(
    student_id: str,
    session: AsyncSession = Depends(get_read_session_dependency)
):
    """학생 상세 조회"""
    service = StudentService(session)
    return await service.get_student_detail(student_id)


@router.get("/{student_id}/attendance", response_model=AttendanceSummaryDto)
async def get_attendance_summary(
    student_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    session: AsyncSession = Depends(get_read_session_dependency)
):
    """출결 요약 조회"""
    service = AttendanceService(session)
    return await service.get_summary(student_id, start_date, end_date)


@router.get("/{student_id}/enrollments", response_model=List[EnrollmentDto])
async def get_enrollments(
    student_id: str,
    status: Optional[EnrollmentStatus] = None,
    session: AsyncSession = Depends(get_read_session_dependency)
):
    """수강 이력 조회"""
    service = EnrollmentService(session)
    return await service.get_by_student(student_id, status)
```

---

## DTO 패턴

```python
# dtos/student.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date

class StudentRegistrationDto(BaseModel):
    """학생 등록 요청"""

    # 학생 정보
    name: str = Field(..., min_length=2, max_length=50)
    birth_date: date
    phone: Optional[str] = Field(None, pattern=r"^01[0-9]-?\d{4}-?\d{4}$")
    school_name: str = Field(..., max_length=100)
    school_type: SchoolType
    grade: int = Field(..., ge=1, le=12)

    # 학원 정보
    academy_id: str

    # 학부모 정보
    parent_info: ParentInfoDto

    @field_validator('grade')
    @classmethod
    def validate_grade_for_school_type(cls, v, info):
        school_type = info.data.get('school_type')
        if school_type == SchoolType.ELEMENTARY and v > 6:
            raise ValueError('초등학생은 1~6학년입니다')
        if school_type in [SchoolType.MIDDLE, SchoolType.HIGH] and v > 3:
            raise ValueError('중/고등학생은 1~3학년입니다')
        return v


class StudentDetailDto(BaseModel):
    """학생 상세 응답"""

    id: str
    name: str
    school_name: str
    school_type: SchoolType
    grade: int
    level: Optional[str]
    status: StudentStatus
    enrollment_date: date

    # 연관 정보
    parent: ParentSummaryDto
    current_enrollments: List[EnrollmentSummaryDto]
    attendance_rate: float

    @classmethod
    def from_model(cls, student: Student) -> "StudentDetailDto":
        return cls(
            id=student.id,
            name=student.name,
            school_name=student.school_name,
            school_type=student.school_type,
            grade=student.grade,
            level=student.level,
            status=student.status,
            enrollment_date=student.enrollment_date,
            parent=ParentSummaryDto.from_model(student.parent),
            current_enrollments=[
                EnrollmentSummaryDto.from_model(e)
                for e in student.enrollments
                if e.status == EnrollmentStatus.ACTIVE
            ],
            attendance_rate=student.attendance_rate
        )
```

---

## 테스트 패턴

```python
# tests/domain/test_enrollment_service.py
import pytest
from datetime import date, timedelta
from decimal import Decimal

class TestEnrollmentService:
    @pytest.fixture
    def service(self, session):
        return EnrollmentService(session)

    @pytest.fixture
    def sample_class(self):
        return Class(
            id="cls-001",
            name="수학A반",
            tuition_monthly=300000,
            capacity=20,
            current_count=15
        )

    async def test_enroll_success(self, service, sample_class):
        """정상 수강 등록"""
        dto = EnrollmentCreateDto(
            student_id="std-001",
            class_id=sample_class.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )

        enrollment = await service.enroll(dto)

        assert enrollment.status == EnrollmentStatus.PENDING
        assert enrollment.final_amount == 300000

    async def test_enroll_fail_when_class_full(self, service):
        """정원 초과 시 실패"""
        full_class = Class(capacity=20, current_count=20)

        with pytest.raises(BusinessError, match="정원이 초과"):
            await service.enroll(...)


class TestRefundCalculation:
    """환불 계산 테스트 (학원법 기준)"""

    def test_refund_before_start(self):
        """수업 시작 전 전액 환불"""
        enrollment = Enrollment(
            start_date=date.today() + timedelta(days=7),
            final_amount=300000
        )

        result = calculate_refund(enrollment, date.today())

        assert result.amount == 300000
        assert result.ratio == Decimal("1.0")

    def test_refund_before_one_third(self):
        """1/3 경과 전 2/3 환불"""
        enrollment = Enrollment(
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=25),
            final_amount=300000
        )

        result = calculate_refund(enrollment, date.today())

        assert result.amount == 200000  # 2/3
        assert result.ratio == Decimal("0.667")

    def test_no_refund_after_half(self):
        """1/2 경과 후 환불 불가"""
        enrollment = Enrollment(
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() + timedelta(days=10),
            final_amount=300000
        )

        result = calculate_refund(enrollment, date.today())

        assert result.amount == 0
        assert result.ratio == Decimal("0")
```
