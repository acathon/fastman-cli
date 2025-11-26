---
sidebar_position: 2
---

# Directory Structure

Fastman supports multiple architectural patterns. Understanding the structure is key to scaling your application.

## Feature Pattern (Default)

The **Feature Pattern** (Vertical Slice) organizes code by domain feature rather than technical layer. This is recommended for most projects as it keeps related code together.

```plaintext
app/
├── core/               # Shared configuration, database, security
│   ├── config.py
│   └── database.py
├── features/           # Your domain features
│   ├── auth/           # Auth feature
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── model.py
│   │   └── schema.py
│   └── pizza/          # Pizza feature
│       ├── router.py
│       ├── ...
├── main.py             # App entrypoint
└── ...
```

## Layer Pattern

The **Layer Pattern** follows a traditional MVC/Clean Architecture approach.

```plaintext
app/
├── api/                # Controllers/Routers
│   └── v1/
│       └── endpoints/
├── core/
├── models/             # Database Models
├── schemas/            # Pydantic Schemas
├── services/           # Business Logic
└── repositories/       # Data Access Layer
```

## API Pattern

The **API Pattern** is a lightweight structure for simple microservices.

```plaintext
app/
├── api/                # Routers
├── models/             # Models
├── schemas/            # Schemas
└── main.py
```

## Choosing a Pattern

- **Feature**: Best for medium-to-large monoliths. Easy to extract services later.
- **Layer**: Best if you prefer strict separation of concerns or have a very large team used to MVC.
- **API**: Best for small, single-purpose microservices.
