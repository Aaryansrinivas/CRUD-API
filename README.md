# crud API — Postgres in Docker (W3)

A CRUD Task API whose storage moved from an in-memory list to a real Postgres
database running in Docker, with the app and database started together via
`docker compose up`.

## Run it

```bash
cp .env.example .env      # adjust values if you want, defaults work as-is
docker compose up --build
```

Then visit `http://localhost:8000/docs`.

To stop: `Ctrl+C`, then `docker compose down` (add `-v` to also delete the
volume and wipe data — don't do that if you want to keep testing persistence).

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

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| GET | / | API info (shows active storage) | 200 | - |
| GET | /health | Health check | 200 | - |
| GET | /tasks | List tasks (`?done=`, `?search=`) | 200 | - |
| GET | /tasks/{id} | Get one task | 200 | 404 |
| POST | /tasks | Create a task | 201 | 400 |
| PUT | /tasks/{id} | Update a task | 200 | 400, 404 |
| DELETE | /tasks/{id} | Delete a task | 204 | 404 |

## Notes

- The Postgres repository was swapped in without changing `service.py` or
  any route in `main.py` — only `main.py`'s repository-selection line and the
  new `postgres_repository.py` / `db.py` files were added.
- Local (non-Docker) dev: run Postgres via Docker anyway
  (`docker run -e POSTGRES_PASSWORD=taskpass -p 5432:5432 postgres:16`), set
  `DATABASE_URL` to use `localhost` instead of `db`, then `uvicorn app.main:app --reload`.
