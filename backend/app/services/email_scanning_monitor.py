"""
Monitoring and error handling for email scanning system
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from app.db.session import get_db
from app.models.email_scanning import EmailScanHistory
from app.models.profile import UserSettings
from app.tasks.email_scanning_tasks import run_full_email_scan
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailScanningMonitor:
    """Monitor email scanning system health and performance"""
    
    def __init__(self):
        self.logger = logger
    
    async def check_system_health(self) -> Dict:
        """Comprehensive health check of email scanning system"""
        
        health_status = {
            'overall_status': 'healthy',
            'checks': {},
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check urgent email scanning
            urgent_check = await self._check_urgent_email_scanning()
            health_status['checks']['urgent_scanning'] = urgent_check
            
            # Check scheduled scanning
            scheduled_check = await self._check_scheduled_scanning()
            health_status['checks']['scheduled_scanning'] = scheduled_check
            
            # Check for stuck scans
            stuck_check = await self._check_stuck_scans()
            health_status['checks']['stuck_scans'] = stuck_check
            
            # Check user settings
            settings_check = await self._check_user_settings()
            health_status['checks']['user_settings'] = settings_check
            
            # Check error rates
            error_check = await self._check_error_rates()
            health_status['checks']['error_rates'] = error_check
            
            # Determine overall status
            if any(check.get('status') == 'critical' for check in health_status['checks'].values()):
                health_status['overall_status'] = 'critical'
            elif any(check.get('status') == 'warning' for check in health_status['checks'].values()):
                health_status['overall_status'] = 'warning'
            
            # Generate alerts
            health_status['alerts'] = await self._generate_alerts(health_status['checks'])
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)
        
        return health_status
    
    async def _check_urgent_email_scanning(self) -> Dict:
        """Check if urgent email scanning is working"""
        
        try:
            db = next(get_db())
            
            # Check if urgent scans have run in the last 3 hours
            cutoff_time = datetime.now() - timedelta(hours=3)
            
            recent_urgent_scans = db.query(EmailScanHistory).filter(
                EmailScanHistory.scan_type == 'urgent',
                EmailScanHistory.scan_started_at >= cutoff_time
            ).count()
            
            db.close()
            
            if recent_urgent_scans == 0:
                return {
                    'status': 'critical',
                    'message': 'No urgent email scans in the last 3 hours',
                    'last_scan': None
                }
            else:
                return {
                    'status': 'healthy',
                    'message': f'{recent_urgent_scans} urgent scans in last 3 hours',
                    'scans_count': recent_urgent_scans
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to check urgent scanning: {e}'
            }
    
    async def _check_scheduled_scanning(self) -> Dict:
        """Check if scheduled scanning is working"""
        
        try:
            db = next(get_db())
            
            # Check if any users have scheduled scans
            users_with_scheduling = db.query(UserSettings).filter(
                UserSettings.email_tracking_enabled == True
            ).count()
            
            # Check recent full scans
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_full_scans = db.query(EmailScanHistory).filter(
                EmailScanHistory.scan_type == 'full',
                EmailScanHistory.scan_started_at >= cutoff_time
            ).count()
            
            db.close()
            
            if users_with_scheduling == 0:
                return {
                    'status': 'warning',
                    'message': 'No users have email scanning enabled',
                    'users_count': 0
                }
            elif recent_full_scans == 0:
                return {
                    'status': 'warning',
                    'message': 'No full scans in the last 24 hours',
                    'users_count': users_with_scheduling,
                    'scans_count': recent_full_scans
                }
            else:
                return {
                    'status': 'healthy',
                    'message': f'{recent_full_scans} full scans for {users_with_scheduling} users',
                    'users_count': users_with_scheduling,
                    'scans_count': recent_full_scans
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to check scheduled scanning: {e}'
            }
    
    async def _check_stuck_scans(self) -> Dict:
        """Check for stuck or failed scans"""
        
        try:
            db = next(get_db())
            
            # Find scans that started but never completed
            stuck_scans = db.query(EmailScanHistory).filter(
                EmailScanHistory.scan_completed_at.is_(None),
                EmailScanHistory.scan_started_at < datetime.now() - timedelta(minutes=30)
            ).all()
            
            # Find scans with errors
            error_scans = db.query(EmailScanHistory).filter(
                EmailScanHistory.errors.isnot(None)
            ).filter(
                EmailScanHistory.scan_started_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            db.close()
            
            if len(stuck_scans) > 0:
                return {
                    'status': 'critical',
                    'message': f'{len(stuck_scans)} scans stuck for >30 minutes',
                    'stuck_scans': [scan.user_id for scan in stuck_scans],
                    'error_scans': error_scans
                }
            elif error_scans > 5:
                return {
                    'status': 'warning',
                    'message': f'{error_scans} scans with errors in last 24h',
                    'error_scans': error_scans
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'No stuck scans, minimal errors',
                    'stuck_scans': 0,
                    'error_scans': error_scans
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to check stuck scans: {e}'
            }
    
    async def _check_user_settings(self) -> Dict:
        """Check user settings configuration"""
        
        try:
            db = next(get_db())
            
            # Check for users with invalid timezone settings
            invalid_timezones = db.query(UserSettings).filter(
                UserSettings.email_scan_timezone.notin_(self._get_valid_timezones())
            ).count()
            
            # Check for users with invalid scan times
            invalid_times = db.query(UserSettings).filter(
                UserSettings.email_scan_time.is_(None)
            ).count()
            
            db.close()
            
            if invalid_timezones > 0 or invalid_times > 0:
                return {
                    'status': 'warning',
                    'message': f'{invalid_timezones} invalid timezones, {invalid_times} invalid times',
                    'invalid_timezones': invalid_timezones,
                    'invalid_times': invalid_times
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'All user settings are valid',
                    'invalid_timezones': 0,
                    'invalid_times': 0
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to check user settings: {e}'
            }
    
    async def _check_error_rates(self) -> Dict:
        """Check error rates and patterns"""
        
        try:
            db = next(get_db())
            
            # Get scans from last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_scans = db.query(EmailScanHistory).filter(
                EmailScanHistory.scan_started_at >= cutoff_time
            ).all()
            
            total_scans = len(recent_scans)
            failed_scans = sum(1 for scan in recent_scans if scan.errors)
            
            error_rate = (failed_scans / total_scans * 100) if total_scans > 0 else 0
            
            db.close()
            
            if error_rate > 20:
                return {
                    'status': 'critical',
                    'message': f'High error rate: {error_rate:.1f}%',
                    'error_rate': error_rate,
                    'total_scans': total_scans,
                    'failed_scans': failed_scans
                }
            elif error_rate > 10:
                return {
                    'status': 'warning',
                    'message': f'Moderate error rate: {error_rate:.1f}%',
                    'error_rate': error_rate,
                    'total_scans': total_scans,
                    'failed_scans': failed_scans
                }
            else:
                return {
                    'status': 'healthy',
                    'message': f'Low error rate: {error_rate:.1f}%',
                    'error_rate': error_rate,
                    'total_scans': total_scans,
                    'failed_scans': failed_scans
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to check error rates: {e}'
            }
    
    async def _generate_alerts(self, checks: Dict) -> List[Dict]:
        """Generate alerts based on health checks"""
        
        alerts = []
        
        for check_name, check_result in checks.items():
            if check_result.get('status') == 'critical':
                alerts.append({
                    'level': 'critical',
                    'component': check_name,
                    'message': check_result.get('message', 'Critical issue detected'),
                    'timestamp': datetime.now().isoformat()
                })
            elif check_result.get('status') == 'warning':
                alerts.append({
                    'level': 'warning',
                    'component': check_name,
                    'message': check_result.get('message', 'Warning detected'),
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def _get_valid_timezones(self) -> List[str]:
        """Get list of valid timezone identifiers"""
        
        import pytz
        return list(pytz.all_timezones)
    
    async def retry_stuck_scans(self) -> Dict:
        """Retry stuck scans"""
        
        try:
            db = next(get_db())
            
            # Find stuck scans
            stuck_scans = db.query(EmailScanHistory).filter(
                EmailScanHistory.scan_completed_at.is_(None),
                EmailScanHistory.scan_started_at < datetime.now() - timedelta(minutes=30)
            ).all()
            
            retried_count = 0
            
            for scan in stuck_scans:
                try:
                    # Mark scan as failed
                    scan.scan_completed_at = datetime.now()
                    scan.errors = json.dumps(['Scan stuck - retrying'])
                    db.commit()
                    
                    # Queue new scan
                    run_full_email_scan.delay(scan.user_id)
                    retried_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to retry scan for user {scan.user_id}: {e}")
                    continue
            
            db.close()
            
            return {
                'status': 'success',
                'message': f'Retried {retried_count} stuck scans',
                'retried_count': retried_count
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to retry stuck scans: {e}'
            }
    
    async def get_performance_metrics(self, days: int = 7) -> Dict:
        """Get performance metrics for email scanning"""
        
        try:
            db = next(get_db())
            
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # Get scan statistics
            scans = db.query(EmailScanHistory).filter(
                EmailScanHistory.scan_started_at >= cutoff_time
            ).all()
            
            metrics = {
                'total_scans': len(scans),
                'successful_scans': sum(1 for scan in scans if scan.scan_completed_at and not scan.errors),
                'failed_scans': sum(1 for scan in scans if scan.errors),
                'total_emails_processed': sum(scan.emails_processed or 0 for scan in scans),
                'total_status_updates': sum(scan.status_updates_made or 0 for scan in scans),
                'total_urgent_emails': sum(scan.urgent_emails_found or 0 for scan in scans),
                'avg_processing_time': self._calculate_avg_processing_time(scans),
                'scan_types': {
                    'full': sum(1 for scan in scans if scan.scan_type == 'full'),
                    'urgent': sum(1 for scan in scans if scan.scan_type == 'urgent')
                }
            }
            
            # Calculate success rate
            if metrics['total_scans'] > 0:
                metrics['success_rate'] = (metrics['successful_scans'] / metrics['total_scans']) * 100
            else:
                metrics['success_rate'] = 0
            
            db.close()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_avg_processing_time(self, scans: List[EmailScanHistory]) -> Optional[float]:
        """Calculate average processing time for scans"""
        
        completed_scans = [
            scan for scan in scans 
            if scan.scan_completed_at and scan.scan_started_at
        ]
        
        if not completed_scans:
            return None
        
        total_time = sum(
            (scan.scan_completed_at - scan.scan_started_at).total_seconds()
            for scan in completed_scans
        )
        
        return total_time / len(completed_scans)


# Global monitor instance
email_scanning_monitor = EmailScanningMonitor()
