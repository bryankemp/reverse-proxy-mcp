"""Application configuration."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Nginx Manager"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./data/nginx_manager.db"

    # JWT Configuration
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api"

    # MCP Configuration
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 5000

    # Nginx Configuration
    nginx_config_path: str = "/etc/nginx/sites-enabled/proxy.conf"
    nginx_socket_path: str = "/var/run/nginx.sock"
    nginx_log_path: str = "/var/log/nginx"

    # Logging
    log_level: str = "INFO"

    # Data Paths
    data_path: str = "./data"
    certs_path: str = "./data/certs"
    logs_path: str = "./data/logs"

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    @property
    def api_url(self) -> str:
        """Get API URL for MCP client."""
        protocol = "https" if not self.debug else "http"
        return f"{protocol}://{self.api_host}:{self.api_port}"

    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        if self.database_url.startswith("sqlite"):
            return self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
        return self.database_url


# Global settings instance
settings = Settings()
