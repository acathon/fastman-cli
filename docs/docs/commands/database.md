---
sidebar_position: 2
---

# Database Commands

Manage your database schema, migrations, and seeds.

## Migrations

### `make:migration`

Creates a new Alembic migration file.

```bash
fastman make:migration {message}
```

- **Arguments**:
    - `message`: A brief description of the change (e.g., "create users table").

### `migrate`

Runs all pending migrations.

```bash
fastman migrate
```

### `migrate:rollback`

Rolls back the last batch of migrations.

```bash
fastman migrate:rollback [--steps=1]
```

### `migrate:reset`

Rolls back all migrations, effectively emptying the database schema. **Use with caution.**

```bash
fastman migrate:reset
```

### `migrate:status`

Shows the current migration status (current revision).

```bash
fastman migrate:status
```

## Seeding

### `db:seed`

Runs the database seeders to populate the database with initial data.

```bash
fastman db:seed [--class=ClassName]
```

- **Options**:
    - `--class`: Run a specific seeder class (e.g., `UserSeeder`).
