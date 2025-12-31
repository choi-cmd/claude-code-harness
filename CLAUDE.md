# Claude Code Harness - Project Guidelines

## Project Overview

Python 기반 풀스택 웹 애플리케이션. FastAPI로 백엔드 API와 프론트엔드(템플릿/정적파일)를 모두 제공.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Package Manager | uv |
| Web Framework | FastAPI |
| ASGI Server | uvicorn |
| Data Storage | JSON 파일 (DB 사용 안 함) |
| Template Engine | Jinja2 (예정) |
| Frontend | HTMX / Alpine.js (선택) |

> **중요**: 이 프로젝트는 데이터베이스를 사용하지 않습니다. 모든 데이터는 JSON 파일로 저장/관리합니다.

---

## Development Commands

### Environment Setup
```bash
# 가상환경 생성 및 활성화
uv venv
source .venv/bin/activate

# 의존성 설치
uv sync

# 새 패키지 추가
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>
```

### Running the Application
```bash
# 개발 서버 실행 (hot reload)
uv run uvicorn src.main:app --reload --port 8000

# 프로덕션 실행
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# 전체 테스트 실행
uv run pytest

# 커버리지 포함
uv run pytest --cov=src --cov-report=term-missing

# 특정 테스트 실행
uv run pytest tests/test_specific.py -v
```

### Code Quality
```bash
# 린팅
uv run ruff check src/ tests/

# 포맷팅
uv run ruff format src/ tests/

# 타입 체크
uv run mypy src/
```

---

## Project Structure

```
claude-code-harness/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 엔트리포인트
│   ├── config.py            # 설정 관리 (pydantic-settings)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # 공통 의존성 (Repository 등)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py    # API 라우터 집합
│   │       └── endpoints/   # 개별 엔드포인트 모듈
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py      # 인증/권한
│   │   └── exceptions.py    # 커스텀 예외
│   ├── domain/
│   │   └── <domain_name>/
│   │       ├── __init__.py
│   │       ├── schemas.py   # Pydantic 스키마 (입력/출력)
│   │       ├── repository.py # JSON 파일 데이터 액세스
│   │       └── service.py   # 비즈니스 로직
│   ├── templates/           # Jinja2 템플릿 (프론트엔드)
│   │   ├── base.html
│   │   ├── components/
│   │   └── pages/
│   └── static/              # 정적 파일 (CSS, JS, 이미지)
│       ├── css/
│       ├── js/
│       └── images/
├── data/                    # JSON 데이터 저장소 (git 제외 권장)
│   ├── users.json
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   ├── unit/
│   └── integration/
├── pyproject.toml
├── uv.lock
├── .env                     # 로컬 환경변수 (git 제외)
├── .env.example             # 환경변수 템플릿
└── CLAUDE.md
```

---

## Coding Conventions

### Python Style
- **Formatter**: ruff format (black 호환)
- **Linter**: ruff
- **Type Hints**: 모든 함수에 타입 힌트 필수
- **Docstrings**: Google style docstring

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| 파일/모듈 | snake_case | `user_service.py` |
| 클래스 | PascalCase | `UserService` |
| 함수/변수 | snake_case | `get_user_by_id` |
| 상수 | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Pydantic 모델 | PascalCase + 접미사 | `UserCreate`, `UserResponse` |

### Import Order
```python
# 1. 표준 라이브러리
from datetime import datetime
from typing import Annotated

# 2. 서드파티
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# 3. 로컬 모듈
from src.core.exceptions import NotFoundError
from src.domain.user.schemas import UserResponse
```

---

## FastAPI Patterns

### Router 정의
```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """사용자 조회"""
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Dependency Injection
```python
# src/api/deps.py
from typing import Annotated
from fastapi import Depends
from src.domain.user.repository import UserRepository

def get_user_repository() -> UserRepository:
    return UserRepository()

UserRepo = Annotated[UserRepository, Depends(get_user_repository)]
```

### Pydantic Schema 패턴
```python
from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

### Exception Handling
```python
# src/core/exceptions.py
from fastapi import HTTPException, status

class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
```

---

