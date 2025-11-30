"""
Enhanced Logging and Monitoring System
Priority 2E: Comprehensive logging for production monitoring
"""
import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import time
import traceback
from pathlib import Path

class RailwayOptimizedFormatter(logging.Formatter):
    """Railway-optimized formatter that outputs structured JSON logs"""

    def __init__(self):
        super().__init__()
        self.is_railway = "RAILWAY_DEPLOYMENT_ID" in os.environ

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add Railway-specific context
        if self.is_railway:
            log_entry.update({
                "railway_deployment": os.getenv("RAILWAY_DEPLOYMENT_ID"),
                "railway_environment": os.getenv("RAILWAY_ENVIRONMENT_NAME"),
                "service_name": "jobflow-pro-backend"
            })

        # Add environment context
        log_entry["environment"] = os.getenv("ENVIRONMENT", "development")

        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'execution_time'):
            log_entry['execution_time_ms'] = record.execution_time
        if hasattr(record, 'api_endpoint'):
            log_entry['api_endpoint'] = record.api_endpoint
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'openai_operation'):
            log_entry['openai_operation'] = record.openai_operation
        if hasattr(record, 'openai_model'):
            log_entry['openai_model'] = record.openai_model
        if hasattr(record, 'tokens_used'):
            log_entry['tokens_used'] = record.tokens_used

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_entry, separators=(',', ':'))

class EnhancedLogger:
    """Enhanced logging system with structured output and monitoring capabilities"""

    def __init__(self, app_name: str = "jobflow-pro"):
        self.app_name = app_name
        self.setup_logging()

    def setup_logging(self):
        """Configure Railway-optimized logging system"""

        # Detect Railway environment
        is_railway = "RAILWAY_DEPLOYMENT_ID" in os.environ
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler optimized for Railway
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        if is_railway or is_production:
            # Railway/Production: Use structured JSON logging
            console_handler.setFormatter(RailwayOptimizedFormatter())
        else:
            # Development: Use human-readable format
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_format)

        root_logger.addHandler(console_handler)

        # Only create file handlers in development (Railway uses its own log collection)
        if not is_railway:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self._setup_file_handlers(root_logger, log_dir)

        # Set specific logger levels
        self._configure_logger_levels()

        # Specialized loggers
        self.perf_logger = logging.getLogger('performance')
        self.security_logger = logging.getLogger('security')
        self.business_logger = logging.getLogger('business')
        self.openai_logger = logging.getLogger('openai')

        # Log startup information
        startup_msg = "Enhanced logging system initialized"
        if is_railway:
            startup_msg += " (Railway deployment)"
            root_logger.info(startup_msg, extra={
                'railway_deployment': os.getenv("RAILWAY_DEPLOYMENT_ID"),
                'environment': os.getenv("ENVIRONMENT", "development"),
                'openai_configured': bool(os.getenv("OPENAI_API_KEY")),
                'deployment_status': 'starting'
            })
        else:
            print(f"✅ {startup_msg}")
            if not is_production:
                log_dir = Path("logs")
                print(f"📂 Log files location: {log_dir.absolute()}")

    def _setup_file_handlers(self, root_logger, log_dir):
        """Setup rotating file handlers for different log levels"""

        # General application logs (rotating)
        app_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.app_name}.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(app_handler)

        # Error logs (rotating)
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.app_name}-errors.log",
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(error_handler)

        # Performance logs (daily rotation)
        perf_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / f"{self.app_name}-performance.log",
            when='midnight',
            backupCount=30
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Security logs (daily rotation)
        security_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / f"{self.app_name}-security.log",
            when='midnight',
            backupCount=90  # Keep security logs longer
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Add handlers to specific loggers
        logging.getLogger('performance').addHandler(perf_handler)
        logging.getLogger('security').addHandler(security_handler)

    def _configure_logger_levels(self):
        """Configure logging levels for different components"""

        # Reduce noise from external libraries
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)

        # Keep our application logs detailed
        logging.getLogger('app').setLevel(logging.INFO)
        logging.getLogger('performance').setLevel(logging.INFO)
        logging.getLogger('security').setLevel(logging.INFO)
        logging.getLogger('business').setLevel(logging.INFO)

