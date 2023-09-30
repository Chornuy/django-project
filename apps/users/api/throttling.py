from rest_framework.throttling import AnonRateThrottle


class EmailVerifyAndPasswordResetRateThrottle(AnonRateThrottle):
    rate = "5/minute"
