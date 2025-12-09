from django.contrib import admin
from .models import User, PasswordResetToken, UserSession


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'username', 'is_active', 'is_verified', 'created_at', 'last_login']
    list_filter = ['is_active', 'is_verified', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'password_hash', 'salt']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'user__username']
    ordering = ['-created_at']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'expires_at', 'is_active', 'ip_address']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'user__username', 'ip_address']
    ordering = ['-created_at']
