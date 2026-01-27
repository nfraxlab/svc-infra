# svc-infra Development Roadmap

> **Current Version**: 1.1.0
> **Target v1.0.0**: Phase 0 completion (Email Infrastructure)
> **Target v2.0.0**: Phase 1-4 completion

---

## Phase 0: Email Infrastructure Module (v1.0.x)

**Goal**: Create a first-class email module following the same DX patterns as `storage`, `webhooks`, and other svc-infra capabilities. Unified API across multiple providers with zero-config setup.

**Current State**:
- Email exists but is buried in `api/fastapi/auth/sender.py`
- SMTP only, no modern providers
- Tightly coupled to auth settings
- Not exposed in public API
- Synchronous (blocking)

**Target State**:
- Top-level `svc_infra.email` module
- Multiple backend support (Console, SMTP, Resend, SendGrid, AWS SES, Postmark)
- Unified `send()` API across all providers
- Async-first with sync fallback
- Template support (Jinja2)
- `add_email(app)` / `easy_email()` / `get_email()` pattern
- Auth module migrated to use new email infrastructure

---

### 0.1 Core Email Infrastructure

> Create the foundational email module structure.

**Files to create:**
- `src/svc_infra/email/__init__.py`
- `src/svc_infra/email/base.py`
- `src/svc_infra/email/settings.py`
- `src/svc_infra/email/add.py`
- `src/svc_infra/email/easy.py`

- [x] **base.py - Email Backend Protocol**
  - [x] `EmailBackend` protocol with `send()` and `send_sync()` methods
  - [x] `EmailMessage` dataclass: `to`, `subject`, `html`, `text`, `from_addr`, `reply_to`, `cc`, `bcc`, `attachments`, `headers`, `tags`
  - [x] `EmailResult` dataclass: `message_id`, `provider`, `status`, `error`
  - [x] `EmailError` base exception with subclasses: `ConfigurationError`, `DeliveryError`, `RateLimitError`, `InvalidRecipientError`

- [x] **settings.py - Email Configuration**
  - [x] `EmailSettings(BaseSettings)` with `EMAIL_*` env prefix
  - [x] `EMAIL_BACKEND`: console, smtp, resend, sendgrid, ses, postmark
  - [x] `EMAIL_FROM`: default sender address
  - [x] `EMAIL_REPLY_TO`: optional default reply-to
  - [x] Provider-specific settings (lazy-loaded based on backend)

- [x] **add.py - FastAPI Integration**
  - [x] `add_email(app, backend=None)` - add email to FastAPI app state
  - [x] `get_email() -> EmailBackend` - FastAPI dependency
  - [x] `health_check_email()` - health check probe
  - [x] Lifespan integration for async backends

- [x] **easy.py - Zero-Config Setup**
  - [x] `easy_email(backend=None, **kwargs)` - auto-detect from env
  - [x] Auto-detect provider from available env vars
  - [x] Sensible defaults (console in dev, warning in prod if not configured)

- [x] **__init__.py - Public API**
  - [x] Export: `add_email`, `easy_email`, `get_email`, `EmailBackend`, `EmailMessage`, `EmailResult`, `EmailSettings`, `EmailError`

**Bonus (completed early):**
- [x] `backends/__init__.py` - Backend module structure
- [x] `backends/console.py` - Console backend for development

---

### 0.2 Console & SMTP Backends

> Built-in backends that require no external dependencies.

**Files to create:**
- `src/svc_infra/email/backends/__init__.py`
- `src/svc_infra/email/backends/console.py`
- `src/svc_infra/email/backends/smtp.py`

- [x] **console.py - Development Backend**
  - [x] `ConsoleBackend` - prints emails to stdout/logger
  - [x] Pretty-print with sender, recipient, subject, truncated body
  - [x] Configurable log level
  - [x] Always returns success

- [x] **smtp.py - Standard SMTP Backend**
  - [x] `SMTPBackend` - async SMTP via `aiosmtplib`
  - [x] Settings: `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_USERNAME`, `EMAIL_SMTP_PASSWORD`, `EMAIL_SMTP_USE_TLS`
  - [x] Connection pooling for high-volume (via aiosmtplib)
  - [x] Sync fallback via `smtplib`
  - [x] StartTLS and SSL/TLS support

---

### 0.3 Modern Provider Backends

> Integration with modern transactional email providers.

**Files to create:**
- `src/svc_infra/email/backends/resend.py`
- `src/svc_infra/email/backends/sendgrid.py`
- `src/svc_infra/email/backends/ses.py`
- `src/svc_infra/email/backends/postmark.py`

