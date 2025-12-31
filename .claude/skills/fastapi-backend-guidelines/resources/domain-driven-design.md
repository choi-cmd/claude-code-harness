# Domain-Driven Design - FastAPI

## Domain Organization

Each domain follows this structure:

```
backend/domain/{domain}/
  __init__.py
  model.py         # SQLModel database models
  repository.py    # Data access layer
  service.py       # Business logic layer
```

## Your Domains

Current domains in your project:
- **admin**: Administrative functions
- **artist**: Artist management
- **artwork**: Artwork management
- **auth**: Authentication and authorization
- **curai**: AI curator features
- **exhibition**: Exhibition management
- **message**: Messaging system
- **notification**: Notifications
- **subscription**: User subscriptions
- **user**: User management
- **shared**: Shared utilities/base classes

## Creating a New Domain

1. **Create directory**: `backend/domain/newdomain/`
2. **Create model.py**: Database models
3. **Create repository.py**: Data access
4. **Create service.py**: Business logic
5. **Create DTOs**: `backend/dtos/newdomain.py`
6. **Create router**: `backend/api/v1/routers/newdomain.py`
7. **Register router**: Add to `main.py`

## Domain Independence

- Domains should be as independent as possible
- Share common code through `shared` domain
- Avoid circular dependencies
- Use DTOs for inter-domain communication

## Best Practices

1. **Single responsibility**: Each domain has one clear purpose
2. **Encapsulation**: Hide implementation details
3. **Consistent structure**: All domains follow same pattern
4. **Shared utilities**: Use `shared` domain for common code
5. **Clear boundaries**: Minimize cross-domain dependencies
