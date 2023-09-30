from rest_framework.throttling import AnonRateThrottle


class LoginAttemptsThrottling(AnonRateThrottle):
    rate = "10/minute"
