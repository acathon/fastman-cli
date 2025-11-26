---
sidebar_position: 6
---

# Deployment

Fastman applications are standard FastAPI applications, so they can be deployed anywhere Python is supported.

## Docker

Fastman generates a `Dockerfile` for you when you create a new project.

1.  **Build the image**:
    ```bash
    docker build -t my-app .
    ```

2.  **Run the container**:
    ```bash
    docker run -d -p 8000:8000 my-app
    ```

## Manual Deployment (Gunicorn/Uvicorn)

For production, it is recommended to use Gunicorn with Uvicorn workers.

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## Cloud Providers

### Heroku

1.  Create a `Procfile`:
    ```plaintext
    web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
    ```
2.  Push to Heroku.

### AWS / Google Cloud / Azure

Deploy as a standard Docker container or Python application.
