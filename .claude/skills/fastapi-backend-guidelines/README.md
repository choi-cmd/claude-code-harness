# FastAPI Backend Guidelines Skill

## Overview

This skill provides comprehensive backend development guidelines adapted specifically for your qwarty project's tech stack:

- **FastAPI** (async Python framework)
- **SQLModel + SQLAlchemy** (ORM)
- **Python 3.12.3** (exact version)
- **PostgreSQL** with asyncpg
- **Domain-Driven Design** architecture
- **Layered Architecture** (Router → Service → Repository)

## What Was Adapted

This skill was created by adapting the showcase repository's `backend-dev-guidelines` (which was designed for Node.js/Express/Prisma) to match your actual Python/FastAPI stack.

### Key Differences from Original

| Original Skill | Your Adapted Skill |
|----------------|-------------------|
| Node.js/Express | Python/FastAPI |
| Prisma ORM | SQLModel + SQLAlchemy |
| TypeScript | Python 3.12.3 with type hints |
| Express Controllers | FastAPI Routers |
| Sync patterns | Async/await throughout |

## What This Skill Covers

1. **Layered Architecture** - Router → Service → Repository pattern
2. **API Routes & Routers** - FastAPI router patterns, dependency injection
3. **Database & ORM** - SQLModel models, async queries, session management
4. **Domain-Driven Design** - Domain organization, separation of concerns
5. **Service Layer** - Business logic, orchestration, domain rules
6. **Repository Pattern** - Data access layer, BaseRepository extension
7. **DTOs & Validation** - Pydantic DTOs, request/response validation
8. **Async/Await Patterns** - Async best practices, concurrent operations
9. **Error Handling** - Custom exceptions, middleware error handling
10. **Complete Examples** - Full CRUD domain implementation

## Skill Activation

The skill is configured to activate when:

### File Triggers
- Working in `backend/backend/**/*.py`
- Files containing FastAPI imports, async patterns, SQLModel, repositories

### Prompt Triggers
- Keywords: "backend", "FastAPI", "service", "repository", "router", "async", "SQLModel", "domain", "dto"
- Intent patterns: Creating/editing routes, services, repositories, database queries

### Enforcement
- **Type**: Domain (suggests, doesn't block)
- **Priority**: High
- The skill will suggest itself when working on backend code

## Quick Start

### Test the Skill

Try editing a backend file:

```bash
# Open a backend file
code backend/backend/domain/artist/service.py
```

The skill should automatically suggest when you:
1. Ask about creating a service or repository
2. Edit a .py file in the backend
3. Ask about FastAPI patterns or async queries

## Project Structure Match

The skill references YOUR actual project structure:

```
backend/
  backend/
    main.py                    # FastAPI app (referenced in skill)

    api/v1/routers/            # Your routers (referenced in skill)
      artist.py
      artwork.py
      ...

    domain/                    # Your domains (referenced in skill)
      artist/
        model.py               # SQLModel models
        repository.py          # Data access
        service.py             # Business logic
      artwork/
      auth/
      ...

    dtos/                      # Your DTOs (referenced in skill)
      artist.py
      artwork.py
      ...

    db/
      orm.py                   # Session management (used in examples)
```

## Integration Status

✅ Skill directory created: `.claude/skills/fastapi-backend-guidelines/`
✅ Main skill.md adapted for FastAPI + SQLModel
✅ 10 resource files created with FastAPI patterns
✅ skill-rules.json updated with new skill configuration
✅ Old backend-dev-guidelines deprecated but kept for reference
✅ Skill activation hooks already set up and working

## Tech Stack Compatibility

✅ **FastAPI**: All patterns use FastAPI routers and dependencies
✅ **SQLModel + SQLAlchemy**: Query patterns and model definitions
✅ **Async/await**: All examples use async throughout
✅ **Python 3.12.3**: Type hints and modern Python patterns
✅ **PostgreSQL + asyncpg**: Async database operations
✅ **Domain-Driven Design**: Matches your domain organization
✅ **Layered Architecture**: Router → Service → Repository pattern
✅ **Pydantic**: DTOs with validation
✅ **Your session management**: Uses `get_read_session_dependency()` and `get_write_session_dependency()`

## Next Steps

1. **Test the skill**: Edit a backend file and the skill should suggest
2. **Review the patterns**: Read through skill.md for quick reference
3. **Expand resources**: Add more examples as your patterns evolve
4. **Update triggers**: Modify skill-rules.json if needed

## Maintenance

As your project evolves, you can:

1. **Add new patterns**: Create new .md files in `resources/`
2. **Update examples**: Edit resource files with project-specific examples
3. **Adjust triggers**: Modify `skill-rules.json` to change activation patterns
4. **Document domains**: Add documentation for new domains as they're created

## Files Created

```
.claude/skills/fastapi-backend-guidelines/
  ├── skill.md                              # Main skill overview
  ├── README.md                             # This file
  └── resources/
      ├── layered-architecture.md           # Router → Service → Repository
      ├── api-routes.md                     # FastAPI routers & endpoints
      ├── database-orm.md                   # SQLModel queries & models
      ├── domain-driven-design.md           # Domain organization
      ├── service-layer.md                  # Business logic layer
      ├── repository-pattern.md             # Data access layer
      ├── dtos-validation.md                # Pydantic DTOs
      ├── async-patterns.md                 # Async/await best practices
      ├── error-handling.md                 # Custom exceptions
      └── complete-examples.md              # Full CRUD implementation
```

## Core Principles Covered

1. **Layered Architecture**: Never bypass layers (Router → Service → Repository)
2. **Domain-Driven Design**: Organize by domain, not by type
3. **Async Everything**: Use async/await throughout the stack
4. **Repository Pattern**: All data access through repositories
5. **Service Layer**: Business logic in services, not routers
6. **DTOs for API**: Use Pydantic DTOs for request/response
7. **Type Hints**: Explicit types on all functions
8. **Error Handling**: Custom exceptions mapped to HTTP
9. **Read/Write Split**: Separate sessions for different operations
10. **Dependency Injection**: Use FastAPI's Depends()

---

**Status**: ✅ Fully integrated and ready to use
**Created**: 2025-11-02
**Adapted from**: claude-code-infrastructure-showcase/backend-dev-guidelines
