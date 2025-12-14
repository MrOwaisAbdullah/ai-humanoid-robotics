"""
Translation Service Configuration Management.

Centralized configuration for the OpenAI Translation Service with
environment-based overrides and validation.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field, validator
from src.utils.translation_logger import get_translation_logger

logger = get_translation_logger(__name__)


class LogLevel(str, Enum):
    """Log levels for the translation service."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class CacheBackend(str, Enum):
    """Cache backend types."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"


@dataclass
class GeminiConfig:
    """Configuration for Gemini API."""
    api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    )
    default_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
    )
    organization: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_ORGANIZATION"))

    # Connection settings
    timeout: float = field(default_factory=lambda: float(os.getenv("GEMINI_TIMEOUT", "60")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("GEMINI_MAX_RETRIES", "3")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("GEMINI_RETRY_DELAY", "1.0")))

    # Advanced settings
    proxy: Optional[str] = field(default_factory=lambda: os.getenv("HTTP_PROXY"))
    custom_headers: Dict[str, str] = field(default_factory=dict)
    http2: bool = field(default_factory=lambda: os.getenv("GEMINI_HTTP2", "true").lower() == "true")

    # Rate limiting
    requests_per_minute: int = field(default_factory=lambda: int(os.getenv("GEMINI_RPM", "60")))
    requests_per_hour: int = field(default_factory=lambda: int(os.getenv("GEMINI_RPH", "1000")))

    # Model pricing (USD per 1M tokens)
    pricing: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "gemini-2.0-flash-lite": {"input": 0.000075, "output": 0.00015},
        "gemini-2.5-pro": {"input": 0.00125, "output": 0.00375}
    })


@dataclass
class OpenAIAgentsConfig:
    """Configuration for OpenAI Agents SDK."""
    enabled: bool = field(default_factory=lambda: os.getenv("OPENAI_AGENTS_ENABLED", "true").lower() == "true")
    enable_tracing: bool = field(default_factory=lambda: os.getenv("OPENAI_AGENTS_TRACING", "false").lower() == "true")
    verbose_logging: bool = field(default_factory=lambda: os.getenv("OPENAI_AGENTS_VERBOSE", "false").lower() == "true")

    # Agent settings
    default_temperature: float = field(default_factory=lambda: float(os.getenv("AGENT_DEFAULT_TEMPERATURE", "0.3")))
    default_max_tokens: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_TOKENS", "2048")))
    max_turns: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_TURNS", "5")))

    # Tool settings
    enable_html_tool: bool = field(default_factory=lambda: os.getenv("AGENT_HTML_TOOL", "true").lower() == "true")
    enable_code_tool: bool = field(default_factory=lambda: os.getenv("AGENT_CODE_TOOL", "true").lower() == "true")
    enable_quality_tool: bool = field(default_factory=lambda: os.getenv("AGENT_QUALITY_TOOL", "true").lower() == "true")

    # Quality settings
    quality_check_enabled: bool = field(default_factory=lambda: os.getenv("AGENT_QUALITY_CHECK", "true").lower() == "true")
    confidence_threshold: float = field(default_factory=lambda: float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", "0.8")))


@dataclass
class CacheConfig:
    """Configuration for caching."""
    backend: CacheBackend = field(
        default_factory=lambda: CacheBackend(os.getenv("CACHE_BACKEND", "memory"))
    )

    # TTL settings
    default_ttl_hours: int = field(default_factory=lambda: int(os.getenv("CACHE_DEFAULT_TTL", "168")))  # 7 days
    high_quality_ttl_hours: int = field(default_factory=lambda: int(os.getenv("CACHE_HIGH_QUALITY_TTL", "720")))  # 30 days
    low_quality_ttl_hours: int = field(default_factory=lambda: int(os.getenv("CACHE_LOW_QUALITY_TTL", "24")))  # 1 day

    # Redis settings
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    redis_prefix: str = field(default_factory=lambda: os.getenv("REDIS_PREFIX", "translation:"))
    redis_max_connections: int = field(default_factory=lambda: int(os.getenv("REDIS_MAX_CONNECTIONS", "10")))

    # Memory cache settings
    memory_max_size: int = field(default_factory=lambda: int(os.getenv("CACHE_MEMORY_MAX_SIZE", "1000")))
    memory_cleanup_interval: int = field(default_factory=lambda: int(os.getenv("CACHE_CLEANUP_INTERVAL", "3600")))


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        "sqlite:///./translation.db"
    ))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5")))
    max_overflow: int = field(default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "10")))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30")))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "3600")))

    # Migration settings
    auto_migrate: bool = field(default_factory=lambda: os.getenv("DB_AUTO_MIGRATE", "true").lower() == "true")
    migration_timeout: int = field(default_factory=lambda: int(os.getenv("DB_MIGRATION_TIMEOUT", "300")))


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: LogLevel = field(default_factory=lambda: LogLevel(os.getenv("LOG_LEVEL", "INFO")))
    format: str = field(
        default_factory=lambda: os.getenv(
            "LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )

    # File logging
    file_logging: bool = field(default_factory=lambda: os.getenv("LOG_FILE_ENABLED", "true").lower() == "true")
    file_path: str = field(default_factory=lambda: os.getenv("LOG_FILE_PATH", "logs/translation.log"))
    file_rotation: str = field(default_factory=lambda: os.getenv("LOG_FILE_ROTATION", "1 day"))
    file_retention: str = field(default_factory=lambda: os.getenv("LOG_FILE_RETENTION", "30 days"))
    max_file_size: str = field(default_factory=lambda: os.getenv("LOG_MAX_FILE_SIZE", "100 MB"))

    # Structured logging
    json_format: bool = field(default_factory=lambda: os.getenv("LOG_JSON_FORMAT", "false").lower() == "true")
    include_request_id: bool = field(default_factory=lambda: os.getenv("LOG_INCLUDE_REQUEST_ID", "true").lower() == "true")

    # Sensitive data filtering
    filter_sensitive_data: bool = field(default_factory=lambda: os.getenv("LOG_FILTER_SENSITIVE", "true").lower() == "true")
    sensitive_fields: List[str] = field(default_factory=lambda: [
        "api_key", "password", "token", "authorization"
    ])


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    enabled: bool = field(default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true")

    # Global limits
    requests_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_RPM", "60")))
    requests_per_hour: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_RPH", "1000")))
    requests_per_day: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_RPD", "10000")))

    # Translation-specific limits
    translation_rpm: int = field(default_factory=lambda: int(os.getenv("TRANSLATION_RPM", "10")))
    translation_rph: int = field(default_factory=lambda: int(os.getenv("TRANSLATION_RPH", "500")))

    # Enforcement
    block_duration: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_BLOCK_DURATION", "3600")))
    warning_threshold: float = field(default_factory=lambda: float(os.getenv("RATE_LIMIT_WARNING_THRESHOLD", "0.8")))

    # Redis backend for distributed limiting
    redis_backend: bool = field(default_factory=lambda: os.getenv("RATE_LIMIT_REDIS", "false").lower() == "true")


@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    # API key validation
    require_api_key: bool = field(default_factory=lambda: os.getenv("SECURITY_REQUIRE_API_KEY", "false").lower() == "true")
    api_key_header: str = field(default_factory=lambda: os.getenv("SECURITY_API_KEY_HEADER", "X-API-Key"))

    # Request validation
    max_text_length: int = field(default_factory=lambda: int(os.getenv("SECURITY_MAX_TEXT_LENGTH", "100000")))
    max_chunks: int = field(default_factory=lambda: int(os.getenv("SECURITY_MAX_CHUNKS", "100")))

    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    cors_methods: List[str] = field(default_factory=lambda: os.getenv("CORS_METHODS", "GET,POST").split(","))
    cors_headers: List[str] = field(default_factory=lambda: os.getenv("CORS_HEADERS", "*").split(","))

    # Content filtering
    enable_content_filter: bool = field(default_factory=lambda: os.getenv("SECURITY_CONTENT_FILTER", "true").lower() == "true")
    blocked_patterns: List[str] = field(default_factory=lambda: os.getenv(
        "SECURITY_BLOCKED_PATTERNS",
        ""
    ).split(",") if os.getenv("SECURITY_BLOCKED_PATTERNS") else [])

    # IP-based restrictions
    ip_whitelist: List[str] = field(default_factory=lambda: os.getenv("SECURITY_IP_WHITELIST", "").split(","))
    ip_blacklist: List[str] = field(default_factory=lambda: os.getenv("SECURITY_IP_BLACKLIST", "").split(","))


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and metrics."""
    enabled: bool = field(default_factory=lambda: os.getenv("MONITORING_ENABLED", "true").lower() == "true")

    # Metrics
    metrics_endpoint: str = field(default_factory=lambda: os.getenv("METRICS_ENDPOINT", "/metrics"))
    metrics_port: int = field(default_factory=lambda: int(os.getenv("METRICS_PORT", "9090")))

    # Health checks
    health_endpoint: str = field(default_factory=lambda: os.getenv("HEALTH_ENDPOINT", "/health"))
    detailed_health: bool = field(default_factory=lambda: os.getenv("HEALTH_DETAILED", "true").lower() == "true")

    # Performance tracking
    track_performance: bool = field(default_factory=lambda: os.getenv("TRACK_PERFORMANCE", "true").lower() == "true")
    slow_query_threshold_ms: int = field(default_factory=lambda: int(os.getenv("SLOW_QUERY_THRESHOLD", "1000")))

    # Error tracking
    track_errors: bool = field(default_factory=lambda: os.getenv("TRACK_ERRORS", "true").lower() == "true")
    error_sample_rate: float = field(default_factory=lambda: float(os.getenv("ERROR_SAMPLE_RATE", "1.0")))

    # External integrations
    sentry_dsn: Optional[str] = field(default_factory=lambda: os.getenv("SENTRY_DSN"))
    prometheus_gateway: Optional[str] = field(default_factory=lambda: os.getenv("PROMETHEUS_GATEWAY"))