- [x] **resend.py - Resend Backend**
  - [x] `ResendBackend` using httpx (no SDK dependency)
  - [x] Settings: `EMAIL_RESEND_API_KEY`
  - [x] Async HTTP via httpx
  - [x] Tag and metadata support
  - [x] Attachment support with base64 encoding

- [x] **sendgrid.py - SendGrid Backend**
  - [x] `SendGridBackend` using httpx (no SDK dependency)
  - [x] Settings: `EMAIL_SENDGRID_API_KEY`
  - [x] Dynamic template support via `send_template()`
  - [x] Category and custom args
  - [x] Sandbox mode for testing

- [x] **ses.py - AWS SES Backend**
  - [x] `SESBackend` using boto3/aioboto3
  - [x] Settings: `EMAIL_SES_REGION`, `EMAIL_SES_ACCESS_KEY`, `EMAIL_SES_SECRET_KEY`
  - [x] Falls back to default AWS credentials chain
  - [x] Configuration set support
  - [x] Raw MIME email support for attachments

- [x] **postmark.py - Postmark Backend**
  - [x] `PostmarkBackend` using httpx
  - [x] Settings: `EMAIL_POSTMARK_API_TOKEN`, `EMAIL_POSTMARK_MESSAGE_STREAM`
  - [x] Template support via `send_template()`
  - [x] Track opens/clicks configuration

---

### 0.4 Template System

> Built-in email templating with Jinja2.

**Files to create:**
- `src/svc_infra/email/templates/__init__.py`
- `src/svc_infra/email/templates/loader.py`
- `src/svc_infra/email/templates/base.html`

- [x] **loader.py - Template Engine**
  - [x] `EmailTemplateLoader` class
  - [x] Load templates from package resources or custom path
  - [x] `render(template_name, **context) -> tuple[str, str]` returns (html, text)
  - [x] Auto-generate text from HTML if not provided
  - [x] Base template with unsubscribe footer, branding

- [x] **Built-in Templates**
  - [x] `base.html` - responsive email base layout
  - [x] `verification.html` - email verification
  - [x] `password_reset.html` - password reset
  - [x] `invitation.html` - workspace/team invitation
  - [x] `welcome.html` - welcome email

---

### 0.5 High-Level Send API

> Unified send method that works across all backends.

**Files created:**
- `src/svc_infra/email/sender.py` - EmailSender class with high-level API

**Files updated:**
- `src/svc_infra/email/__init__.py` - exports EmailSender, easy_sender, add_sender, get_sender
- `src/svc_infra/email/easy.py` - added easy_sender() function
- `src/svc_infra/email/add.py` - added add_sender() and get_sender() for FastAPI

- [x] **Unified send() method**
  ```python
  async def send(
      to: str | list[str],
      subject: str,
      *,
      html: str | None = None,
      text: str | None = None,
      template: str | None = None,
      context: dict | None = None,
      from_addr: str | None = None,
      reply_to: str | None = None,
      cc: list[str] | None = None,
      bcc: list[str] | None = None,
      attachments: list[Attachment] | None = None,
      tags: list[str] | None = None,
      metadata: dict | None = None,
  ) -> EmailResult:
  ```
  - [x] Validate recipient addresses
  - [x] Load template if specified
  - [x] Fall back to settings for from_addr
  - [x] Return consistent `EmailResult`

- [x] **Convenience Methods**
  - [x] `send_verification(to, code, verification_url, user_name)` - uses verification template
  - [x] `send_password_reset(to, reset_url, user_name)` - uses password_reset template
  - [x] `send_invitation(to, invitation_url, inviter_name, workspace_name, role)` - uses invitation template
  - [x] `send_welcome(to, user_name, features)` - uses welcome template

---

### 0.6 Auth Module Migration

> Migrate existing auth sender to use new email infrastructure.

**Files updated:**
- `src/svc_infra/api/fastapi/auth/sender.py` - Now wraps new email module
- `tests/unit/api/fastapi/auth/test_sender_coverage.py` - Updated tests

**Note:** `users.py` and `mfa/router.py` require no changes - they use the same
`get_sender().send()` interface which is now backed by the new email infrastructure.

- [x] **Replace old sender.py**
  - [x] Update `sender.py` to use new `svc_infra.email` module via `_EmailSenderAdapter`
  - [x] Keep `Sender` protocol for backward compatibility
  - [x] Keep `SMTPSender` and `ConsoleSender` classes for legacy usage

- [x] **Update auth consumers**
  - [x] `users.py`: No changes needed - same interface
  - [x] `mfa/router.py`: No changes needed - same interface
  - [x] Support both `AUTH_SMTP_*` and `EMAIL_*` env vars via `_sync_auth_env_to_email_env()`

---

### 0.7 Testing & Documentation ✅

> Comprehensive tests and documentation.

