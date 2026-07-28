"""
Consolidation metrics tracking for memory consolidation operations.

Provides metrics collection, persistence, and querying for consolidation runs.
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from typing import Any, Optional
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of consolidation alerts."""
    EXCESSIVE_PRUNING = "excessive_pruning"
    EXCESSIVE_DEDUPLICATION = "excessive_deduplication"
    LONG_DURATION = "long_duration"
    HIGH_ERROR_RATE = "high_error_rate"
    STORAGE_GROWTH = "storage_growth"
    LOW_ENTRIES_PROCESSED = "low_entries_processed"
    AGGREGATE_GENERATION_FAILED = "aggregate_generation_failed"


@dataclass
class ConsolidationAlert:
    """Alert generated from consolidation metrics anomalies."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    memory_type: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["alert_type"] = self.alert_type.value
        data["severity"] = self.severity.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsolidationAlert":
        """Create from dictionary."""
        data = data.copy()
        data["alert_type"] = AlertType(data["alert_type"])
        data["severity"] = AlertSeverity(data["severity"])
        return cls(**data)


@dataclass
class ConsolidationMetrics:
    """Metrics collected for a single consolidation run."""
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    duration_ms: float = 0.0
    
    # Per-memory-type metrics
    entries_processed: dict[str, int] = field(default_factory=dict)
    entries_before: dict[str, int] = field(default_factory=dict)
    entries_after: dict[str, int] = field(default_factory=dict)
    entries_pruned: dict[str, int] = field(default_factory=dict)
    entries_deduplicated: dict[str, int] = field(default_factory=dict)
    entries_decayed: dict[str, int] = field(default_factory=dict)
    entries_pruned_by_age: dict[str, int] = field(default_factory=dict)
    entries_pruned_by_decay: dict[str, int] = field(default_factory=dict)
    entries_pruned_by_cap: dict[str, int] = field(default_factory=dict)
    
    # Storage metrics
    storage_size_before_bytes: int = 0
    storage_size_after_bytes: int = 0
    
    # Aggregate metrics
    aggregates_generated: int = 0
    aggregate_generation_failed: bool = False
    
    # Errors and warnings
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Alerts generated
    alerts: list[ConsolidationAlert] = field(default_factory=list)
    
    # Scheduler info
    tick_count: int = 0
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "entries_processed": self.entries_processed,
            "entries_before": self.entries_before,
            "entries_after": self.entries_after,
            "entries_pruned": self.entries_pruned,
            "entries_deduplicated": self.entries_deduplicated,
            "entries_decayed": self.entries_decayed,
            "entries_pruned_by_age": self.entries_pruned_by_age,
            "entries_pruned_by_decay": self.entries_pruned_by_decay,
            "entries_pruned_by_cap": self.entries_pruned_by_cap,
            "storage_size_before_bytes": self.storage_size_before_bytes,
            "storage_size_after_bytes": self.storage_size_after_bytes,
            "aggregates_generated": self.aggregates_generated,
            "aggregate_generation_failed": self.aggregate_generation_failed,
            "errors": self.errors,
            "warnings": self.warnings,
            "alerts": [a.to_dict() for a in self.alerts],
            "tick_count": self.tick_count,
            "config_snapshot": self.config_snapshot,
        }
        return data
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsolidationMetrics":
        """Create from dictionary."""
        data = data.copy()
        alerts = [ConsolidationAlert.from_dict(a) for a in data.get("alerts", [])]
        data["alerts"] = alerts
        return cls(**data)
    
    def get_total_entries_processed(self) -> int:
        """Get total entries processed across all memory types."""
        return sum(self.entries_processed.values())
    
    def get_total_entries_pruned(self) -> int:
        """Get total entries pruned across all memory types."""
        return sum(self.entries_pruned.values())
    
    def get_total_entries_deduplicated(self) -> int:
        """Get total entries deduplicated across all memory types."""
        return sum(self.entries_deduplicated.values())
    
    def get_storage_saved_bytes(self) -> int:
        """Get storage saved in bytes (negative means growth)."""
        return self.storage_size_before_bytes - self.storage_size_after_bytes
    
    def get_pruning_ratio(self, memory_type: str) -> float:
        """Get pruning ratio for a memory type (0.0 to 1.0)."""
        before = self.entries_before.get(memory_type, 0)
        if before == 0:
            return 0.0
        return self.entries_pruned.get(memory_type, 0) / before
    
    def get_deduplication_ratio(self, memory_type: str) -> float:
        """Get deduplication ratio for a memory type (0.0 to 1.0)."""
        before = self.entries_before.get(memory_type, 0)
        if before == 0:
            return 0.0
        return self.entries_deduplicated.get(memory_type, 0) / before


@dataclass
class ConsolidationMetricsConfig:
    """Configuration for metrics collection and alerting."""
    # Storage
    metrics_dir: str = "memory/metrics"
    max_history_runs: int = 1000
    max_alerts_per_run: int = 10
    
    # Alerting thresholds
    pruning_ratio_warning: float = 0.3      # Warn if >30% pruned
    pruning_ratio_critical: float = 0.5     # Critical if >50% pruned
    deduplication_ratio_warning: float = 0.4  # Warn if >40% deduplicated
    deduplication_ratio_critical: float = 0.7 # Critical if >70% deduplicated
    duration_warning_ms: float = 5000       # Warn if >5 seconds
    duration_critical_ms: float = 30000     # Critical if >30 seconds
    storage_growth_warning_bytes: int = 1024 * 1024 * 10  # 10MB growth warning
    storage_growth_critical_bytes: int = 1024 * 1024 * 100  # 100MB growth critical
    min_entries_processed_warning: int = 0  # Warn if 0 entries processed
    
    # Alert cooldown (seconds)
    alert_cooldown_seconds: int = 3600  # 1 hour cooldown between same alerts


DEFAULT_METRICS_CONFIG = ConsolidationMetricsConfig()


class ConsolidationMetricsStore:
    """File-based store for consolidation metrics history."""
    
    def __init__(self, directory: str):
        self.dir = directory
        import os
        os.makedirs(directory, exist_ok=True)
    
    def _get_metrics_path(self) -> str:
        return f"{self.dir}/consolidation_metrics.json"
    
    def _get_alerts_path(self) -> str:
        return f"{self.dir}/consolidation_alerts.json"
    
    def save_metrics(self, metrics: ConsolidationMetrics) -> None:
        """Save a metrics record, maintaining history limit."""
        import json
        import os
        
        path = self._get_metrics_path()
        history = self.load_metrics()
        history.append(metrics.to_dict())
        
        # Trim history
        config = DEFAULT_METRICS_CONFIG
        if len(history) > config.max_history_runs:
            history = history[-config.max_history_runs:]
        
        # Atomic write
        fd, tmp_path = tempfile.mkstemp(dir=self.dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
    
    def load_metrics(self) -> list[ConsolidationMetrics]:
        """Load all metrics history."""
        import json
        import os
        
        path = self._get_metrics_path()
        if not os.path.exists(path):
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return [ConsolidationMetrics.from_dict(d) for d in data]
    
    def save_alert(self, alert: ConsolidationAlert) -> None:
        """Save an alert."""
        import json
        import os
        
        path = self._get_alerts_path()
        alerts = self.load_alerts()
        alerts.append(alert.to_dict())
        
        # Keep last 10000 alerts
        if len(alerts) > 10000:
            alerts = alerts[-10000:]
        
        fd, tmp_path = tempfile.mkstemp(dir=self.dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(alerts, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
    
    def load_alerts(self) -> list[ConsolidationAlert]:
        """Load all alerts."""
        import json
        import os
        
        path = self._get_alerts_path()
        if not os.path.exists(path):
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return [ConsolidationAlert.from_dict(d) for d in data]
    
    def query_metrics(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        memory_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        min_duration_ms: Optional[float] = None,
        max_duration_ms: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> list[ConsolidationMetrics]:
        """Query metrics with filters."""
        metrics = self.load_metrics()
        
        # Filter by time range
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        # Filter by memory type (check if any entries processed for that type)
        if memory_type:
            metrics = [m for m in metrics if m.entries_processed.get(memory_type, 0) > 0]
        
        # Filter by duration
        if min_duration_ms is not None:
            metrics = [m for m in metrics if m.duration_ms >= min_duration_ms]
        if max_duration_ms is not None:
            metrics = [m for m in metrics if m.duration_ms <= max_duration_ms]
        
        # Sort by timestamp descending (newest first)
        metrics.sort(key=lambda m: m.timestamp, reverse=True)
        
        if limit:
            metrics = metrics[:limit]
        
        return metrics
    
    def query_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[ConsolidationAlert]:
        """Query alerts with filters."""
        alerts = self.load_alerts()
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if start_time:
            alerts = [a for a in alerts if a.timestamp >= start_time]
        if end_time:
            alerts = [a for a in alerts if a.timestamp <= end_time]
        
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        if limit:
            alerts = alerts[:limit]
        
        return alerts
    
    def get_latest_metrics(self) -> Optional[ConsolidationMetrics]:
        """Get the most recent metrics record."""
        metrics = self.load_metrics()
        if not metrics:
            return None
        return max(metrics, key=lambda m: m.timestamp)
    
    def get_aggregated_stats(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get aggregated statistics over a time range."""
        metrics = self.query_metrics(start_time=start_time, end_time=end_time)
        
        if not metrics:
            return {
                "total_runs": 0,
                "total_entries_processed": 0,
                "total_entries_pruned": 0,
                "total_entries_deduplicated": 0,
                "avg_duration_ms": 0.0,
                "total_storage_saved_bytes": 0,
                "total_alerts": 0,
                "alert_breakdown": {},
            }
        
        total_runs = len(metrics)
        total_entries_processed = sum(m.get_total_entries_processed() for m in metrics)
        total_entries_pruned = sum(m.get_total_entries_pruned() for m in metrics)
        total_entries_dedup = sum(m.get_total_entries_deduplicated() for m in metrics)
        avg_duration = sum(m.duration_ms for m in metrics) / total_runs
        total_storage_saved = sum(m.get_storage_saved_bytes() for m in metrics)
        
        # Alert breakdown
        all_alerts = []
        for m in metrics:
            all_alerts.extend(m.alerts)
        
        alert_breakdown = {}
        for alert in all_alerts:
            key = f"{alert.alert_type.value}_{alert.severity.value}"
            alert_breakdown[key] = alert_breakdown.get(key, 0) + 1
        
        return {
            "total_runs": total_runs,
            "total_entries_processed": total_entries_processed,
            "total_entries_pruned": total_entries_pruned,
            "total_entries_deduplicated": total_entries_dedup,
            "avg_duration_ms": avg_duration,
            "total_storage_saved_bytes": total_storage_saved,
            "total_alerts": len(all_alerts),
            "alert_breakdown": alert_breakdown,
            "time_range": {
                "start": metrics[-1].timestamp if metrics else None,
                "end": metrics[0].timestamp if metrics else None,
            },
        }


# Import tempfile at module level
import tempfile