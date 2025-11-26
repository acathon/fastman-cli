---
sidebar_position: 1
---

# Your First Project

Let's build a simple "Pizza Ordering" API to see Fastman in action.

## 1. Create a New Project

Run the `new` command to generate a project. We'll use the default **Feature Architecture** and **uv** package manager.

```bash
fastman new pizza-api
```

This will:
- Create a `pizza-api` directory.
- Set up a virtual environment.
- Install FastAPI, SQLAlchemy, and other dependencies.
- Initialize a SQLite database.

## 2. Enter the Project

```bash
cd pizza-api
```

## 3. Scaffold a Feature

We want to manage Pizzas. Instead of creating files manually, use `make:feature`.

```bash
fastman make:feature pizza --crud
```

This single command generates:
- `app/features/pizza/router.py` (API Endpoints)
- `app/features/pizza/service.py` (Business Logic)
- `app/features/pizza/model.py` (Database Model)
- `app/features/pizza/schema.py` (Pydantic Schemas)

It also automatically registers the router in `app/main.py`.

## 4. Run Migrations

Fastman uses Alembic for migrations. Create a migration for the new Pizza model:

```bash
fastman make:migration "create pizza table"
fastman migrate
```

## 5. Start the Server

```bash
fastman serve
```

Visit `http://localhost:8000/docs`. You'll see full CRUD endpoints for `/pizza` ready to use!

## 6. Interact with the Shell

Want to test your model without the API? Use `tinker`.

```bash
fastman tinker
```

```python
>>> from app.features.pizza.model import Pizza
>>> p = Pizza(name="Margherita", price=10.99)
>>> db.add(p)
>>> db.commit()
>>> db.query(Pizza).all()
[<Pizza(id=1, name='Margherita')>]
```

Congratulations! You've built a working API in under a minute.