**Files created:**
- `tests/unit/email/test_email_backends.py` ✅
- `tests/unit/email/test_email_templates.py` ✅
- `tests/unit/email/test_email_send.py` ✅
- `tests/unit/email/test_email_integration.py` ✅
- `docs/email.md` ✅

- [x] **Unit Tests**
  - [x] Test ConsoleBackend output format
  - [x] Test SMTPBackend connection and send
  - [x] Test each provider backend with mocked responses
  - [x] Test template rendering
  - [x] Test email validation
  - [x] Test error handling

- [x] **Integration Tests**
  - [x] Test `add_email()` FastAPI integration
  - [x] Test `get_email()` dependency injection
  - [x] Test health check endpoint

- [x] **Documentation**
  - [x] Quick start guide
  - [x] Provider configuration reference
  - [x] Template customization guide
  - [x] Migration guide from old sender

---

### 0.8 Examples ✅

> Working examples for common use cases.

**Files created:**
- `examples/email/basic_send.py` ✅
- `examples/email/with_templates.py` ✅
- `examples/email/fastapi_integration.py` ✅
- `examples/email/README.md` ✅

- [x] **basic_send.py** - Simple HTML email sending with auto-detection
- [x] **with_templates.py** - Template-based emails (verification, password reset, invitation, welcome)
- [x] **fastapi_integration.py** - Full FastAPI app with health check, auth endpoints, team invitations

---

### Phase 0 Success Criteria ✅

| Deliverable | Status |
|-------------|--------|
| `svc_infra.email` module created | [x] |
| Console + SMTP backends | [x] |
| Resend backend | [x] |
| SendGrid backend | [x] |
| AWS SES backend | [x] |
| Postmark backend | [x] |
| Template system | [x] |
| Unified `send()` API | [x] |
| Auth module migrated | [x] |
| Tests (>80% coverage for email module) | [x] |
| Documentation complete | [x] |
| Examples working | [x] |

---

### Environment Variables Reference

```bash
# Backend selection (auto-detected if not set)
EMAIL_BACKEND=resend  # console, smtp, resend, sendgrid, ses, postmark

# Common settings
EMAIL_FROM=noreply@example.com
EMAIL_REPLY_TO=support@example.com

# SMTP
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=user@gmail.com
EMAIL_SMTP_PASSWORD=app-password
EMAIL_SMTP_USE_TLS=true

# Resend
EMAIL_RESEND_API_KEY=re_xxxxx

# SendGrid
EMAIL_SENDGRID_API_KEY=SG.xxxxx

# AWS SES
EMAIL_SES_REGION=us-east-1
EMAIL_SES_ACCESS_KEY=AKIA...
EMAIL_SES_SECRET_KEY=xxxxx

# Postmark
EMAIL_POSTMARK_API_TOKEN=xxxxx
EMAIL_POSTMARK_MESSAGE_STREAM=outbound

# Templates
EMAIL_TEMPLATES_PATH=/app/templates/email  # Optional custom path
```

---

## Overview

This roadmap outlines the path from current state to v1.0.0 (production-ready release) and v2.0.0 (feature-complete platform). Each phase is designed to be independently shippable.

### Current State Summary

**Fully Implemented:**
- [OK] Auth (JWT, sessions, OAuth/OIDC, MFA, API keys, lockout)
- [OK] Database (PostgreSQL, MongoDB, migrations, repositories, multi-tenancy)
- [OK] Jobs (Redis/memory queue, retries, DLQ, scheduling)
- [OK] Cache (Redis/memory, decorators, namespacing)
- [OK] Webhooks (outbox pattern, HMAC signing, delivery retries)
- [OK] Billing (usage tracking, metering, invoices, subscriptions)
- [OK] Storage (S3, local, memory backends, signed URLs)
- [OK] Observability (Prometheus, OTEL, Grafana dashboards, health probes)
- [OK] Security (CORS, CSP, HIBP, lockout, rate limiting)
- [OK] Multi-tenancy (soft-tenant isolation, automatic scoping)
- [OK] Admin Operations (impersonation, role-gated routes)
- [OK] Resilience (retries, circuit breakers, timeouts)
- [OK] Idempotency (request deduplication)
- [OK] SDK Generation (TypeScript, Python, Postman)
- [OK] WebSocket (real-time, Redis pub/sub scaling)
- [OK] Data Lifecycle (backup, retention, GDPR erasure)

---

## Phase 1: Admin Dashboard UI

**Goal**: Provide a framework-agnostic admin dashboard for managing svc-infra resources.

### 1.1 Architecture Design

> Design an admin UI that works with FastAPI, Django, Litestar, and potentially standalone.

