"""
HOLOGIX Constants

Global constants used throughout the HOLOGIX system.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class APIConstants:
    """API-related constants."""
    API_VERSION: str = "v1"
    DEFAULT_TIMEOUT_SECONDS: int = 300
    MAX_TOKENS_DEFAULT: int = 2048
    MAX_TOKENS_LIMIT: int = 128000
    CHUNK_SIZE_BYTES: int = 8192
    SSE_CONTENT_TYPE: str = "text/event-stream"
    
    # OpenAI compatible endpoints
    CHAT_COMPLETIONS_PATH: str = "/chat/completions"
    COMPLETIONS_PATH: str = "/completions"
    EMBEDDINGS_PATH: str = "/embeddings"
    MODELS_PATH: str = "/models"
    FILES_PATH: str = "/files"
    AUDIO_TRANSCRIPTIONS_PATH: str = "/audio/transcriptions"
    AUDIO_SPEECH_PATH: str = "/audio/speech"
    IMAGES_GENERATIONS_PATH: str = "/images/generations"
    
    # Response defaults
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_TOP_P: float = 1.0
    DEFAULT_FREQUENCY_PENALTY: float = 0.0
    DEFAULT_PRESENCE_PENALTY: float = 0.0


@dataclass
class ModelConstants:
    """Model-related constants."""
    SUPPORTED_FORMATS: List[str] = field(default_factory=lambda: [
        "gguf", "safetensors", "pytorch", "onnx", "tensorrt"
    ])
    QUANTIZATION_TYPES: List[str] = field(default_factory=lambda: [
        "q4_0", "q4_1", "q5_0", "q5_1", "q8_0", 
        "f16", "f32", "ternary", "int4", "int8"
    ])
    MODEL_TYPES: List[str] = field(default_factory=lambda: [
        "llm", "embedding", "vision", "audio", "multimodal"
    ])
    
    # Download settings
    DOWNLOAD_CHUNK_SIZE: int = 8388608  # 8MB
    DOWNLOAD_TIMEOUT: int = 3600  # 1 hour
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5
    
    # HuggingFace
    HF_BASE_URL: str = "https://huggingface.co"
    HF_API_BASE: str = "https://huggingface.co/api"


@dataclass
class EngineConstants:
    """Engine-related constants."""
    TENSOR_DTYPE_MAP: Dict[str, str] = field(default_factory=lambda: {
        "f32": "float32",
        "f16": "float16",
        "bf16": "bfloat16",
        "i8": "int8",
        "i4": "int4",
        "ternary": "ternary",
    })
    
    # Memory limits
    DEFAULT_RAM_LIMIT_MB: int = 4096
    MIN_RAM_REQUIREMENT_MB: int = 512
    VRAM_THRESHOLD_MB: int = 2048
    
    # Sparse execution
    MAX_EXPERTS_PER_LAYER: int = 64
    ACTIVE_EXPERTS_DEFAULT: int = 2
    EXPERT_CACHE_LINES: int = 8
    
    # KV Cache
    KV_CACHE_BLOCK_SIZE: int = 256
    KV_SWAP_FILE_PREFIX: str = "kv_swap_"


@dataclass
class SecurityConstants:
    """Security-related constants."""
    API_KEY_HEADER: str = "Authorization"
    API_KEY_PREFIX: str = "Bearer"
    CUSTOM_KEY_HEADER: str = "X-API-Key"
    
    # Key generation
    DEFAULT_KEY_LENGTH: int = 32
    KEY_CHARSET: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    # Rate limiting
    RATE_LIMIT_HEADER: str = "X-RateLimit-Limit"
    RATE_LIMIT_REMAINING_HEADER: str = "X-RateLimit-Remaining"
    RATE_LIMIT_RESET_HEADER: str = "X-RateLimit-Reset"
    
    # LAN security
    PRIVATE_IP_RANGES: List[str] = field(default_factory=lambda: [
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
    ])


@dataclass
class DatabaseConstants:
    """Database-related constants."""
    TABLE_MODELS: str = "models"
    TABLE_API_KEYS: str = "api_keys"
    TABLE_REQUESTS: str = "requests"
    TABLE_USAGE: str = "usage"
    TABLE_JOBS: str = "jobs"
    TABLE_ARTIFACTS: str = "artifacts"
    
    # Schema versions
    SCHEMA_VERSION: int = 1


@dataclass
class LoggingConstants:
    """Logging-related constants."""
    LOGGER_NAME: str = "hologix"
    LOG_LEVELS: Dict[str, int] = field(default_factory=lambda: {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    })


@dataclass
class FileConstants:
    """File and path constants."""
    CONFIG_FILENAME: str = "config.yaml"
    API_KEYS_FILENAME: str = "api_keys.yaml"
    DATABASE_FILENAME: str = "hologix.db"
    LOG_FILENAME: str = "hologix.log"
    
    # Model files
    MODEL_CONFIG_FILENAME: str = "config.json"
    MODEL_MANIFEST_FILENAME: str = "manifest.yaml"
    TOKENIZER_FILENAME: str = "tokenizer.json"
    
    # Temp directories
    TEMP_DIR_PREFIX: str = "hologix_tmp_"


@dataclass
class ErrorCodes:
    """Error code definitions."""
    SUCCESS: int = 0
    ERROR_GENERIC: int = 1000
    ERROR_AUTH_FAILED: int = 1001
    ERROR_RATE_LIMITED: int = 1002
    ERROR_MODEL_NOT_FOUND: int = 1003
    ERROR_MODEL_LOAD_FAILED: int = 1004
    ERROR_INVALID_REQUEST: int = 1005
    ERROR_TIMEOUT: int = 1006
    ERROR_QUEUE_FULL: int = 1007
    ERROR_DISK_FULL: int = 1008
    ERROR_UNSUPPORTED_FORMAT: int = 1009
    ERROR_HARDWARE_INCOMPATIBLE: int = 1010


class Constants:
    """Main constants container."""
    
    def __init__(self):
        self.api = APIConstants()
        self.model = ModelConstants()
        self.engine = EngineConstants()
        self.security = SecurityConstants()
        self.database = DatabaseConstants()
        self.logging = LoggingConstants()
        self.files = FileConstants()
        self.errors = ErrorCodes()


# Global constants instance
constants = Constants()
