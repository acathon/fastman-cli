---
sidebar_position: 1
---

# Introduction

Fastman is a Laravel-inspired CLI tool for FastAPI. It eliminates boilerplate fatigue by generating project structures, handling database migrations, and scaffolding features, models, and middleware instantly.

Whether you prefer Vertical Slice (Feature) architecture or Layered architecture, Fastman sets it up for you in seconds.

## Why Fastman?

FastAPI is amazing, but it leaves architectural decisions up to you. This often leads to:
- Inconsistent project structures
- Manual setup of database and migrations
- Boilerplate code for every new feature
- "Analysis paralysis" when starting new projects

Fastman solves this by providing a **standard, opinionated structure** that scales from simple APIs to enterprise applications.

## Features

- Zero-Dependency Core: Runs with standard library (Rich/Pyfiglet optional for UI).
- Smart Package Detection: Automatically uses `uv`, `poetry`, `pipenv`, or `pip`.
- Multiple Architectures: Supports feature (default), api, and layer patterns.
- Database Ready: First-class support for SQLite, PostgreSQL, MySQL, Oracle, and Firebase.
- Interactive Shell: Includes a `tinker` command to interact with your app context.
- Auth Scaffolding: One-command JWT or Keycloak authentication setup.
- Production Ready: Docker builds, config caching, and optimization tools.
