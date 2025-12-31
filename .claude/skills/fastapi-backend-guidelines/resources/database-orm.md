# Database & ORM - SQLModel + SQLAlchemy

## SQLModel Models

SQLModel combines SQLAlchemy ORM with Pydantic validation.

### Basic Model

```python
# backend/domain/artist/model.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(primary_key=True)
    name: str = Field(max_length=255, index=True)
    bio: Optional[str] = Field(default=None)
    email: str = Field(unique=True, index=True)
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
```

### Relationships

```python
from sqlmodel import Relationship
from typing import List

class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(primary_key=True)
    name: str

    # One-to-many relationship
    artworks: List["Artwork"] = Relationship(back_populates="artist")

class Artwork(SQLModel, table=True):
    __tablename__ = "artworks"

    id: str = Field(primary_key=True)
    title: str
    artist_id: str = Field(foreign_key="artists.id")

    # Many-to-one relationship
    artist: Optional[Artist] = Relationship(back_populates="artworks")
```

## Queries with SQLModel

### Basic Queries

```python
from sqlmodel import select

# Get by ID
stmt = select(Artist).where(Artist.id == artist_id)
result = await session.execute(stmt)
artist = result.scalar_one_or_none()

# Get all
stmt = select(Artist)
result = await session.execute(stmt)
artists = result.scalars().all()

# Filter
stmt = select(Artist).where(Artist.status == "approved")
result = await session.execute(stmt)
approved = result.scalars().all()
```

### Complex Queries

```python
from sqlmodel import select, or_, and_

# Multiple conditions
stmt = select(Artist).where(
    and_(
        Artist.status == "approved",
        Artist.created_at > some_date
    )
)

# OR conditions
stmt = select(Artist).where(
    or_(
        Artist.name.ilike(f"%{keyword}%"),
        Artist.bio.ilike(f"%{keyword}%")
    )
)

# Ordering
stmt = select(Artist).order_by(Artist.created_at.desc())

# Pagination
stmt = select(Artist).offset(offset).limit(limit)

# Count
from sqlalchemy import func
stmt = select(func.count(Artist.id))
result = await session.execute(stmt)
count = result.scalar()
```

### Joins

```python
# Join with related table
stmt = (
    select(Artwork, Artist)
    .join(Artist, Artist.id == Artwork.artist_id)
    .where(Artist.status == "approved")
)
result = await session.execute(stmt)
artworks_with_artists = result.all()
```

## Session Management

Your project uses read/write session split:

```python
# backend/db/orm.py provides:

# Read session (SELECT queries)
async def get_read_session_dependency():
    async with get_read_session() as session:
        yield session

# Write session (INSERT, UPDATE, DELETE)
async def get_write_session_dependency():
    async with get_write_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## CRUD Operations

### Create

```python
artist = Artist(
    id="artist_123",
    name="John Doe",
    email="john@example.com"
)
session.add(artist)
await session.commit()
await session.refresh(artist)  # Get DB defaults
```

### Read

```python
stmt = select(Artist).where(Artist.id == artist_id)
result = await session.execute(stmt)
artist = result.scalar_one_or_none()
```

### Update

```python
stmt = select(Artist).where(Artist.id == artist_id)
result = await session.execute(stmt)
artist = result.scalar_one_or_none()

if artist:
    artist.name = "New Name"
    artist.updated_at = datetime.utcnow()
    session.add(artist)
    await session.commit()
    await session.refresh(artist)
```

### Delete

```python
stmt = select(Artist).where(Artist.id == artist_id)
result = await session.execute(stmt)
artist = result.scalar_one_or_none()

if artist:
    await session.delete(artist)
    await session.commit()
```

## Transactions

```python
async def create_artist_with_artworks(session: AsyncSession):
    # All operations in same session = same transaction
    artist = Artist(name="John")
    session.add(artist)
    await session.flush()  # Get artist.id without committing

    artwork1 = Artwork(title="Art 1", artist_id=artist.id)
    artwork2 = Artwork(title="Art 2", artist_id=artist.id)
    session.add_all([artwork1, artwork2])

    await session.commit()  # Commits all changes atomically
```

## Best Practices

1. **Async all the way**: Use AsyncSession, await all queries
2. **Read/Write split**: Use correct session dependency
3. **Refresh after commit**: Get DB-generated values
4. **Index frequently queried columns**: Add `index=True`
5. **Unique constraints**: Use `unique=True` for unique fields
6. **Flush before using IDs**: Use `flush()` to get generated IDs
7. **Transactions**: Related operations in same session
8. **Rollback on error**: Session dependency handles this
