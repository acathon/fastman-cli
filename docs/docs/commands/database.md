---
sidebar_position: 2
---

# Database Commands

Manage your database schema, migrations, and seeds.

## Migrations

### `make:migration`

Creates a new Alembic migration file.

```bash
fastman make:migration "create users table"
```

- **Arguments**:
    - `message`: A brief description of the change (e.g., "create users table").

### `database:migrate`

Runs all pending migrations.

```bash
fastman database:migrate
```

### `migrate:rollback`

Rolls back the last batch of migrations. Prompts for confirmation before proceeding.

```bash
fastman migrate:rollback [--steps=1]
```

- **Options**:
    - `--steps`: Number of migrations to rollback (default: 1).

### `migrate:reset`

Rolls back all migrations, effectively emptying the database schema. Prompts for confirmation. **Use with caution.**

```bash
fastman migrate:reset
```

### `migrate:status`

Shows the current migration status (current revision).

```bash
fastman migrate:status
```

## Seeding

### `database:seed`

Runs the database seeders to populate the database with initial data.

```bash
fastman database:seed [--class=ClassName]
```

- **Options**:
    - `--class`: Run a specific seeder class by name or module (e.g., `UserSeeder` or `user_seeder`).

:::tip Important
Run this command from your **project root directory** (where your `app/` folder is), not from inside subdirectories.
:::

### Creating Seeders

Use `make:seeder` to create a new seeder file:

```bash
fastman make:seeder user
```

This creates `database/seeders/user_seeder.py`:

```python
from app.features.user.models import User

class UserSeeder:
    @staticmethod
    def run(db):
        users = [
            User(name="Admin", email="admin@example.com"),
            User(name="Test", email="test@example.com"),
        ]
        db.add_all(users)
        db.commit()
```
