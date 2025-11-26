---
sidebar_position: 1
---

# Custom Commands

Fastman allows you to extend the CLI with your own commands. This is incredibly powerful for automating tasks like cron jobs, maintenance scripts, data imports, or domain-specific operations.

## Creating a Command

To create a new command, use the `make:command` generator:

```bash
fastman make:command {Name}
```

For example, to create a command that cleans up inactive users:

```bash
fastman make:command PruneUsers
```

This will generate a file at `app/console/commands/prune_users.py`.

## Command Structure

A command is a Python class decorated with `@register` that inherits from `Command`. It must implement a `handle` method.

### The `signature`

The `signature` property defines how your command is called from the CLI. It supports arguments and options.

- **Command Name**: The first part of the signature (e.g., `email:send`).
- **Arguments**: Required parameters enclosed in braces (e.g., `{user}`).
- **Options**: Optional parameters prefixed with `--` (e.g., `{--dry-run}`). You can also specify defaults (e.g., `{--days=30}`).

### The `handle` Method

This is the entry point of your command. Inside `handle`, you can access:
- `self.argument(index)`: Get a positional argument.
- `self.option(name, default)`: Get a named option.
- `self.flag(name)`: Check if a boolean flag is present.
- `self.context`: Access project context (root path, package manager).

## Real-World Example: Pruning Inactive Users

Let's build a command that deletes users who haven't logged in for a certain number of days.

**File**: `app/console/commands/prune_users.py`

```python
from datetime import datetime, timedelta
from fastman.cli import Command, register, Output
from app.core.database import SessionLocal
from app.models.user import User

@register
class PruneUsersCommand(Command):
    """
    Delete users who haven't logged in for X days.
    
    Usage:
        fastman users:prune {--days=30} {--dry-run}
    """
    
    # Signature defines the command name and options
    signature = "users:prune {--days=30} {--dry-run}"
    description = "Delete inactive users"
    
    def handle(self):
        # 1. Parse options
        days = int(self.option("days", "30"))
        dry_run = self.flag("dry-run")
        
        # 2. Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        Output.info(f"Finding users inactive since {cutoff_date.date()}...")
        
        # 3. Database operations
        db = SessionLocal()
        try:
            # Find users
            query = db.query(User).filter(User.last_login < cutoff_date)
            users_to_delete = query.all()
            count = len(users_to_delete)
            
            if count == 0:
                Output.success("No inactive users found.")
                return

            # Display users to be deleted
            rows = [[str(u.id), u.email, str(u.last_login)] for u in users_to_delete]
            Output.table(["ID", "Email", "Last Login"], rows, title="Inactive Users")
            
            # 4. Confirm and Execute
            if dry_run:
                Output.info(f"[DRY RUN] Would delete {count} users.")
                return
            
            if Output.confirm(f"Are you sure you want to delete {count} users?"):
                # Bulk delete for efficiency
                query.delete(synchronize_session=False)
                db.commit()
                Output.success(f"Successfully deleted {count} users.")
            else:
                Output.info("Operation cancelled.")
                
        except Exception as e:
            Output.error(f"An error occurred: {e}")
            db.rollback()
        finally:
            db.close()
```

## Running Your Command

Once you save the file, Fastman automatically discovers it.

```bash
# List commands to see it registered
fastman list

# Run help (if you implemented it, or just run it)
fastman users:prune --days=60 --dry-run
```

## Output Helpers

The `Output` class provides styled output methods to make your CLI tools look professional.

| Method | Description |
|--------|-------------|
| `Output.info("msg")` | Prints blue informational text. |
| `Output.success("msg")` | Prints green success text with a checkmark. |
| `Output.error("msg")` | Prints red error text with an X. |
| `Output.warn("msg")` | Prints yellow warning text. |
| `Output.table(headers, rows)` | Renders a formatted ASCII table. |
| `Output.confirm("msg")` | Prompts the user for Yes/No confirmation. |
| `Output.banner()` | Prints the Fastman banner. |
