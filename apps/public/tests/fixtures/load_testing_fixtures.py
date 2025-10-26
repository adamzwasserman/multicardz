"""
Fixtures for load testing and performance benchmarking.
"""
import pytest
import time
import asyncio
import statistics
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient


@pytest.fixture
def performance_timer():
    """
    Measure execution time with statistics.

    Returns function that executes callable N times and returns metrics.
    """
    def time_multiple(func: Callable, iterations: int = 100, *args, **kwargs) -> Dict[str, Any]:
        """Execute function multiple times and collect timing metrics."""
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        return {
            'iterations': iterations,
            'times_ms': times,
            'avg_ms': statistics.mean(times),
            'median_ms': statistics.median(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'p95_ms': statistics.quantiles(times, n=20)[18],  # 95th percentile
            'p99_ms': statistics.quantiles(times, n=100)[98],  # 99th percentile
            'stddev_ms': statistics.stdev(times) if len(times) > 1 else 0,
            'total_time_ms': sum(times)
        }

    return time_multiple


@pytest.fixture
def concurrent_executor():
    """
    Execute functions concurrently and measure performance.

    Returns function that runs N concurrent calls and collects results.
    """
    def execute_concurrent(func: Callable, num_concurrent: int = 50, *args, **kwargs) -> Dict[str, Any]:
        """Execute function concurrently and measure total time."""
        start_time = time.perf_counter()
        results = []
        errors = []

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(func, *args, **kwargs) for _ in range(num_concurrent)]

            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        return {
            'num_concurrent': num_concurrent,
            'successful': len(results),
            'failed': len(errors),
            'total_time_ms': total_time_ms,
            'avg_time_per_request_ms': total_time_ms / num_concurrent if num_concurrent > 0 else 0,
            'results': results,
            'errors': errors
        }

    return execute_concurrent


