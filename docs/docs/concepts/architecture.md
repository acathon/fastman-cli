---
sidebar_position: 1
---

# Architecture

Fastman is built on the philosophy of **"Convention over Configuration"**. While FastAPI is unopinionated, Fastman provides the opinions needed to move fast.

## The "Fastman Way"

1.  **Dependency Injection**: Everything is injected. Services are injected into Routers. Repositories (if used) are injected into Services.
2.  **Thin Routers**: Routers should only handle HTTP request/response logic. Business logic belongs in Services.
3.  **Rich Models**: Models should encapsulate data behavior.
4.  **Centralized Config**: All settings live in `app/core/config.py` and are loaded from `.env`.

## Service Layer

When you run `make:feature --crud`, Fastman generates a Service class.

```python
class PizzaService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Pizza).all()
```

This service is then injected into your router:

```python
@router.get("/")
def get_pizzas(
    db: Session = Depends(get_db),
    service: PizzaService = Depends(get_pizza_service)
):
    return service.get_all()
```

This makes your code testable and modular.
