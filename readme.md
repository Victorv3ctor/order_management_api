# Order Management API

REST API for a small shop, built to stay correct under concurrent requests, retries and partial failures.

`Python 3.12` · `FastAPI` · `PostgreSQL 16` · `SQLAlchemy 2` · `Alembic` · `Redis 7` · `Docker` · `JWT` · `OAuth2` · `Argon2` · `Pydantic` · `pytest` · `GitHub Actions`
## 1. What is this?

Customers register and place orders\
Admin manages products and order statuses.

| Highlight                | How                                                                                               |
|--------------------------|---------------------------------------------------------------------------------------------------|
| **NO OVERSELLING**       | Stock is reduced by one conditional `UPDATE`; an order is saved fully or not at all               |
| **SAFE STATUS CHANGES**  | Order state machine enforced in SQL, so concurrent requests cannot break it                       |
| **IDEMPOTENT PAYMENTS**  | `Idempotency-Key` header, response cached in Redis for 24 h; still works if Redis is down         |
| **CAREFUL AUTH**         | JWT + Argon2; role read from the database, not the token; same login timing for unknown e-mails   |
| **CLEAN ERROR HANDLING** | Infrastructure errors become domain exceptions, mapped to HTTP codes at the edge                  |
| **LOGGING**              | Infrastructure failures and unexpected errors logged with tracebacks                              |
| **HONEST `/health`**     | Reports PostgreSQL and Redis separately, `503` when either is down                                |
| **LAYERED DESIGN**       | The repository pattern - keeps queries and constraint-error translation out of the business logic |
| **TESTED**               | 35 tests on a real PostgreSQL database, Redis replaced by `fakeredis`; CI on every push           |

**Decisions**

- `require_admin` is only a gate and returns no user, so the app assumes neither one nor several admins; adding more later is cheap
- Customer is the only user model (customer = user), no extra user layer
- No per-exception global handlers: endpoints map domain errors to HTTP codes, one catch-all returns a generic `500` and logs the traceback

**Limitations**

- Cancelling an order does not return stock
- No timeouts configured for PostgreSQL; the Redis client uses 5 s


## 2. Requirements

Python 3.12 and Docker with Docker Compose (PostgreSQL and Redis run as containers). Libraries are pinned in `requirements.txt`.

## 3. Installation

```bash
git clone https://github.com/Victorv3ctor/order_management_api.git
cd order_management_api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # fill in the values
```

## 4. Environment variables
[.env.example](.env.example)


## 5. How to run

```bash
# everything in Docker
docker compose up --build
docker compose exec app alembic upgrade head      # first run: create tables

# or: app locally, database and cache in Docker
docker compose up -d db redis
alembic upgrade head
uvicorn app.main:app --reload
```

API at `http://localhost:8000`, docs at `/docs`. Registration always creates a customer; to get an admin:

```sql
UPDATE customers SET role = 'ADMIN' WHERE email = 'you@example.com';
```

## 6. How to run tests

Tests run against a separate database, so your development data is never touched.

1. Start the database container:

   ```bash
   docker compose up -d db
   ```

2. Create the test database manually (the tests create the tables, but not the database itself):

   ```bash
   docker compose exec db psql -U <user> -c "CREATE DATABASE tests_db;"
   ```

3. Set the test database URL in `.env`:

   ```
   DB_TESTS=postgresql://<user>:<password>@localhost:5433/tests_db
   ```

4. Run the tests:

   ```bash
   pytest
   ```

Tables are created automatically at the start of the test session and dropped at
the end. In CI (`CI=true`) this step is skipped, because the schema comes from
`alembic upgrade head`.
## 7. API overview


| Method | Path                   | Access | Description |
|---|------------------------|---|---|
| GET | `/health`              | public | PostgreSQL and Redis status |
| POST | `/auth/register`       | public | Register a customer |
| POST | `/auth/login`          | public | Get a token |
| GET | `/customers/me`        | customer | Current user |
| GET | `/customers`           | admin | All customers |
| GET | `/products`            | public | Paginated; filter and sort |
| POST | `/products`            | admin | Create a product |
| GET | `/orders`              | customer / admin | Paginated; customers see only their own |
| POST | `/orders`              | customer | Create an order |
| PATCH | `/orders/{id}`         | admin | Change status |
| POST | `/orders/{id}/payment` | customer | Pay, needs `Idempotency-Key` header |

List endpoints require `page` and `page_size` (1-20)