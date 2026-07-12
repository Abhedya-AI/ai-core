"""
Project-wide constants.

Import from here — never hardcode strings or magic numbers in modules.
"""

# ── API ───────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
APP_VERSION = "1.0.0"

# ── Database ──────────────────────────────────────────────────────────────────
DB_CONNECT_TIMEOUT = 3          # seconds
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10

# ── LLM ──────────────────────────────────────────────────────────────────────
LLM_MAX_TOKENS = 8192
LLM_TEMPERATURE = 0.1

# ── Retrieval ────────────────────────────────────────────────────────────────
RETRIEVAL_TOP_K = 10
RERANK_TOP_N = 5
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
