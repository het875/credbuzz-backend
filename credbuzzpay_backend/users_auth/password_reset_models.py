"""
Password Reset Token Model
Separate token for unauthenticated password reset flow
"""
import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone


class PasswordResetToken(models.Model):
    """
    Temporary reset token issued after OTP verification
    Used for unauthenticated password reset flow
    """
    user = models.ForeignKey('users_auth.User', on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    @classmethod
    def generate_token(cls, user, expiry_minutes=15):
        """Generate a new reset token for user"""
        token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        if self.is_used:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])
    
    def __str__(self):
        return f"Reset token for {self.user.email} - {'Used' if self.is_used else 'Active'}"
