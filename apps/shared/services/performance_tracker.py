"""
3-Layer Adaptive Performance Tracking System for MultiCardz.

Layer 1: Conservative global baselines (always available)
Layer 2: Per-session adaptive learning (personalizes to user)
Layer 3: ML telemetry hooks (optional external optimization)
"""

import logging
import os
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for performance tracking."""
    card_count: int
    unique_tags: int
    operation_type: str
    operation_count: int
    cache_hit: bool = False
    memory_delta: float = 0.0


@dataclass
class PerformanceMetrics:
    """Metrics from an execution."""
    mode: str
    context: ExecutionContext
    actual_ms: float
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class TTLCache:
    """Simple TTL cache for predictions."""

    def __init__(self, maxsize: int = 100, ttl: int = 60):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        self._lock = Lock()

    def get(self, key: tuple) -> float | None:
        """Get cached value if not expired."""
        with self._lock:
            if key in self._cache:
                if time.time() - self._timestamps[key] < self.ttl:
                    return self._cache[key]
                else:
                    # Expired
                    del self._cache[key]
                    del self._timestamps[key]
        return None

    def put(self, key: tuple, value: float) -> None:
        """Store value with TTL."""
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.maxsize and key not in self._cache:
                oldest_key = min(self._timestamps, key=self._timestamps.get)
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]

            self._cache[key] = value
            self._timestamps[key] = time.time()


class PerformanceTelemetryHook:
    """Telemetry hook for streaming to external ML services."""

    def __init__(self):
        self.handlers: list[Callable] = []
        self.buffer: deque = deque(maxlen=1000)
        self.enabled = os.getenv('MULTICARDZ_TELEMETRY_ENABLED', 'false').lower() == 'true'
        self.endpoint = os.getenv('MULTICARDZ_ML_ENDPOINT')

        if self.enabled:
            logger.info(f"Telemetry enabled, endpoint: {self.endpoint}")

    def register_handler(self, handler: Callable) -> None:
        """Register a telemetry handler."""
        self.handlers.append(handler)

    def record_execution(self, metrics: PerformanceMetrics) -> None:
        """Record execution metrics."""
        if not self.enabled:
            return

        event = {
            "timestamp": metrics.timestamp,
            "mode": metrics.mode,
            "card_count": metrics.context.card_count,
            "unique_tags": metrics.context.unique_tags,
            "operation_type": metrics.context.operation_type,
            "actual_ms": metrics.actual_ms,
            "cache_hit": metrics.context.cache_hit,
            "memory_delta": metrics.context.memory_delta,
        }

        # Add to buffer
        self.buffer.append(event)

        # Stream to handlers asynchronously
        for handler in self.handlers:
            try:
                handler(event)
            except Exception as e:
                logger.debug(f"Telemetry handler error: {e}")

    def get_prediction_async(self, mode: str, context: ExecutionContext,
                            timeout_ms: int = 5) -> float | None:
        """Get prediction from ML service (non-blocking)."""
        if not self.endpoint:
            return None

        # In production, this would make an async HTTP request
        # For now, return None to use local predictions
        return None

    def is_connected(self) -> bool:
        """Check if ML service is available."""
        return self.endpoint is not None


class AdaptivePerformanceTracker:
    """
    3-Layer Adaptive Performance Tracker.

    Layer 1: Conservative global baselines
    Layer 2: Per-session adaptive learning
    Layer 3: ML telemetry integration
    """

    def __init__(self):
        # Layer 1: Global baselines (conservative defaults)
        # These are tuned based on actual measurements
        self.global_baseline = {
            "regular": {
                "slope": 0.0015,  # ms per card
                "intercept": 0.2,  # base overhead
                "tag_factor": 0.01  # additional cost per unique tag
            },
            "parallel": {
                "slope": 0.001,
                "intercept": 2.0,  # thread startup cost
                "tag_factor": 0.008
            },
            "turbo_bitmap": {
                "slope": 0.0003,
                "intercept": 15.0,  # bitmap construction overhead
                "tag_factor": 0.005
            },
            "roaring_bitmap": {
                "slope": 0.0002,
                "intercept": 8.0,
                "tag_factor": 0.003
            }
        }

        # Layer 2: Per-session adaptive learning
        self.session_history = defaultdict(lambda: deque(maxlen=20))
        self.session_models = {}
        self.confidence = 0.0
        self._lock = Lock()

        # Layer 3: ML telemetry
        self.telemetry = PerformanceTelemetryHook()
        self.ml_cache = TTLCache(maxsize=100, ttl=60)

    def predict_time(self, mode: str, context: ExecutionContext) -> float:
        """
        Predict execution time for a given mode and context.
        Combines all three layers of prediction.
        """
        # Layer 1: Start with global baseline
        baseline = self.global_baseline.get(mode, self.global_baseline["regular"])
        predicted = (
            baseline["intercept"] +
            baseline["slope"] * context.card_count +
            baseline["tag_factor"] * context.unique_tags
        )

        # Layer 2: Blend with session-specific learning
        session_key = (mode, context.operation_type)
        if session_key in self.session_models and self.confidence > 0.1:
            session_pred = self._predict_from_history(mode, context)
            if session_pred is not None:
                # Weighted average based on confidence
                predicted = (1 - self.confidence) * predicted + self.confidence * session_pred

        # Layer 3: Check ML service prediction
        cache_key = (mode, context.card_count, context.unique_tags, context.operation_type)
        ml_prediction = self.ml_cache.get(cache_key)

        if ml_prediction is None and self.telemetry.is_connected():
            # Try to get from ML service
            ml_prediction = self.telemetry.get_prediction_async(mode, context)
            if ml_prediction is not None:
                self.ml_cache.put(cache_key, ml_prediction)

        if ml_prediction is not None:
            # Trust ML service more (70% weight)
            ml_weight = 0.7
            predicted = (1 - ml_weight) * predicted + ml_weight * ml_prediction

        return max(0.1, predicted)  # Never predict negative time

    def _predict_from_history(self, mode: str, context: ExecutionContext) -> float | None:
        """Predict based on session history using simple linear regression."""
        session_key = (mode, context.operation_type)
        history = self.session_history[session_key]

        if len(history) < 3:
            return None

        # Simple linear regression on recent history
        x_values = [m.context.card_count for m in history]
        y_values = [m.actual_ms for m in history]

        n = len(x_values)
        if n == 0:
            return None

        # Calculate slope and intercept
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=False))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Predict for current context
        return max(0.1, intercept + slope * context.card_count)

    def record_actual(self, metrics: PerformanceMetrics) -> None:
        """Record actual performance metrics for learning."""
        with self._lock:
            # Update Layer 2: Session history
            session_key = (metrics.mode, metrics.context.operation_type)
            self.session_history[session_key].append(metrics)

            # Increase confidence as we gather more data
            self.confidence = min(0.8, self.confidence + 0.02)

        # Stream to Layer 3: Telemetry
        self.telemetry.record_execution(metrics)

    def select_best_mode(self, context: ExecutionContext,
                        available_modes: list[str]) -> str:
        """
        Select the best processing mode based on predictions.
        This replaces the static threshold-based selection.
        """
        predictions = {}

        for mode in available_modes:
            predicted_time = self.predict_time(mode, context)
            predictions[mode] = predicted_time

        # Add small penalty for bitmap modes to account for memory overhead
        if "turbo_bitmap" in predictions:
            predictions["turbo_bitmap"] *= 1.1
        if "roaring_bitmap" in predictions:
            predictions["roaring_bitmap"] *= 1.05

        # Select mode with lowest predicted time
        best_mode = min(predictions, key=predictions.get)

        logger.debug(
            f"Mode selection for {context.card_count} cards: "
            f"{best_mode} (predicted {predictions[best_mode]:.2f}ms)"
        )

        return best_mode

    def get_stats(self) -> dict[str, Any]:
        """Get tracker statistics."""
        stats = {
            "confidence": self.confidence,
            "session_samples": sum(len(h) for h in self.session_history.values()),
            "ml_connected": self.telemetry.is_connected(),
            "ml_cache_size": len(self.ml_cache._cache),
        }
        return stats


# Global singleton instance
_tracker_instance = None
_tracker_lock = Lock()


def get_performance_tracker() -> AdaptivePerformanceTracker:
    """Get the global performance tracker instance."""
    global _tracker_instance

    if _tracker_instance is None:
        with _tracker_lock:
            if _tracker_instance is None:
                _tracker_instance = AdaptivePerformanceTracker()

    return _tracker_instance
