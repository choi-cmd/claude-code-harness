# Complete Examples - FastAPI

## Full CRUD Domain Example

### Model
```python
# backend/domain/artist/model.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(primary_key=True)
    name: str = Field(max_length=255, index=True)
    email: str = Field(unique=True, index=True)
    bio: Optional[str] = None
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
```

### Repository
```python
# backend/domain/artist/repository.py
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.domain.artist.model import Artist
from backend.domain.shared.base_repository import BaseRepository

class ArtistRepository(BaseRepository[Artist]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Artist)

    async def find_by_email(self, email: str) -> Optional[Artist]:
        stmt = select(Artist).where(Artist.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_approved(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Artist]:
        stmt = (
            select(Artist)
            .where(Artist.status == "approved")
            .order_by(Artist.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

### Service
```python
# backend/domain/artist/service.py
from typing import List
from datetime import datetime
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
        artist = await self._repository.get_by_id(artist_id)
        if not artist:
            raise NotFoundError(f"Artist {artist_id} not found")
        return ArtistResponseDto.from_model(artist)

    async def get_all_artists(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[ArtistResponseDto]:
        artists = await self._repository.find_all_approved(limit, offset)
        return [ArtistResponseDto.from_model(a) for a in artists]

    async def create_artist(self, dto: ArtistRequestDto) -> ArtistResponseDto:
        # Business rule: Email must be unique
        existing = await self._repository.find_by_email(dto.email)
        if existing:
            raise ValidationError("Email already registered")

        artist = Artist(**dto.model_dump())
        created = await self._repository.create(artist)
        return ArtistResponseDto.from_model(created)

    async def update_artist(
        self,
        artist_id: str,
        dto: ArtistRequestDto
    ) -> ArtistResponseDto:
        artist = await self._repository.get_by_id(artist_id)
        if not artist:
            raise NotFoundError(f"Artist {artist_id} not found")

        # Update fields
        artist.name = dto.name
        artist.email = dto.email
        artist.bio = dto.bio
        artist.updated_at = datetime.utcnow()

        updated = await self._repository.update(artist)
        return ArtistResponseDto.from_model(updated)

    async def delete_artist(self, artist_id: str) -> None:
        artist = await self._repository.get_by_id(artist_id)
        if not artist:
            raise NotFoundError(f"Artist {artist_id} not found")
        await self._repository.delete(artist)
```

### DTOs
```python
# backend/dtos/artist.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class ArtistRequestDto(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    bio: Optional[str] = Field(default=None, max_length=2000)

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class ArtistResponseDto(BaseModel):
    id: str
    name: str
    email: str
    bio: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_model(cls, model: Artist) -> "ArtistResponseDto":
        return cls(
            id=model.id,
            name=model.name,
            email=model.email,
            bio=model.bio,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    class Config:
        from_attributes = True
```

### Router
```python
# backend/api/v1/routers/artist.py
from fastapi import APIRouter, Depends, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.artist.service import ArtistService
from backend.dtos.artist import ArtistRequestDto, ArtistResponseDto

router = APIRouter(prefix="/api/v1/artists", tags=["artists"])

@router.get("/", response_model=List[ArtistResponseDto])
async def list_artists(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """List all approved artists with pagination"""
    service = ArtistService(session)
    return await service.get_all_artists(limit=limit, offset=offset)

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

@router.put("/{artist_id}", response_model=ArtistResponseDto)
async def update_artist(
    artist_id: str,
    dto: ArtistRequestDto,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """Update existing artist"""
    service = ArtistService(session)
    return await service.update_artist(artist_id, dto)

@router.delete("/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artist(
    artist_id: str,
    session: AsyncSession = Depends(get_write_session_dependency),
):
    """Delete artist"""
    service = ArtistService(session)
    await service.delete_artist(artist_id)
```

### Register Router
```python
# backend/main.py
from backend.api.v1.routers.artist import router as artist_router

def create_application() -> FastAPI:
    app = FastAPI()
    app.include_router(artist_router)
    return app
```

This complete example demonstrates:
- ✅ Layered architecture (Router → Service → Repository)
- ✅ Domain-Driven Design structure
- ✅ SQLModel models
- ✅ Repository pattern with BaseRepository
- ✅ Service layer with business logic
- ✅ Pydantic DTOs with validation
- ✅ FastAPI routers with dependency injection
- ✅ Async/await throughout
- ✅ Error handling with custom exceptions
- ✅ CRUD operations
- ✅ Pagination
- ✅ Type hints everywhere
