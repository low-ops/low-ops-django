# Low-Ops Django Default Template

<p align="left">
  <img src="./images/lowops-logo.svg" height="50" width="60" alt="Low-Ops logo" style="background: white; padding: 20px; border-radius: 10px; margin-right: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1)"/>
  <img src="./images/django-logo.svg" height="50" width="60" alt="Django logo" style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1)"/>
</p>

A production-ready Django starter with authentication, admin dashboard, user management, PostgreSQL, and S3-compatible storage.

## Local development

PostgreSQL and MinIO are required for both local development and production. Start them with Docker Compose:

```bash
docker compose up -d postgres minio minio-init
```

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

#### Start development server

```bash
python manage.py runserver 0.0.0.0:8000
```

### API endpoints

| Method   | Path                                          | Description             |
| -------- | --------------------------------------------- | ----------------------- |
| `POST`   | `/api/auth/sign-in/`                          | Sign in                 |
| `POST`   | `/api/auth/sign-up/`                          | Sign up                 |
| `POST`   | `/api/auth/sign-out/`                         | Sign out                |
| `GET`    | `/api/auth/session/`                          | Current session         |
| `POST`   | `/api/auth/verify-email/`                     | Verify email            |
| `POST`   | `/api/auth/revoke-sessions/{user_id}/`        | Revoke sessions         |
| `PATCH`  | `/api/user/profile/`                          | Update profile          |
| `POST`   | `/api/user/avatar/`                           | Upload avatar           |
| `GET`    | `/api/user/avatar/{user_id}/`                 | Serve avatar            |
| `GET`    | `/api/admin/users/`                           | List users (admin)      |
| `POST`   | `/api/admin/users/create/`                    | Create user (admin)     |
| `POST`   | `/api/admin/users/{user_id}/ban/`             | Ban user (admin)        |
| `POST`   | `/api/admin/users/{user_id}/unban/`           | Unban user (admin)      |
| `POST`   | `/api/admin/users/{user_id}/role/`            | Set role (admin)        |
| `DELETE` | `/api/admin/users/{user_id}/`                 | Delete user (admin)     |
| `POST`   | `/api/admin/users/{user_id}/revoke-sessions/` | Revoke sessions (admin) |

OpenAPI schema: `/api/schema/`, Swagger UI: `/api/docs/`

### Behavior notes

- Sign-up is open only until the first user exists. That user is created as **admin**; further sign-ups return **403**.
- After `migrate`, visit `/auth/sign-up/` locally to create the first admin account.
- `/api/schema/` and `/api/docs/` are public when `DEBUG=true`; in production they require an admin session.
- `/metrics` requires `METRICS_AUTH_TOKEN` when `DEBUG=false` (`Authorization: Bearer <token>` or `?token=`).

### Environment variables

| Variable                                    | Required | Default     | Description                                                              |
| ------------------------------------------- | -------- | ----------- | ------------------------------------------------------------------------ |
| `APPLICATION_URL`                           | yes      | —           | Public app URL. (✅ Available in Low-Ops)                                |
| `POSTGRES_HOST`                             | yes      | —           | PostgreSQL host. (✅ Available in Low-Ops)                               |
| `POSTGRES_PORT`                             | no       | `5432`      | PostgreSQL port. (✅ Available in Low-Ops)                               |
| `POSTGRES_DATABASE`                         | yes      | —           | PostgreSQL database name. (✅ Available in Low-Ops)                      |
| `POSTGRES_USER`                             | yes      | —           | PostgreSQL user. (✅ Available in Low-Ops)                               |
| `POSTGRES_PASSWORD`                         | yes      | —           | PostgreSQL password. (✅ Available in Low-Ops)                           |
| `S3_ENDPOINT`                               | yes      | —           | S3 endpoint. (✅ Available in Low-Ops)                                   |
| `S3_BUCKET_NAME`                            | yes      | —           | Bucket name. (✅ Available in Low-Ops)                                   |
| `S3_ACCESS_KEY_ID`                          | yes      | —           | S3 access key. (✅ Available in Low-Ops)                                 |
| `S3_SECRET_ACCESS_KEY`                      | yes      | —           | S3 secret key. (✅ Available in Low-Ops)                                 |
| `S3_REGION`                                 | no       | `us-east-1` | S3 region. (✅ Available in Low-Ops)                                     |
| `S3_PUBLIC_BASE_URL`                        | no       | —           | Public URL for browser-accessible file links. (✅ Available in Low-Ops)  |
| `OTEL_EXPORTER_OTLP_ENDPOINT`               | no       | —           | OpenTelemetry collector endpoint. (✅ Available in Low-Ops)              |
| `OTEL_SERVICE_NAME`                         | no       | —           | OpenTelemetry service name. (✅ Available in Low-Ops)                    |
| `RESEND_API_KEY`                            | no       | —           | Enables email verification when set (optional).                          |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | no       | —           | To use Google as sign-in provider (optional).                            |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | no       | —           | To use GitHub as sign-in provider (optional).                            |
| `SECRET_KEY`                                | yes      | —           | Django signing key. Auto-derived from DB config if unset.                |
| `DEBUG`                                     | no       | false       | Whether to enable debug mode.                                            |
| `PORT`                                      | no       | `8000`      | HTTP server port.                                                        |
| `METRICS_PORT`                              | no       | `8001`      | Prometheus metrics port.                                                 |
| `METRICS_BIND_HOST`                         | no       | `127.0.0.1` | Host interface for the metrics server.                                   |
| `METRICS_AUTH_TOKEN`                        | prod     | —           | Bearer token for `/metrics` when `DEBUG=false`.                          |
| `ALLOWED_HOSTS`                             | prod     | —           | Extra comma-separated hostnames; `APPLICATION_URL` hostname is included. |
| `MAX_LOGIN_ATTEMPTS`                        | no       | `5`         | Failed sign-in attempts before lockout.                                  |
| `LOGIN_LOCKOUT_MINUTES`                     | no       | `15`        | Lockout duration after too many failed sign-ins.                         |
| `SECURE_SSL_REDIRECT`                       | no       | `true`      | Redirect HTTP to HTTPS when `DEBUG=false`.                               |
| `DB_CONN_MAX_AGE`                           | no       | `600`       | PostgreSQL connection pool age in seconds.                               |

See `.env.example` for a full local template.

### Platform endpoints

| Endpoint       | Port           | Description                                                           |
| -------------- | -------------- | --------------------------------------------------------------------- |
| `GET /ready`   | `PORT`         | Readiness probe. Returns `{ status, checks: { postgres, s3 } }`.      |
| `GET /metrics` | `METRICS_PORT` | Prometheus metrics. Requires `METRICS_AUTH_TOKEN` when `DEBUG=false`. |
