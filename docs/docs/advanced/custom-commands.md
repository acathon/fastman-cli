---
sidebar_position: 2
---

# Custom Commands

Extend Fastman with your own CLI commands.

## Creating a Command

```bash
fastman make:command send-newsletter
```

This creates a command file that you can register with your application.

## Command Structure

```python
# commands/send_newsletter.py
from fastman.commands.base import Command, register
from fastman.console import Output

@register
class SendNewsletterCommand(Command):
    signature = "newsletter:send {--test}"
    description = "Send newsletter to all subscribers"

    def handle(self):
        test_mode = self.flag("test")
        
        if test_mode:
            Output.info("Running in test mode...")
            recipient = "test@example.com"
        else:
            # Get subscribers from database
            recipient = "all subscribers"
        
        Output.info(f"Sending newsletter to {recipient}...")
        
        # Your logic here
        self._send_emails(test_mode)
        
        Output.success("Newsletter sent successfully!")
    
    def _send_emails(self, test_mode: bool):
        # Implementation
        pass
```

## Signature Syntax

The `signature` attribute defines how your command is called:

```python
# Basic command
signature = "newsletter:send"

# With required argument
signature = "newsletter:send {email}"

# With optional argument (default value)
signature = "newsletter:send {email?}"

# With options (flags)
signature = "newsletter:send {--test} {--limit=}"
```

## Getting Arguments and Options

```python
def handle(self):
    # Get positional argument (index 0)
    email = self.argument(0)
    
    # Get optional argument with default
    limit = self.argument(1, default="10")
    
    # Get named option
    format_type = self.option("format", default="html")
    
    # Check if flag is present
    is_test = self.flag("test")
```

## Output Methods

Fastman provides rich output methods:

```python
from fastman.console import Output

# Messages
Output.success("Operation completed!")
Output.error("Something went wrong")
Output.warn("This might be dangerous")
Output.info("Processing...")

# Interactive
confirmed = Output.confirm("Are you sure?")
name = Output.ask("Enter your name")
choice = Output.choice("Select option", ["A", "B", "C"])

# Progress
with Output.progress(total=100) as progress:
    for i in range(100):
        # do work
        progress.advance()

# Tables
Output.table(
    headers=["ID", "Name", "Email"],
    rows=[
        ["1", "John", "john@example.com"],
        ["2", "Jane", "jane@example.com"],
    ],
    title="Users"
)
```

## Example: Database Backup Command

```python
@register
class BackupCommand(Command):
    signature = "database:backup {--output=}"
    description = "Create a database backup"

    def handle(self):
        output_path = self.option("output", default="backup.sql")
        
        Output.info("Starting database backup...")
        
        with Output.spinner("Creating backup..."):
            self._create_backup(output_path)
        
        Output.success(f"Backup saved to {output_path}")
    
    def _create_backup(self, path: str):
        import subprocess
        subprocess.run([
            "pg_dump", 
            "-h", "localhost",
            "-U", "postgres",
            "-d", "myapp",
            "-f", path
        ], check=True)
```

## Registering Commands

Commands decorated with `@register` are automatically discovered. Make sure your command file is imported in your application.

For project-specific commands, add to your `app/commands/__init__.py`:

```python
from . import send_newsletter
from . import backup
```