class TranslationConfig(BaseModel):
    """Main configuration for the translation service."""
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # Component configurations
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    openai_agents: OpenAIAgentsConfig = Field(default_factory=OpenAIAgentsConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Feature flags
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "streaming": True,
        "quality_check": True,
        "chunking": True,
        "code_preservation": True,
        "html_preservation": True,
        "batch_translation": True
    })

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("environment", pre=True)
    def parse_environment(cls, v):
        """Parse environment from string."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    def __init__(self, **data):
        """Initialize configuration with environment detection."""
        # Auto-detect environment if not specified
        if "environment" not in data:
            env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
            data["environment"] = Environment(env)

        # Set debug flag based on environment
        if "debug" not in data:
            data["debug"] = data["environment"] == Environment.DEVELOPMENT

        super().__init__(**data)

        # Validate configuration
        self.validate_config()

    def validate_config(self) -> None:
        """Validate the configuration."""
        errors = []

        # Validate Gemini configuration
        if not self.gemini.api_key:
            errors.append("GEMINI_API_KEY is required")

        if self.gemini.timeout <= 0:
            errors.append("GEMINI_TIMEOUT must be positive")

        if self.gemini.max_retries < 0:
            errors.append("GEMINI_MAX_RETRIES must be non-negative")

        # Validate database URL if provided
        if self.database.url and not self.database.url.startswith(("sqlite://", "postgresql://", "mysql://")):
            errors.append("DATABASE_URL must be a valid database connection string")

        # Validate cache configuration
        if self.cache.backend == CacheBackend.REDIS and not self.cache.redis_url:
            errors.append("REDIS_URL is required when using Redis cache backend")

        # Validate rate limits
        if self.rate_limit.requests_per_minute <= 0:
            errors.append("RATE_LIMIT_RPM must be positive")

        # Log errors and raise if any
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

        logger.info("Configuration validated successfully", environment=self.environment.value)

    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "TranslationConfig":
        """Load configuration from file."""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Parse based on file extension
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")

        # Override with environment variables
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "gemini": asdict(self.gemini),
            "openai_agents": asdict(self.openai_agents),
            "cache": asdict(self.cache),
            "database": asdict(self.database),
            "logging": {
                **asdict(self.logging),
                "level": self.logging.level.value
            },
            "rate_limit": asdict(self.rate_limit),
            "security": asdict(self.security),
            "monitoring": asdict(self.monitoring),
            "features": self.features
        }

    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.to_dict()

        with open(config_path, "w", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            elif config_path.suffix.lower() == ".json":
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")

        logger.info(f"Configuration saved to {config_path}")

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing for a specific model."""
        return self.gemini.pricing.get(model, self.gemini.pricing["gemini-2.0-flash-lite"])

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature, False)

    def should_use_agents(self) -> bool:
        """Determine if OpenAI Agents SDK should be used."""
        return self.openai_agents.enabled and self.is_feature_enabled("quality_check")


# Global configuration instance
_config: Optional[TranslationConfig] = None


def get_config() -> TranslationConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = TranslationConfig()
    return _config


def load_config(config_path: Optional[Union[str, Path]] = None) -> TranslationConfig:
    """Load configuration from file or environment."""
    global _config

    if config_path:
        _config = TranslationConfig.from_file(config_path)
    else:
        _config = TranslationConfig()

    return _config


def reload_config() -> TranslationConfig:
    """Reload configuration from environment."""
    global _config
    _config = TranslationConfig()
    return _config