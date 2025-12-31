# Service Layer - FastAPI

## Service Pattern

Services contain business logic and orchestrate repositories.

### Basic Service

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
        """Get artist by ID"""
        artist = await self._repository.get_by_id(artist_id)
        if not artist:
            raise NotFoundError(f"Artist {artist_id} not found")
        return ArtistResponseDto.from_model(artist)

    async def create_artist(self, dto: ArtistRequestDto) -> ArtistResponseDto:
        """Create new artist"""
        # Business rule: Check uniqueness
        existing = await self._repository.find_by_email(dto.email)
        if existing:
            raise ValidationError("Email already registered")

        artist = Artist(**dto.model_dump())
        created = await self._repository.create(artist)
        return ArtistResponseDto.from_model(created)
```

## Service Responsibilities

1. **Business Logic**: Implement domain rules
2. **Validation**: Business-level validation (beyond DTO)
3. **Orchestration**: Coordinate multiple repositories
4. **Transformation**: Model ↔ DTO conversion
5. **Error Handling**: Raise domain exceptions
6. **Transaction Management**: Coordinate commits/rollbacks

## Multi-Repository Services

```python
class ArtworkService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._artwork_repository = ArtworkRepository(session)
        self._artist_repository = ArtistRepository(session)

    async def create_artwork(
        self,
        artist_id: str,
        dto: ArtworkRequestDto
    ) -> ArtworkResponseDto:
        # Verify artist exists
        artist = await self._artist_repository.get_by_id(artist_id)
        if not artist:
            raise NotFoundError("Artist not found")

        # Create artwork
        artwork = Artwork(**dto.model_dump(), artist_id=artist_id)
        created = await self._artwork_repository.create(artwork)

        return ArtworkResponseDto.from_model(created)
```

## Best Practices

1. **One service per domain**: ArtistService for artist domain
2. **Inject session**: Accept AsyncSession in constructor
3. **Return DTOs**: Never return models directly
4. **Raise exceptions**: Use domain exceptions for errors
5. **Business rules**: Enforce in service, not repository
6. **Transaction scope**: Service owns transaction lifecycle
