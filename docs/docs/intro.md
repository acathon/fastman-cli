---
sidebar_position: 1
slug: /
---

# Fastman

**The elegant CLI for FastAPI artisans.**

Fastman is a Laravel-inspired command-line tool that streamlines FastAPI development. Generate projects, scaffold features, manage databases, and deploy with confidence.

```bash
# Create a new project in seconds
fastman new my-api --pattern=feature --database=postgresql
```

## Why Fastman?

FastAPI gives you incredible performance and flexibility—but that flexibility comes with decisions. Every new project means:

- Choosing between architectures
- Setting up database connections and migrations
- Writing repetitive CRUD boilerplate
- Configuring authentication from scratch

**Fastman makes these decisions for you**, providing opinionated defaults that follow best practices while remaining fully customizable.

## Features at a Glance

| Feature | Description |
|---------|-------------|
| 🏗️ **Project Scaffolding** | Create production-ready projects with one command |
| 📐 **Multiple Architectures** | Feature-based, API-based, or layered patterns |
| 🗄️ **Database Ready** | SQLite, PostgreSQL, MySQL, Oracle, Firebase |
| 🔐 **Auth Scaffolding** | JWT, OAuth, or Keycloak in one command |
| 🧪 **Testing Built-in** | Factories, seeders, and test scaffolding |
| 📦 **Smart Package Detection** | Works with uv, poetry, pipenv, or pip |
| 🚀 **Production Tools** | Docker builds, config caching, optimization |

## Quick Start

```bash
# Install with pip
pip install fastman

# Or with uv (recommended)
uv tool install fastman

# Create your first project
fastman new blog-api

# Start the development server
cd blog-api && fastman serve
```

## What's New

### v0.3.0

- **Improved reliability** — Fixed subprocess handling with proper timeouts
- **Safer operations** — Cache clearing and file operations handle errors gracefully  
- **Performance boost** — Cached package manager detection
- **Clean output** — Laravel-style ASCII formatting

---

<div className="row">
  <div className="col col--6">
    <h3>📖 Getting Started</h3>
    <p>New to Fastman? Start here with installation and your first project.</p>
    <a href="/getting-started/installation">Read the Guide →</a>
  </div>
  <div className="col col--6">
    <h3>🎯 Commands Reference</h3>
    <p>Explore all available commands and their options.</p>
    <a href="/commands/project">View Commands →</a>
  </div>
</div>
