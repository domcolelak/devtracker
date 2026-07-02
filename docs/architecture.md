# DevTracker architecture

This document covers the parts of the system that the top-level README only
summarizes: who owns which data, how requests and events flow between services,
how authentication works across framework boundaries, and why the architecture
looks the way it does.

## Service responsibilities

| Service | Framework | Writes | Reads | Never touches |
|---|---|---|---|---|
| core-django | Django 5 + DRF | `common_user`, `teams_team`, `teams_membership`, `projects_project`, `analytics_teamproductivitystats` | its own tables plus `tasks` (read-only, for analytics) | nothing else exists |
| api-fastapi | FastAPI | `tasks` | `projects_project`, `common_user` (read-only existence checks) | Django table writes |
| reports-flask | Flask | nothing | every table listed above (read-only) | any write |

The rule that makes the shared database safe: **every table has exactly one
writing service, and only that service ever migrates it.**

## Migration strategy

Two migration systems coexist against one PostgreSQL schema without conflicts
because their scopes are disjoint:

- **Django migrations** create and evolve everything under core-django's
  ownership. They run automatically on container start
  (`services/core-django/entrypoint.sh`).
- **Alembic** owns exactly one table, `tasks`
  (`services/api-fastapi/migrations/versions/0001_create_tasks_table.py`). It also
  runs on container start, and docker-compose orders it after core-django's
  healthcheck passes, because `tasks` declares real foreign keys into
  `projects_project` and `common_user` which must exist first.

Two implementation details worth calling out, because both were the source of a
real bug during development:

1. In api-fastapi, the read-only reflections of Django's tables
   (`app/models/external.py`) must live in the **same** SQLAlchemy `MetaData` as
   the `Task` model. SQLAlchemy resolves string `ForeignKey` targets through the
   owning table's metadata, and that resolution happens not only for DDL but on
   every ORM flush. A separate `MetaData` produces `NoReferencedTableError` at
   runtime. Keeping them in one metadata is safe because this service's Alembic
   migrations are written by hand and only ever touch `tasks`; autogenerate is
   deliberately not used.
2. In core-django, the mirror in the opposite direction
   (`apps/analytics/models.ExternalTask`) is declared `managed = False`, so Django
   migrations never try to create or alter the `tasks` table, while Celery tasks
   can still use the ORM (including JOINs like `filter(project__team=...)`)
   instead of raw SQL.

## Authentication: one JWT across three frameworks

core-django is the only token issuer. The other services validate tokens locally;
no service ever calls another service to check a token.

```
  CLIENT                core-django               api-fastapi / reports-flask
    |                        |                              |
    |  POST /auth/token/     |                              |
    |  username + password   |                              |
    |------------------------|                              |
    |  access + refresh      |                              |
    |  (HS256, SIGNED WITH   |                              |
    |   JWT_SIGNING_KEY)     |                              |
    |                        |                              |
    |  Authorization: Bearer access                         |
    |-------------------------------------------------------|
    |                        |   VERIFY SIGNATURE LOCALLY   |
    |                        |   WITH THE SAME KEY, CHECK   |
    |                        |   exp AND token_type=access, |
    |                        |   READ user_id CLAIM         |
```

The contract all services agree on:

- Algorithm `HS256`, shared secret `JWT_SIGNING_KEY` (one value in `.env`, injected
  into every container).
- Claims produced by `djangorestframework-simplejwt`: `token_type`, `exp`, `iat`,
  `jti`, `user_id`.
- Consumers accept only `token_type == "access"` and reject expired or foreign
  signatures. There is no per-request user lookup outside Django; possession of a
  validly signed, unexpired access token is the authorization boundary.

Trade-off: symmetric signing means every service could technically mint tokens.
For an internal cluster with one shared secret this is acceptable and simple; the
upgrade path is RS256 (Django holds the private key, other services get the public
key) with no structural changes to any consumer.

## Task write path and real-time notifications

```
  CLIENT               api-fastapi              PostgreSQL        Redis
    |                       |                       |               |
    |  POST /api/tasks      |                       |               |
    |-----------------------|                       |               |
    |                       |  CHECK PROJECT EXISTS |               |
    |                       |  (SELECT ON DJANGO'S  |               |
    |                       |   projects_project)   |               |
    |                       |-----------------------|               |
    |                       |  INSERT INTO tasks    |               |
    |                       |-----------------------|               |
    |                       |  PUBLISH task.created ON task_events  |
    |                       |---------------------------------------|
    |  201 + TASK JSON      |                       |               |
    |                       |                       |               |
    |             EVERY CONNECTED /ws/notifications CLIENT          |
    |             RECEIVES THE EVENT JSON, FANNED OUT VIA           |
    |             REDIS PUB/SUB (WORKS ACROSS REPLICAS)             |
```

