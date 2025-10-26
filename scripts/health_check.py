"""
Health Check and Performance Monitoring for multicardz™ on Render.

Provides real-time performance metrics and system health information
for monitoring set operations performance in production.
"""

import json
import multiprocessing
import time
from datetime import datetime
from typing import Any

import psutil

from apps.shared.models.card import CardSummary
from apps.shared.services.set_operations_unified import (
    apply_unified_operations,
    get_unified_metrics,
)


class PerformanceHealthCheck:
    """Health check service for performance monitoring."""

    def __init__(self):
        """Initialize health check service."""
        self.startup_time = datetime.utcnow()
        self.last_benchmark = None
        self.benchmark_history = []

    def get_system_info(self) -> dict[str, Any]:
        """Get system information for monitoring."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)

            return {
                "cpu_count": multiprocessing.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent,
                "uptime_hours": (datetime.utcnow() - self.startup_time).total_seconds()
                / 3600,
            }
        except Exception as e:
            return {"error": f"Failed to get system info: {e}"}

    def run_performance_benchmark(self, card_count: int = 1000) -> dict[str, Any]:
        """Run a quick performance benchmark."""
        try:
            # Generate test cards
            cards = []
            for i in range(card_count):
                card = CardSummary(
                    id=f"HEALTH{i:04d}",
                    title=f"Health Check Card {i}",
                    tags=frozenset(
                        ["test", "health"] if i % 2 == 0 else ["test", "monitor"]
                    ),
                )
                cards.append(card)

            cards_set = frozenset(cards)
            operations = [("intersection", [("test", card_count)])]

            # Run benchmark
            start_time = time.perf_counter()
            result = apply_unified_operations(cards_set, operations)
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            benchmark_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "card_count": card_count,
                "execution_time_ms": round(execution_time_ms, 2),
                "results_count": len(result.cards),
                "operations_applied": result.operations_applied,
                "cache_hit": result.cache_hit,
                "short_circuited": result.short_circuited,
                "cards_per_ms": round(card_count / execution_time_ms, 2)
                if execution_time_ms > 0
                else 0,
            }

            # Store benchmark history (keep last 10)
            self.benchmark_history.append(benchmark_result)
            if len(self.benchmark_history) > 10:
                self.benchmark_history.pop(0)

            self.last_benchmark = benchmark_result
            return benchmark_result

        except Exception as e:
            return {"error": f"Benchmark failed: {e}"}

    def get_cache_health(self) -> dict[str, Any]:
        """Get cache health information."""
        try:
            unified_metrics = get_unified_metrics()

            return {
                "cache_hit_rate": unified_metrics.cache_hit_rate,
                "total_time_ms": unified_metrics.total_time_ms,
                "processing_mode": unified_metrics.processing_mode,
                "parallel_workers": unified_metrics.parallel_workers,
                "operations_count": unified_metrics.operations_count,
            }
        except Exception as e:
            return {"error": f"Failed to get cache health: {e}"}

    def get_render_config(self) -> dict[str, Any]:
        """Get Render deployment configuration."""
        try:
            from render_performance_config import render_config

            return {
                "is_render": render_config.is_render,
                "plan_tier": render_config.plan_tier,
                "cpu_count": render_config.cpu_count,
                "memory_gb": round(render_config.memory_gb, 2),
                "optimal_settings": render_config.get_optimal_settings(100000),
                "performance_expectations": render_config.get_performance_expectations(),
            }
        except ImportError:
            return {"render_config": "not_available"}
        except Exception as e:
            return {"error": f"Failed to get Render config: {e}"}

    def health_check(self) -> dict[str, Any]:
        """Complete health check with all metrics."""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": self.get_system_info(),
            "cache": self.get_cache_health(),
            "render": self.get_render_config(),
            "last_benchmark": self.last_benchmark,
            "benchmark_history_count": len(self.benchmark_history),
        }

        # Determine overall health status
        system_info = health_data["system"]
        if isinstance(system_info, dict) and "memory_percent" in system_info:
            if system_info["memory_percent"] > 90:
                health_data["status"] = "warning"
                health_data["warnings"] = ["High memory usage"]
            elif system_info["cpu_percent"] > 90:
                health_data["status"] = "warning"
                health_data["warnings"] = health_data.get("warnings", []) + [
                    "High CPU usage"
                ]

        return health_data

    def performance_report(self) -> dict[str, Any]:
        """Detailed performance report."""
        # Run fresh benchmark
        benchmark_1k = self.run_performance_benchmark(1000)
        benchmark_5k = self.run_performance_benchmark(5000)

        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "system_info": self.get_system_info(),
            "render_config": self.get_render_config(),
            "benchmarks": {"1k_cards": benchmark_1k, "5k_cards": benchmark_5k},
            "cache_status": self.get_cache_health(),
            "benchmark_history": self.benchmark_history,
            "performance_targets": {
                "1k_cards": "< 10ms",
                "5k_cards": "< 25ms",
                "10k_cards": "< 50ms",
                "status": {
                    "1k_met": benchmark_1k.get("execution_time_ms", 999) < 10,
                    "5k_met": benchmark_5k.get("execution_time_ms", 999) < 25,
                },
            },
        }


# Global health check instance
health_checker = PerformanceHealthCheck()


def health_endpoint() -> str:
    """Health check endpoint for Render."""
    health_data = health_checker.health_check()
    return json.dumps(health_data, indent=2)


def performance_endpoint() -> str:
    """Performance report endpoint."""
    performance_data = health_checker.performance_report()
    return json.dumps(performance_data, indent=2)


def quick_health() -> dict[str, Any]:
    """Quick health check for frequent monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "memory_percent": psutil.virtual_memory().percent,
        "cpu_count": multiprocessing.cpu_count(),
        "uptime_hours": round(
            (datetime.utcnow() - health_checker.startup_time).total_seconds() / 3600, 2
        ),
    }


# CLI interface for manual testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        card_count = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        result = health_checker.run_performance_benchmark(card_count)
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "report":
        result = health_checker.performance_report()
        print(json.dumps(result, indent=2))
    else:
        result = health_checker.health_check()
        print(json.dumps(result, indent=2))