- [ ] **Define admin dashboard scope**
 - [ ] User management (CRUD, search, sessions)
 - [ ] Tenant management (list, switch, usage)
 - [ ] Billing dashboard (usage graphs, invoices)
 - [ ] Job queue monitoring (pending, failed, DLQ)
 - [ ] Webhook delivery status (success rate, retries)
 - [ ] Cache management (stats, invalidation)
 - [ ] Health/metrics overview

- [ ] **Choose UI approach**
 - [ ] Option A: Server-rendered (HTMX + Tailwind) - recommended
 - [ ] Option B: Standalone SPA (talks to API)
 - [ ] Option C: Embeddable components
 - [ ] Document decision in ADR

- [ ] **Design API endpoints**
 - [ ] `GET /admin/api/users` - List users with pagination
 - [ ] `GET /admin/api/users/{id}` - User details
 - [ ] `GET /admin/api/tenants` - List tenants
 - [ ] `GET /admin/api/billing/usage` - Usage stats
 - [ ] `GET /admin/api/jobs/status` - Queue status
 - [ ] `GET /admin/api/webhooks/stats` - Delivery stats
 - [ ] `GET /admin/api/health` - Health overview

### 1.2 Create Admin Module Structure

> Build the `admin/` module following existing patterns.

- [ ] **Create directory structure**
 ```
 src/svc_infra/admin/
 ├── __init__.py
 ├── add.py # add_admin_dashboard()
 ├── settings.py # AdminSettings
 ├── router.py # Admin API routes
 ├── templates/ # HTMX templates (if server-rendered)
 │ ├── base.html
 │ ├── dashboard.html
 │ ├── users/
 │ ├── tenants/
 │ ├── billing/
 │ ├── jobs/
 │ └── webhooks/
 ├── static/ # CSS, JS assets
 │ ├── admin.css
 │ └── htmx.min.js
 └── services/
 ├── user_service.py
 ├── tenant_service.py
 ├── billing_service.py
 ├── job_service.py
 └── webhook_service.py
 ```

- [ ] **Create `admin/__init__.py`**
 - [ ] Export `add_admin_dashboard`
 - [ ] Export `AdminSettings`
 - [ ] Add module docstring

- [ ] **Create `admin/settings.py`**
 - [ ] `ADMIN_ENABLED` - Enable/disable admin
 - [ ] `ADMIN_BASE_PATH` - Mount path (default: `/_admin`)
 - [ ] `ADMIN_REQUIRE_SUPERUSER` - Require superuser role
 - [ ] `ADMIN_THEME` - Light/dark theme
 - [ ] `ADMIN_LOGO_URL` - Custom logo
 - [ ] `ADMIN_TITLE` - Dashboard title

- [ ] **Create `admin/add.py`**
 - [ ] Follow `add_*` pattern
 - [ ] Mount admin routes
 - [ ] Add static file serving
 - [ ] Register admin services

### 1.3 Implement Admin Services

> Create service layer for admin operations.

- [ ] **Create `admin/services/user_service.py`**
 - [ ] `list_users(page, per_page, search)` - Paginated user list
 - [ ] `get_user(user_id)` - User details with sessions
 - [ ] `update_user(user_id, data)` - Update user fields
 - [ ] `delete_user(user_id)` - Soft delete
 - [ ] `list_sessions(user_id)` - Active sessions
 - [ ] `revoke_session(session_id)` - Revoke session

- [ ] **Create `admin/services/tenant_service.py`**
 - [ ] `list_tenants(page, per_page, search)` - Tenant list
 - [ ] `get_tenant(tenant_id)` - Tenant details
 - [ ] `get_tenant_usage(tenant_id)` - Usage summary
 - [ ] `get_tenant_users(tenant_id)` - Users in tenant

- [ ] **Create `admin/services/billing_service.py`**
 - [ ] `get_usage_summary(tenant_id, period)` - Usage stats
 - [ ] `list_invoices(tenant_id, page)` - Invoice list
 - [ ] `get_invoice(invoice_id)` - Invoice details
 - [ ] `get_subscription(tenant_id)` - Current plan

- [ ] **Create `admin/services/job_service.py`**
 - [ ] `get_queue_status()` - Pending/processing/failed counts
 - [ ] `list_failed_jobs(page)` - Failed job list
 - [ ] `retry_job(job_id)` - Retry single job
 - [ ] `retry_all_failed()` - Retry all failed
 - [ ] `purge_dlq()` - Clear dead letter queue

- [ ] **Create `admin/services/webhook_service.py`**
 - [ ] `get_delivery_stats()` - Success/failure rates
 - [ ] `list_subscriptions(tenant_id)` - Webhook subscriptions
 - [ ] `list_deliveries(subscription_id, status)` - Delivery log
 - [ ] `retry_delivery(delivery_id)` - Retry delivery

### 1.4 Implement Admin API Routes