Details:

- Project existence is validated with a direct SELECT against the shared database
  rather than an HTTP call to core-django. This is the shared-DB decision paying
  off: no timeout handling, no retry logic, no dependency on Django being up for
  the hot path.
- Events go through Redis pub/sub (channel `task_events`), not an in-process
  list of WebSocket connections. That keeps notifications correct when
  api-fastapi runs more than one replica: whichever replica handles the write,
  every replica's WebSocket clients get the event.
- Browser WebSocket clients cannot set an Authorization header during the
  handshake, so `/ws/notifications` authenticates with a `token` query parameter
  instead. Invalid tokens are rejected with close code 1008.

## Reporting path

reports-flask builds its PDF and CSV outputs from plain SQLAlchemy Core SELECTs
with explicit JOINs across both services' tables (`tasks` joined to
`projects_project`, `common_user`, `teams_team`). Aggregations (task counts,
completion rates per project and per assignee) happen in SQL, and the rows feed
`reportlab` (PDF) or the stdlib `csv` module. The service holds no state and owns
no tables, which is what makes it safe for it to be this small.

## Background processing

Celery worker and beat run as separate containers built from the core-django
image, sharing its settings and ORM models:

| Task | Schedule | What it does |
|---|---|---|
| `recalculate_productivity_stats` | hourly | Counts total and done tasks per team by querying the `tasks` table through the unmanaged `ExternalTask` model, appends a snapshot row to `analytics_teamproductivitystats`. |
| `send_productivity_email_summary` | daily 08:00 UTC | Reads each team's newest snapshot and emails a summary to team owners. The email backend is the console logger (mock SMTP); production would swap `EMAIL_BACKEND` without touching the task. |

Snapshots are append-only and exposed read-only in the Django admin, so the
history of productivity over time is preserved.

## Request routing (Nginx)

| Public prefix | Upstream | Prefix rewritten | Notes |
|---|---|---|---|
| `/admin/`, `/auth/`, `/static/` | core-django:8000 | kept | admin UI, JWT endpoints, static files served by WhiteNoise |
| `/api/` | api-fastapi:8001 | stripped (`/api/tasks` arrives as `/tasks`) | WebSocket upgrade headers set conditionally via a `map`; read timeout raised to one hour so idle notification sockets survive |
| `/reports/` | reports-flask:5000 | stripped | read timeout 120 seconds for large PDF generation |

Rate limiting: 10 requests per second per client IP with a burst of 20, applied
across the whole server block.

## Startup ordering and health

docker-compose encodes the dependency chain with healthchecks rather than sleep
loops:

```
  postgres, redis          FIRST  (pg_isready / redis-cli ping)
  core-django              AFTER postgres AND redis ARE HEALTHY
                           (runs Django migrations, then serves; healthy when
                            /health/ RESPONDS)
  api-fastapi              AFTER core-django IS HEALTHY
                           (runs alembic upgrade head, WHICH NEEDS DJANGO'S
                            TABLES TO EXIST FOR ITS FOREIGN KEYS)
  reports-flask            AFTER postgres IS HEALTHY (READ-ONLY, NEEDS NO DDL)
  celery-worker, beat      AFTER postgres AND redis ARE HEALTHY
  nginx                    AFTER ALL THREE HTTP SERVICES ARE HEALTHY
```

`docker compose up --wait` therefore only returns once the whole stack is
actually usable, which the CI integration job relies on.

## The shared-database trade-off, honestly

What the shared instance with per-service ownership buys:

- Referential integrity across service boundaries (real foreign keys from
  `tasks` into `projects_project` and `common_user`; the database itself
  prevents orphaned tasks).
- JOIN-based reporting without data duplication or an ETL pipeline.
- No inter-service HTTP on hot paths, so fewer failure modes and no
  retry/backoff/idempotency machinery.

What it costs, and why that is acceptable here:

- Services are coupled at the schema level: if core-django renames a column that
  api-fastapi reads, FastAPI breaks. Mitigation: the reflected columns are few,
  stable identifiers (ids, names, slugs, status), and the integration test suite
  exercises the real schema on every CI run.
- The database is a single point of failure and a shared performance domain.
  At this project's scale a single PostgreSQL instance is the right call; the
  escape hatch, if one service outgrows it, is to move that service to its own
  database and replace its cross-service reads with API calls, one seam at a
  time.
- One team could accidentally migrate another team's tables. Mitigation is
  convention enforced by tooling: Alembic autogenerate is not used, Django's
  mirror of `tasks` is unmanaged, and both facts are documented in the code at
  the exact places a future developer would be tempted to change them.
