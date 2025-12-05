from django.apps import AppConfig


class KycVerificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kyc_verification'
    verbose_name = 'KYC Verification'
    
    def ready(self):
        # Import signals to register them
        try:
            from . import models  # noqa: F401
        except ImportError:
            pass

