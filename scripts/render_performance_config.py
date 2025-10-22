"""
Render Deployment Performance Configuration for multicardz™.

Optimizes set operations performance based on Render's infrastructure
characteristics and automatically detects available resources.
"""

import logging
import multiprocessing
import os
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class RenderPerformanceConfig:
    """Performance configuration optimized for Render deployment."""

    def __init__(self):
        """Initialize with Render environment detection."""
        self.is_render = self._detect_render_environment()
        self.plan_tier = self._detect_render_plan()
        self.cpu_count = multiprocessing.cpu_count()
        self.memory_gb = self._get_available_memory_gb()

        logger.info(f"Render deployment detected: {self.is_render}")
        logger.info(f"Plan tier: {self.plan_tier}")
        logger.info(f"CPU cores: {self.cpu_count}")
        logger.info(f"Memory: {self.memory_gb:.1f}GB")

    def _detect_render_environment(self) -> bool:
        """Detect if running on Render."""
        render_indicators = [
            "RENDER",
            "RENDER_SERVICE_NAME",
            "RENDER_SERVICE_ID",
            "RENDER_EXTERNAL_URL",
        ]
        return any(env_var in os.environ for env_var in render_indicators)

    def _detect_render_plan(self) -> str:
        """Detect Render plan based on available resources."""
        if not self.is_render:
            return "local"

        cpu_count = multiprocessing.cpu_count()
        memory_gb = self._get_available_memory_gb()

        if cpu_count >= 4 and memory_gb >= 7:
            return "pro_plus"
        elif cpu_count >= 2 and memory_gb >= 3:
            return "pro"
        elif cpu_count >= 1 and memory_gb >= 1.5:
            return "standard"
        else:
            return "starter"

    def _get_available_memory_gb(self) -> float:
        """Get available memory in GB."""
        try:
            memory = psutil.virtual_memory()
            return memory.total / (1024**3)
        except:
            # Fallback estimation
            return 2.0

    def get_optimal_settings(self, card_count: int) -> dict[str, Any]:
        """Get optimal settings for given card count and Render plan."""
        settings = {
            "use_cache": True,
            "use_parallel": False,
            "use_turbo": False,
            "chunk_size": 1000,
            "max_cache_entries": 50,
            "enable_monitoring": True,
        }

        # Render-specific optimizations
        if self.plan_tier == "starter":
            # Starter plan: Very limited resources
            settings.update(
                {
                    "use_cache": card_count < 10000,  # Limited memory
                    "use_parallel": False,  # Single core
                    "use_turbo": card_count > 50000,  # Bitmap efficiency
                    "chunk_size": 500,  # Small chunks
                    "max_cache_entries": 25,  # Minimal cache
                    "card_limit": 100000,  # Hard limit for safety
                }
            )

        elif self.plan_tier == "standard":
            # Standard plan: 1 vCPU, 2GB RAM
            settings.update(
                {
                    "use_cache": True,
                    "use_parallel": False,  # Single vCPU
                    "use_turbo": card_count > 75000,
                    "chunk_size": 1000,
                    "max_cache_entries": 100,
                    "card_limit": 500000,
                }
            )

        elif self.plan_tier == "pro":
            # Pro plan: 2 vCPUs, 4GB RAM
            settings.update(
                {
                    "use_cache": True,
                    "use_parallel": card_count > 25000,  # Multi-core available
                    "use_turbo": card_count > 100000,
                    "chunk_size": 2000,
                    "max_cache_entries": 200,
                    "card_limit": 1000000,
                }
            )

        elif self.plan_tier == "pro_plus":
            # Pro Plus plan: 4 vCPUs, 8GB RAM - Full optimization
            settings.update(
                {
                    "use_cache": True,
                    "use_parallel": card_count > 10000,
                    "use_turbo": card_count > 50000,
                    "chunk_size": 5000,
                    "max_cache_entries": 500,
                    "card_limit": 2000000,
                }
            )

        else:
            # Local development: Full capabilities
            settings.update(
                {
                    "use_cache": True,
                    "use_parallel": card_count > 50000,
                    "use_turbo": card_count > 100000,
                    "chunk_size": card_count // (self.cpu_count * 4)
                    if card_count > 10000
                    else 1000,
                    "max_cache_entries": 1000,
                    "card_limit": 5000000,
                }
            )

        return settings

    def get_performance_expectations(self) -> dict[str, str]:
        """Get expected performance for different card counts."""
        expectations = {
            "starter": {
                "1k": "20-50ms",
                "5k": "100-200ms",
                "10k": "300-600ms",
                "50k": "2-5 seconds",
                "100k": "5-15 seconds (may timeout)",
                "1M": "Not recommended (memory limits)",
            },
            "standard": {
                "1k": "10-20ms",
                "5k": "50-100ms",
                "10k": "150-300ms",
                "50k": "1-3 seconds",
                "100k": "3-8 seconds",
                "1M": "30-60 seconds (may timeout)",
            },
            "pro": {
                "1k": "5-15ms",
                "5k": "25-50ms",
                "10k": "75-150ms",
                "50k": "500ms-1.5s",
                "100k": "1.5-4 seconds",
                "1M": "15-30 seconds",
            },
            "pro_plus": {
                "1k": "<10ms ✅",
                "5k": "<25ms ✅",
                "10k": "<50ms ✅",
                "50k": "<300ms ✅",
                "100k": "<1 second ✅",
                "1M": "<10 seconds ✅",
            },
        }

        return expectations.get(self.plan_tier, expectations["standard"])

    def recommend_render_plan(
        self, expected_card_count: int, target_response_time_ms: int
    ) -> str:
        """Recommend optimal Render plan for requirements."""
        if expected_card_count <= 10000 and target_response_time_ms >= 500:
            return "Standard Plan ($25/month) - Good for small to medium datasets"
        elif expected_card_count <= 100000 and target_response_time_ms >= 1000:
            return "Pro Plan ($85/month) - Good for large datasets with reasonable performance"
        elif expected_card_count <= 1000000 and target_response_time_ms >= 5000:
            return "Pro Plus Plan ($185/month) - Required for very large datasets"
        else:
            return "Pro Plus Plan ($185/month) - Maximum performance for enterprise use"


