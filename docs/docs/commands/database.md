---
sidebar_position: 2
---

# Database Commands

Commands for managing your database schema through migrations and populating data with seeders. Fastman wraps [Alembic](https://alembic.sqlalchemy.org/) with a simpler, consistent interface for everyday migration tasks.

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

### `migrate:status`

Displays the current migration revision, so you can see which migrations have been applied and which are pending.

```bash
fastman migrate:status
```

### `db:fresh`

Wipes every migrated table and reapplies all migrations in one shot — the "blow it away and start fresh" loop that's common during development. Optionally re-seeds afterwards.

```bash
fastman db:fresh [--seed] [--force]
```

| Option | Description |
|--------|-------------|
| `--seed` | Also run `database:seed` after re-applying migrations |
| `--force` | Skip the confirmation prompt (use in CI / non-interactive runs) |

What it does, in order:

1. `alembic downgrade base` — drops every migrated table.
2. `alembic upgrade head` — reapplies every migration.
3. `database:seed` (if `--seed`) — runs all seeders.

```bash
# Confirm + wipe + migrate
fastman db:fresh

# Wipe + migrate + seed, unattended
fastman db:fresh --seed --force
```

:::danger Production safety net
`db:fresh` refuses to run when `ENVIRONMENT=production`, even with `--force`. If you genuinely need this, unset the env var or invoke the underlying `alembic` commands directly.
:::

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

---

## Introspection

### `model:show`

Introspects a SQLAlchemy model and renders its structure as Rich tables — columns with types/constraints/defaults, relationships with direction, and indexes.

```bash
fastman model:show <name>
```

The locator walks `app/models/`, `app/features/*/models.py`, and `app/api/*/models.py` and matches case-insensitively, tolerant of snake_case ↔ PascalCase (so `model:show user_profile` resolves to `class UserProfile`).

```bash
fastman model:show User
fastman model:show user_profile      # auto-converts to UserProfile
```

Example output:

```text
▶ Model: User
  table: users

  Column      | Type           | Constraints       | Default
  id          | INTEGER        | PK NOT NULL INDEX | —
  email       | VARCHAR(255)   | NOT NULL UNIQUE   | —
  created_at  | DATETIME       | NOT NULL          | —

  Relations
  Relationship | Target | Direction | Collection
  posts        | Post   | onetomany | yes

  Indexes
  Index            | Columns | Unique
  ix_users_email   | email   | yes
```
