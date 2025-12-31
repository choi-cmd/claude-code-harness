# Repository Pattern - FastAPI

## Repository Pattern

Repositories encapsulate all database access for a domain.

### BaseRepository

Your project has a BaseRepository:

```python
# backend/domain/shared/base_repository.py
from typing import Generic, TypeVar, Optional, List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: str) -> Optional[T]:
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.flush()
```

### Domain-Specific Repository

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

    async def find_by_email(self, email: str) -> Optional[Artist]:
        """Find artist by email"""
        stmt = select(Artist).where(Artist.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_approved(self, limit: int = 100) -> List[Artist]:
        """Get all approved artists"""
        stmt = (
            select(Artist)
            .where(Artist.status == "approved")
            .order_by(Artist.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, keyword: str, limit: int = 10) -> List[Artist]:
        """Search artists by keyword"""
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

## Repository Responsibilities

1. **Database queries**: All SELECT/INSERT/UPDATE/DELETE
2. **Query optimization**: Efficient queries with indexes
3. **Return models**: Always return domain models
4. **No business logic**: Pure data access only
5. **No DTOs**: Work with models only

## Best Practices

1. **Extend BaseRepository**: Reuse common CRUD operations
2. **Domain-specific methods**: Add methods for domain queries
3. **Return models**: Never return DTOs
4. **Async queries**: All methods async
5. **Type hints**: Explicit return types
6. **No transactions**: Repository doesn't commit/rollback