> Create FastAPI routes for admin operations.

- [ ] **Create `admin/router.py`**
 - [ ] Mount under `/_admin/api`
 - [ ] Apply admin role guard
 - [ ] Implement all endpoints from 1.1

- [ ] **Add pagination support**
 - [ ] Use existing `svc_infra.api.fastapi.pagination` module
 - [ ] Consistent page/per_page/cursor pattern

- [ ] **Add search support**
 - [ ] Filter parameters for list endpoints
 - [ ] Full-text search where applicable

### 1.5 Implement Admin UI (HTMX)

> Build server-rendered templates with HTMX for interactivity.

- [ ] **Create base template**
 - [ ] Sidebar navigation
 - [ ] Header with user info
 - [ ] Dark/light mode toggle
 - [ ] Responsive layout

- [ ] **Create dashboard page**
 - [ ] Quick stats (users, tenants, jobs, webhooks)
 - [ ] Recent activity feed
 - [ ] Health status indicators

- [ ] **Create users pages**
 - [ ] User list with search/filter
 - [ ] User detail/edit form
 - [ ] Session management
 - [ ] Impersonation button

- [ ] **Create tenants pages**
 - [ ] Tenant list
 - [ ] Tenant detail with usage
 - [ ] Switch tenant context

- [ ] **Create billing pages**
 - [ ] Usage graphs (Chart.js or similar)
 - [ ] Invoice list
 - [ ] Subscription management

- [ ] **Create jobs pages**
 - [ ] Queue status overview
 - [ ] Failed jobs list
 - [ ] Retry/purge actions
 - [ ] Job detail view

- [ ] **Create webhooks pages**
 - [ ] Delivery stats dashboard
 - [ ] Subscription list
 - [ ] Delivery log viewer
 - [ ] Retry failed deliveries

### 1.6 Documentation and Tests

- [ ] **Create `docs/admin-dashboard.md`**
 - [ ] Setup and configuration
 - [ ] Customization options
 - [ ] Extending with custom pages
 - [ ] Security considerations
 - [ ] Screenshots

- [ ] **Add tests**
 - [ ] Unit tests for admin services
 - [ ] Integration tests for API routes
 - [ ] E2E tests for UI flows (optional)

---

## Phase 2: Framework Adapters

**Goal**: Enable svc-infra to work with Django, Litestar, and Flask in addition to FastAPI.

### 2.1 Abstraction Layer Design

> Create framework-agnostic core with framework-specific adapters.

- [ ] **Identify framework-coupled code**
 - [ ] Audit all `add_*` functions
 - [ ] List FastAPI-specific imports
 - [ ] Document required abstractions

- [ ] **Design adapter protocol**
 - [ ] `AppAdapter` protocol for lifecycle hooks
 - [ ] `RouterAdapter` protocol for route registration
 - [ ] `MiddlewareAdapter` protocol for middleware
 - [ ] `DependencyAdapter` protocol for DI

- [ ] **Document adapter architecture**
 - [ ] Create ADR for framework adapters
 - [ ] Define interface contracts
 - [ ] Plan backward compatibility

### 2.2 Create Core Abstractions

> Move framework-agnostic code to core modules.

- [ ] **Create `src/svc_infra/core/` module**
 ```
 src/svc_infra/core/
 ├── __init__.py
 ├── app.py # Abstract app interface
 ├── router.py # Abstract router interface
 ├── middleware.py # Abstract middleware interface
 ├── request.py # Abstract request interface
 └── response.py # Abstract response interface
 ```

- [ ] **Define protocols**
 - [ ] `AppProtocol` - startup/shutdown, state, include_router
 - [ ] `RouterProtocol` - add route, middleware
 - [ ] `RequestProtocol` - headers, body, user, state
 - [ ] `ResponseProtocol` - status, headers, body

### 2.3 Implement Django Adapter

> Enable svc-infra modules to work with Django.

- [ ] **Create `src/svc_infra/adapters/django/` module**
 ```
 src/svc_infra/adapters/django/
 ├── __init__.py
 ├── app.py # Django app adapter
 ├── views.py # View adapters
 ├── middleware.py # Middleware adapters
 ├── urls.py # URL patterns
 └── settings.py # Settings integration
 ```

- [ ] **Wrap django-allauth for auth**
 - [ ] Map to svc-infra auth interface
 - [ ] JWT support via djangorestframework-simplejwt
 - [ ] MFA integration

- [ ] **Wrap Django ORM for database**
 - [ ] Repository pattern adapter
 - [ ] Migration compatibility

- [ ] **Wrap django-rq or Celery for jobs**
 - [ ] Map to JobQueue interface
 - [ ] Scheduler integration

- [ ] **Create Django integration docs**

### 2.4 Implement Litestar Adapter

