"""
Security utilities and helper functions
"""

import hashlib
import secrets
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import ipaddress
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security validation utilities"""

    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """Check if filename is safe for storage"""
        # Remove path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False

        # Check for null bytes
        if '\x00' in filename:
            return False

        # Check length
        if len(filename) > 255:
            return False

        # Check for valid characters (alphanumeric, dots, dashes, underscores)
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]

        # Remove null bytes
        filename = filename.replace('\x00', '')

        # Keep only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = 255 - len(ext) - 1 if ext else 255
            filename = name[:max_name_length] + ('.' + ext if ext else '')

        return filename

    @staticmethod
    def is_safe_email(email: str) -> bool:
        """Basic email validation"""
        if not email or len(email) > 254:
            return False

        # Basic regex for email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    @staticmethod
    def contains_suspicious_patterns(text: str) -> tuple[bool, List[str]]:
        """Check for suspicious patterns in text input"""
        suspicious_patterns = [
            # SQL injection patterns
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)',
            r'(--|/\*|\*/)',
            r'(\b(or|and)\s+\d+\s*=\s*\d+)',

            # XSS patterns
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',

            # Path traversal
            r'\.\./',
            r'\.\.\\',

            # Command injection
            r'[;&|`]',
            r'\$\(',
            r'\${',

            # File inclusion
            r'(file|ftp|http|https)://',
            r'/etc/passwd',
            r'/proc/',
            r'cmd\.exe',
            r'powershell',
        ]

        found_patterns = []
        text_lower = text.lower()

        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_patterns.append(pattern)

        return bool(found_patterns), found_patterns

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash sensitive data with salt"""
        if salt is None:
            salt = secrets.token_hex(16)

        # Use PBKDF2 for password-like data
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt

    @staticmethod
    def verify_hash(data: str, hash_value: str, salt: str) -> bool:
        """Verify hashed data"""
        computed_hash, _ = SecurityValidator.hash_sensitive_data(data, salt)
        return secrets.compare_digest(computed_hash, hash_value)


