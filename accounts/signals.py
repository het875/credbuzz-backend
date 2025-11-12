"""
Django signals for automatic operations like creating related records.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import UserAccount, SecuritySettings, RegistrationProgress
from accounts.utils.code_generator import generate_unique_id


@receiver(post_save, sender=UserAccount)
def create_user_security_settings(sender, instance, created, **kwargs):
    """
    Create SecuritySettings and RegistrationProgress when a new user is created.
    """
    if created:
        # Create security settings
        security_id = generate_unique_id(prefix='SEC_')
        SecuritySettings.objects.create(
            id=security_id,
            user_code=instance,
            two_factor_enabled=False,
        )
        
        # Create registration progress
        reg_id = generate_unique_id(prefix='REG_')
        RegistrationProgress.objects.create(
            id=reg_id,
            user_code=instance,
            current_step=0,
            steps_completed=[],
            step_data={},
            last_completed_step=0,
        )
