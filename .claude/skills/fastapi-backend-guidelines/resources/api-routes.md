# API Routes & Routers - FastAPI

## Router Basics

FastAPI routers organize your API endpoints by domain.

### Creating a Router

```python
# backend/api/v1/routers/artist.py
from fastapi import APIRouter, Depends, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from backend.db.orm import get_read_session_dependency, get_write_session_dependency
from backend.domain.artist.service import ArtistService
from backend.dtos.artist import ArtistResponseDto, ArtistRequestDto

router = APIRouter(
    prefix="/api/v1/artists",
    tags=["artists"],  # For OpenAPI docs
)
```

### Read Operations (GET)

```python
@router.get("/", response_model=List[ArtistResponseDto])
async def list_artists(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """List all artists with pagination"""
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

@router.get("/search", response_model=List[ArtistResponseDto])
async def search_artists(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, le=100),
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """Search artists by keyword"""
    service = ArtistService(session)
    return await service.search_artists(q, limit)
```

### Write Operations (POST, PUT, DELETE)

```python
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

## Read/Write Session Split

**IMPORTANT**: Use the correct session dependency:

```python
# Read operations (SELECT)
session: AsyncSession = Depends(get_read_session_dependency)

# Write operations (INSERT, UPDATE, DELETE)
session: AsyncSession = Depends(get_write_session_dependency)
```

## Query Parameters

```python
from fastapi import Query

@router.get("/")
async def list_items(
    # Required
    category: str = Query(..., description="Category to filter by"),

    # Optional with default
    limit: int = Query(default=10, ge=1, le=100),

    # With validation
    search: str = Query(default=None, min_length=3, max_length=50),

    # Multiple values
    tags: List[str] = Query(default=None),

    session: AsyncSession = Depends(get_read_session_dependency),
):
    pass
```

## Path Parameters

```python
@router.get("/{artist_id}/artworks/{artwork_id}")
async def get_artwork(
    artist_id: str,
    artwork_id: str,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    """Get specific artwork for an artist"""
    service = ArtworkService(session)
    return await service.get_artwork(artist_id, artwork_id)
```

## Request Body

```python
from pydantic import BaseModel

class CreateArtistDto(BaseModel):
    name: str
    bio: str

@router.post("/")
async def create_artist(
    dto: CreateArtistDto,  # Automatically validates request body
    session: AsyncSession = Depends(get_write_session_dependency),
):
    service = ArtistService(session)
    return await service.create_artist(dto)
```

## Status Codes

```python
from fastapi import status

# Success codes
@router.post("/", status_code=status.HTTP_201_CREATED)  # Created
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)  # No content
@router.get("/", status_code=status.HTTP_200_OK)  # OK (default)

# Error codes (raised as HTTPException)
from fastapi import HTTPException

if not item:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found"
    )
```

## Registering Routers

In `backend/main.py`:

```python
from backend.api.v1.routers.artist import router as artist_router

def create_application() -> FastAPI:
    app = FastAPI()

    # Register routers
    app.include_router(artist_router)

    return app
```

## Best Practices

1. **Prefix**: Use `/api/v1/{domain}` for all routes
2. **Tags**: Group related endpoints with tags for docs
3. **Response Models**: Always specify `response_model`
4. **Status Codes**: Use appropriate HTTP status codes
5. **Validation**: Use Pydantic Query/Path validators
6. **Session Dependency**: Read vs Write session split
7. **Docstrings**: Document each endpoint
8. **Async**: All route handlers must be async