> Enable svc-infra modules to work with Litestar.

- [ ] **Create `src/svc_infra/adapters/litestar/` module**
 ```
 src/svc_infra/adapters/litestar/
 ├── __init__.py
 ├── app.py # Litestar app adapter
 ├── routes.py # Route adapters
 ├── middleware.py # Middleware adapters
 └── dependencies.py # DI adapters
 ```

- [ ] **Map existing patterns to Litestar**
 - [ ] `add_*` functions for Litestar
 - [ ] Dependency injection mapping
 - [ ] Middleware adaptation

- [ ] **Create Litestar integration docs**

### 2.5 Implement Flask Adapter (Optional)

> Enable svc-infra modules to work with Flask.

- [ ] **Create `src/svc_infra/adapters/flask/` module**
- [ ] **Wrap Flask-Login for auth**
- [ ] **Wrap Flask-SQLAlchemy for database**
- [ ] **Wrap Flask-RQ for jobs**
- [ ] **Create Flask integration docs**

### 2.6 Backward Compatibility

> Ensure FastAPI users are not affected.

- [ ] **Keep `svc_infra.api.fastapi` as primary interface**
- [ ] **Add framework detection utility**
- [ ] **Update examples for multi-framework**
- [ ] **Add migration guide for existing users**

---

## Phase 3: New Modules

**Goal**: Add commonly requested infrastructure modules.

### 3.1 Search Module

> Full-text search abstraction with multiple backends.

- [ ] **Create `src/svc_infra/search/` module**
 ```
 src/svc_infra/search/
 ├── __init__.py
 ├── add.py # add_search()
 ├── settings.py # SearchSettings
 ├── backends/
 │ ├── __init__.py
 │ ├── base.py # SearchBackend protocol
 │ ├── postgres.py # PostgreSQL FTS
 │ ├── meilisearch.py # Meilisearch
 │ ├── typesense.py # Typesense
 │ └── memory.py # In-memory (testing)
 ├── index.py # SearchIndex class
 └── query.py # Query builder
 ```

- [ ] **Define SearchBackend protocol**
 - [ ] `index(documents)` - Index documents
 - [ ] `search(query, filters, limit)` - Search
 - [ ] `delete(ids)` - Remove from index
 - [ ] `create_index(name, schema)` - Create index

- [ ] **Implement PostgreSQL FTS backend**
 - [ ] Use `tsvector` and `tsquery`
 - [ ] GIN index creation
 - [ ] Ranking and highlighting

- [ ] **Implement Meilisearch backend**
 - [ ] Wrap meilisearch-python
 - [ ] Index management
 - [ ] Faceted search

- [ ] **Implement Typesense backend**
 - [ ] Wrap typesense-python
 - [ ] Collection management
 - [ ] Geo search support

- [ ] **Create FastAPI integration**
 - [ ] `add_search(app)` function
 - [ ] Search dependency injection
 - [ ] Optional routes

- [ ] **Create docs and tests**
 - [ ] `docs/search.md`
 - [ ] Unit tests for each backend
 - [ ] Integration tests

### 3.2 Feature Flags Module

> Feature flag management with multiple backends.

- [ ] **Create `src/svc_infra/flags/` module**
 ```
 src/svc_infra/flags/
 ├── __init__.py
 ├── add.py # add_feature_flags()
 ├── settings.py # FlagSettings
 ├── backends/
 │ ├── __init__.py
 │ ├── base.py # FlagBackend protocol
 │ ├── memory.py # In-memory
 │ ├── database.py # Database-backed
 │ ├── unleash.py # Unleash integration
 │ └── launchdarkly.py # LaunchDarkly integration
 ├── models.py # Flag, Segment, Rule models
 ├── context.py # EvaluationContext
 └── decorators.py # @feature_flag decorator
 ```

- [ ] **Define FlagBackend protocol**
 - [ ] `is_enabled(flag_name, context)` - Check flag
 - [ ] `get_variant(flag_name, context)` - Get variant
 - [ ] `list_flags()` - List all flags
 - [ ] `create_flag(flag)` - Create flag
 - [ ] `update_flag(flag)` - Update flag

- [ ] **Implement database backend**
 - [ ] Flag model with rules
 - [ ] Segment targeting
 - [ ] Percentage rollouts

- [ ] **Implement Unleash backend**
 - [ ] Wrap unleash-client-python
 - [ ] Strategy mapping

- [ ] **Create decorator API**
 ```python
 @feature_flag("new_checkout", default=False)
 async def checkout(enabled: bool):
 if enabled:
 return new_checkout()
 return old_checkout()
 ```

- [ ] **Create FastAPI integration**
 - [ ] `add_feature_flags(app)` function
 - [ ] Dependency injection
 - [ ] Admin routes for flag management