# Global configuration instance
render_config = RenderPerformanceConfig()


def get_render_optimized_settings(card_count: int) -> dict[str, Any]:
    """Get Render-optimized settings for given card count."""
    return render_config.get_optimal_settings(card_count)


def apply_render_optimizations():
    """Apply Render-specific optimizations to set operations."""
    from apps.shared.services import operation_cache

    # Adjust cache settings based on Render plan
    settings = render_config.get_optimal_settings(100000)  # Representative size

    # Update global cache settings
    if hasattr(operation_cache, "_operation_cache"):
        cache_instance = operation_cache.get_operation_cache()

        # Adjust cache limits based on available memory
        if render_config.plan_tier == "starter":
            cache_instance.max_entries = 25
            cache_instance.max_memory_bytes = 10 * 1024 * 1024  # 10MB
        elif render_config.plan_tier == "standard":
            cache_instance.max_entries = 100
            cache_instance.max_memory_bytes = 50 * 1024 * 1024  # 50MB
        elif render_config.plan_tier == "pro":
            cache_instance.max_entries = 200
            cache_instance.max_memory_bytes = 100 * 1024 * 1024  # 100MB
        else:  # pro_plus or local
            cache_instance.max_entries = 500
            cache_instance.max_memory_bytes = 200 * 1024 * 1024  # 200MB


def render_performance_middleware(card_count: int):
    """Middleware to validate performance expectations on Render."""
    settings = render_config.get_optimal_settings(card_count)

    # Check if operation is within limits
    if card_count > settings.get("card_limit", 1000000):
        raise ValueError(
            f"Card count {card_count:,} exceeds limit for {render_config.plan_tier} plan. "
            f"Consider upgrading to a higher Render plan or reducing dataset size."
        )

    # Log performance expectations
    expectations = render_config.get_performance_expectations()
    if card_count >= 1000000:
        expected_time = expectations.get("1M", "Unknown")
    elif card_count >= 100000:
        expected_time = expectations.get("100k", "Unknown")
    elif card_count >= 50000:
        expected_time = expectations.get("50k", "Unknown")
    elif card_count >= 10000:
        expected_time = expectations.get("10k", "Unknown")
    elif card_count >= 5000:
        expected_time = expectations.get("5k", "Unknown")
    else:
        expected_time = expectations.get("1k", "Unknown")

    logger.info(
        f"Processing {card_count:,} cards on Render {render_config.plan_tier} plan"
    )
    logger.info(f"Expected performance: {expected_time}")

    return settings


# Auto-apply optimizations on import
if render_config.is_render:
    apply_render_optimizations()
    logger.info(f"Applied Render optimizations for {render_config.plan_tier} plan")