## Repository Pattern (JSON 기반)

> **주의**: DB 사용 금지. 반드시 JSON 파일로 데이터 저장/조회 구현

```python
# src/domain/user/repository.py
import json
from pathlib import Path
from src.domain.user.schemas import UserCreate, UserResponse

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

class UserRepository:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        if not USERS_FILE.exists():
            USERS_FILE.write_text("[]")

    def _load(self) -> list[dict]:
        return json.loads(USERS_FILE.read_text())

    def _save(self, data: list[dict]) -> None:
        USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def get_by_id(self, user_id: int) -> dict | None:
        users = self._load()
        return next((u for u in users if u["id"] == user_id), None)

    def get_all(self) -> list[dict]:
        return self._load()

    def create(self, user: UserCreate) -> dict:
        users = self._load()
        new_id = max((u["id"] for u in users), default=0) + 1
        new_user = {"id": new_id, **user.model_dump()}
        users.append(new_user)
        self._save(users)
        return new_user

    def update(self, user_id: int, data: dict) -> dict | None:
        users = self._load()
        for i, u in enumerate(users):
            if u["id"] == user_id:
                users[i] = {**u, **data}
                self._save(users)
                return users[i]
        return None

    def delete(self, user_id: int) -> bool:
        users = self._load()
        filtered = [u for u in users if u["id"] != user_id]
        if len(filtered) < len(users):
            self._save(filtered)
            return True
        return False
```

### JSON 데이터 파일 구조
```
data/
├── users.json
├── posts.json
└── settings.json
```

---

## Frontend (Templates + HTMX)

### Jinja2 Base Template
```html
<!-- src/templates/base.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}App{% endblock %}</title>
    <script src="https://unpkg.com/htmx.org@2.0.0"></script>
    <link href="/static/css/style.css" rel="stylesheet">
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

### HTMX 패턴
```html
<!-- 폼 제출 -->
<form hx-post="/api/users" hx-target="#result" hx-swap="innerHTML">
    <input name="email" type="email" required>
    <button type="submit">Submit</button>
</form>
<div id="result"></div>

<!-- 무한 스크롤 -->
<div hx-get="/api/items?page=2"
     hx-trigger="revealed"
     hx-swap="afterend">
    Loading...
</div>
```

---

## Testing Guidelines

### Fixture 패턴
```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
```

### API 테스트
```python
# tests/integration/test_users.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/api/v1/users", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "secret123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
```

---

## Environment Variables

```bash
# .env.example
# App
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Data
DATA_DIR=data  # JSON 파일 저장 경로
```

### Config 클래스
```python
# src/config.py
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "dev-secret-key"
    data_dir: Path = Path("data")

    model_config = {"env_file": ".env"}

settings = Settings()
```

---

## Git Workflow

### Branch Naming
- `feature/<feature-name>` - 새 기능
- `fix/<bug-description>` - 버그 수정
- `refactor/<scope>` - 리팩토링

### Commit Message
```
<type>: <subject>

<body>

Types: feat, fix, refactor, test, docs, chore
```

---

## Claude Code 작업 규칙

### DO (해야 할 것)
- 모든 API 엔드포인트에 타입 힌트와 response_model 명시
- Repository 패턴으로 데이터 액세스 분리
- Pydantic으로 입력 검증 철저히
- 비동기(async/await) 패턴 일관되게 사용
- 테스트 코드 함께 작성

### DON'T (하지 말 것)
- **DB 연결 절대 금지** - SQLAlchemy, asyncpg, SQLite 등 DB 라이브러리 사용 금지
- 라우터에 직접 파일 I/O 작성 금지 (Repository 통해서만)
- 하드코딩된 설정값 금지 (환경변수 사용)
- `Any` 타입 사용 최소화
- print 문 대신 logging 사용

### 파일 생성 시 위치
| 파일 유형 | 위치 |
|----------|------|
| API 엔드포인트 | `src/api/v1/endpoints/` |
| Pydantic 스키마 | `src/domain/<name>/schemas.py` |
| JSON Repository | `src/domain/<name>/repository.py` |
| 비즈니스 로직 | `src/domain/<name>/service.py` |
| JSON 데이터 파일 | `data/<name>.json` |
| 테스트 | `tests/unit/` 또는 `tests/integration/` |
| 템플릿 | `src/templates/` |

---

## Recommended Dependencies

```bash
# 핵심
uv add fastapi uvicorn[standard] pydantic-settings

