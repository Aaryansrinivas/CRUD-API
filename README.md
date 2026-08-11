# crud API — Postgres in Docker + Supabase Auth (W2 A4)

A CRUD Task API whose storage moved from an in-memory list to a real Postgres
database running in Docker, and now has real user authentication on top:
sign up, log in, log out, and protected routes guarded by a Supabase-issued
JSON Web Token (JWT).

We never hash a password or verify a token signature ourselves — Supabase
(the Identity Provider) does that. Our server's job is to hand credentials to
Supabase, and to verify the JWT it hands back.

## Setup

1. Create a free project at [supabase.com](https://supabase.com) (no card).
2. In the Supabase Dashboard, go to **Project Settings → API** and copy your
   **Project URL** and **anon key** (never the `service_role` key here).
3. In **Authentication → Sign In / Providers → Email**, turn **Confirm email**
   off, so a fresh signup can log in immediately in this dev project.
4. Copy the env template and fill in your Supabase values:

```bash
cp .env.example .env
```

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key
```

## Run it

```bash
docker compose up --build
```

Then visit `http://localhost:8000/docs`. Click **Authorize**, paste an
`access_token` from `/auth/login`, and try the protected routes right from
the browser.

To stop: `Ctrl+C`, then `docker compose down` (add `-v` to also delete the
volume and wipe data — don't do that if you want to keep testing persistence).

### Local (non-Docker) dev

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Auth flow

| Step | Who does it | What happens |
|---|---|---|
| 1. Sign up / log in | Client → Supabase | Client sends email + password to Supabase via our `/auth/signup` or `/auth/login` route. |
| 2. The token | Supabase → Client | Supabase checks the credentials and returns a JWT (access token) + refresh token. |
| 3. The request | Client → server | Client calls a protected route with `Authorization: Bearer <token>`. |
| 4. Verification | Server → Supabase | Our `get_current_user` dependency asks Supabase "is this token real?" via `auth.get_user(token)`. If yes, the route runs. |

`app/auth.py` holds the Supabase client and the `get_current_user` dependency
— the one reusable guard. `app/auth_routes.py` holds the auth/profile routes.
`app/main.py` just plugs the guard into any route with
`Depends(get_current_user)`; `/protected/profile` and `/protected/dashboard`
both use it, with zero duplicated auth code.

### Try it with curl

```bash
# Sign up
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Log in — copy the access_token from the response
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Call a protected route
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN>"

# Tamper with the token -> 401
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN>x"

# Log out (protected)
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN>"
```

## Architecture — why swapping storage only touched one file

```
routes (main.py)  ->  service (service.py)  ->  repository interface (repository.py)
                                                        |
                                        InMemoryTaskRepository   PostgresTaskRepository
```

- `repository.py` defines the contract: `list`, `get`, `create`, `update`, `delete`.
- `memory_repository.py` and `postgres_repository.py` both implement that exact
  contract.
- `service.py` (business rules: title required, etc.) only ever calls methods
  on the interface — it has no idea whether rows live in a Python list or a
  Postgres table.
- `main.py` (HTTP routes) only ever calls the service.

**The only line that changes between memory and Postgres** is in `main.py`:

```python
REPO_TYPE = os.environ.get("REPO_TYPE", "postgres")
repository = PostgresTaskRepository() if REPO_TYPE == "postgres" else InMemoryTaskRepository()
```

Flip `REPO_TYPE=memory` in `.env` and every route, every validation rule, and
every status code behaves identically — proof that the layering does what
it's supposed to.

## Environment variables

`.env` is gitignored; `.env.example` is committed as the template.

| Variable | Meaning |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credentials Postgres itself uses to init |
| `DATABASE_URL` | Full connection string the app uses; host is `db` (the compose service name), not `localhost` |
| `REPO_TYPE` | `postgres` (default) or `memory` |

## Database

`sql/init.sql` creates the `tasks` table and seeds 3 rows. It's mounted into
Postgres's `/docker-entrypoint-initdb.d/`, which Postgres's official image runs
automatically **only the first time** a container starts against an empty
data volume. If you edit `init.sql` later, you must `docker compose down -v`
(drops the volume) to see the change take effect.

## Proving persistence

1. `docker compose up --build`
2. Create a task: `curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Survive a restart"}'`
3. Confirm it's there: `curl http://localhost:8000/tasks`
4. Restart everything: `docker compose down` then `docker compose up` (no `-v` — the volume is untouched)
5. `curl http://localhost:8000/tasks` again — the task from step 2 is still there.

This works because `pgdata` is a **named Docker volume**: it lives outside the
container's writable layer, on the host, and survives the container being
stopped, removed, and recreated. Only `docker compose down -v` (or deleting
the volume directly) erases it — which is exactly the boundary between "the
container restarted" and "I actually asked to wipe my data."

## Endpoints

| Method | Path | Description | Auth required | Success | Errors |
|---|---|---|---|---|---|
| GET | / | API info (shows active storage) | no | 200 | - |
| GET | /health | Health check | no | 200 | - |
| GET | /tasks | List tasks (`?done=`, `?search=`) | no | 200 | - |
| GET | /tasks/{id} | Get one task | no | 200 | 404 |
| POST | /tasks | Create a task | no | 201 | 400 |
| PUT | /tasks/{id} | Update a task | no | 200 | 400, 404 |
| DELETE | /tasks/{id} | Delete a task | no | 204 | 404 |
| POST | /auth/signup | Create a new user account | no | 201 | 400 |
| POST | /auth/login | Authenticate, return a JWT | no | 200 | 400, 401 |
| POST | /auth/logout | End the user's session | **yes (bearer)** | 204 | 401 |
| GET | /public/info | Public, open data | no | 200 | - |
| GET | /protected/profile | Read the logged-in user's profile | **yes (bearer)** | 200 | 401 |
| GET | /protected/dashboard | Second protected route (proves middleware reuse) | **yes (bearer)** | 200 | 401 |

## Notes

- The Postgres repository was swapped in without changing `service.py` or
  any route in `main.py` — only `main.py`'s repository-selection line and the
  new `postgres_repository.py` / `db.py` files were added.
- Local (non-Docker) dev: run Postgres via Docker anyway
  (`docker run -e POSTGRES_PASSWORD=taskpass -p 5432:5432 postgres:16`), set
  `DATABASE_URL` to use `localhost` instead of `db`, then `uvicorn app.main:app --reload`.
