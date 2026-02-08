---
sidebar_position: 3
---

# Interactive Shell (Tinker)

Fastman's `tinker` command provides an interactive Python shell with your application context pre-loaded. Inspired by Laravel's Tinker, it's perfect for quick debugging, data exploration, and testing.

## Basic Usage

```bash
fastman tinker
```

This starts an interactive Python shell with:
- Database session (`db`)
- Application settings (`settings`)  
- SQLAlchemy `Base` model
- All your models auto-imported

## Features

### Pre-loaded Database Session

```python
>>> from app.features.user.models import User
>>> users = db.query(User).all()
>>> len(users)
42
```

### IPython Support

If IPython is installed, tinker uses it automatically for:
- Syntax highlighting
- Tab completion
- Better tracebacks
- Magic commands (`%history`, `%timeit`, etc.)

```bash
pip install ipython
fastman tinker
```

---

## Tinker Tricks

### 1. Quick Data Inspection

```python
# Count records
>>> db.query(User).count()
150

# Get first/last
>>> db.query(User).first()
<User id=1 email='admin@example.com'>

>>> db.query(User).order_by(User.id.desc()).first()
<User id=150 email='latest@example.com'>

# Filter with conditions
>>> db.query(User).filter(User.is_active == True).count()
142
```

### 2. Create Test Data Quickly

```python
>>> from app.features.user.models import User
>>> user = User(email="test@example.com", name="Test User")
>>> db.add(user)
>>> db.commit()
>>> user.id
151
```

### 3. Update Records

```python
>>> user = db.query(User).filter(User.email == "test@example.com").first()
>>> user.name = "Updated Name"
>>> db.commit()
```

### 4. Delete Records

```python
>>> user = db.query(User).filter(User.id == 151).first()
>>> db.delete(user)
>>> db.commit()
```

### 5. Raw SQL Queries

```python
>>> from sqlalchemy import text
>>> result = db.execute(text("SELECT COUNT(*) FROM users"))
>>> result.scalar()
150
```

### 6. Explore Relationships

```python
>>> user = db.query(User).first()
>>> user.posts  # Lazy load related posts
[<Post id=1>, <Post id=2>, <Post id=3>]

>>> user.orders[-1].total  # Latest order total
Decimal('99.99')
```

### 7. Test Services

```python
>>> from app.features.user.service import UserService
>>> service = UserService(db)
>>> service.get_active_users()
[<User id=1>, <User id=2>, ...]
```

### 8. Inspect Model Schema

```python
>>> User.__table__.columns.keys()
['id', 'email', 'name', 'password', 'is_active', 'created_at']

>>> for col in User.__table__.columns:
...     print(f"{col.name}: {col.type}")
id: INTEGER
email: VARCHAR(255)
name: VARCHAR(100)
...
```

### 9. Check Environment

```python
>>> settings.DATABASE_URL
'postgresql://localhost/myapp'

>>> settings.DEBUG
True

>>> settings.SECRET_KEY[:10]
'abc123...'
```

### 10. Bulk Operations

```python
# Bulk insert
>>> users = [User(email=f"user{i}@test.com") for i in range(100)]
>>> db.add_all(users)
>>> db.commit()

# Bulk update
>>> db.query(User).filter(User.is_active == False).update({"is_active": True})
>>> db.commit()

# Bulk delete
>>> db.query(User).filter(User.email.like("%@test.com")).delete()
>>> db.commit()
```

---

## IPython Magic Commands

When using IPython, these magic commands are helpful:

| Command | Description |
|---------|-------------|
| `%history` | Show command history |
| `%timeit` | Time execution of a statement |
| `%who` | List all variables |
| `%whos` | Detailed variable list |
| `%reset` | Clear all variables |
| `%paste` | Paste from clipboard |
| `%edit` | Open editor for multi-line code |

### Example: Timing Queries

```python
>>> %timeit db.query(User).filter(User.is_active == True).all()
2.34 ms ± 123 µs per loop
```

---

## Tips

:::tip Use Rollback for Safety
When experimenting with data changes, wrap operations in a transaction you can rollback:
```python
>>> user.name = "Oops"
>>> db.rollback()  # Undo changes
```
:::

:::tip Exit Cleanly
Always use `exit()` or `Ctrl+D` to exit tinker, which properly closes the database connection.
:::

:::warning Production Caution
Be careful running tinker in production! Any database changes are permanent. Consider using a read-only database connection for production debugging.
:::