@pytest.fixture
def http_benchmark():
    """
    Benchmark HTTP endpoint performance.

    Returns function that benchmarks TestClient requests.
    """
    def benchmark_endpoint(
        client: TestClient,
        method: str,
        path: str,
        iterations: int = 100,
        data: Dict = None,
        json_data: Dict = None
    ) -> Dict[str, Any]:
        """Benchmark HTTP endpoint with statistics."""
        times = []
        status_codes = []
        response_sizes = []

        for _ in range(iterations):
            start = time.perf_counter()

            if method.upper() == 'GET':
                response = client.get(path)
            elif method.upper() == 'POST':
                response = client.post(path, data=data, json=json_data)
            elif method.upper() == 'PUT':
                response = client.put(path, data=data, json=json_data)
            elif method.upper() == 'DELETE':
                response = client.delete(path)
            else:
                raise ValueError(f"Unsupported method: {method}")

            end = time.perf_counter()

            times.append((end - start) * 1000)
            status_codes.append(response.status_code)
            response_sizes.append(len(response.content))

        success_count = sum(1 for code in status_codes if 200 <= code < 300)

        return {
            'method': method,
            'path': path,
            'iterations': iterations,
            'success_count': success_count,
            'success_rate': (success_count / iterations) * 100,
            'avg_ms': statistics.mean(times),
            'median_ms': statistics.median(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'p95_ms': statistics.quantiles(times, n=20)[18],
            'p99_ms': statistics.quantiles(times, n=100)[98],
            'avg_response_size': statistics.mean(response_sizes),
            'status_codes': set(status_codes)
        }

    return benchmark_endpoint


@pytest.fixture
def memory_profiler():
    """
    Monitor memory usage during test execution.

    Returns function that tracks memory before/after.
    """
    def track_memory(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Track memory usage for function execution."""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Measure before
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Execute function
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        # Measure after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB

        return {
            'result': result,
            'execution_time_ms': (end_time - start_time) * 1000,
            'memory_before_mb': mem_before,
            'memory_after_mb': mem_after,
            'memory_delta_mb': mem_after - mem_before,
            'memory_growth_pct': ((mem_after - mem_before) / mem_before) * 100 if mem_before > 0 else 0
        }

    return track_memory


@pytest.fixture
def stress_test_data(db_connection):
    """
    Generate large dataset for stress testing.

    Creates realistic production-like data volumes.
    """
    import uuid
    from datetime import datetime, timedelta, UTC
    from sqlalchemy import text

    def create_stress_dataset(
        num_sessions: int = 100000,
        num_page_views: int = 500000
    ) -> Dict[str, int]:
        """Create large dataset for stress testing."""

        # Create landing pages for stress test
        landing_page_ids = []
        for i in range(10):
            page_id = uuid.uuid4()
            landing_page_ids.append(page_id)

            db_connection.execute(text("""
                INSERT INTO landing_pages (id, slug, category, name, headline, is_active, created, modified)
                VALUES (:id, :slug, 'replacement', :name, 'Stress Test', true, now(), now())
            """), {
                'id': page_id,
                'slug': f'stress-test-{i}',
                'name': f'Stress Test Page {i}'
            })

        db_connection.commit()

        # Create sessions in batches
        session_ids = []
        batch_size = 1000

        for i in range(0, num_sessions, batch_size):
            batch_count = min(batch_size, num_sessions - i)

            for j in range(batch_count):
                session_id = uuid.uuid4()
                session_ids.append(session_id)

                page_id = landing_page_ids[j % len(landing_page_ids)]
                first_seen = datetime.now(UTC) - timedelta(days=(i + j) % 90)

                db_connection.execute(text("""
                    INSERT INTO analytics_sessions
                    (session_id, landing_page_id, landing_page_slug, referrer_url, referrer_domain,
                     user_agent, ip_address, first_seen, last_seen)
                    VALUES (:sid, :lpid, :slug, 'https://google.com', 'google.com',
                            'Mozilla/5.0', :ip, :first_seen, :last_seen)
                """), {
                    'sid': session_id,
                    'lpid': page_id,
                    'slug': f'stress-test-{j % 10}',
                    'ip': f'192.168.{(i+j) // 256}.{(i+j) % 256}',
                    'first_seen': first_seen,
                    'last_seen': first_seen
                })

            db_connection.commit()

        # Create page views
        for i in range(0, num_page_views, batch_size):
            batch_count = min(batch_size, num_page_views - i)

            for j in range(batch_count):
                session_id = session_ids[(i + j) % len(session_ids)]
                page_id = landing_page_ids[j % len(landing_page_ids)]

                db_connection.execute(text("""
                    INSERT INTO analytics_page_views
                    (id, session_id, landing_page_id, url, duration_ms, scroll_depth_percent,
                     viewport_width, viewport_height, created)
                    VALUES (:id, :sid, :lpid, :url, :duration, :scroll, 1920, 1080, now())
                """), {
                    'id': uuid.uuid4(),
                    'sid': session_id,
                    'lpid': page_id,
                    'url': f'/stress-test-{j % 10}',
                    'duration': (j % 60) * 1000,
                    'scroll': min(100, (j % 10) * 10)
                })

            db_connection.commit()

        return {
            'sessions_created': len(session_ids),
            'page_views_created': num_page_views,
            'landing_pages_created': len(landing_page_ids)
        }

    return create_stress_dataset


@pytest.fixture
def cleanup_stress_data(db_connection):
    """
    Cleanup stress test data after tests complete.
    """
    yield

    # Clean up stress test data
    try:
        db_connection.rollback()
    except Exception:
        pass

    try:
        db_connection.execute(text("""
            DELETE FROM analytics_page_views WHERE landing_page_id IN (
                SELECT id FROM landing_pages WHERE slug LIKE 'stress-test-%'
            )
        """))
        db_connection.execute(text("""
            DELETE FROM analytics_events WHERE session_id IN (
                SELECT session_id FROM analytics_sessions WHERE landing_page_slug LIKE 'stress-test-%'
            )
        """))
        db_connection.execute(text("""
            DELETE FROM analytics_sessions WHERE landing_page_slug LIKE 'stress-test-%'
        """))
        db_connection.execute(text("""
            DELETE FROM landing_pages WHERE slug LIKE 'stress-test-%'
        """))
        db_connection.commit()
    except Exception:
        db_connection.rollback()
