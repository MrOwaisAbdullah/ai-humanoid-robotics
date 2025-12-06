"""
Performance monitoring for RAG backend.

Tracks metrics, response times, and system health.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import psutil
import json

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Tracks performance metrics for the RAG system."""

    def __init__(
        self,
        max_history_size: int = 1000,
        cleanup_interval: int = 300  # 5 minutes
    ):
        self.max_history_size = max_history_size
        self.cleanup_interval = cleanup_interval

        # Metrics storage
        self.request_times: deque = deque(maxlen=max_history_size)
        self.token_usage: Dict[str, List[int]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.endpoint_counts: Dict[str, int] = defaultdict(int)

        # System metrics
        self.cpu_usage: deque = deque(maxlen=60)  # Last 60 data points
        self.memory_usage: deque = deque(maxlen=60)

        # Last cleanup time
        self.last_cleanup = datetime.utcnow()

    def record_request(
        self,
        endpoint: str,
        duration: float,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Record a request metric."""
        # Record request time
        self.request_times.append({
            "timestamp": datetime.utcnow(),
            "endpoint": endpoint,
            "duration": duration
        })

        # Update endpoint count
        self.endpoint_counts[endpoint] += 1

        # Record token usage
        if tokens_used:
            self.token_usage[endpoint].append(tokens_used)
            # Keep only last 100 entries per endpoint
            if len(self.token_usage[endpoint]) > 100:
                self.token_usage[endpoint] = self.token_usage[endpoint][-100:]

        # Record error
        if error:
            self.error_counts[error] += 1

    async def collect_system_metrics(self):
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.append({
                "timestamp": datetime.utcnow(),
                "value": cpu_percent
            })

            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.append({
                "timestamp": datetime.utcnow(),
                "value": memory.percent,
                "used_gb": memory.used / (1024**3),
                "total_gb": memory.total / (1024**3)
            })

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")

    def get_request_metrics(
        self,
        minutes: int = 5
    ) -> Dict[str, Any]:
        """Get request metrics for the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        # Filter recent requests
        recent_requests = [
            r for r in self.request_times
            if r["timestamp"] > cutoff_time
        ]

        if not recent_requests:
            return {
                "count": 0,
                "avg_duration": 0,
                "p95_duration": 0,
                "p99_duration": 0,
                "error_rate": 0,
                "requests_per_minute": 0
            }

        # Calculate metrics
        durations = [r["duration"] for r in recent_requests]
        durations.sort()

        error_count = sum(
            1 for r in recent_requests
            if r.get("error")
        )

        return {
            "count": len(recent_requests),
            "avg_duration": sum(durations) / len(durations),
            "p95_duration": durations[int(len(durations) * 0.95)] if durations else 0,
            "p99_duration": durations[int(len(durations) * 0.99)] if durations else 0,
            "error_rate": error_count / len(recent_requests),
            "requests_per_minute": len(recent_requests) / minutes,
            "endpoint_breakdown": self._get_endpoint_breakdown(recent_requests)
        }

    def _get_endpoint_breakdown(
        self,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Get breakdown of metrics by endpoint."""
        breakdown = defaultdict(lambda: {
            "count": 0,
            "total_duration": 0,
            "errors": 0
        })

        for req in requests:
            endpoint = req["endpoint"]
            breakdown[endpoint]["count"] += 1
            breakdown[endpoint]["total_duration"] += req["duration"]
            if req.get("error"):
                breakdown[endpoint]["errors"] += 1

        # Calculate averages
        result = {}
        for endpoint, metrics in breakdown.items():
            avg_duration = metrics["total_duration"] / metrics["count"]
            result[endpoint] = {
                "count": metrics["count"],
                "avg_duration": avg_duration,
                "error_rate": metrics["errors"] / metrics["count"],
                "tokens_used_avg": self._get_avg_tokens(endpoint)
            }

        return result

    def _get_avg_tokens(self, endpoint: str) -> float:
        """Get average token usage for an endpoint."""
        tokens = self.token_usage.get(endpoint, [])
        return sum(tokens) / len(tokens) if tokens else 0

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        # Get latest CPU and memory data
        latest_cpu = self.cpu_usage[-1] if self.cpu_usage else None
        latest_memory = self.memory_usage[-1] if self.memory_usage else None

        return {
            "cpu": {
                "current": latest_cpu["value"] if latest_cpu else 0,
                "avg_1min": sum(d["value"] for d in list(self.cpu_usage)[-60:]) / min(60, len(self.cpu_usage))
            },
            "memory": {
                "current_percent": latest_memory["value"] if latest_memory else 0,
                "used_gb": latest_memory["used_gb"] if latest_memory else 0,
                "total_gb": latest_memory["total_gb"] if latest_memory else 0
            }
        }

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        # Get recent errors (last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        recent_requests = [
            r for r in self.request_times
            if r["timestamp"] > cutoff_time and r.get("error")
        ]

        # Group by error type
        error_groups = defaultdict(list)
        for req in recent_requests:
            error = req["error"]
            error_groups[error].append(req["timestamp"])

        # Create summary
        summary = {}
        for error, timestamps in error_groups.items():
            summary[error] = {
                "count": len(timestamps),
                "last_occurrence": max(timestamps).isoformat(),
                "rate_per_hour": len(timestamps)
            }

        return summary

    def get_health_score(self) -> Dict[str, Any]:
        """Calculate overall health score."""
        # Get recent metrics
        request_metrics = self.get_request_metrics()
        system_metrics = self.get_system_metrics()

        score = 100
        issues = []

        # Check error rate (penalize high error rates)
        if request_metrics["error_rate"] > 0.1:  # 10% error rate
            score -= 30
            issues.append("High error rate")
        elif request_metrics["error_rate"] > 0.05:  # 5% error rate
            score -= 15
            issues.append("Elevated error rate")

        # Check response times
        if request_metrics["p95_duration"] > 5.0:  # 5 seconds
            score -= 20
            issues.append("Slow response times")
        elif request_metrics["p95_duration"] > 3.0:  # 3 seconds
            score -= 10
            issues.append("Elevated response times")

        # Check system resources
        if system_metrics["cpu"]["current"] > 90:
            score -= 25
            issues.append("High CPU usage")
        elif system_metrics["cpu"]["current"] > 80:
            score -= 10
            issues.append("Elevated CPU usage")

        if system_metrics["memory"]["current_percent"] > 90:
            score -= 25
            issues.append("High memory usage")
        elif system_metrics["memory"]["current_percent"] > 80:
            score -= 10
            issues.append("Elevated memory usage")

        # Determine status
        if score >= 90:
            status = "excellent"
        elif score >= 75:
            status = "good"
        elif score >= 60:
            status = "degraded"
        else:
            status = "poor"

        return {
            "score": max(0, score),
            "status": status,
            "issues": issues,
            "request_metrics": request_metrics,
            "system_metrics": system_metrics
        }

    def cleanup_old_metrics(self):
        """Remove old metrics data."""
        current_time = datetime.utcnow()

        # Check if cleanup is needed
        if (current_time - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return

        # Clean old request data (older than 1 hour)
        cutoff_time = current_time - timedelta(hours=1)
        self.request_times = deque(
            (r for r in self.request_times if r["timestamp"] > cutoff_time),
            maxlen=self.max_history_size
        )

        # Clean old system metrics (older than 1 hour)
        self.cpu_usage = deque(
            (c for c in self.cpu_usage if c["timestamp"] > cutoff_time),
            maxlen=60
        )
        self.memory_usage = deque(
            (m for m in self.memory_usage if m["timestamp"] > cutoff_time),
            maxlen=60
        )

        # Reset error counts periodically
        if current_time.hour == 0:  # At midnight
            self.error_counts.clear()

        self.last_cleanup = current_time
        logger.info("Cleaned up old metrics")

    def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": self.get_health_score(),
            "request_metrics": {
                "last_5min": self.get_request_metrics(5),
                "last_1hour": self.get_request_metrics(60)
            },
            "system_metrics": self.get_system_metrics(),
            "error_summary": self.get_error_summary(),
            "endpoint_stats": {
                endpoint: count for endpoint, count in self.endpoint_counts.items()
            },
            "total_requests": len(self.request_times),
            "uptime_hours": (
                (datetime.utcnow() - self.request_times[0]["timestamp"]).total_seconds() / 3600
                if self.request_times else 0
            )
        }


class MetricsCollector:
    """Periodic metrics collector."""

    def __init__(
        self,
        metrics: PerformanceMetrics,
        collection_interval: int = 30  # 30 seconds
    ):
        self.metrics = metrics
        self.collection_interval = collection_interval
        self.running = False
        self.task = None

    async def start(self):
        """Start the metrics collector."""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collector started")

    async def stop(self):
        """Stop the metrics collector."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _collection_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                await self.metrics.collect_system_metrics()
                self.metrics.cleanup_old_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                await asyncio.sleep(self.collection_interval)


# Performance decorator for endpoints
def monitor_performance(metrics: PerformanceMetrics):
    """Decorator to monitor endpoint performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = func.__name__
            error = None
            tokens_used = None

            try:
                result = await func(*args, **kwargs)

                # Extract token usage if available
                if hasattr(result, 'get') and callable(result.get):
                    tokens_used = result.get('tokens_used')
                elif isinstance(result, dict) and 'tokens_used' in result:
                    tokens_used = result['tokens_used']

                return result

            except Exception as e:
                error = str(e)
                raise

            finally:
                duration = time.time() - start_time
                metrics.record_request(
                    endpoint=endpoint,
                    duration=duration,
                    tokens_used=tokens_used,
                    error=error
                )

        return wrapper
    return decorator