---
sidebar_position: 2
---

# Database Commands

Commands for managing your database schema through migrations and populating data with seeders. Fastman wraps [Alembic](https://alembic.sqlalchemy.org/) to provide a simpler, Laravel-style interface for migration management.

## Migrations

### `make:migration`

Generates a new Alembic migration file in `database/migrations/versions/`. The message you provide becomes the migration's description and is included in the filename.

```bash
fastman make:migration "<message>"
```

```bash
fastman make:migration "create users table"
fastman make:migration "add email column to posts"
fastman make:migration "create orders index"
```

:::tip
Write descriptive migration messages — they help you understand the migration history when running `migrate:status` or reviewing the `versions/` directory.
:::

### `database:migrate`

Applies all pending migrations to bring your database schema up to date. This runs Alembic's `upgrade head` under the hood.

```bash
fastman database:migrate
```

### `migrate:rollback`

Rolls back the most recent migration(s). Prompts for confirmation before making changes. This is useful during development when you need to adjust a migration.

```bash
fastman migrate:rollback [--steps=1]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--steps` | Number of migrations to undo | `1` |

```bash
# Undo the last migration
fastman migrate:rollback

# Undo the last 3 migrations
fastman migrate:rollback --steps=3
```

### `migrate:reset`

Rolls back **all** migrations, effectively dropping all tables and returning the database to a blank state. Always prompts for confirmation.

```bash
fastman migrate:reset
```

:::danger
This is a destructive operation — all data in the database will be lost. Only use this during development. In production, use targeted rollbacks instead.
:::

### `migrate:status`

Displays the current migration revision, so you can see which migrations have been applied and which are pending.

```bash
fastman migrate:status
```

---

## Seeding

### `database:seed`

Runs database seeder classes to populate your database with initial or test data. By default, it discovers and runs all seeders in `database/seeders/`. You can target a specific seeder with the `--class` option.

```bash
fastman database:seed [--class=ClassName]
```

| Option | Description |
|--------|-------------|
| `--class` | Run a specific seeder by class name (`UserSeeder`) or module name (`user_seeder`) |

```bash
# Run all seeders
fastman database:seed

# Run only the UserSeeder
fastman database:seed --class=UserSeeder
```

:::tip
Always run seeder commands from your **project root directory** (where your `app/` folder is), not from inside subdirectories.
:::

### Creating Seeders

Use `make:seeder` to generate a new seeder file:

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
