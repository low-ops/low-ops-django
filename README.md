# Low-Ops Django Default Template

<p align="left">
  <img src="./images/logo.svg" height="50" width="60" alt="Low-Ops logo" style="background: white; padding: 20px; border-radius: 10px; margin-right: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1)"/>
  <img src="./images/django-logo.svg" height="50" width="60" alt="Django logo" style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1)"/>
</p>

A production-ready Django starter with authentication, admin dashboard, user management, PostgreSQL, and S3-compatible storage. Mirrors the [Low-Ops Next.js template](https://github.com/low-ops/low-ops-nextjs) and follows the [Low-Ops application specification](https://github.com/low-ops/low-ops-application-specification).

## Local development

PostgreSQL and MinIO are required for both local development and production. Start them with Docker Compose:

```bash
docker compose up -d postgres minio minio-init
```

If port `5432` is already in use locally, set `POSTGRES_PUBLISH_PORT=5433` in `.env` and keep `POSTGRES_PORT=5432`.

#### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

#### Run database migrations

```bash
python manage.py migrate
```

#### Seed the database with mock data (optional — also runs automatically on app startup)

```bash
python manage.py seed
```

#### Start development server

```bash
python manage.py runserver 0.0.0.0:8000
```

Default admin after seed: `admin@gmail.com` / `admin`

## Low-Ops application specification

### Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `SECRET_KEY` | yes | — | Django secret (min 32 chars). Generate with `openssl rand -base64 32`. |
| `APPLICATION_URL` | yes | — | Public app URL. |
| `PORT` | no | `8000` | HTTP server port. |
| `METRICS_PORT` | no | `8001` | Prometheus metrics port. |
| `POSTGRES_HOST` | yes | — | PostgreSQL host. |
| `POSTGRES_PORT` | no | `5432` | PostgreSQL port. |
| `POSTGRES_DATABASE` | yes | — | PostgreSQL database name. |
| `POSTGRES_USER` | yes | — | PostgreSQL user. |
| `POSTGRES_PASSWORD` | yes | — | PostgreSQL password. |
| `S3_ENDPOINT` | yes | — | S3 endpoint (protocol optional; `http` for localhost/minio). |
| `S3_BUCKET_NAME` | yes | — | Bucket name, or `bucket/prefix`. |
| `S3_ACCESS_KEY_ID` | yes | — | S3 access key. |
| `S3_SECRET_ACCESS_KEY` | yes | — | S3 secret key. |
| `S3_REGION` | no | `us-east-1` | S3 region. |
| `S3_PUBLIC_BASE_URL` | no | `S3_ENDPOINT` | Public URL for browser-accessible file links. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | no | — | OpenTelemetry collector endpoint. |
| `OTEL_SERVICE_NAME` | no | — | OpenTelemetry service name (required with OTEL endpoint). |
| `RESEND_API_KEY` | no | — | Enables email verification when set. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | no | — | Google OAuth (optional). |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | no | — | GitHub OAuth (optional). |

Django-only (not part of the spec):

| Variable | Default | Description |
| --- | --- | --- |
| `DEBUG` | `true` | Django debug mode (local dev). |
| `ALLOW_PUBLIC_SIGN_UP` | `false` | Allow public sign-up page and API. |

See `.env.example` for a full local template.

### Platform endpoints

| Endpoint | Port | Description |
| --- | --- | --- |
| `GET /ready` | `PORT` | Readiness probe. Returns `{ status, checks: { postgres, s3 } }`. |
| `GET /metrics` | `METRICS_PORT` | Prometheus metrics. |

### API endpoints

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/auth/sign-in/` | Sign in |
| `POST` | `/api/auth/sign-up/` | Sign up |
| `POST` | `/api/auth/sign-out/` | Sign out |
| `GET` | `/api/auth/session/` | Current session |
| `POST` | `/api/auth/verify-email/` | Verify email |
| `POST` | `/api/auth/revoke-sessions/{userId}/` | Revoke sessions |
| `PATCH` | `/api/user/profile/` | Update profile |
| `POST` | `/api/user/avatar/` | Upload avatar |
| `GET` | `/api/user/avatar/{userId}/` | Serve avatar |
| `GET` | `/api/admin/users/` | List users (admin) |
| `POST` | `/api/admin/users/create/` | Create user (admin) |
| `POST` | `/api/admin/users/{userId}/ban/` | Ban user (admin) |
| `POST` | `/api/admin/users/{userId}/unban/` | Unban user (admin) |
| `POST` | `/api/admin/users/{userId}/role/` | Set role (admin) |
| `DELETE` | `/api/admin/users/{userId}/` | Delete user (admin) |
| `POST` | `/api/admin/users/{userId}/revoke-sessions/` | Revoke sessions (admin) |

OpenAPI schema: `/api/schema/`, Swagger UI: `/api/docs/`

## Features

- Email & password sign-in and sign-up
- Email verification (optional, via `RESEND_API_KEY`)
- Session management with secure cookies
- Role-based access control (Admin, User)
- Admin dashboard: user list, ban/unban, role assignment, session revocation
- User settings: profile name and avatar upload
- S3-compatible avatar storage with authenticated proxy
- Prometheus metrics and OpenTelemetry support

## Docker

Start dependencies only (local dev):

```bash
docker compose up -d postgres minio minio-init
```

Run the full stack (app + dependencies):

```bash
docker compose --profile app up --build
```
