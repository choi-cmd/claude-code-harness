# Error Handling - FastAPI

## Custom Exceptions

Define domain-specific exceptions:

```python
# backend/error/__init__.py

class DomainException(Exception):
    """Base exception for domain errors"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(DomainException):
    """Resource not found"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class ValidationError(DomainException):
    """Validation failed"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class UnauthorizedError(DomainException):
    """Unauthorized access"""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

class ForbiddenError(DomainException):
    """Forbidden access"""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)
```

## Using Exceptions in Services

```python
from backend.error import NotFoundError, ValidationError

class ArtistService:
    async def get_artist(self, artist_id: str):
        artist = await self._repository.get_by_id(artist_id)

        # Raise domain exception
        if not artist:
            raise NotFoundError(f"Artist {artist_id} not found")

        return ArtistResponseDto.from_model(artist)

    async def create_artist(self, dto: ArtistRequestDto):
        # Business validation
        existing = await self._repository.find_by_email(dto.email)
        if existing:
            raise ValidationError("Email already registered")

        artist = Artist(**dto.model_dump())
        return await self._repository.create(artist)
```

## Error Handler Middleware

```python
# backend/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.error import DomainException

class ErrorHandlerMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
        except DomainException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.message}
            )
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
```

## FastAPI HTTPException

For simple cases:

```python
from fastapi import HTTPException, status

@router.get("/{id}")
async def get_item(id: str):
    item = await get_item_from_db(id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item
```

## Validation Errors

Pydantic automatically handles validation:

```python
@router.post("/")
async def create_item(dto: ItemRequestDto):
    # If DTO validation fails, FastAPI returns 422
    # No manual handling needed
    pass
```

## Best Practices

1. **Domain exceptions**: Use custom exceptions in services
2. **Middleware**: Handle exceptions globally
3. **Specific errors**: NotFoundError, ValidationError, etc.
4. **HTTP mapping**: Middleware converts to HTTP responses
5. **Logging**: Log unexpected errors
6. **Consistent format**: Same error response structure