# 템플릿/프론트엔드
uv add jinja2 python-multipart

# 개발 도구
uv add --dev pytest pytest-asyncio pytest-cov httpx ruff mypy
```

> **주의**: DB 관련 패키지(sqlalchemy, asyncpg, databases 등) 설치 금지

---

## .gitignore 권장 항목

```gitignore
# 데이터 파일 (JSON 저장소)
data/

# 환경 변수
.env
.env.local
```

---

## Domain Knowledge System

프로젝트별 도메인 지식을 스킬로 관리하여 자동으로 컨텍스트에 주입하는 시스템입니다.

### 구조

```
.claude/skills/
├── domain-router/                  # 도메인 라우팅 메타 스킬
│   └── skill.md
├── kr-private-education/           # 사교육 도메인 스킬
│   ├── skill.md                    # 메인 스킬
│   └── resources/
│       ├── entities.md             # 엔티티 모델
│       ├── business-rules.md       # 비즈니스 규칙
│       ├── workflows.md            # 워크플로우
│       ├── code-patterns.md        # 코드 패턴
│       └── terminology.md          # 용어 사전
└── skill-rules.json                # 트리거 규칙
```

### 등록된 도메인

| 도메인 | 스킬명 | 설명 |
|--------|--------|------|
| **사교육** | `kr-private-education` | 학원/과외 시스템 개발을 위한 도메인 지식 |

### 사교육 도메인 (kr-private-education)

#### 포함된 지식

| 카테고리 | 내용 |
|----------|------|
| **엔티티** | Academy, Student, Parent, Instructor, Class, Schedule, Enrollment, Attendance, Payment, Consultation |
| **비즈니스 규칙** | 심야제한(EDU-001), 환불규정(EDU-002), 개인정보(EDU-003), 수강계약서(EDU-004), 출결관리(EDU-005), 강사자격(EDU-006) |
| **워크플로우** | 신규상담→등록(WF-001), 수강등록→결제(WF-002), 출결관리(WF-003), 환불처리(WF-004), 정기상담(WF-005) |
| **코드 패턴** | StudentService, EnrollmentService, RefundService, AttendanceService 등 |

#### 트리거 키워드

**한국어**: 학원, 교습소, 과외, 수강, 원비, 학생, 강사, 출결, 환불, 상담, 레벨테스트, 반편성, 내신, 수능, 입시...

**영문**: academy, student, enrollment, attendance, tuition, refund...

#### 사용법

**자동 활성화**: 프롬프트에 키워드가 포함되면 자동 제안
```
"학원 수강등록 API 만들어줘"  → kr-private-education 자동 제안
```

**수동 활성화**:
```bash
/kr-private-education
```

### 새 도메인 추가 방법

1. `.claude/skills/<domain-name>/` 디렉토리 생성
2. `skill.md` 작성 (메인 스킬 파일)
3. `resources/` 폴더에 지식 파일 작성
   - `entities.md`: 엔티티 모델
   - `business-rules.md`: 비즈니스 규칙 (ID 부여, 법적 근거 명시)
   - `workflows.md`: 업무 흐름도
   - `code-patterns.md`: 복사-붙여넣기 가능한 코드 패턴
   - `terminology.md`: 업계 용어 ↔ 시스템 용어 매핑
4. `skill-rules.json`에 트리거 규칙 추가

### 도메인 스킬 작성 원칙

1. **구체적인 예시 포함**: 추상적 설명보다 실제 코드/데이터 예시
2. **비즈니스 규칙 명확화**: ID 부여 (예: EDU-001), 근거 명시 (법률, 정책)
3. **용어 일관성**: terminology.md에 모든 용어 매핑
4. **패턴 재사용성**: 바로 사용 가능한 코드 템플릿 제공
