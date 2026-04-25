from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "LinkedIn Simulation Profile Service"
    app_env: str = "development"
    api_v1_prefix: str = "/api"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    client_origin: str = "http://localhost:5173"
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "linkedin_sim"
    upload_dir: str = "app/uploads"
    max_file_size_mb: int = 5

    # Kafka settings
    kafka_enabled: bool = True
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "profile-service"
    kafka_member_created_topic: str = "member.created"
    kafka_member_updated_topic: str = "member.updated"
    kafka_profile_viewed_topic: str = "profile.viewed"
    kafka_request_timeout_ms: int = 5000

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        )

    @property
    def upload_path(self) -> Path:
        path = BASE_DIR / self.upload_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def kafka_bootstrap_server_list(self) -> list[str]:
        return [server.strip() for server in self.kafka_bootstrap_servers.split(",") if server.strip()]


settings = Settings()