# DTOs & Validation - Pydantic

## DTOs (Data Transfer Objects)

DTOs define API contracts using Pydantic.

### Request DTO

```python
# backend/dtos/artist.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class ArtistRequestDto(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    bio: Optional[str] = Field(default=None, max_length=2000)
    website: Optional[str] = None

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @field_validator('website')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Website must start with http:// or https://')
        return v
```

### Response DTO

```python
from datetime import datetime

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
        """Convert domain model to DTO"""
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
        from_attributes = True  # Allow conversion from ORM models
```

## Validation Patterns

### Field Validation

```python
from pydantic import Field, field_validator

class Dto(BaseModel):
    # Length constraints
    name: str = Field(min_length=1, max_length=100)

    # Number constraints
    age: int = Field(ge=0, le=150)  # >= 0, <= 150
    price: float = Field(gt=0)  # > 0

    # Regex pattern
    phone: str = Field(pattern=r'^\+?1?\d{9,15}$')

    # Custom validator
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if 'banned' in v.lower():
            raise ValueError('Name contains banned word')
        return v
```

### Multiple Field Validation

```python
from pydantic import model_validator

class EventDto(BaseModel):
    start_date: datetime
    end_date: datetime

    @model_validator(mode='after')
    def check_dates(self) -> 'EventDto':
        if self.end_date < self.start_date:
            raise ValueError('end_date must be after start_date')
        return self
```

## Usage in Routes

```python
@router.post("/", response_model=ArtistResponseDto)
async def create_artist(
    dto: ArtistRequestDto,  # Auto-validates request body
    session: AsyncSession = Depends(get_write_session_dependency),
):
    service = ArtistService(session)
    return await service.create_artist(dto)
```

## Best Practices

1. **Separate Request/Response**: Different DTOs for input/output
2. **Validation**: Use Pydantic validators liberally
3. **from_model method**: Convert models to response DTOs
4. **Type hints**: Explicit types on all fields
5. **Docstrings**: Document DTO purpose
6. **No business logic**: DTOs are data containers only