- [ ] **Create docs and tests**
 - [ ] `docs/feature-flags.md`
 - [ ] Unit tests for backends
 - [ ] Integration tests

### 3.3 Email Module

> Transactional email with templates and multiple providers.

- [ ] **Create `src/svc_infra/email/` module**
 ```
 src/svc_infra/email/
 ├── __init__.py
 ├── add.py # add_email()
 ├── settings.py # EmailSettings
 ├── providers/
 │ ├── __init__.py
 │ ├── base.py # EmailProvider protocol
 │ ├── smtp.py # SMTP (extend existing)
 │ ├── resend.py # Resend
 │ ├── sendgrid.py # SendGrid
 │ ├── ses.py # AWS SES
 │ └── console.py # Console (dev)
 ├── templates/
 │ ├── __init__.py
 │ └── loader.py # Template loading
 ├── models.py # Email, Attachment models
 └── service.py # EmailService
 ```

- [ ] **Define EmailProvider protocol**
 - [ ] `send(email)` - Send single email
 - [ ] `send_batch(emails)` - Send batch
 - [ ] `get_status(message_id)` - Delivery status

- [ ] **Implement providers**
 - [ ] Resend (recommended default)
 - [ ] SendGrid
 - [ ] AWS SES
 - [ ] SMTP (extend existing auth sender)

- [ ] **Template support**
 - [ ] Jinja2 templates
 - [ ] MJML support (optional)
 - [ ] Inline CSS

- [ ] **Create EmailService**
 - [ ] Queue integration for async sending
 - [ ] Retry logic for failures
 - [ ] Template rendering

- [ ] **Create FastAPI integration**
 - [ ] `add_email(app)` function
 - [ ] Dependency injection

- [ ] **Create docs and tests**
 - [ ] `docs/email.md`
 - [ ] Unit tests for providers
 - [ ] Integration tests

### 3.4 Notifications Module

> Multi-channel notifications (push, SMS, in-app, email).

- [ ] **Create `src/svc_infra/notifications/` module**
 ```
 src/svc_infra/notifications/
 ├── __init__.py
 ├── add.py # add_notifications()
 ├── settings.py # NotificationSettings
 ├── channels/
 │ ├── __init__.py
 │ ├── base.py # Channel protocol
 │ ├── email.py # Uses email module
 │ ├── sms.py # Twilio/Vonage
 │ ├── push.py # FCM/APNs
 │ └── inapp.py # In-app (WebSocket/database)
 ├── models.py # Notification, Preference models
 ├── service.py # NotificationService
 └── router.py # Preference API routes
 ```

- [ ] **Define Channel protocol**
 - [ ] `send(user, notification)` - Send notification
 - [ ] `supports_batch` - Batch capability

- [ ] **Implement channels**
 - [ ] Email (uses email module)
 - [ ] SMS (Twilio)
 - [ ] Push (FCM for Android/web, APNs for iOS)
 - [ ] In-app (WebSocket or polling)

- [ ] **Create preference management**
 - [ ] User notification preferences
 - [ ] Channel opt-in/opt-out
 - [ ] Quiet hours

- [ ] **Create FastAPI integration**
 - [ ] `add_notifications(app)` function
 - [ ] Preference API routes
 - [ ] WebSocket for in-app

- [ ] **Create docs and tests**
 - [ ] `docs/notifications.md`
 - [ ] Unit tests for channels
 - [ ] Integration tests

---

## Phase 4: Enterprise Features

**Goal**: Add enterprise-grade features for larger customers.

### 4.1 SAML/SSO Support

> Enterprise single sign-on via SAML 2.0.

- [ ] **Create `src/svc_infra/enterprise/sso/` module**
 ```
 src/svc_infra/enterprise/sso/
 ├── __init__.py
 ├── add.py # add_saml_sso()
 ├── settings.py # SAMLSettings
 ├── providers/
 │ ├── __init__.py
 │ ├── base.py # SSOProvider protocol
 │ ├── saml.py # SAML 2.0 (python-saml)
 │ └── oidc.py # OIDC enterprise (extend existing)
 ├── models.py # SSOConfig, SSOConnection
 ├── router.py # SAML endpoints
 └── service.py # SSOService
 ```

- [ ] **Implement SAML 2.0**
 - [ ] Wrap python3-saml
 - [ ] SP-initiated SSO
 - [ ] IdP-initiated SSO
 - [ ] Metadata exchange

- [ ] **Per-tenant SSO configuration**
 - [ ] SSOConnection model
 - [ ] Admin UI for SSO setup
 - [ ] Certificate management

- [ ] **Create docs and tests**
 - [ ] `docs/enterprise-sso.md`
 - [ ] Integration tests with mock IdP

