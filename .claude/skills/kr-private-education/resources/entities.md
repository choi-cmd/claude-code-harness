# 엔티티 모델 정의

대한민국 사교육 시스템의 핵심 엔티티와 관계를 정의합니다.

---

## 엔티티 관계도

```
┌─────────────┐       ┌─────────────┐
│   Academy   │───────│  Instructor │
└──────┬──────┘       └──────┬──────┘
       │                     │
       │    ┌────────────────┤
       │    │                │
       ▼    ▼                ▼
┌─────────────┐       ┌─────────────┐
│    Class    │◄──────│  Schedule   │
└──────┬──────┘       └─────────────┘
       │
       │ ┌─────────────┐
       │ │   Student   │◄────┐
       │ └──────┬──────┘     │
       │        │            │
       ▼        ▼            │
┌─────────────────────┐ ┌────┴──────┐
│     Enrollment      │ │   Parent  │
└──────────┬──────────┘ └───────────┘
           │
     ┌─────┴─────┬──────────────┐
     ▼           ▼              ▼
┌─────────┐ ┌─────────┐  ┌─────────────┐
│ Payment │ │Attendance│  │Consultation │
└─────────┘ └─────────┘  └─────────────┘
```

---

## Academy (학원/교습소)

학원 또는 교습소의 기본 정보를 관리합니다.

```python
class Academy(SQLModel, table=True):
    __tablename__ = "academies"

    id: str = Field(primary_key=True)
    name: str = Field(max_length=100)                    # 학원명
    business_number: str = Field(max_length=12)          # 사업자등록번호
    academy_reg_number: str = Field(max_length=20)       # 학원등록번호

    # 위치
    address: str                                          # 주소
    sido: str                                             # 시/도 (심야제한 적용)

    # 운영정보
    phone: str
    operating_hours_start: time                           # 운영시작 (예: 09:00)
    operating_hours_end: time                             # 운영종료 (예: 22:00)
    curfew_time: time                                     # 심야학습제한시간

    # 카테고리
    subjects: List[str]                                   # 과목 (수학, 영어, 국어...)
    target_grades: List[str]                              # 대상학년 (초1~고3)

    status: AcademyStatus                                 # ACTIVE, SUSPENDED, CLOSED

    created_at: datetime
    updated_at: datetime
```

### 비즈니스 규칙
- `academy_reg_number`: 관할 교육청 등록 필수
- `curfew_time`: 지역별 심야학습 제한시간 자동 적용
- `subjects`: 등록된 교습과목만 운영 가능

---

## Student (학생/수강생)

학원에 등록된 학생 정보를 관리합니다.

```python
class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: str = Field(primary_key=True)

    # 기본정보
    name: str = Field(max_length=50)
    phone: Optional[str]                                  # 본인 연락처 (고등학생)
    birth_date: date
    gender: Gender                                        # MALE, FEMALE

    # 학교정보
    school_name: str                                      # 학교명
    school_type: SchoolType                               # ELEMENTARY, MIDDLE, HIGH
    grade: int                                            # 학년 (1~6 또는 1~3)

    # 학원정보
    academy_id: str = Field(foreign_key="academies.id")
    enrollment_date: date                                 # 최초 등록일
    level: Optional[str]                                  # 레벨 (학원 자체 기준)

    # 학부모 연결
    parent_id: str = Field(foreign_key="parents.id")

    status: StudentStatus                                 # ACTIVE, INACTIVE, GRADUATED, WITHDRAWN

    # 메모
    notes: Optional[str]                                  # 특이사항

    created_at: datetime
    updated_at: datetime
```

### 주요 속성 설명
- `grade`: 학년 (초등 1~6, 중등 1~3, 고등 1~3)
- `level`: 학원 자체 레벨 시스템 (예: A1, A2, B1...)
- `status`: 재원생/휴원생/졸업/퇴원 상태

---

## Parent (학부모)

학부모 정보 및 결제 관련 정보를 관리합니다.

```python
class Parent(SQLModel, table=True):
    __tablename__ = "parents"

    id: str = Field(primary_key=True)

    # 기본정보
    name: str = Field(max_length=50)
    phone: str                                            # 필수 연락처
    phone_secondary: Optional[str]                        # 보조 연락처
    email: Optional[str]

    # 관계
    relationship: Relationship                            # FATHER, MOTHER, GRANDPARENT, OTHER

    # 결제정보
    payment_method: PaymentMethod                         # CARD, BANK_TRANSFER, CASH
    card_info: Optional[dict]                             # 자동결제 카드정보 (암호화)
    bank_account: Optional[str]                           # 계좌이체용 계좌

    # 알림설정
    notification_enabled: bool = True
    notification_channels: List[str]                      # SMS, KAKAO, APP_PUSH

    # 동의
    privacy_consent: bool                                 # 개인정보 동의
    marketing_consent: bool                               # 마케팅 동의
    consent_date: date

    created_at: datetime
    updated_at: datetime
```

