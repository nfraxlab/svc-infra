# svc-infra Development Roadmap

> **Current Version**: 1.1.0
> **Production Readiness**: 45% (5/11 pts) -> Target: 82%+ (9/11 pts)
> **Target v1.0.0**: Phase 0 completion
> **Target v2.0.0**: Phase 1-4 completion

---

## Phase 0: Production Readiness Gate (v1.0.x)

**Goal**: Increase production readiness from 45% (5/11 pts) to 82%+ (9/11 pts) by achieving 60%+ test coverage.

**Current State**:
- [OK] Linting (1 pt)
- [OK] Type checking (1 pt)
- [X] Tests pass (2 pts) - blocked by coverage threshold
- [X] Coverage >=60% (2 pts) - currently 52.84%
- [!] Vulnerability scan (2 pts) - pip-audit not installed
- [OK] Package builds (2 pts)
- [OK] Documentation (1 pt)

**Target State**: 9/11 pts (82%) with all critical checks passing.

---

### 0.1 Install Security Tooling (+2 pts)

> Add pip-audit to dev dependencies for vulnerability scanning.

- [x] **Add pip-audit to pyproject.toml** [OK]
 - [x] Add `pip-audit` to dev dependencies
 - [x] Run `poetry lock && poetry install`
 - [x] Fix 7 vulnerabilities in 6 packages (fastapi-users, filelock, mcp, starlette, urllib3, werkzeug)
 - [x] Verify `make report` shows vulnerability scan passing (+2 pts)

**Result**: Production readiness improved from 45% (5/11 pts) -> 63% (7/11 pts)

---

### 0.2 Auth Module Tests (~15% -> 60% coverage)

> The auth module has the lowest coverage. Focus on high-impact areas.

- [ ] **test_auth_guard.py** (target: +108 lines covered)
 - [ ] Test `require_auth` decorator with valid JWT
 - [ ] Test `require_auth` decorator with expired JWT
 - [ ] Test `require_auth` decorator with invalid signature
 - [ ] Test `require_roles` with matching roles
 - [ ] Test `require_roles` with missing roles (403)
 - [ ] Test `require_permissions` decorator
 - [ ] Test anonymous access rejection

- [ ] **test_auth_providers.py** (target: +13 lines covered)
 - [ ] Test Google OAuth provider configuration
 - [ ] Test GitHub OAuth provider configuration
 - [ ] Test provider registry lookup
 - [ ] Test invalid provider handling

- [ ] **test_auth_cookies.py** (target: +14 lines covered)
 - [ ] Test `set_auth_cookie` with secure flags
 - [ ] Test `clear_auth_cookie` functionality
 - [ ] Test cookie extraction from request

- [ ] **test_auth_sender.py** (target: +31 lines covered)
 - [ ] Test email sender interface
 - [ ] Test mock email sender
 - [ ] Test verification email generation
 - [ ] Test password reset email generation

---

### 0.3 MFA Module Tests (~10% -> 60% coverage)

> MFA is critical for security but has minimal test coverage.

- [ ] **test_mfa_router.py** (target: +176 lines covered)
 - [ ] Test TOTP enrollment endpoint
 - [ ] Test TOTP verification endpoint
 - [ ] Test TOTP disable endpoint
 - [ ] Test backup codes generation
 - [ ] Test backup code redemption
 - [ ] Test MFA required middleware
 - [ ] Test invalid TOTP code rejection
 - [ ] Test rate limiting on verification attempts

- [ ] **test_mfa_pre_auth.py** (target: +20 lines covered)
 - [ ] Test pre-auth token generation
 - [ ] Test pre-auth token validation
 - [ ] Test pre-auth token expiry

- [ ] **test_mfa_verify.py** (target: +33 lines covered)
 - [ ] Test TOTP code verification
 - [ ] Test backup code verification
 - [ ] Test verification with invalid codes
 - [ ] Test verification rate limiting

- [ ] **test_mfa_security.py** (target: +9 lines covered)
 - [ ] Test TOTP secret generation
 - [ ] Test TOTP secret encryption
 - [ ] Test QR code URL generation

---

### 0.4 OAuth Router Tests (~29% -> 60% coverage)

> OAuth flows are complex and need comprehensive testing.

- [ ] **test_oauth_router.py** (target: +150 lines covered)
 - [ ] Test OAuth authorization URL generation
 - [ ] Test OAuth callback with valid code
 - [ ] Test OAuth callback with invalid state
 - [ ] Test OAuth token exchange
 - [ ] Test OAuth user info retrieval
 - [ ] Test OAuth account linking
 - [ ] Test OAuth account unlinking
 - [ ] Test PKCE flow
 - [ ] Test refresh token rotation

---

### 0.5 Payments Module Tests (~25% -> 50% coverage)

> Payments are business-critical. Focus on core flows.

- [ ] **test_stripe_provider.py** (target: +100 lines covered)
 - [ ] Test customer creation
 - [ ] Test payment method attachment
 - [ ] Test subscription creation
 - [ ] Test invoice generation
 - [ ] Test webhook signature verification
 - [ ] Test refund processing
 - [ ] Test payment intent creation

- [ ] **test_apf_payments_service.py** (target: +100 lines covered)
 - [ ] Test usage metering
 - [ ] Test billing cycle management
 - [ ] Test invoice calculation
 - [ ] Test subscription state transitions
 - [ ] Test payment failure handling

---

### 0.6 Validation & Final Gate

> Ensure all checks pass before closing Phase 0.

- [ ] **Run full test suite**
 - [ ] `poetry run pytest -q` - all tests pass
 - [ ] Coverage >= 60%

- [ ] **Run production readiness gate**
 - [ ] `make report` shows 9/11 pts (82%+)
 - [ ] No critical failures

- [ ] **Update documentation**
 - [ ] Update CHANGELOG.md with Phase 0 completion
 - [ ] Update README.md production readiness badge

---

### Phase 0 Success Criteria

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| Test Coverage | 52.84% | >=60% | [ ] |
| Tests Passing | [OK] | [OK] | [ ] |
| Vulnerability Scan | [!] SKIP | [OK] PASS | [ ] |
| Production Readiness | 45% (5/11) | 82% (9/11) | [ ] |

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
