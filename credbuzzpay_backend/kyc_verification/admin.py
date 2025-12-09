"""
KYC Verification Admin Configuration
======================================
Django admin configuration for KYC models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    OTPVerification, KYCApplication, IdentityProof, BusinessDetails,
    VerificationImages, BankDetails, KYCProgressTracker, KYCAuditLog
)


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """Admin configuration for OTP Verification."""
    list_display = ['id', 'user_email', 'otp_type', 'is_verified', 'attempts', 'created_at', 'expires_at']
    list_filter = ['otp_type', 'is_verified', 'created_at']
    search_fields = ['user__email', 'user__user_code']
    readonly_fields = ['id', 'otp_code', 'created_at', 'verified_at', 'ip_address', 'user_agent']
    ordering = ['-created_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


class IdentityProofInline(admin.StackedInline):
    """Inline for Identity Proof in KYC Application."""
    model = IdentityProof
    can_delete = False
    readonly_fields = ['aadhaar_masked', 'pan_masked', 'created_at', 'updated_at']
    
    def aadhaar_masked(self, obj):
        return obj.aadhaar_masked
    aadhaar_masked.short_description = 'Aadhaar Number (Masked)'
    
    def pan_masked(self, obj):
        return obj.pan_masked
    pan_masked.short_description = 'PAN Number (Masked)'


class BusinessDetailsInline(admin.StackedInline):
    """Inline for Business Details in KYC Application."""
    model = BusinessDetails
    can_delete = False
    readonly_fields = ['created_at', 'updated_at']


class VerificationImagesInline(admin.StackedInline):
    """Inline for Verification Images in KYC Application."""
    model = VerificationImages
    can_delete = False
    readonly_fields = ['created_at', 'updated_at']


class BankDetailsInline(admin.StackedInline):
    """Inline for Bank Details in KYC Application."""
    model = BankDetails
    can_delete = False
    readonly_fields = ['account_number_masked', 'created_at', 'updated_at']
    
    def account_number_masked(self, obj):
        return obj.account_number_masked
    account_number_masked.short_description = 'Account Number (Masked)'


class KYCProgressTrackerInline(admin.TabularInline):
    """Inline for Progress Tracker in KYC Application."""
    model = KYCProgressTracker
    can_delete = False
    extra = 0
    readonly_fields = ['step_name', 'step_number', 'mega_step', 'status', 'started_at', 'completed_at']


class KYCAuditLogInline(admin.TabularInline):
    """Inline for Audit Log in KYC Application."""
    model = KYCAuditLog
    can_delete = False
    extra = 0
    readonly_fields = ['action', 'performed_by', 'old_status', 'new_status', 'remarks', 'created_at']
    ordering = ['-created_at']


@admin.register(KYCApplication)
class KYCApplicationAdmin(admin.ModelAdmin):
    """Admin configuration for KYC Application."""
    list_display = [
        'application_id', 'user_email', 'status_badge', 'mega_step', 
        'completion_percentage', 'submitted_at', 'created_at'
    ]
    list_filter = ['status', 'mega_step', 'is_email_verified', 'is_phone_verified', 'created_at']
    search_fields = ['application_id', 'user__email', 'user__user_code']
    readonly_fields = [
        'id', 'application_id', 'completion_percentage', 
        'created_at', 'updated_at', 'submitted_at', 'reviewed_at', 'approved_at'
    ]
    ordering = ['-created_at']
    inlines = [
        IdentityProofInline, BusinessDetailsInline, 
        VerificationImagesInline, BankDetailsInline,
        KYCProgressTrackerInline, KYCAuditLogInline
    ]
    
    fieldsets = (
        ('Application Info', {
            'fields': ('id', 'application_id', 'user', 'status', 'mega_step')
        }),
        ('Progress', {
            'fields': ('current_step', 'total_steps', 'completion_percentage')
        }),
        ('Verification Status', {
            'fields': ('is_email_verified', 'email_verified_at', 'is_phone_verified', 'phone_verified_at')
        }),
        ('Review Info', {
            'fields': ('reviewed_by', 'review_remarks', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at', 'reviewed_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def status_badge(self, obj):
        colors = {
            'NOT_STARTED': '#6c757d',
            'IN_PROGRESS': '#007bff',
            'SUBMITTED': '#17a2b8',
            'UNDER_REVIEW': '#ffc107',
            'APPROVED': '#28a745',
            'REJECTED': '#dc3545',
            'RESUBMIT': '#fd7e14',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(IdentityProof)
class IdentityProofAdmin(admin.ModelAdmin):
    """Admin configuration for Identity Proof."""
    list_display = ['application_id', 'aadhaar_masked', 'aadhaar_verified', 'pan_masked', 'pan_verified']
    list_filter = ['aadhaar_verified', 'pan_verified']
    search_fields = ['kyc_application__application_id', 'kyc_application__user__email']
    readonly_fields = ['id', 'aadhaar_masked', 'pan_masked', 'created_at', 'updated_at']
    
    def application_id(self, obj):
        return obj.kyc_application.application_id
    application_id.short_description = 'Application ID'
    
    def aadhaar_masked(self, obj):
        return obj.aadhaar_masked
    aadhaar_masked.short_description = 'Aadhaar (Masked)'
    
    def pan_masked(self, obj):
        return obj.pan_masked
    pan_masked.short_description = 'PAN (Masked)'


@admin.register(BusinessDetails)
class BusinessDetailsAdmin(admin.ModelAdmin):
    """Admin configuration for Business Details."""
    list_display = ['application_id', 'business_name', 'business_phone', 'city', 'state', 'pincode']
    list_filter = ['state', 'city']
    search_fields = ['kyc_application__application_id', 'business_name', 'business_phone']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def application_id(self, obj):
        return obj.kyc_application.application_id
    application_id.short_description = 'Application ID'


@admin.register(VerificationImages)
class VerificationImagesAdmin(admin.ModelAdmin):
    """Admin configuration for Verification Images."""
    list_display = [
        'application_id', 'selfie_status', 'office_status', 
        'address_proof_status', 'address_proof_type'
    ]
    list_filter = ['selfie_verified', 'office_photos_verified', 'address_proof_verified']
    search_fields = ['kyc_application__application_id', 'kyc_application__user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def application_id(self, obj):
        return obj.kyc_application.application_id
    application_id.short_description = 'Application ID'
    
    def selfie_status(self, obj):
        if obj.selfie_image:
            return format_html('<span style="color: green;">✓ Uploaded</span>')
        return format_html('<span style="color: red;">✗ Pending</span>')
    selfie_status.short_description = 'Selfie'
    
    def office_status(self, obj):
        if obj.office_sitting_image and obj.office_door_image:
            return format_html('<span style="color: green;">✓ Uploaded</span>')
        return format_html('<span style="color: red;">✗ Pending</span>')
    office_status.short_description = 'Office Photos'
    
    def address_proof_status(self, obj):
        if obj.address_proof_image:
            return format_html('<span style="color: green;">✓ Uploaded</span>')
        return format_html('<span style="color: red;">✗ Pending</span>')
    address_proof_status.short_description = 'Address Proof'


@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    """Admin configuration for Bank Details."""
    list_display = ['application_id', 'account_holder_name', 'bank_name', 'ifsc_code', 'account_type', 'is_verified']
    list_filter = ['account_type', 'is_verified', 'bank_name']
    search_fields = ['kyc_application__application_id', 'account_holder_name', 'bank_name', 'ifsc_code']
    readonly_fields = ['id', 'account_number_masked', 'created_at', 'updated_at']
    
    def application_id(self, obj):
        return obj.kyc_application.application_id
    application_id.short_description = 'Application ID'
    
    def account_number_masked(self, obj):
        return obj.account_number_masked
    account_number_masked.short_description = 'Account Number (Masked)'


@admin.register(KYCProgressTracker)
class KYCProgressTrackerAdmin(admin.ModelAdmin):
    """Admin configuration for KYC Progress Tracker."""
    list_display = ['application_id', 'step_number', 'step_name', 'mega_step', 'status', 'completed_at']
    list_filter = ['status', 'mega_step', 'step_name']
    search_fields = ['kyc_application__application_id']
    readonly_fields = ['id', 'data_snapshot']
    ordering = ['kyc_application', 'step_number']
    
    def application_id(self, obj):
        return obj.kyc_application.application_id
    application_id.short_description = 'Application ID'


@admin.register(KYCAuditLog)
class KYCAuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for KYC Audit Log."""
    list_display = ['application_id', 'action', 'performed_by_email', 'old_status', 'new_status', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['kyc_application__application_id', 'performed_by__email', 'remarks']
    readonly_fields = ['id', 'kyc_application', 'action', 'performed_by', 'old_status', 'new_status', 
                       'remarks', 'data_changed', 'ip_address', 'user_agent', 'created_at']
    ordering = ['-created_at']
    
    def application_id(self, obj):
        return obj.kyc_application.application_id
    application_id.short_description = 'Application ID'
    
    def performed_by_email(self, obj):
        if obj.performed_by:
            return obj.performed_by.email
        return '-'
    performed_by_email.short_description = 'Performed By'