### 4.2 SCIM Provisioning

> Automatic user provisioning via SCIM 2.0.

- [ ] **Create `src/svc_infra/enterprise/scim/` module**
 ```
 src/svc_infra/enterprise/scim/
 ├── __init__.py
 ├── add.py # add_scim()
 ├── settings.py # SCIMSettings
 ├── router.py # SCIM endpoints
 ├── models.py # SCIMUser, SCIMGroup schemas
 └── service.py # SCIMService
 ```

- [ ] **Implement SCIM 2.0 endpoints**
 - [ ] `/scim/v2/Users` - User CRUD
 - [ ] `/scim/v2/Groups` - Group CRUD
 - [ ] `/scim/v2/ServiceProviderConfig` - Config
 - [ ] `/scim/v2/Schemas` - Schema discovery

- [ ] **Integration with auth module**
 - [ ] Auto-create users from SCIM
 - [ ] Sync groups/roles
 - [ ] Deprovisioning

- [ ] **Create docs and tests**
 - [ ] `docs/enterprise-scim.md`
 - [ ] Compliance tests

### 4.3 Advanced Audit Logging

> Tamper-proof audit trail with compliance features.

- [ ] **Enhance `src/svc_infra/security/audit_service.py`**
 - [ ] Hash chain integrity
 - [ ] Log export (JSON, CSV)
 - [ ] Retention policies
 - [ ] Search/filter

- [ ] **Add compliance features**
 - [ ] SOC 2 event types
 - [ ] HIPAA audit requirements
 - [ ] PCI-DSS logging

- [ ] **Create admin UI integration**
 - [ ] Audit log viewer
 - [ ] Export functionality
 - [ ] Integrity verification

- [ ] **Create `docs/enterprise-audit.md`**

### 4.4 IP Allowlisting

> Per-tenant IP restriction.

- [ ] **Create `src/svc_infra/enterprise/ip_allowlist/` module**
 - [ ] IPAllowlist model
 - [ ] Middleware for enforcement
 - [ ] Admin API for management

- [ ] **Integration with tenancy**
 - [ ] Per-tenant allowlists
 - [ ] Global allowlists
 - [ ] Override for admins

- [ ] **Create docs and tests**

### 4.5 Data Residency

> GDPR/compliance data location controls.

- [ ] **Create `src/svc_infra/enterprise/residency/` module**
 - [ ] Region configuration
 - [ ] Per-tenant region assignment
 - [ ] Database routing based on region

- [ ] **Integration with database module**
 - [ ] Multi-database routing
 - [ ] Region-aware queries

- [ ] **Create docs**
 - [ ] `docs/enterprise-residency.md`
 - [ ] Compliance documentation

---

## Phase 5: v2.0.0 Release

**Goal**: Finalize, document, and release v2.0.0.

### 5.1 Final Integration

- [ ] **Verify all new modules integrate cleanly**
- [ ] **Update main `__init__.py` exports**
- [ ] **Cross-module testing**

### 5.2 Documentation Polish

- [ ] **Update README.md with new features**
- [ ] **Create migration guide v1->v2**
- [ ] **Update all examples**
- [ ] **Create video tutorials (optional)**

### 5.3 Performance Optimization

- [ ] **Profile critical paths**
- [ ] **Optimize database queries**
- [ ] **Cache frequently accessed data**

### 5.4 Release

- [ ] **Update CHANGELOG.md**
- [ ] **Update pyproject.toml to 2.0.0**
- [ ] **Tag and publish**
- [ ] **Announce release**

---

## Appendix: Module Structure Reference

### Standard Module Pattern

Every new module should follow this pattern:

```
src/svc_infra/{module}/
├── __init__.py # Exports with __all__, module docstring
├── add.py # add_{module}(app) for FastAPI integration
├── settings.py # {Module}Settings with env var support
├── service.py # Main service class (async preferred)
├── models.py # SQLAlchemy/Pydantic models
├── router.py # FastAPI router (if has endpoints)
├── backends/ # Backend implementations (if multi-backend)
│ ├── __init__.py
│ ├── base.py # Backend protocol
│ └── {backend}.py # Specific implementations
└── exceptions.py # Module-specific exceptions
```

### Standard Test Pattern

```
tests/unit/{module}/
├── test_{module}.py # Main module tests
├── test_{module}_service.py # Service tests
├── test_{module}_backends.py # Backend tests (if applicable)
└── conftest.py # Module fixtures

tests/integration/{module}/
└── test_{module}_integration.py # Integration with real services
```

### Standard Documentation Pattern

```
docs/{module}.md
├── Quick Start
├── Configuration (Environment Variables)
├── API Reference
├── Examples
├── Backends (if applicable)
└── Troubleshooting
```