def log_performance(operation_name: str):
    """Decorator to log function performance metrics"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger('performance')

            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # ms

                logger.info(
                    f"Operation completed: {operation_name}",
                    extra={
                        'operation': operation_name,
                        'execution_time': execution_time,
                        'status': 'success'
                    }
                )
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000  # ms
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra={
                        'operation': operation_name,
                        'execution_time': execution_time,
                        'status': 'error',
                        'error': str(e)
                    }
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger('performance')

            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # ms

                logger.info(
                    f"Operation completed: {operation_name}",
                    extra={
                        'operation': operation_name,
                        'execution_time': execution_time,
                        'status': 'success'
                    }
                )
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000  # ms
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra={
                        'operation': operation_name,
                        'execution_time': execution_time,
                        'status': 'error',
                        'error': str(e)
                    }
                )
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "info"):
    """Log security-related events"""
    logger = logging.getLogger('security')

    log_data = {
        'event_type': event_type,
        'severity': severity,
        **details
    }

    if severity == "critical":
        logger.critical(f"Security event: {event_type}", extra=log_data)
    elif severity == "error":
        logger.error(f"Security event: {event_type}", extra=log_data)
    elif severity == "warning":
        logger.warning(f"Security event: {event_type}", extra=log_data)
    else:
        logger.info(f"Security event: {event_type}", extra=log_data)

def log_business_event(event_type: str, user_id: str, details: Dict[str, Any]):
    """Log business logic events for analytics"""
    logger = logging.getLogger('business')

    logger.info(
        f"Business event: {event_type}",
        extra={
            'event_type': event_type,
            'user_id': user_id,
            **details
        }
    )

def log_openai_request(operation: str, model: str, tokens_used: int = None, cost_estimate: float = None):
    """Log OpenAI API usage for monitoring"""
    logger = logging.getLogger('openai')

    logger.info(
        f"OpenAI API call: {operation}",
        extra={
            'openai_operation': operation,
            'openai_model': model,
            'tokens_used': tokens_used,
            'cost_estimate_usd': cost_estimate,
            'railway_deployment': "RAILWAY_DEPLOYMENT_ID" in os.environ
        }
    )

def log_openai_error(operation: str, error: Exception, retry_count: int = 0):
    """Log OpenAI API errors with context for Railway debugging"""
    logger = logging.getLogger('openai')

    logger.error(
        f"OpenAI API error: {operation}",
        extra={
            'openai_operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'retry_count': retry_count,
            'railway_deployment': "RAILWAY_DEPLOYMENT_ID" in os.environ,
            'openai_key_configured': bool(os.getenv("OPENAI_API_KEY"))
        }
    )

def validate_railway_config():
    """Validate Railway deployment configuration and log results"""
    logger = logging.getLogger('railway_config')

    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API integration',
        'SUPABASE_URL': 'Database connection',
        'SQLALCHEMY_DATABASE_URI': 'SQLAlchemy database',
        'SUPABASE_JWT_SECRET': 'JWT verification'
    }

    missing_vars = []
    configured_vars = []

    for var_name, purpose in required_vars.items():
        if os.getenv(var_name):
            configured_vars.append({'name': var_name, 'purpose': purpose})
        else:
            missing_vars.append({'name': var_name, 'purpose': purpose})

    if missing_vars:
        logger.error(
            "Missing required environment variables for Railway deployment",
            extra={
                'missing_variables': missing_vars,
                'configured_variables': configured_vars,
                'deployment_status': 'configuration_error',
                'railway_deployment': os.getenv("RAILWAY_DEPLOYMENT_ID")
            }
        )
        return False
    else:
        logger.info(
            "Railway deployment configuration validated successfully",
            extra={
                'configured_variables': configured_vars,
                'deployment_status': 'ready',
                'railway_deployment': os.getenv("RAILWAY_DEPLOYMENT_ID")
            }
        )
        return True

class HealthMonitor:
    """System health monitoring and metrics collection"""

    def __init__(self):
        self.logger = logging.getLogger('health')
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0

    def record_request(self):
        """Record API request"""
        self.request_count += 1

    def record_error(self):
        """Record error occurrence"""
        self.error_count += 1

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get current system health metrics"""
        uptime = time.time() - self.start_time

        return {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "timestamp": datetime.utcnow().isoformat()
        }

    def log_health_status(self):
        """Log current health status"""
        metrics = self.get_health_metrics()
        self.logger.info("Health check", extra=metrics)

# Global instances
enhanced_logger = None
health_monitor = HealthMonitor()

def setup_enhanced_logging():
    """Initialize the enhanced logging system"""
    global enhanced_logger
    enhanced_logger = EnhancedLogger()
    return enhanced_logger

# Import asyncio for coroutine detection
import asyncio