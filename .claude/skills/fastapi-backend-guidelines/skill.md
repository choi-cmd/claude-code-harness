---
name: fastapi-backend-guidelines
description: FastAPI backend development guidelines for Python async applications. Domain-Driven Design with FastAPI routers, SQLModel/SQLAlchemy ORM, repository pattern, service layer, async/await patterns, Pydantic validation, and error handling. Use when creating APIs, routes, services, repositories, or working with backend code.
---

# FastAPI Backend Development Guidelines

## Purpose

Comprehensive guide for modern FastAPI development with async Python, emphasizing Domain-Driven Design, layered architecture (Router → Service → Repository), SQLModel ORM, and async best practices.

## When to Use This Skill

- Creating new API routes or endpoints
- Building domain services and business logic
- Implementing repositories for data access
- Setting up database models with SQLModel
- Async/await patterns and error handling
- Organizing backend code with DDD
- Pydantic validation and DTOs
- Python async best practices

---

## Quick Start

### New API Route Checklist

Creating an API endpoint? Follow this checklist:

- [ ] Define route in `backend/api/v1/routers/{domain}.py`
- [ ] Use FastAPI dependency injection for session
- [ ] Call service layer (don't access repository directly)
- [ ] Use Pydantic DTOs for request/response
- [ ] Handle errors with custom exceptions
- [ ] Add proper HTTP status codes
- [ ] Use async/await throughout
- [ ] Document with docstrings
- [ ] Use type hints on all parameters

### New Domain Feature Checklist

Creating a new domain? Set up this structure:

- [ ] Create `backend/domain/{domain}/` directory
- [ ] Create `model.py` - SQLModel database models
- [ ] Create `repository.py` - Data access layer
- [ ] Create `service.py` - Business logic layer
- [ ] Create DTOs in `backend/dtos/{domain}.py`
- [ ] Create router in `backend/api/v1/routers/{domain}.py`
- [ ] Register router in `main.py`
- [ ] Follow async patterns throughout

---

## Project Structure Quick Reference

Your qwarty backend structure:

```
backend/
  backend/
    main.py                  # FastAPI app creation

    api/
      v1/
        routers/             # API route handlers
          artist.py
          artwork.py
          auth.py
          ...

    domain/                  # Domain-Driven Design
      artist/
        model.py             # SQLModel models
        repository.py        # Data access layer
        service.py           # Business logic
      artwork/
      auth/
      ...

    dtos/                    # Pydantic DTOs
      artist.py
      artwork.py
      ...

    db/
      orm.py                 # DB session management

    core/
      config.py              # App configuration

    middleware/              # Middleware
      error_handler.py

    utils/                   # Utilities

    error/                   # Custom exceptions
```

---

## Common Imports Cheatsheet

```python
# FastAPI
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

# SQLModel & SQLAlchemy
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

# Database
from backend.db.orm import get_write_session_dependency, get_read_session_dependency

# Pydantic
from pydantic import BaseModel, Field, field_validator

# Your domain
from backend.domain.artist.model import Artist
from backend.domain.artist.service import ArtistService
from backend.dtos.artist import ArtistRequestDto, ArtistResponseDto
from backend.error import NotFoundError

# Type hints
from typing import List, Optional, Dict, Any
```

---

## Topic Guides

### 🏗️ Layered Architecture

**Three-Layer Pattern:**
1. **Router Layer**: API endpoints, request validation, response formatting
2. **Service Layer**: Business logic, orchestration, domain rules
3. **Repository Layer**: Data access, queries, database operations

**Key Concepts:**
- Routers call Services (never Repositories directly)
- Services orchestrate business logic
- Repositories handle all database operations
- Each layer has clear responsibilities
- Async/await throughout the stack

**[📖 Complete Guide: resources/layered-architecture.md](resources/layered-architecture.md)**

---

### 🛣️ API Routes & Routers

**PRIMARY PATTERN: FastAPI Routers**
- Create routers in `backend/api/v1/routers/`
- Use dependency injection for sessions
- Follow REST conventions
- Use appropriate HTTP methods and status codes
- Async route handlers

**Router Structure:**
```python
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.db.orm import get_write_session_dependency

router = APIRouter(prefix="/api/v1/artists", tags=["artists"])

@router.get("/{artist_id}")
async def get_artist(
    artist_id: str,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    service = ArtistService(session)
    return await service.get_artist(artist_id)
```

**[📖 Complete Guide: resources/api-routes.md](resources/api-routes.md)**

---

### 🗄️ Database & ORM

**SQLModel + SQLAlchemy:**
- SQLModel for models (combines SQLAlchemy + Pydantic)
- Async sessions with asyncpg driver
- Read/Write session separation
- Repository pattern for all queries

**Model Pattern:**
```python
from sqlmodel import SQLModel, Field

class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(primary_key=True)
    name: str = Field(max_length=255)
    bio: Optional[str] = None
```

**[📖 Complete Guide: resources/database-orm.md](resources/database-orm.md)**

---

### 📦 Domain-Driven Design

**Domain Organization:**
- Each domain in `backend/domain/{name}/`
- Contains: `model.py`, `repository.py`, `service.py`
- Clear separation of concerns
- Business logic in services
- Data access in repositories

**Your Domains:**
- admin, artist, artwork, auth, curai, exhibition
- message, notification, subscription, user, shared

**[📖 Complete Guide: resources/domain-driven-design.md](resources/domain-driven-design.md)**

---

### 🔄 Service Layer

**Service Pattern:**
- Business logic orchestration
- Domain rule enforcement
- Calls repositories for data
- Returns DTOs, not models directly
- Transaction management

**Service Structure:**
```python
class ArtistService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repository = ArtistRepository(session)

    async def get_artist(self, artist_id: str) -> ArtistResponseDto:
        artist = await self._repository.get_by_id(artist_id)
        if not artist:
            raise NotFoundError("Artist not found")
        return ArtistResponseDto.from_model(artist)
```

**[📖 Complete Guide: resources/service-layer.md](resources/service-layer.md)**

---

### 💾 Repository Pattern

**Repository Pattern:**
- Encapsulates data access
- Extends BaseRepository
- Domain-specific queries
- Returns domain models
- All queries are async

**Repository Structure:**
```python
class ArtistRepository(BaseRepository[Artist]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Artist)

    async def find_by_name(self, name: str) -> Optional[Artist]:
        stmt = select(Artist).where(Artist.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

**[📖 Complete Guide: resources/repository-pattern.md](resources/repository-pattern.md)**

---

### 📝 DTOs & Validation

**Pydantic DTOs:**
- Request/Response data transfer objects
- Validation with Pydantic
- Separate from domain models
- Located in `backend/dtos/`

**DTO Pattern:**
```python
from pydantic import BaseModel, Field, field_validator

class ArtistRequestDto(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    bio: Optional[str] = None

    @field_validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v
```

**[📖 Complete Guide: resources/dtos-validation.md](resources/dtos-validation.md)**

---

### ⚡ Async/Await Patterns

**Async Best Practices:**
- Use async/await throughout
- Async database sessions
- Proper session cleanup
- Avoid blocking operations
- Use asyncio for concurrency

**Async Patterns:**
```python
# Async route handler
@router.get("/artists")
async def get_artists(
    session: AsyncSession = Depends(get_read_session_dependency),
):
    service = ArtistService(session)
    return await service.get_all_artists()

# Async service method
async def get_all_artists(self) -> List[ArtistResponseDto]:
    artists = await self._repository.find_all()
    return [ArtistResponseDto.from_model(a) for a in artists]
```

**[📖 Complete Guide: resources/async-patterns.md](resources/async-patterns.md)**

---

### 🚨 Error Handling

**Error Handling Strategy:**
- Custom exception classes
- HTTP exception mapping
- Middleware for error handling
- Consistent error responses

**Error Pattern:**
```python
from backend.error import NotFoundError

# In service
if not artist:
    raise NotFoundError(f"Artist {artist_id} not found")

# Middleware handles conversion to HTTP response
```

**[📖 Complete Guide: resources/error-handling.md](resources/error-handling.md)**

---

### 📚 Complete Examples

**Full working examples:**
- Complete domain (model + repository + service + router)
- CRUD operations with async
- Complex queries with SQLModel
- Authentication patterns
- File upload to S3
- Pagination and filtering

**[📖 Complete Guide: resources/complete-examples.md](resources/complete-examples.md)**

---

## Navigation Guide

| Need to... | Read this resource |
|------------|-------------------|
| Understand architecture | [layered-architecture.md](resources/layered-architecture.md) |
| Create API routes | [api-routes.md](resources/api-routes.md) |
| Work with database | [database-orm.md](resources/database-orm.md) |
| Organize domains | [domain-driven-design.md](resources/domain-driven-design.md) |
| Build services | [service-layer.md](resources/service-layer.md) |
| Create repositories | [repository-pattern.md](resources/repository-pattern.md) |
| Validate requests | [dtos-validation.md](resources/dtos-validation.md) |
| Use async patterns | [async-patterns.md](resources/async-patterns.md) |
| Handle errors | [error-handling.md](resources/error-handling.md) |
| See full examples | [complete-examples.md](resources/complete-examples.md) |

---

## Core Principles

1. **Layered Architecture**: Router → Service → Repository (never skip layers)
2. **Domain-Driven Design**: Organize by domain, not by type
3. **Async Everything**: Use async/await throughout the stack
4. **Repository Pattern**: All data access through repositories
5. **Service Layer**: Business logic in services, not routers or repositories
6. **DTOs for API**: Use Pydantic DTOs for request/response
7. **Type Hints**: Explicit types on all functions and parameters
8. **Error Handling**: Custom exceptions, middleware for HTTP mapping
9. **Read/Write Split**: Separate sessions for read and write operations
10. **Dependency Injection**: Use FastAPI's Depends() for sessions

---

## Quick Reference: New Domain Template

```python
# backend/domain/myfeature/model.py
from sqlmodel import SQLModel, Field

class MyFeature(SQLModel, table=True):
    __tablename__ = "my_features"
    id: str = Field(primary_key=True)
    name: str

# backend/domain/myfeature/repository.py
from backend.domain.shared.base_repository import BaseRepository

class MyFeatureRepository(BaseRepository[MyFeature]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MyFeature)

# backend/domain/myfeature/service.py
class MyFeatureService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repository = MyFeatureRepository(session)

    async def get_feature(self, id: str):
        return await self._repository.get_by_id(id)

# backend/api/v1/routers/myfeature.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/myfeature", tags=["myfeature"])

@router.get("/{id}")
async def get_feature(
    id: str,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    service = MyFeatureService(session)
    return await service.get_feature(id)
```

---

## Related Skills

- **nextjs-frontend-guidelines**: Frontend patterns that consume this API
- **error-tracking**: Error tracking with Sentry (backend integration)

---

**Skill Status**: Modular structure with progressive loading for optimal context management