class IPValidator:
    """IP address validation and security checks"""

    PRIVATE_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),
        ipaddress.ip_network('::1/128'),
        ipaddress.ip_network('fc00::/7'),
        ipaddress.ip_network('fe80::/10'),
    ]

    @classmethod
    def is_private_ip(cls, ip_str: str) -> bool:
        """Check if IP address is private/internal"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in network for network in cls.PRIVATE_NETWORKS)
        except ValueError:
            return False

    @classmethod
    def is_valid_ip(cls, ip_str: str) -> bool:
        """Check if string is a valid IP address"""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    @classmethod
    def get_real_ip(cls, request_headers: Dict[str, str]) -> str:
        """Extract real IP from request headers"""
        # Check common forwarded headers
        forwarded_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'CF-Connecting-IP',  # Cloudflare
            'X-Client-IP',
            'X-Forwarded',
            'Forwarded-For',
            'Forwarded'
        ]

        for header in forwarded_headers:
            if header in request_headers:
                # X-Forwarded-For can contain multiple IPs
                ip = request_headers[header].split(',')[0].strip()
                if cls.is_valid_ip(ip):
                    return ip

        return 'unknown'


class RequestSanitizer:
    """Request data sanitization"""

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)

        # Remove null bytes
        value = value.replace('\x00', '')

        # Remove control characters except newlines and tabs
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')

        # Trim whitespace
        value = value.strip()

        # Limit length
        if max_length and len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_string_length: int = 1000) -> Dict[str, Any]:
        """Recursively sanitize dictionary data"""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            clean_key = RequestSanitizer.sanitize_string(str(key), 100)

            # Sanitize value
            if isinstance(value, str):
                clean_value = RequestSanitizer.sanitize_string(value, max_string_length)
            elif isinstance(value, dict):
                clean_value = RequestSanitizer.sanitize_dict(value, max_string_length)
            elif isinstance(value, list):
                clean_value = [
                    RequestSanitizer.sanitize_string(item, max_string_length)
                    if isinstance(item, str) else item
                    for item in value[:100]  # Limit list size
                ]
            else:
                clean_value = value

            sanitized[clean_key] = clean_value

        return sanitized


class SecurityLogger:
    """Security event logging"""

    @staticmethod
    def log_security_event(
        event_type: str,
        details: Dict[str, Any],
        severity: str = 'INFO',
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Log security events with structured data"""
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'details': details
        }

        if client_ip:
            log_data['client_ip'] = client_ip

        if user_id:
            log_data['user_id'] = user_id

        if severity.upper() == 'CRITICAL':
            logger.critical(f"Security Event: {event_type}", extra=log_data)
        elif severity.upper() == 'ERROR':
            logger.error(f"Security Event: {event_type}", extra=log_data)
        elif severity.upper() == 'WARNING':
            logger.warning(f"Security Event: {event_type}", extra=log_data)
        else:
            logger.info(f"Security Event: {event_type}", extra=log_data)

    @staticmethod
    def log_suspicious_activity(
        activity: str,
        client_ip: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log suspicious activity"""
        SecurityLogger.log_security_event(
            event_type='SUSPICIOUS_ACTIVITY',
            details={
                'activity': activity,
                'additional_details': details or {}
            },
            severity='WARNING',
            client_ip=client_ip
        )

    @staticmethod
    def log_rate_limit_violation(
        client_ip: str,
        endpoint: str,
        request_count: int,
        time_window: str
    ):
        """Log rate limit violations"""
        SecurityLogger.log_security_event(
            event_type='RATE_LIMIT_VIOLATION',
            details={
                'endpoint': endpoint,
                'request_count': request_count,
                'time_window': time_window
            },
            severity='WARNING',
            client_ip=client_ip
        )

    @staticmethod
    def log_authentication_failure(
        client_ip: str,
        username: Optional[str] = None,
        reason: str = 'invalid_credentials'
    ):
        """Log authentication failures"""
        SecurityLogger.log_security_event(
            event_type='AUTHENTICATION_FAILURE',
            details={
                'username': username,
                'reason': reason
            },
            severity='WARNING',
            client_ip=client_ip
        )


# Pre-configured security rules

SECURITY_RULES = {
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'allowed_file_types': [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ],
    'max_string_length': 10000,
    'max_list_length': 1000,
    'max_nested_depth': 10,
    'rate_limits': {
        'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
        'auth': {'requests': 10, 'window': 3600},      # 10 auth attempts per hour
        'upload': {'requests': 10, 'window': 3600},    # 10 uploads per hour
    }
}


def validate_file_upload(filename: str, content_type: str, file_size: int) -> tuple[bool, Optional[str]]:
    """Validate file upload parameters"""
    # Check file size
    if file_size > SECURITY_RULES['max_file_size']:
        return False, f"File too large. Maximum size is {SECURITY_RULES['max_file_size'] // (1024*1024)}MB"

    # Check file type
    if content_type not in SECURITY_RULES['allowed_file_types']:
        return False, f"File type not allowed: {content_type}"

    # Check filename
    if not SecurityValidator.is_safe_filename(filename):
        return False, "Invalid filename"

    return True, None


def is_request_safe(request_data: Dict[str, Any], client_ip: str) -> tuple[bool, Optional[str]]:
    """Comprehensive request safety check"""
    # Check for suspicious patterns in all string values
    def check_values(obj, path=""):
        if isinstance(obj, str):
            has_suspicious, patterns = SecurityValidator.contains_suspicious_patterns(obj)
            if has_suspicious:
                SecurityLogger.log_suspicious_activity(
                    f"Suspicious patterns detected in {path}",
                    client_ip,
                    {'patterns': patterns, 'value': obj[:100]}
                )
                return False, f"Suspicious content detected in {path}"
        elif isinstance(obj, dict):
            for key, value in obj.items():
                safe, reason = check_values(value, f"{path}.{key}" if path else key)
                if not safe:
                    return safe, reason
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                safe, reason = check_values(item, f"{path}[{i}]")
                if not safe:
                    return safe, reason
        return True, None

    return check_values(request_data)