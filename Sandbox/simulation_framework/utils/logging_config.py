"""
Logging configuration for the simulation framework.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import structlog
from rich.logging import RichHandler


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_structured: bool = True,
    enable_metrics: bool = True
) -> None:
    """
    Configure logging for the simulation framework.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        enable_structured: Whether to use structured logging
        enable_metrics: Whether to enable basic metrics logging
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure standard logging
    handlers = []
    
    # Console handler with rich formatting
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=True
    )
    console_handler.setLevel(numeric_level)
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        format="%(message)s"
    )
    
    # Configure structlog if enabled
    if enable_structured:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if log_file else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Set up framework-specific loggers
    framework_logger = logging.getLogger("simulation_framework")
    framework_logger.setLevel(numeric_level)
    
    # Reduce verbosity of third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger for the given name."""
    return structlog.get_logger(name)


class MetricsLogger:
    """Simple metrics collection for monitoring simulation performance."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = get_logger("simulation_framework.metrics")
        self._metrics = {}
    
    def increment(self, metric: str, value: int = 1, **tags) -> None:
        """Increment a counter metric."""
        if not self.enabled:
            return
        
        key = f"{metric}.{'.'.join(f'{k}={v}' for k, v in tags.items())}"
        self._metrics[key] = self._metrics.get(key, 0) + value
        
        self.logger.info(
            "metric_increment",
            metric=metric,
            value=value,
            total=self._metrics[key],
            **tags
        )
    
    def gauge(self, metric: str, value: float, **tags) -> None:
        """Set a gauge metric value."""
        if not self.enabled:
            return
        
        self.logger.info(
            "metric_gauge",
            metric=metric,
            value=value,
            **tags
        )
    
    def timing(self, metric: str, duration: float, **tags) -> None:
        """Record a timing metric."""
        if not self.enabled:
            return
        
        self.logger.info(
            "metric_timing",
            metric=metric,
            duration_ms=duration * 1000,
            **tags
        )
    
    def get_metrics(self) -> dict:
        """Get current metrics snapshot."""
        return self._metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()


# Global metrics instance
_metrics: Optional[MetricsLogger] = None


def get_metrics() -> MetricsLogger:
    """Get the global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsLogger()
    return _metrics


def setup_metrics(enabled: bool = True) -> MetricsLogger:
    """Set up and return the global metrics instance."""
    global _metrics
    _metrics = MetricsLogger(enabled=enabled)
    return _metrics