### 비즈니스 규칙
- `privacy_consent`: 필수, 자녀 정보 처리 동의 포함
- 만14세 미만 학생은 학부모 동의 필수 (개인정보보호법)

---

## Instructor (강사)

강사 정보 및 근무 조건을 관리합니다.

```python
class Instructor(SQLModel, table=True):
    __tablename__ = "instructors"

    id: str = Field(primary_key=True)
    academy_id: str = Field(foreign_key="academies.id")

    # 기본정보
    name: str = Field(max_length=50)
    phone: str
    email: Optional[str]

    # 자격/전문분야
    subjects: List[str]                                   # 담당 과목
    certifications: Optional[List[str]]                   # 자격증
    education: Optional[str]                              # 학력

    # 근무조건
    employment_type: EmploymentType                       # FULL_TIME, PART_TIME, CONTRACT
    hourly_rate: Optional[int]                            # 시급 (파트타임)
    monthly_salary: Optional[int]                         # 월급 (정규직)

    # 상태
    status: InstructorStatus                              # ACTIVE, ON_LEAVE, RESIGNED

    created_at: datetime
    updated_at: datetime
```

---

## Class (수업/반)

개설된 수업(반) 정보를 관리합니다.

```python
class Class(SQLModel, table=True):
    __tablename__ = "classes"

    id: str = Field(primary_key=True)
    academy_id: str = Field(foreign_key="academies.id")
    instructor_id: str = Field(foreign_key="instructors.id")

    # 기본정보
    name: str                                             # 반 이름 (예: 수학A반, 고3정규반)
    subject: str                                          # 과목
    class_type: ClassType                                 # REGULAR, INTENSIVE, CAMP, SPECIAL

    # 대상
    target_school_type: SchoolType                        # ELEMENTARY, MIDDLE, HIGH
    target_grades: List[int]                              # 대상 학년
    level: Optional[str]                                  # 레벨 (상/중/하 또는 A/B/C)

    # 정원
    capacity: int                                         # 정원
    current_count: int = 0                                # 현재 인원

    # 수강료
    tuition_monthly: int                                  # 월 수강료
    material_fee: Optional[int]                           # 교재비

    # 기간
    start_date: date                                      # 개강일
    end_date: Optional[date]                              # 종강일 (정규반은 null)

    status: ClassStatus                                   # OPEN, CLOSED, FULL, CANCELLED

    created_at: datetime
    updated_at: datetime
```

### ClassType 정의
- `REGULAR`: 정규반 (상시 운영)
- `INTENSIVE`: 특강반 (기간 한정)
- `CAMP`: 캠프 (방학 특별반)
- `SPECIAL`: 특별반 (보충, 심화 등)

---

## Schedule (시간표)

수업 시간표를 관리합니다.

```python
class Schedule(SQLModel, table=True):
    __tablename__ = "schedules"

    id: str = Field(primary_key=True)
    class_id: str = Field(foreign_key="classes.id")

    day_of_week: DayOfWeek                                # MON, TUE, WED, THU, FRI, SAT, SUN
    start_time: time                                      # 시작 시간
    end_time: time                                        # 종료 시간

    room: Optional[str]                                   # 강의실

    # 예외 처리
    is_active: bool = True
    exception_dates: Optional[List[date]]                 # 휴강일
```

---

## Enrollment (수강등록)

학생의 수강 등록 정보를 관리합니다.

```python
class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"

    id: str = Field(primary_key=True)
    student_id: str = Field(foreign_key="students.id")
    class_id: str = Field(foreign_key="classes.id")

    # 수강 기간
    start_date: date                                      # 수강 시작일
    end_date: Optional[date]                              # 수강 종료일

    # 수강료 정보
    tuition_amount: int                                   # 수강료
    discount_amount: int = 0                              # 할인금액
    discount_reason: Optional[str]                        # 할인사유 (형제할인, 조기등록 등)
    final_amount: int                                     # 최종금액

    # 상태
    status: EnrollmentStatus                              # ACTIVE, COMPLETED, CANCELLED, REFUNDED

    # 취소/환불
    cancelled_at: Optional[datetime]
    refund_amount: Optional[int]
    refund_reason: Optional[str]

    created_at: datetime
    updated_at: datetime
```

### EnrollmentStatus 정의
- `ACTIVE`: 수강 중
- `COMPLETED`: 수강 완료
- `CANCELLED`: 수강 취소 (환불 전)
- `REFUNDED`: 환불 완료

---

## Attendance (출결)

일별 출결 기록을 관리합니다.

