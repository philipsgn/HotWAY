"""
HotWAY Core Configuration & Settings Management
Author: Backend & WebGIS Engineer
Framework: Pydantic v2 Settings (pydantic-settings)
"""

from typing import Any, List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central Application Settings for HotWAY Monolith Backend.
    Loads environment variables with fallbacks to defaults.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 1. Project Identity & Metadata
    PROJECT_NAME: str = "HotWAY Dynamic Thermal Delivery Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"  # development | production | test
    DEBUG: bool = True

    # 2. CORS Allowed Origins
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid CORS format: {v}")

    @property
    def all_cors_origins(self) -> List[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    # 3. PostgreSQL & PostGIS Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "hotway_user"
    POSTGRES_PASSWORD: str = "hotway_password"
    POSTGRES_DB: str = "hotway_db"
    DATABASE_URL: str | None = None

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    @property
    def async_database_url(self) -> str:
        """Returns the async connection string for SQLAlchemy async engine."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("sqlite"):
                if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
                    return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
                return url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Returns the sync connection string for Alembic migrations."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("sqlite"):
                return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
            if url.startswith("postgresql+asyncpg://"):
                return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            return url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # 4. Redis Telemetry & State Cache Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str | None = None

    REDIS_TELEMETRY_TTL_SECONDS: int = 3600
    REDIS_GEO_KEY: str = "shipper:locations"
    REDIS_CHANNEL_TELEMETRY: str = "channel:telemetry"

    @property
    def redis_connection_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # 5. Security & Authentication
    SECRET_KEY: str = "hotway_super_secret_development_key_change_in_production_32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # 6. Spatial Target & Road Network Constants (Bình Thạnh, TP. Hồ Chí Minh)
    DEPOT_NAME: str = "Quán Bánh Canh Gà 490 Điện Biên Phủ"
    DEPOT_LATITUDE: float = 10.8012
    DEPOT_LONGITUDE: float = 106.7145
    MAX_DELIVERY_RADIUS_KM: float = 4.0
    # Bounding box for Bình Thạnh: [min_lat, min_lon, max_lat, max_lon]
    BINHTHANH_BBOX: tuple[float, float, float, float] = (10.78, 106.68, 10.83, 106.73)
    HANGGON_BBOX: tuple[float, float, float, float] = (10.90, 107.21, 10.96, 107.27)

    # 7. Newton Cooling Law Thermal Physics Constants
    T_ENV_DEFAULT: float = 30.0           # Ambient air temperature (°C)
    T0_HOT_SOUP: float = 88.0             # Freshly boiled chicken soup (°C)
    T_MIN_DELICIOUS: float = 60.0         # Culinary delicious threshold (°C)
    T_RUINED_THRESHOLD: float = 50.0      # Cold ruined soup threshold (°C)

    K_DISH_SOUP: float = 0.038            # Hot soup heat loss rate (min^-1)
    K_DISH_DRY: float = 0.022             # Warm/dry salad heat loss rate (min^-1)
    K_DISH_COLD_DRINK: float = 0.030      # Cold drink warming rate (min^-1)

    ALPHA_INSULATED_BAG: float = 0.50     # Thermal insulation multiplier (50% reduction)
    ALPHA_FOAM_BOX: float = 0.70          # Styrofoam insulation multiplier
    ALPHA_OPEN_BASKET: float = 1.00       # No insulation (open air)

    # 8. Reinforcement Learning & Inference Configuration
    RL_MODEL_PATH: str = "models/rl_best_model.zip"
    OSM_GRAPH_PATH: str = "data/binhthanh_graph.graphml"
    GHOST_TRAJECTORY_PATH: str = "experiments/trajectories/best_route_ghost.json"
    USE_DIJKSTRA_FALLBACK: bool = True
    MAX_BATCH_ORDERS: int = 5

    # 9. Real-Time Telemetry & WebSocket Parameters
    WS_HEARTBEAT_INTERVAL_SECONDS: int = 15
    WS_HEARTBEAT_TIMEOUT_SECONDS: int = 30
    ENABLE_MOCK_GPS: bool = True
    MOCK_GPS_SPEED_KMH: float = 32.0


# Instantiate global singleton settings instance
settings = Settings()
