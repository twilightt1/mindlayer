"""Google OAuth 2.0 via Authlib + token refresh for MindLayer ingestion."""
import time
import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from app.config import settings

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://openidconnect.googleapis.com/v1/userinfo"

NOTION_API_BASE  = "https://api.notion.com/v1"
NOTION_VERSION   = "2022-06-28"


class GoogleOAuthService:
    @property
    def _redirect_uri(self) -> str:
        return f"{settings.API_BASE_URL}/api/v1/auth/google/callback"

    def _client(self) -> AsyncOAuth2Client:
        return AsyncOAuth2Client(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=self._redirect_uri,
        )

    def create_authorization_url(self) -> tuple[str, str]:
        client = self._client()
        return client.create_authorization_url(
            GOOGLE_AUTH_URL,
            scope="openid email profile",
            access_type="offline",
            prompt="select_account",
        )

    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for user info. Returns {sub, email, name, picture}."""
        async with self._client() as client:
            await client.fetch_token(
                GOOGLE_TOKEN_URL,
                code=code,
                redirect_uri=self._redirect_uri,
            )
            resp = await client.get(GOOGLE_USERINFO)
            resp.raise_for_status()
            return resp.json()


google_oauth = GoogleOAuthService()


# ── Token refresh for ingestion connectors (Phase 2.5) ───────────────────────

class GoogleTokenRefresher:
    """Refreshes expired Google access tokens using a stored refresh_token.

    Used by the Drive and Gmail ingestion connectors. Stateless: returns the
    (possibly refreshed) access token but does not persist it back. The caller
    is responsible for updating Source.config if persistence is desired.
    """

    def __init__(self) -> None:
        self.token_url = GOOGLE_TOKEN_URL

    async def get_valid_token(self, source_type: str, config: dict) -> str:
        """Return a valid access_token, refreshing if expired or missing.

        Args:
            source_type: "drive" | "gmail" — used only for error context.
            config: Source.config dict. Recognized keys:
                - credentials.access_token (str, optional)
                - credentials.refresh_token (str, optional)
                - credentials.expires_at (int, unix ts, optional)
                - credentials.client_id     (str, optional, falls back to settings)
                - credentials.client_secret (str, optional, falls back to settings)

        Returns:
            A valid access_token string.

        Raises:
            ValueError: if no token or refresh_token can be used.
            httpx.HTTPError: if the refresh request fails.
        """
        creds = (config or {}).get("credentials") or {}
        access_token = creds.get("access_token")
        expires_at   = int(creds.get("expires_at") or 0)
        refresh_tok  = creds.get("refresh_token")

        client_id     = creds.get("client_id")     or settings.GOOGLE_CLIENT_ID
        client_secret = creds.get("client_secret") or settings.GOOGLE_CLIENT_SECRET

        # 1) Cached token still valid (60s safety buffer)
        if access_token and expires_at and expires_at > int(time.time()) + 60:
            return access_token

        # 2) Refresh via refresh_token
        if refresh_tok:
            if not client_id or not client_secret:
                raise ValueError(
                    f"[{source_type}] Missing Google client_id/client_secret. "
                    "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in env, "
                    "or store them in Source.config['credentials']."
                )
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    self.token_url,
                    data={
                        "grant_type":    "refresh_token",
                        "refresh_token": refresh_tok,
                        "client_id":     client_id,
                        "client_secret": client_secret,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            return data["access_token"]

        # 3) Fall back to whatever access_token we have, even if expired
        if access_token:
            return access_token

        raise ValueError(
            f"[{source_type}] No access_token or refresh_token in Source.config['credentials']"
        )


google_token_refresher = GoogleTokenRefresher()


async def get_valid_notion_token(config: dict) -> str:
    """Notion internal-integration tokens don't expire. Just return the static token."""
    tok = (config or {}).get("token")
    if not tok:
        raise ValueError("[notion] Missing 'token' in Source.config")
    return tok
