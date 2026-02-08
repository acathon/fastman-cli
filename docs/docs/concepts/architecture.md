---
sidebar_position: 1
---

# Architecture Patterns

Fastman supports three architectural patterns. Choose based on your project's complexity.

## Feature Pattern (Recommended)

**Best for:** Medium to large applications, microservices-ready code.

The feature pattern organizes code into **vertical slices**. Each feature is self-contained with its own models, schemas, services, and routes.

```
app/features/
├── user/
│   ├── models.py     # User model
│   ├── schemas.py    # Request/Response DTOs
│   ├── service.py    # Business logic
│   └── router.py     # API endpoints
│
└── order/
    ├── models.py
    ├── schemas.py
    ├── service.py
    └── router.py
```

### Benefits

- **Cohesion** — Related code lives together
- **Isolation** — Features don't leak into each other
- **Scalability** — Easy to extract into microservices
- **Testability** — Test features independently

### When to Use

- APIs with 5+ distinct resources
- Teams with multiple developers
- Projects that may scale to microservices

---

## API Pattern

**Best for:** Simple REST APIs, rapid prototyping.

The API pattern groups code by HTTP resource with API versioning built-in.

```
app/
├── api/
│   ├── v1/
│   │   ├── users.py
│   │   └── posts.py
│   └── v2/
│       └── users.py
├── models/
└── schemas/
```

### When to Use

- Small APIs (1-4 resources)
- Quick prototypes
- APIs requiring version namespacing

---

## Layer Pattern

**Best for:** Traditional enterprise applications.

The layer pattern separates code by technical concern (MVC-style).

```
app/
├── controllers/      # Request handling
├── services/         # Business logic
├── repositories/     # Data access
├── models/           # Database models
└── schemas/          # DTOs
```

### When to Use

- Teams familiar with MVC patterns
- Applications with complex business rules
- When strict separation of concerns is required

---

## Switching Patterns

You can specify the pattern when creating a project:

```bash
# Feature pattern (default)
fastman new my-api --pattern=feature

# API pattern
fastman new my-api --pattern=api

# Layer pattern
fastman new my-api --pattern=layer
```

:::tip
Start with the **feature pattern** if you're unsure. It scales well and you can always refactor later.
:::
