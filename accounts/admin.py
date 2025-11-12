"""
Django Admin configuration for accounts models.
"""
from django.contrib import admin
from django.utils.html import format_html
from accounts.models import (
    UserAccount, OTPRecord, Branch, AppFeature, AadhaarKYC, PANKYC,
    BusinessDetails, BankDetails, UserPlatformAccess, AppAccessControl,
    LoginActivity, AuditTrail, RegistrationProgress, SecuritySettings
)


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = [
        'user_code', 'email', 'mobile', 'user_role', 'is_active',
        'is_email_verified', 'is_mobile_verified', 'is_kyc_complete', 'created_at'
    ]
    list_filter = ['user_role', 'is_active', 'is_email_verified', 'is_mobile_verified', 'created_at']
    search_fields = ['user_code', 'email', 'mobile', 'first_name', 'last_name']
    readonly_fields = ['user_code', 'created_at', 'updated_at', 'last_login']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user_code', 'email', 'mobile', 'password', 'first_name', 'middle_name', 'last_name', 'gender', 'dob')
        }),
        ('Role & Permissions', {
            'fields': ('user_role', 'branch_code', 'is_staff', 'is_superuser')
        }),
        ('Verification Status', {
            'fields': ('is_mobile_verified', 'is_email_verified', 'is_kyc_complete', 'kyc_verification_step',
                      'is_aadhaar_verified', 'is_pan_verified', 'is_bank_verified')
        }),
        ('Account Status', {
            'fields': ('is_active', 'user_blocked', 'user_block_reason', 'blocked_until')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'address_line3', 'city', 'state', 'country', 'pincode')
        }),
        ('Security & Audit', {
            'fields': ('register_device_ip', 'register_device_info', 'last_login', 'last_login_ip',
                      'password_changed_at', 'created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_code', 'otp_type', 'otp_purpose', 'is_used', 'expires_at', 'created_at']
    list_filter = ['otp_type', 'otp_purpose', 'is_used', 'created_at']
    search_fields = ['user_code__email', 'user_code__mobile', 'sent_to_email', 'sent_to_mobile']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['branch_code', 'branch_name', 'city', 'state', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'state']
    search_fields = ['branch_code', 'branch_name', 'city']
    readonly_fields = ['branch_code', 'created_at', 'updated_at']
    fieldsets = (
        ('Branch Information', {
            'fields': ('branch_code', 'branch_name', 'phone', 'email')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'address_line3', 'city', 'state', 'country', 'pincode')
        }),
        ('Management', {
            'fields': ('manager_name', 'manager_user_code', 'referred_by', 'is_active')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(AppFeature)
class AppFeatureAdmin(admin.ModelAdmin):
    list_display = ['feature_code', 'feature_name', 'feature_category', 'is_active', 'created_at']
    list_filter = ['is_active', 'feature_category', 'created_at']
    search_fields = ['feature_code', 'feature_name']
    readonly_fields = ['feature_code', 'created_at', 'updated_at']
    fieldsets = (
        ('Feature Information', {
            'fields': ('feature_code', 'feature_name', 'feature_description', 'feature_category', 'parent_feature')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(AadhaarKYC)
class AadhaarKYCAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'aadhaar_name', 'is_verified', 'verification_method', 'created_at']
    list_filter = ['is_verified', 'verification_method', 'created_at']
    search_fields = ['user_code__email', 'aadhaar_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'verified_at']
    ordering = ['-created_at']


@admin.register(PANKYC)
class PANKYCAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'pan_name', 'is_verified', 'verification_method', 'name_match_score', 'created_at']
    list_filter = ['is_verified', 'verification_method', 'created_at']
    search_fields = ['user_code__email', 'pan_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'verified_at']
    ordering = ['-created_at']


@admin.register(BusinessDetails)
class BusinessDetailsAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'business_name', 'business_type', 'is_verified', 'created_at']
    list_filter = ['business_type', 'is_verified', 'created_at']
    search_fields = ['user_code__email', 'business_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'bank_name', 'account_type', 'is_verified', 'verification_method', 'created_at']
    list_filter = ['account_type', 'verification_method', 'is_verified', 'created_at']
    search_fields = ['user_code__email', 'bank_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'account_number_last4']
    ordering = ['-created_at']


@admin.register(UserPlatformAccess)
class UserPlatformAccessAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'platform', 'is_allowed', 'access_level', 'granted_at']
    list_filter = ['platform', 'is_allowed', 'access_level']
    search_fields = ['user_code__email', 'user_code__user_code']
    readonly_fields = ['id', 'granted_at', 'revoked_at']
    ordering = ['-granted_at']


@admin.register(AppAccessControl)
class AppAccessControlAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'feature', 'is_allowed', 'access_level', 'granted_at', 'expires_at']
    list_filter = ['is_allowed', 'access_level', 'granted_at']
    search_fields = ['user_code__email', 'user_code__user_code', 'feature__feature_code']
    readonly_fields = ['id', 'granted_at', 'revoked_at']
    ordering = ['-granted_at']


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_code', 'status', 'ip_address', 'risk_score', 'login_timestamp']
    list_filter = ['status', 'is_suspicious', 'login_timestamp']
    search_fields = ['user_code__email', 'login_identifier', 'ip_address']
    readonly_fields = ['id', 'login_timestamp', 'logout_timestamp', 'session_duration']
    ordering = ['-login_timestamp']


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['action', 'resource_type', 'resource_identifier', 'user_code', 'created_at']
    list_filter = ['action', 'resource_type', 'created_at']
    search_fields = ['resource_identifier', 'user_code__email', 'description']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(RegistrationProgress)
class RegistrationProgressAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'current_step', 'last_completed_step', 'abandoned', 'last_active_at']
    list_filter = ['current_step', 'abandoned', 'last_active_at']
    search_fields = ['user_code__email', 'user_code__user_code']
    readonly_fields = ['id', 'started_at', 'last_active_at']
    ordering = ['-last_active_at']


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ['user_code', 'two_factor_enabled', 'login_notification_enabled', 'suspicious_activity_alert']
    list_filter = ['two_factor_enabled', 'login_notification_enabled', 'suspicious_activity_alert']
    search_fields = ['user_code__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