```python
class Attendance(SQLModel, table=True):
    __tablename__ = "attendances"

    id: str = Field(primary_key=True)
    enrollment_id: str = Field(foreign_key="enrollments.id")
    schedule_id: str = Field(foreign_key="schedules.id")

    date: date                                            # 수업일

    # 출결 상태
    status: AttendanceStatus                              # PRESENT, ABSENT, LATE, EARLY_LEAVE, MAKEUP

    # 시간 기록 (선택)
    check_in_time: Optional[time]                         # 입실 시간
    check_out_time: Optional[time]                        # 퇴실 시간

    # 사유
    reason: Optional[str]                                 # 결석/지각 사유

    # 보강
    is_makeup: bool = False                               # 보강 수업 여부
    makeup_for_date: Optional[date]                       # 보강 대상 날짜

    # 알림
    notification_sent: bool = False                       # 학부모 알림 발송 여부

    created_at: datetime
    updated_by: Optional[str]                             # 수정한 사람
```

### AttendanceStatus 정의
- `PRESENT`: 출석
- `ABSENT`: 결석
- `LATE`: 지각
- `EARLY_LEAVE`: 조퇴
- `MAKEUP`: 보강 출석

---

## Payment (결제)

수강료 결제 정보를 관리합니다.

```python
class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: str = Field(primary_key=True)
    enrollment_id: str = Field(foreign_key="enrollments.id")
    parent_id: str = Field(foreign_key="parents.id")

    # 결제 정보
    amount: int                                           # 결제 금액
    payment_type: PaymentType                             # TUITION, MATERIAL, OTHER
    payment_method: PaymentMethod                         # CARD, BANK_TRANSFER, CASH

    # 결제 상태
    status: PaymentStatus                                 # PENDING, COMPLETED, FAILED, REFUNDED

    # 결제 일시
    paid_at: Optional[datetime]
    due_date: date                                        # 납부 기한

    # PG 연동 정보
    pg_tid: Optional[str]                                 # PG 거래번호
    pg_response: Optional[dict]                           # PG 응답 원본

    # 영수증
    receipt_number: Optional[str]
    receipt_issued: bool = False

    # 환불
    refund_amount: Optional[int]
    refunded_at: Optional[datetime]
    refund_reason: Optional[str]

    created_at: datetime
    updated_at: datetime
```

---

## Consultation (상담)

학부모/학생 상담 기록을 관리합니다.

```python
class Consultation(SQLModel, table=True):
    __tablename__ = "consultations"

    id: str = Field(primary_key=True)
    student_id: str = Field(foreign_key="students.id")
    parent_id: Optional[str] = Field(foreign_key="parents.id")
    instructor_id: Optional[str] = Field(foreign_key="instructors.id")

    # 상담 유형
    consultation_type: ConsultationType                   # ADMISSION, REGULAR, GRADE, BEHAVIOR, EXIT

    # 상담 일시
    scheduled_at: datetime                                # 예약 일시
    conducted_at: Optional[datetime]                      # 실제 상담 일시
    duration_minutes: Optional[int]                       # 상담 시간

    # 상담 방식
    method: ConsultationMethod                            # IN_PERSON, PHONE, VIDEO

    # 상담 내용
    topic: str                                            # 상담 주제
    content: str                                          # 상담 내용

    # 후속 조치
    action_items: Optional[List[str]]                     # 후속 조치 사항
    next_consultation_date: Optional[date]                # 다음 상담 예정일

    status: ConsultationStatus                            # SCHEDULED, COMPLETED, CANCELLED, NO_SHOW

    created_at: datetime
    updated_at: datetime
```

### ConsultationType 정의
- `ADMISSION`: 입학 상담 (신규 등록 전)
- `REGULAR`: 정기 상담 (월별/분기별)
- `GRADE`: 성적 상담
- `BEHAVIOR`: 학습태도/행동 상담
- `EXIT`: 퇴원 상담

---

## Enum 정의 요약

```python
class SchoolType(str, Enum):
    ELEMENTARY = "elementary"   # 초등
    MIDDLE = "middle"           # 중등
    HIGH = "high"               # 고등

class StudentStatus(str, Enum):
    ACTIVE = "active"           # 재원
    INACTIVE = "inactive"       # 휴원
    GRADUATED = "graduated"     # 졸업
    WITHDRAWN = "withdrawn"     # 퇴원

class ClassType(str, Enum):
    REGULAR = "regular"         # 정규반
    INTENSIVE = "intensive"     # 특강
    CAMP = "camp"               # 캠프
    SPECIAL = "special"         # 특별반

class AttendanceStatus(str, Enum):
    PRESENT = "present"         # 출석
    ABSENT = "absent"           # 결석
    LATE = "late"               # 지각
    EARLY_LEAVE = "early_leave" # 조퇴
    MAKEUP = "makeup"           # 보강

class PaymentStatus(str, Enum):
    PENDING = "pending"         # 대기
    COMPLETED = "completed"     # 완료
    FAILED = "failed"           # 실패
    REFUNDED = "refunded"       # 환불
```
