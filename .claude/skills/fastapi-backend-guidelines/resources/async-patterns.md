# Async/Await Patterns - FastAPI

## Async Basics

FastAPI is async-first. All database operations should be async.

### Async Route Handler

```python
@router.get("/{id}")
async def get_item(
    id: str,
    session: AsyncSession = Depends(get_read_session_dependency),
):
    service = ItemService(session)
    return await service.get_item(id)  # await async method
```

### Async Service Method

```python
class ItemService:
    async def get_item(self, id: str) -> ItemResponseDto:
        # Await repository call
        item = await self._repository.get_by_id(id)
        if not item:
            raise NotFoundError("Item not found")
        return ItemResponseDto.from_model(item)
```

### Async Repository Query

```python
class ItemRepository:
    async def get_by_id(self, id: str) -> Optional[Item]:
        stmt = select(Item).where(Item.id == id)
        # Await database query
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

## Concurrent Operations

### Parallel Queries

```python
import asyncio

async def get_dashboard_data(self, user_id: str):
    # Run multiple queries in parallel
    artists, artworks, exhibitions = await asyncio.gather(
        self._artist_repo.find_by_user(user_id),
        self._artwork_repo.find_by_user(user_id),
        self._exhibition_repo.find_active(),
    )

    return DashboardDto(
        artists=artists,
        artworks=artworks,
        exhibitions=exhibitions,
    )
```

### Sequential Dependencies

```python
async def create_with_dependencies(self, dto: CreateDto):
    # Must run sequentially (artwork depends on artist)
    artist = await self._artist_repo.create(dto.artist_data)
    artwork = await self._artwork_repo.create(
        dto.artwork_data,
        artist_id=artist.id  # Needs artist.id
    )
    return artwork
```

## Session Management

### AsyncSession Context

```python
from sqlmodel.ext.asyncio.session import AsyncSession

# Session provided by dependency injection
async def route_handler(
    session: AsyncSession = Depends(get_write_session_dependency),
):
    # Session automatically managed (commit/rollback)
    service = Service(session)
    return await service.do_work()
```

## Common Pitfalls

### ❌ Blocking Operations

```python
# ❌ Don't use blocking I/O in async functions
async def bad_handler():
    time.sleep(1)  # Blocks event loop!
    return "done"

# ✅ Use async alternatives
async def good_handler():
    await asyncio.sleep(1)  # Non-blocking
    return "done"
```

### ❌ Missing await

```python
# ❌ Forgot await - returns coroutine, not result
async def bad_service():
    item = self._repository.get_by_id(id)  # Missing await!
    return item  # This is a coroutine object, not Item

# ✅ Always await async calls
async def good_service():
    item = await self._repository.get_by_id(id)
    return item  # This is Item object
```

## Best Practices

1. **Async all the way**: Route → Service → Repository
2. **await async calls**: Never forget await
3. **No blocking I/O**: Use async libraries
4. **Parallel when possible**: Use asyncio.gather()
5. **Session per request**: Dependency injection
6. **Error handling**: try/except works with async
