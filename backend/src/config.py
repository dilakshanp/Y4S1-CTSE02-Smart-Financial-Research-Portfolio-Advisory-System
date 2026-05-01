"""
Configuration Module for the Smart Financial Research MAS.

Centralizes all system configuration including LLM settings,
database paths, logging configuration, and directory paths.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# Project Root Directory
# ============================================
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# ============================================
# Ollama / LLM Configuration
# ============================================
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:8b")

# LLM parameters for deterministic financial analysis
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ============================================
# Database Configuration
# ============================================
DATABASE_PATH: Path = PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/research_db.sqlite")

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: Path = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")

# ============================================
# Reports Configuration
# ============================================
REPORTS_DIR: Path = PROJECT_ROOT / os.getenv("REPORTS_DIR", "reports")

# ============================================
# Ensure directories exist
# ============================================
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ============================================
# Agent Configuration Defaults
# ============================================
AGENT_CONFIG = {
    "max_iterations": 10,
    "max_rpm": 30,  # Rate limit for LLM requests per minute
    "verbose": True,
    "allow_delegation": False,
}

# ============================================
# Tool Configuration
# ============================================
MARKET_DATA_DEFAULT_PERIOD: str = "1mo"
SENTIMENT_MAX_ARTICLES: int = 5
RISK_FREE_RATE: float = 0.05  # Annual risk-free rate for Sharpe ratio calculation
