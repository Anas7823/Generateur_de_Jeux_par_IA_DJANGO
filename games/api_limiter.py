from django.utils import timezone
import datetime

class APIRateLimiter:
    def __init__(self, max_attempts=5, cooldown_minutes=30):
        self.max_attempts = max_attempts
        self.cooldown_minutes = cooldown_minutes
        self.attempts = {}

    def check_limit(self, ip_address):
        now = timezone.now()
        attempt_info = self.attempts.get(ip_address, {'count': 0, 'blocked_until': None})

        if attempt_info['blocked_until'] and now < attempt_info['blocked_until']:
            wait_time = int((attempt_info['blocked_until'] - now).total_seconds())
            return False, wait_time

        if attempt_info['count'] >= self.max_attempts:
            attempt_info['blocked_until'] = now + datetime.timedelta(minutes=self.cooldown_minutes)
            self.attempts[ip_address] = attempt_info
            return False, self.cooldown_minutes * 60

        attempt_info['count'] = attempt_info.get('count', 0) + 1
        self.attempts[ip_address] = attempt_info
        return True, 0

# Instance globale du limiteur
api_limiter = APIRateLimiter()