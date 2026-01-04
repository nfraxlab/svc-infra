# Quickstart

> From zero to a running service in 5 minutes.

## 1. Install

```bash
pip install svc-infra
```

With optional database and auth:

```bash
pip install svc-infra[pg]
```

## 2. Create Your App

```python
from svc_infra import easy_service_app

app = easy_service_app(name="MyService")

@app.get("/")
async def root():
    return {"message": "Hello, World!"}
```

## 3. Run It

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000` - your service is running.

---

## 4. Add Authentication

```python
from svc_infra import easy_service_app
from svc_infra.auth import setup_auth, CurrentUser

app = easy_service_app(name="MyService")
setup_auth(app, secret_key="your-secret-key")

@app.get("/me")
async def get_me(user: CurrentUser):
    return {"user_id": user.id, "email": user.email}
```

---

## 5. Add Database

```python
from svc_infra.db import init_db, get_session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)

# In your startup
await init_db(url="sqlite+aiosqlite:///./app.db")
```

---

## 6. Add Caching

```python
from svc_infra.cache import init_cache, cached

# Initialize (in-memory for dev, Redis for prod)
await init_cache(url="memory://")

@cached(ttl=300)  # Cache for 5 minutes
async def get_user_profile(user_id: str):
    return await fetch_from_db(user_id)
```

---

## Complete Example

```python
from svc_infra import easy_service_app
from svc_infra.auth import setup_auth, CurrentUser
from svc_infra.cache import init_cache, cached

app = easy_service_app(name="MyService")
setup_auth(app, secret_key="dev-secret")

@app.on_event("startup")
async def startup():
    await init_cache(url="memory://")

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/me")
async def get_me(user: CurrentUser):
    return {"user_id": user.id}

@cached(ttl=60)
@app.get("/data/{id}")
async def get_data(id: str):
    return {"id": id, "value": "cached"}
```

---

## Next Steps

- [Getting Started](getting-started.md) - Full guide with all features
- [Authentication](auth.md) - JWT, OAuth2, API keys
- [Database](database.md) - PostgreSQL, SQLite, MongoDB
- [Caching](cache.md) - Redis, in-memory caching
- [Jobs](jobs.md) - Background task queues
