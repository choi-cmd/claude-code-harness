# Layered Architecture - FastAPI

## Overview

Your backend follows a three-layer architecture pattern:

**Router → Service → Repository**

Each layer has specific responsibilities and should not be bypassed.

---

## The Three Layers

### 1. Router Layer (API/Presentation)

**Location**: `backend/api/v1/routers/`

**Responsibilities**:
- Handle HTTP requests/responses
- Request validation (via Pydantic)
- Response formatting
- HTTP status codes
- Authentication/authorization checks
- Call service layer

**What it DOES NOT do**:
- Business logic
- Direct database access
- Complex data transformations

**Example**:
```python
# backend/api/v1/routers/artist.py
from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.artist.service import ArtistService
from backend.dtos.artist import ArtistResponseDto, ArtistRequestDto

router = APIRouter(prefix="/api/v1/artists", tags=["artists"])

@router.get("/{artist_id}", response_model=ArtistResponseDto)
async def get_artist(
    artist_id: str,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """Get artist by ID"""
    service = ArtistService(session)
    return await service.get_artist(artist_id)

@router.post("/", response_model=ArtistResponseDto, status_code=status.HTTP_201_CREATED)
async def create_artist(
    dto: ArtistRequestDto,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """Create new artist"""
    service = ArtistService(session)
    return await service.create_artist(dto)
```

### 2. Service Layer (Business Logic)

**Location**: `backend/domain/{domain}/service.py`

**Responsibilities**:
- Business logic implementation
- Domain rule enforcement
- Transaction orchestration
- Call repositories for data
- Data transformation (model → DTO)
- Error handling with domain exceptions

**What it DOES NOT do**:
- HTTP concerns (status codes, headers)
- Direct SQL queries
- Database session management

**Example**:
```python
# backend/domain/artist/service.py
from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.domain.artist.repository import ArtistRepository
from backend.domain.artist.model import Artist
from backend.dtos.artist import ArtistRequestDto, ArtistResponseDto
from backend.error import NotFoundError, ValidationError

class ArtistService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repository = ArtistRepository(session)

    async def get_artist(self, artist_id: str) -> ArtistResponseDto:
        """Get artist by ID with business logic"""
        artist = await self._repository.get_by_id(artist_id)

        if not artist:
            raise NotFoundError(f"Artist {artist_id} not found")

        # Business logic: Check if artist is approved
        if artist.status != "approved":
            raise ValidationError("Artist is not approved yet")

        return ArtistResponseDto.from_model(artist)

    async def create_artist(self, dto: ArtistRequestDto) -> ArtistResponseDto:
        """Create new artist with business rules"""
        # Business rule: Check if name already exists
        existing = await self._repository.find_by_name(dto.name)
        if existing:
            raise ValidationError(f"Artist with name '{dto.name}' already exists")

        # Create artist
        artist = Artist(**dto.model_dump())
        created = await self._repository.create(artist)

        return ArtistResponseDto.from_model(created)

    async def get_all_artists(self, limit: int = 100) -> List[ArtistResponseDto]:
        """Get all approved artists"""
        artists = await self._repository.find_all_approved(limit=limit)
        return [ArtistResponseDto.from_model(a) for a in artists]
```

### 3. Repository Layer (Data Access)

**Location**: `backend/domain/{domain}/repository.py`

**Responsibilities**:
- Database queries (SELECT, INSERT, UPDATE, DELETE)
- Data retrieval and persistence
- Query optimization
- Return domain models

**What it DOES NOT do**:
- Business logic
- DTOs (works with domain models only)
- HTTP concerns
- Validation beyond database constraints

**Example**:
```python
# backend/domain/artist/repository.py
from typing import List, Optional
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.domain.artist.model import Artist
from backend.domain.shared.base_repository import BaseRepository

class ArtistRepository(BaseRepository[Artist]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Artist)

    async def find_by_name(self, name: str) -> Optional[Artist]:
        """Find artist by exact name"""
        stmt = select(Artist).where(Artist.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_approved(self, limit: int = 100) -> List[Artist]:
        """Find all approved artists"""
        stmt = (
            select(Artist)
            .where(Artist.status == "approved")
            .limit(limit)
            .order_by(Artist.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Artist]:
        """Search artists by keyword in name or bio"""
        stmt = (
            select(Artist)
            .where(
                or_(
                    Artist.name.ilike(f"%{keyword}%"),
                    Artist.bio.ilike(f"%{keyword}%")
                )
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

---

## Data Flow

### Read Operation Flow

```
1. Client Request
   ↓
2. Router validates request
   ↓
3. Router calls Service
   ↓
4. Service calls Repository
   ↓
5. Repository queries database
   ↓
6. Repository returns Model
   ↓
7. Service applies business logic
   ↓
8. Service converts Model → DTO
   ↓
9. Router returns HTTP response
```

### Write Operation Flow

```
1. Client Request with data
   ↓
2. Router validates DTO
   ↓
3. Router calls Service with DTO
   ↓
4. Service applies business rules
   ↓
5. Service converts DTO → Model
   ↓
6. Service calls Repository with Model
   ↓
7. Repository persists to database
   ↓
8. Repository returns saved Model
   ↓
9. Service converts Model → DTO
   ↓
10. Router returns HTTP response (201 Created)
```

---

## Why This Architecture?

### Separation of Concerns
- Each layer has clear responsibilities
- Easy to test each layer independently
- Changes in one layer don't affect others

### Maintainability
- Business logic centralized in services
- Data access logic in repositories
- API contracts in routers

### Testability
- Mock services in router tests
- Mock repositories in service tests
- Test repositories against database

### Flexibility
- Swap database implementation (repository)
- Change business rules (service)
- Modify API contracts (router)

---

## Common Patterns

### Pattern: Router with Multiple Operations

```python
@router.get("/")
async def list_artists(
    limit: int = 100,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    service = ArtistService(session)
    return await service.get_all_artists(limit)

@router.post("/")
async def create_artist(
    dto: ArtistRequestDto,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    service = ArtistService(session)
    return await service.create_artist(dto)

@router.put("/{artist_id}")
async def update_artist(
    artist_id: str,
    dto: ArtistRequestDto,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    service = ArtistService(session)
    return await service.update_artist(artist_id, dto)

@router.delete("/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artist(
    artist_id: str,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    service = ArtistService(session)
    await service.delete_artist(artist_id)
```

### Pattern: Service with Transaction

```python
async def create_artist_with_artworks(
    self,
    artist_dto: ArtistRequestDto,
    artwork_dtos: List[ArtworkRequestDto],
) -> ArtistResponseDto:
    """Create artist and their artworks in a transaction"""
    # Both operations use same session (transaction)
    artist = Artist(**artist_dto.model_dump())
    created_artist = await self._artist_repository.create(artist)

    for artwork_dto in artwork_dtos:
        artwork = Artwork(**artwork_dto.model_dump(), artist_id=created_artist.id)
        await self._artwork_repository.create(artwork)

    await self.session.commit()  # Commit transaction

    return ArtistResponseDto.from_model(created_artist)
```

---

## Best Practices

1. **Never bypass layers**: Always Router → Service → Repository
2. **Services own business logic**: Don't put logic in routers or repositories
3. **Repositories return models**: DTOs are for API layer only
4. **Use dependency injection**: FastAPI's Depends() for sessions
5. **Async throughout**: All layers use async/await
6. **Read/Write split**: Use appropriate session dependency
7. **One service per request**: Create service instance in each route
8. **Error handling**: Raise domain exceptions in service, handle in middleware
