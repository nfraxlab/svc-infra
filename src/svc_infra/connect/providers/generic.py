"""Master OAuth provider catalog and loading logic for svc_infra.connect.

This is the single source of truth for OAuth provider URL definitions.  It
powers BOTH:
  - svc_infra.connect  — workspace tool connections (stores tokens in DB)
  - svc_infra.auth     — user login (issues JWT sessions)

Any app that uses either module only needs to configure credentials once.

Env var convention
------------------
Primary (works for every provider, including custom unknown ones):
    CONNECT_{NAME}_CLIENT_ID=...
    CONNECT_{NAME}_CLIENT_SECRET=...

Legacy / convenience names for the built-in set (checked when primary not set):
    GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET
    GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET      (also GOOGLE_CONNECT_CLIENT_ID)
    MICROSOFT_CLIENT_ID / MICROSOFT_CLIENT_SECRET (also MICROSOFT_CONNECT_*)
    NOTION_CLIENT_ID / NOTION_CLIENT_SECRET
    SLACK_CLIENT_ID / SLACK_CLIENT_SECRET
    LINEAR_CLIENT_ID / LINEAR_CLIENT_SECRET
    ATLASSIAN_CLIENT_ID / ATLASSIAN_CLIENT_SECRET
    LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET
    FIGMA_CLIENT_ID / FIGMA_CLIENT_SECRET
    STRIPE_CLIENT_ID / STRIPE_CLIENT_SECRET

Dynamic-URL provider env vars (subdomain / domain required):
    CONNECT_MICROSOFT_TENANT_ID  or  MICROSOFT_TENANT_ID  (default: common)
    CONNECT_OKTA_DOMAIN          or  OKTA_DOMAIN
    CONNECT_AUTH0_DOMAIN         or  AUTH0_DOMAIN
    CONNECT_KEYCLOAK_BASE_URL    or  KEYCLOAK_BASE_URL
    CONNECT_KEYCLOAK_REALM       or  KEYCLOAK_REALM          (default: master)
    CONNECT_COGNITO_DOMAIN       or  COGNITO_DOMAIN
    CONNECT_ZENDESK_SUBDOMAIN    or  ZENDESK_SUBDOMAIN
    CONNECT_FRESHDESK_SUBDOMAIN  or  FRESHDESK_SUBDOMAIN
    CONNECT_SHOPIFY_SHOP         or  SHOPIFY_SHOP

Arbitrary extra providers (URLs pre-filled for known entries; full URL config
required for anything not in _KNOWN):
    CONNECT_PROVIDERS=dropbox,acmecorp
    CONNECT_DROPBOX_CLIENT_ID=...          # known — URLs already in catalog
    CONNECT_ACMECORP_CLIENT_ID=...
    CONNECT_ACMECORP_AUTHORIZE_URL=https://acme.com/oauth/authorize
    CONNECT_ACMECORP_TOKEN_URL=https://acme.com/oauth/token

Per-provider optional overrides (work for any provider):
    CONNECT_{NAME}_SCOPES=scope1,scope2
    CONNECT_{NAME}_PKCE=true|false
    CONNECT_{NAME}_AUTHORIZE_URL=https://...
    CONNECT_{NAME}_TOKEN_URL=https://...
    CONNECT_{NAME}_REVOKE_URL=https://...
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from pydantic import SecretStr

from svc_infra.connect.registry import OAuthProvider

# ---------------------------------------------------------------------------
# Dynamic URL builders
# Providers whose URLs depend on tenant / subdomain / domain env vars.
# Each builder returns a dict of URL fields to merge into the provider config,
# or None when the required env var is missing (provider is skipped).
# ---------------------------------------------------------------------------


def _build_microsoft_urls() -> dict[str, str] | None:
    tenant = os.getenv("CONNECT_MICROSOFT_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID", "common")
    base = f"https://login.microsoftonline.com/{tenant}"
    return {
        "authorize_url": f"{base}/oauth2/v2.0/authorize",
        "token_url": f"{base}/oauth2/v2.0/token",
        "oidc_discovery_url": f"{base}/v2.0",
    }


def _build_okta_urls() -> dict[str, str] | None:
    domain = os.getenv("CONNECT_OKTA_DOMAIN") or os.getenv("OKTA_DOMAIN")
    if not domain:
        return None
    domain = domain.strip().rstrip("/")
    base = f"https://{domain}/oauth2/default"
    return {
        "authorize_url": f"{base}/v1/authorize",
        "token_url": f"{base}/v1/token",
        "revoke_url": f"{base}/v1/revoke",
        "oidc_discovery_url": base,
    }


def _build_auth0_urls() -> dict[str, str] | None:
    domain = os.getenv("CONNECT_AUTH0_DOMAIN") or os.getenv("AUTH0_DOMAIN")
    if not domain:
        return None
    domain = domain.strip().rstrip("/")
    return {
        "authorize_url": f"https://{domain}/authorize",
        "token_url": f"https://{domain}/oauth/token",
        "revoke_url": f"https://{domain}/oauth/revoke",
        "oidc_discovery_url": f"https://{domain}",
    }


def _build_keycloak_urls() -> dict[str, str] | None:
    base = os.getenv("CONNECT_KEYCLOAK_BASE_URL") or os.getenv("KEYCLOAK_BASE_URL")
    if not base:
        return None
    realm = os.getenv("CONNECT_KEYCLOAK_REALM") or os.getenv("KEYCLOAK_REALM", "master")
    realm_url = f"{base.rstrip('/')}/realms/{realm}"
    return {
        "authorize_url": f"{realm_url}/protocol/openid-connect/auth",
        "token_url": f"{realm_url}/protocol/openid-connect/token",
        "revoke_url": f"{realm_url}/protocol/openid-connect/revoke",
        "oidc_discovery_url": realm_url,
    }


def _build_cognito_urls() -> dict[str, str] | None:
    domain = os.getenv("CONNECT_COGNITO_DOMAIN") or os.getenv("COGNITO_DOMAIN")
    if not domain:
        return None
    domain = domain.strip().rstrip("/")
    return {
        "authorize_url": f"https://{domain}/oauth2/authorize",
        "token_url": f"https://{domain}/oauth2/token",
        "revoke_url": f"https://{domain}/oauth2/revoke",
        "oidc_discovery_url": domain,
    }


def _build_zendesk_urls() -> dict[str, str] | None:
    subdomain = os.getenv("CONNECT_ZENDESK_SUBDOMAIN") or os.getenv("ZENDESK_SUBDOMAIN")
    if not subdomain:
        return None
    return {
        "authorize_url": f"https://{subdomain}.zendesk.com/oauth/authorizations/new",
        "token_url": f"https://{subdomain}.zendesk.com/oauth/tokens",
    }


def _build_freshdesk_urls() -> dict[str, str] | None:
    subdomain = os.getenv("CONNECT_FRESHDESK_SUBDOMAIN") or os.getenv("FRESHDESK_SUBDOMAIN")
    if not subdomain:
        return None
    return {
        "authorize_url": f"https://{subdomain}.freshdesk.com/login/oauth/authorize",
        "token_url": f"https://{subdomain}.freshdesk.com/login/oauth/token",
    }


def _build_shopify_urls() -> dict[str, str] | None:
    shop = os.getenv("CONNECT_SHOPIFY_SHOP") or os.getenv("SHOPIFY_SHOP")
    if not shop:
        return None
    shop = shop.strip().rstrip("/")
    return {
        "authorize_url": f"https://{shop}/admin/oauth/authorize",
        "token_url": f"https://{shop}/admin/oauth/access_token",
    }


_URL_BUILDERS: dict[str, Callable[[], dict[str, str] | None]] = {
    "microsoft": _build_microsoft_urls,
    "okta": _build_okta_urls,
    "auth0": _build_auth0_urls,
    "keycloak": _build_keycloak_urls,
    "cognito": _build_cognito_urls,
    "zendesk": _build_zendesk_urls,
    "freshdesk": _build_freshdesk_urls,
    "shopify": _build_shopify_urls,
}

# ---------------------------------------------------------------------------
# Legacy env var fallbacks
# Maps provider name -> ([id_env_fallbacks], [secret_env_fallbacks]).
# Checked when CONNECT_{NAME}_CLIENT_ID is not set.
# ---------------------------------------------------------------------------
_LEGACY_ENVS: dict[str, tuple[list[str], list[str]]] = {
    "github": (["GITHUB_CLIENT_ID"], ["GITHUB_CLIENT_SECRET"]),
    "google": (
        ["GOOGLE_CONNECT_CLIENT_ID", "GOOGLE_CLIENT_ID"],
        ["GOOGLE_CONNECT_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET"],
    ),
    "microsoft": (
        ["MICROSOFT_CONNECT_CLIENT_ID", "MICROSOFT_CLIENT_ID"],
        ["MICROSOFT_CONNECT_CLIENT_SECRET", "MICROSOFT_CLIENT_SECRET"],
    ),
    "notion": (["NOTION_CLIENT_ID"], ["NOTION_CLIENT_SECRET"]),
    "slack": (["SLACK_CLIENT_ID"], ["SLACK_CLIENT_SECRET"]),
    "linear": (["LINEAR_CLIENT_ID"], ["LINEAR_CLIENT_SECRET"]),
    "atlassian": (["ATLASSIAN_CLIENT_ID"], ["ATLASSIAN_CLIENT_SECRET"]),
    "linkedin": (["LINKEDIN_CLIENT_ID"], ["LINKEDIN_CLIENT_SECRET"]),
    "figma": (["FIGMA_CLIENT_ID"], ["FIGMA_CLIENT_SECRET"]),
    "stripe": (["STRIPE_CLIENT_ID"], ["STRIPE_CLIENT_SECRET"]),
    "hubspot": (["HUBSPOT_CLIENT_ID"], ["HUBSPOT_CLIENT_SECRET"]),
    "dropbox": (["DROPBOX_CLIENT_ID"], ["DROPBOX_CLIENT_SECRET"]),
    "box": (["BOX_CLIENT_ID"], ["BOX_CLIENT_SECRET"]),
    "discord": (["DISCORD_CLIENT_ID"], ["DISCORD_CLIENT_SECRET"]),
    "zoom": (["ZOOM_CLIENT_ID"], ["ZOOM_CLIENT_SECRET"]),
    "salesforce": (["SALESFORCE_CLIENT_ID"], ["SALESFORCE_CLIENT_SECRET"]),
    "gitlab": (["GITLAB_CLIENT_ID"], ["GITLAB_CLIENT_SECRET"]),
    "bitbucket": (["BITBUCKET_CLIENT_ID"], ["BITBUCKET_CLIENT_SECRET"]),
    "airtable": (["AIRTABLE_CLIENT_ID"], ["AIRTABLE_CLIENT_SECRET"]),
    "asana": (["ASANA_CLIENT_ID"], ["ASANA_CLIENT_SECRET"]),
    "monday": (["MONDAY_CLIENT_ID"], ["MONDAY_CLIENT_SECRET"]),
    "clickup": (["CLICKUP_CLIENT_ID"], ["CLICKUP_CLIENT_SECRET"]),
    "calendly": (["CALENDLY_CLIENT_ID"], ["CALENDLY_CLIENT_SECRET"]),
    "quickbooks": (["QUICKBOOKS_CLIENT_ID"], ["QUICKBOOKS_CLIENT_SECRET"]),
    "xero": (["XERO_CLIENT_ID"], ["XERO_CLIENT_SECRET"]),
    "twitter": (["TWITTER_CLIENT_ID"], ["TWITTER_CLIENT_SECRET"]),
    "spotify": (["SPOTIFY_CLIENT_ID"], ["SPOTIFY_CLIENT_SECRET"]),
    "intercom": (["INTERCOM_CLIENT_ID"], ["INTERCOM_CLIENT_SECRET"]),
}

# ---------------------------------------------------------------------------
# Known provider URL catalog
# Entries whose URLs depend on env vars at runtime use _uses_builder=True;
# this instructs _load_known_provider to call _URL_BUILDERS[name]() for URLs.
#
# All non-underscore keys map directly to OAuthProvider fields.
# ---------------------------------------------------------------------------
_KNOWN: dict[str, dict[str, Any]] = {
    # ---------------------------------------------------------------------- #
    # IDENTITY / LOGIN PROVIDERS                                              #
    # ---------------------------------------------------------------------- #
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "revoke_url": "https://api.github.com/applications/{client_id}/token",
        "userinfo_url": "https://api.github.com/user",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "github",
        "default_scopes": ["repo", "user:email"],
        "extra_authorize_params": {"allow_signup": "false"},
    },
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "revoke_url": "https://oauth2.googleapis.com/revoke",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "oidc_discovery_url": "https://accounts.google.com",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/calendar.readonly",
        ],
        "extra_authorize_params": {"access_type": "offline", "prompt": "consent"},
    },
    "microsoft": {
        # URLs are tenant-specific; built at load time by _build_microsoft_urls
        "_uses_builder": True,
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["Files.Read", "Calendars.Read", "offline_access"],
    },
    "linkedin": {
        "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "userinfo_url": "https://api.linkedin.com/v2/me",
        "pkce_required": False,
        "login_enabled": True,
        "userinfo_kind": "linkedin",
        "default_scopes": ["r_liteprofile", "r_emailaddress"],
    },
    "apple": {
        "authorize_url": "https://appleid.apple.com/auth/authorize",
        "token_url": "https://appleid.apple.com/auth/token",
        "revoke_url": "https://appleid.apple.com/auth/revoke",
        "oidc_discovery_url": "https://appleid.apple.com",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["name", "email"],
        "extra_authorize_params": {"response_mode": "form_post"},
    },
    "discord": {
        "authorize_url": "https://discord.com/api/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "revoke_url": "https://discord.com/api/oauth2/token/revoke",
        "userinfo_url": "https://discord.com/api/users/@me",
        "pkce_required": False,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["identify", "email"],
    },
    "twitter": {
        "authorize_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "revoke_url": "https://api.twitter.com/2/oauth2/revoke",
        "userinfo_url": "https://api.twitter.com/2/users/me",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["tweet.read", "users.read", "offline.access"],
    },
    "twitch": {
        "authorize_url": "https://id.twitch.tv/oauth2/authorize",
        "token_url": "https://id.twitch.tv/oauth2/token",
        "revoke_url": "https://id.twitch.tv/oauth2/revoke",
        "userinfo_url": "https://api.twitch.tv/helix/users",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["user:read:email"],
    },
    "spotify": {
        "authorize_url": "https://accounts.spotify.com/authorize",
        "token_url": "https://accounts.spotify.com/api/token",
        "userinfo_url": "https://api.spotify.com/v1/me",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["user-read-email", "playlist-read-private"],
    },
    "reddit": {
        "authorize_url": "https://www.reddit.com/api/v1/authorize",
        "token_url": "https://www.reddit.com/api/v1/access_token",
        "revoke_url": "https://www.reddit.com/api/v1/revoke_token",
        "userinfo_url": "https://oauth.reddit.com/api/v1/me",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["identity"],
        "extra_authorize_params": {"duration": "permanent"},
    },
    "gitlab": {
        "authorize_url": "https://gitlab.com/oauth/authorize",
        "token_url": "https://gitlab.com/oauth/token",
        "revoke_url": "https://gitlab.com/oauth/revoke",
        "oidc_discovery_url": "https://gitlab.com",
        "userinfo_url": "https://gitlab.com/oauth/userinfo",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["read_user", "openid", "email"],
    },
    "bitbucket": {
        "authorize_url": "https://bitbucket.org/site/oauth2/authorize",
        "token_url": "https://bitbucket.org/site/oauth2/access_token",
        "userinfo_url": "https://api.bitbucket.org/2.0/user",
        "pkce_required": False,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["account", "repository"],
    },
    "heroku": {
        "authorize_url": "https://id.heroku.com/oauth/authorize",
        "token_url": "https://id.heroku.com/oauth/token",
        "userinfo_url": "https://api.heroku.com/account",
        "pkce_required": False,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["global"],
    },
    "webex": {
        "authorize_url": "https://webexapis.com/v1/authorize",
        "token_url": "https://webexapis.com/v1/access_token",
        "revoke_url": "https://webexapis.com/v1/access_token",
        "userinfo_url": "https://webexapis.com/v1/people/me",
        "pkce_required": False,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["spark:people_read"],
    },
    "zoom": {
        "authorize_url": "https://zoom.us/oauth/authorize",
        "token_url": "https://zoom.us/oauth/token",
        "revoke_url": "https://zoom.us/oauth/revoke",
        "userinfo_url": "https://api.zoom.us/v2/users/me",
        "pkce_required": False,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["user:read:admin"],
    },
    "facebook": {
        "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "revoke_url": "https://graph.facebook.com/me/permissions",
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "standard",
        "default_scopes": ["email", "public_profile"],
    },
    "salesforce": {
        "authorize_url": "https://login.salesforce.com/services/oauth2/authorize",
        "token_url": "https://login.salesforce.com/services/oauth2/token",
        "revoke_url": "https://login.salesforce.com/services/oauth2/revoke",
        "userinfo_url": "https://login.salesforce.com/services/oauth2/userinfo",
        "oidc_discovery_url": "https://login.salesforce.com",
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["api", "refresh_token", "openid"],
    },
    # ---------------------------------------------------------------------- #
    # ENTERPRISE IDENTITY (OIDC — dynamic URLs via builder)                  #
    # ---------------------------------------------------------------------- #
    "okta": {
        "_uses_builder": True,
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["openid", "email", "profile"],
    },
    "auth0": {
        "_uses_builder": True,
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["openid", "email", "profile"],
    },
    "keycloak": {
        "_uses_builder": True,
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["openid", "email", "profile"],
    },
    "cognito": {
        "_uses_builder": True,
        "pkce_required": True,
        "login_enabled": True,
        "userinfo_kind": "oidc",
        "default_scopes": ["openid", "email", "profile"],
    },
    # ---------------------------------------------------------------------- #
    # PRODUCTIVITY / PROJECT MANAGEMENT                                       #
    # ---------------------------------------------------------------------- #
    "notion": {
        "authorize_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        "pkce_required": True,
        "default_scopes": [],
        "extra_authorize_params": {"owner": "user"},
    },
    "airtable": {
        "authorize_url": "https://airtable.com/oauth2/v1/authorize",
        "token_url": "https://airtable.com/oauth2/v1/token",
        "revoke_url": "https://airtable.com/oauth2/v1/token/revoke",
        "pkce_required": True,
        "default_scopes": ["data.records:read", "data.records:write"],
    },
    "asana": {
        "authorize_url": "https://app.asana.com/-/oauth_authorize",
        "token_url": "https://app.asana.com/-/oauth_token",
        "revoke_url": "https://app.asana.com/-/oauth_revoke",
        "userinfo_url": "https://app.asana.com/api/1.0/users/me",
        "pkce_required": False,
        "default_scopes": ["default"],
    },
    "monday": {
        "authorize_url": "https://auth.monday.com/oauth2/authorize",
        "token_url": "https://auth.monday.com/oauth2/token",
        "pkce_required": False,
        "default_scopes": [],
    },
    "figma": {
        "authorize_url": "https://www.figma.com/oauth",
        "token_url": "https://www.figma.com/api/oauth/token",
        "revoke_url": "https://www.figma.com/api/oauth/revoke",
        "userinfo_url": "https://api.figma.com/v1/me",
        "pkce_required": False,
        "default_scopes": ["files:read"],
    },
    "clickup": {
        "authorize_url": "https://app.clickup.com/api",
        "token_url": "https://api.clickup.com/api/v2/oauth/token",
        "userinfo_url": "https://api.clickup.com/api/v2/user",
        "pkce_required": False,
        "default_scopes": [],
    },
    "todoist": {
        "authorize_url": "https://todoist.com/oauth/authorize",
        "token_url": "https://todoist.com/oauth/access_token",
        "revoke_url": "https://todoist.com/oauth/revoke",
        "pkce_required": False,
        "default_scopes": ["data:read_write"],
    },
    "basecamp": {
        "authorize_url": "https://launchpad.37signals.com/authorization/new",
        "token_url": "https://launchpad.37signals.com/authorization/token",
        "pkce_required": False,
        "default_scopes": [],
    },
    "wrike": {
        "authorize_url": "https://login.wrike.com/oauth2/authorize/v4",
        "token_url": "https://login.wrike.com/oauth2/token",
        "revoke_url": "https://login.wrike.com/oauth2/revoke_token/v4",
        "pkce_required": False,
        "default_scopes": [],
    },
    "miro": {
        "authorize_url": "https://miro.com/oauth/authorize",
        "token_url": "https://api.miro.com/v1/oauth/token",
        "revoke_url": "https://api.miro.com/v1/oauth/token/revoke",
        "pkce_required": True,
        "default_scopes": ["boards:read", "boards:write"],
    },
    "smartsheet": {
        "authorize_url": "https://app.smartsheet.com/b/authorize",
        "token_url": "https://api.smartsheet.com/2.0/token",
        "pkce_required": False,
        "default_scopes": ["READ_SHEETS", "WRITE_SHEETS"],
    },
    # ---------------------------------------------------------------------- #
    # DEVELOPER TOOLS                                                         #
    # ---------------------------------------------------------------------- #
    "vercel": {
        "authorize_url": "https://vercel.com/oauth/authorize",
        "token_url": "https://api.vercel.com/v2/oauth/access_token",
        "pkce_required": False,
        "default_scopes": [],
    },
    "netlify": {
        "authorize_url": "https://app.netlify.com/authorize",
        "token_url": "https://api.netlify.com/oauth/token",
        "pkce_required": False,
        "default_scopes": [],
    },
    "render": {
        "authorize_url": "https://dashboard.render.com/oauth/authorize",
        "token_url": "https://render.com/oauth/token",
        "pkce_required": True,
        "default_scopes": [],
    },
    # ---------------------------------------------------------------------- #
    # COMMUNICATION                                                           #
    # ---------------------------------------------------------------------- #
    "slack": {
        "authorize_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "revoke_url": "https://slack.com/api/auth.revoke",
        "userinfo_url": "https://slack.com/api/users.identity",
        "pkce_required": True,
        "default_scopes": ["channels:read", "chat:write"],
    },
    "intercom": {
        "authorize_url": "https://app.intercom.com/oauth",
        "token_url": "https://api.intercom.io/auth/eagle/token",
        "pkce_required": False,
        "default_scopes": [],
    },
    # ---------------------------------------------------------------------- #
    # CRM / SUPPORT                                                           #
    # ---------------------------------------------------------------------- #
    "hubspot": {
        "authorize_url": "https://app.hubspot.com/oauth/authorize",
        "token_url": "https://api.hubspot.com/oauth/v1/token",
        "pkce_required": False,
        "default_scopes": ["contacts", "crm.objects.contacts.read"],
    },
    "pipedrive": {
        "authorize_url": "https://oauth.pipedrive.com/oauth/authorize",
        "token_url": "https://oauth.pipedrive.com/oauth/token",
        "pkce_required": False,
        "default_scopes": [],
    },
    "zendesk": {
        "_uses_builder": True,
        "pkce_required": False,
        "default_scopes": ["read", "write"],
    },
    "freshdesk": {
        "_uses_builder": True,
        "pkce_required": False,
        "default_scopes": [],
    },
    # ---------------------------------------------------------------------- #
    # FINANCE                                                                 #
    # ---------------------------------------------------------------------- #
    "stripe": {
        "authorize_url": "https://connect.stripe.com/oauth/authorize",
        "token_url": "https://connect.stripe.com/oauth/token",
        "pkce_required": False,
        "default_scopes": ["read_write"],
    },
    "quickbooks": {
        "authorize_url": "https://appcenter.intuit.com/connect/oauth2",
        "token_url": "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
        "revoke_url": "https://developer.api.intuit.com/v2/oauth2/tokens/revoke",
        "pkce_required": False,
        "default_scopes": ["com.intuit.quickbooks.accounting"],
    },
    "xero": {
        "authorize_url": "https://login.xero.com/identity/connect/authorize",
        "token_url": "https://identity.xero.com/connect/token",
        "revoke_url": "https://identity.xero.com/connect/revocation",
        "oidc_discovery_url": "https://identity.xero.com",
        "pkce_required": True,
        "default_scopes": [
            "openid",
            "profile",
            "email",
            "accounting.transactions",
        ],
    },
    "freshbooks": {
        "authorize_url": "https://auth.freshbooks.com/oauth/authorize",
        "token_url": "https://api.freshbooks.com/auth/oauth/token",
        "revoke_url": "https://api.freshbooks.com/auth/oauth/revoke",
        "pkce_required": False,
        "default_scopes": [],
    },
    # ---------------------------------------------------------------------- #
    # CALENDAR / SCHEDULING                                                   #
    # ---------------------------------------------------------------------- #
    "calendly": {
        "authorize_url": "https://auth.calendly.com/oauth/authorize",
        "token_url": "https://auth.calendly.com/oauth/token",
        "revoke_url": "https://auth.calendly.com/oauth/revoke",
        "userinfo_url": "https://api.calendly.com/users/me",
        "pkce_required": False,
        "default_scopes": [],
    },
    # ---------------------------------------------------------------------- #
    # STORAGE / CLOUD                                                         #
    # ---------------------------------------------------------------------- #
    "dropbox": {
        "authorize_url": "https://www.dropbox.com/oauth2/authorize",
        "token_url": "https://api.dropboxapi.com/oauth2/token",
        "revoke_url": "https://api.dropboxapi.com/2/auth/token/revoke",
        "pkce_required": True,
        "default_scopes": [],
    },
    "box": {
        "authorize_url": "https://account.box.com/api/oauth2/authorize",
        "token_url": "https://api.box.com/oauth2/token",
        "revoke_url": "https://api.box.com/oauth2/revoke",
        "pkce_required": False,
        "default_scopes": ["root_readonly"],
    },
    # ---------------------------------------------------------------------- #
    # SOCIAL / CONTENT                                                        #
    # ---------------------------------------------------------------------- #
    "instagram": {
        "authorize_url": "https://api.instagram.com/oauth/authorize",
        "token_url": "https://api.instagram.com/oauth/access_token",
        "pkce_required": False,
        "default_scopes": ["user_profile", "user_media"],
    },
    # ---------------------------------------------------------------------- #
    # MARKETING / EMAIL                                                       #
    # ---------------------------------------------------------------------- #
    "mailchimp": {
        "authorize_url": "https://login.mailchimp.com/oauth2/authorize",
        "token_url": "https://login.mailchimp.com/oauth2/token",
        "pkce_required": False,
        "default_scopes": [],
    },
    "mailerlite": {
        "authorize_url": "https://dashboard.mailerlite.com/oauth/authorize",
        "token_url": "https://connect.mailerlite.com/oauth/token",
        "pkce_required": True,
        "default_scopes": [],
    },
    # ---------------------------------------------------------------------- #
    # DEVELOPER PLATFORMS                                                     #
    # ---------------------------------------------------------------------- #
    "atlassian": {
        "authorize_url": "https://auth.atlassian.com/authorize",
        "token_url": "https://auth.atlassian.com/oauth/token",
        "userinfo_url": "https://api.atlassian.com/me",
        "pkce_required": True,
        "default_scopes": [
            "read:jira-work",
            "write:jira-work",
            "read:confluence-content.all",
            "offline_access",
        ],
        "extra_authorize_params": {
            "audience": "api.atlassian.com",
            "prompt": "consent",
        },
    },
    "linear": {
        "authorize_url": "https://linear.app/oauth/authorize",
        "token_url": "https://api.linear.app/oauth/token",
        "revoke_url": "https://api.linear.app/oauth/revoke",
        "userinfo_url": "https://api.linear.app/graphql",
        "pkce_required": True,
        "default_scopes": ["read", "write"],
    },
    # ---------------------------------------------------------------------- #
    # E-COMMERCE                                                              #
    # ---------------------------------------------------------------------- #
    "shopify": {
        "_uses_builder": True,
        "pkce_required": True,
        "default_scopes": ["read_products", "read_orders"],
    },
}


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------


def _resolve_creds(name: str) -> tuple[str, str] | None:
    """Return (client_id, client_secret) for a provider, or None.

    Resolution order:
      1. CONNECT_{NAME}_CLIENT_ID / CONNECT_{NAME}_CLIENT_SECRET
      2. Legacy / convenience env vars declared in _LEGACY_ENVS
    """
    prefix = f"CONNECT_{name.upper()}_"
    cid = os.getenv(f"{prefix}CLIENT_ID")
    csecret = os.getenv(f"{prefix}CLIENT_SECRET")
    if cid and csecret:
        return cid, csecret

    legacy = _LEGACY_ENVS.get(name, ([], []))
    for env in legacy[0]:
        val = os.getenv(env)
        if val:
            cid = val
            break
    for env in legacy[1]:
        val = os.getenv(env)
        if val:
            csecret = val
            break

    if cid and csecret:
        return cid, csecret
    return None


# ---------------------------------------------------------------------------
# Provider loading
# ---------------------------------------------------------------------------


def _load_known_provider(name: str) -> OAuthProvider | None:
    """Load a known provider by name using env vars.

    Returns a configured OAuthProvider ready to register, or None when the
    required credentials or dynamic URL variables are absent.
    """
    creds = _resolve_creds(name)
    if creds is None:
        return None

    cid, csecret = creds
    entry = _KNOWN.get(name)
    if entry is None:
        return None

    cfg: dict[str, Any] = {k: v for k, v in entry.items() if not k.startswith("_")}

    # Dynamic URL providers
    uses_builder = entry.get("_uses_builder", False)
    if uses_builder:
        builder = _URL_BUILDERS.get(name)
        if builder is None:
            return None
        urls = builder()
        if urls is None:
            return None
        cfg.update(urls)

    # Validate required URL fields are present
    if not cfg.get("authorize_url") or not cfg.get("token_url"):
        return None

    # Per-provider env var overrides
    prefix = f"CONNECT_{name.upper()}_"
    for field, env_suffix in (
        ("authorize_url", "AUTHORIZE_URL"),
        ("token_url", "TOKEN_URL"),
        ("revoke_url", "REVOKE_URL"),
    ):
        val = os.getenv(f"{prefix}{env_suffix}")
        if val:
            cfg[field] = val

    # Scope override: CONNECT_{NAME}_SCOPES or {NAME}_SCOPES
    for scope_env in (f"{prefix}SCOPES", f"{name.upper()}_SCOPES"):
        raw = os.getenv(scope_env, "")
        if raw:
            cfg["default_scopes"] = [s.strip() for s in raw.split(",") if s.strip()]
            break

    # PKCE override
    pkce_val = os.getenv(f"{prefix}PKCE")
    if pkce_val is not None:
        cfg["pkce_required"] = pkce_val.lower() in ("true", "1", "yes")

    # LOGIN override: CONNECT_{NAME}_LOGIN=false disables login for this provider
    login_val = os.getenv(f"{prefix}LOGIN")
    if login_val is not None:
        cfg["login_enabled"] = login_val.lower() in ("true", "1", "yes")

    return OAuthProvider(name=name, client_id=cid, client_secret=SecretStr(csecret), **cfg)


def load_all_connect_providers() -> list[OAuthProvider]:
    """Load all configured OAuth providers.

    Scans the entire _KNOWN catalog for credentials then processes any
    additional providers listed in CONNECT_PROVIDERS.  CONNECT_PROVIDERS
    entries override catalog entries when the same name appears in both.

    This is the primary entry point — used by connect/providers/__init__.py
    to initialise the global registry at startup.
    """
    providers: dict[str, OAuthProvider] = {}

    # Step 1: scan all known providers
    for name in _KNOWN:
        provider = _load_known_provider(name)
        if provider is not None:
            providers[name] = provider

    # Step 2: CONNECT_PROVIDERS list — can add unknown providers or override
    for provider in _load_generic_providers():
        providers[provider.name] = provider

    return list(providers.values())


def _load_generic_providers() -> list[OAuthProvider]:
    """Load providers declared explicitly via CONNECT_PROVIDERS env var.

    Known providers (in _KNOWN) are loaded via the full catalog loader.
    Unknown providers require explicit URL configuration:
      CONNECT_{NAME}_AUTHORIZE_URL=...
      CONNECT_{NAME}_TOKEN_URL=...

    Returns a list of OAuthProvider instances ready to register.
    """
    names_raw = os.getenv("CONNECT_PROVIDERS", "").strip()
    if not names_raw:
        return []

    result: list[OAuthProvider] = []
    for raw in names_raw.split(","):
        name = raw.strip().lower()
        if not name:
            continue

        # Known provider: use full catalog loading (inherits metadata + login fields)
        if name in _KNOWN:
            provider = _load_known_provider(name)
            if provider is not None:
                result.append(provider)
            continue

        # Unknown provider: require explicit URL config
        prefix = f"CONNECT_{name.upper()}_"
        client_id = os.getenv(f"{prefix}CLIENT_ID")
        client_secret = os.getenv(f"{prefix}CLIENT_SECRET")
        if not client_id or not client_secret:
            continue

        authorize_url = os.getenv(f"{prefix}AUTHORIZE_URL")
        token_url = os.getenv(f"{prefix}TOKEN_URL")
        if not authorize_url or not token_url:
            continue

        revoke_url = os.getenv(f"{prefix}REVOKE_URL")
        scopes_raw = os.getenv(f"{prefix}SCOPES", "")
        scopes = [s.strip() for s in scopes_raw.split(",") if s.strip()]
        pkce_raw = os.getenv(f"{prefix}PKCE", "true")
        pkce_required = pkce_raw.lower() in ("true", "1", "yes")

        result.append(
            OAuthProvider(
                name=name,
                client_id=client_id,
                client_secret=SecretStr(client_secret),
                authorize_url=authorize_url,
                token_url=token_url,
                revoke_url=revoke_url,
                default_scopes=scopes,
                pkce_required=pkce_required,
            )
        )

    return result
