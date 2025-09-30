"""
ERP Admin Configuration
Django admin interface for ERP models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserAccount, Branch, AadhaarKYC, PanKYC, BusinessDetails,
    BusinessImages, BankDetails, LoginActivity, AuditTrail,
    AppFeature, UserPlatformAccess, AppAccessControl
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['branch_code', 'branch_name', 'city', 'state', 'manager_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'state', 'country', 'created_at']
    search_fields = ['branch_code', 'branch_name', 'city', 'manager_name']
    ordering = ['branch_code']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'branch_code', 'branch_name', 'manager_name', 'is_active')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'pincode')
        }),
        ('Contact', {
            'fields': ('phone', 'email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    list_display = ['id', 'email', 'full_name', 'role', 'branch', 'is_active', 'is_email_verified', 'is_mobile_verified', 'created_at']
    list_filter = ['role', 'is_active', 'is_email_verified', 'is_mobile_verified', 'is_kyc_completed', 'branch', 'created_at']
    search_fields = ['id', 'email', 'mobile', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['id', 'login_count', 'created_at', 'updated_at', 'last_login']
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Full Name'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'first_name', 'last_name', 'email', 'mobile')
        }),
        ('Role & Branch', {
            'fields': ('role', 'branch')
        }),
        ('Verification Status', {
            'fields': ('is_email_verified', 'is_mobile_verified', 'is_kyc_completed', 'is_business_verified', 'is_bank_verified')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Security', {
            'fields': ('login_count', 'login_attempts', 'login_blocked_until', 'last_login_ip', 'last_login_device'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        })
    )
    
    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('email', 'mobile', 'first_name', 'last_name', 'password1', 'password2', 'role', 'branch'),
        }),
    )


@admin.register(AadhaarKYC)
class AadhaarKYCAdmin(admin.ModelAdmin):
    list_display = ['user', 'aadhaar_name', 'masked_aadhaar', 'is_verified', 'verified_at', 'created_at']
    list_filter = ['is_verified', 'verified_at', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'aadhaar_name']
    readonly_fields = ['id', 'masked_aadhaar', 'created_at', 'updated_at']
    
    def masked_aadhaar(self, obj):
        return obj.get_masked_aadhaar()
    masked_aadhaar.short_description = 'Aadhaar Number'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'aadhaar_name')
        }),
        ('Aadhaar Details', {
            'fields': ('masked_aadhaar', 'aadhaar_front_image', 'aadhaar_back_image')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verification_remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PanKYC)
class PanKYCAdmin(admin.ModelAdmin):
    list_display = ['user', 'pan_number', 'pan_name', 'date_of_birth', 'is_verified', 'verified_at']
    list_filter = ['is_verified', 'verified_at', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'pan_number', 'pan_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'pan_name', 'date_of_birth')
        }),
        ('PAN Details', {
            'fields': ('pan_number', 'pan_image')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verification_remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(BusinessDetails)
class BusinessDetailsAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_name', 'city', 'state', 'is_business_phone_verified', 'is_business_email_verified', 'is_verified']
    list_filter = ['is_business_phone_verified', 'is_business_email_verified', 'is_verified', 'state', 'created_at']
    search_fields = ['user__email', 'business_name', 'city', 'business_phone', 'business_email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_selfie')
        }),
        ('Business Details', {
            'fields': ('business_name', 'business_address_line1', 'business_address_line2', 'city', 'state', 'country', 'pincode')
        }),
        ('Contact Details', {
            'fields': ('business_phone', 'business_email', 'is_business_phone_verified', 'is_business_email_verified')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verification_remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class BusinessImagesInline(admin.TabularInline):
    model = BusinessImages
    extra = 0
    readonly_fields = ['id', 'uploaded_at']
    fields = ['image', 'image_description', 'uploaded_at']


@admin.register(BusinessImages)
class BusinessImagesAdmin(admin.ModelAdmin):
    list_display = ['business', 'image_description', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['business__business_name', 'business__user__email', 'image_description']
    readonly_fields = ['id', 'uploaded_at']


# Add inline to BusinessDetailsAdmin
BusinessDetailsAdmin.inlines = [BusinessImagesInline]


@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_holder_name', 'bank_name', 'masked_account_number', 'ifsc_code', 'is_verified']
    list_filter = ['is_verified', 'account_type', 'bank_name', 'created_at']
    search_fields = ['user__email', 'account_holder_name', 'bank_name', 'ifsc_code']
    readonly_fields = ['id', 'masked_account_number', 'created_at', 'updated_at']
    
    def masked_account_number(self, obj):
        return obj.get_masked_account_number()
    masked_account_number.short_description = 'Account Number'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'account_holder_name')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'branch_name', 'ifsc_code', 'account_type', 'masked_account_number')
        }),
        ('Documentation', {
            'fields': ('bank_proof_image',)
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verification_remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_or_mobile', 'ip_address', 'status', 'login_timestamp', 'session_duration']
    list_filter = ['status', 'login_timestamp', 'logout_timestamp']
    search_fields = ['user__email', 'email_or_mobile', 'ip_address', 'user_agent']
    readonly_fields = ['id', 'login_timestamp', 'logout_timestamp', 'session_duration']
    ordering = ['-login_timestamp']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email_or_mobile')
        }),
        ('Session Details', {
            'fields': ('ip_address', 'user_agent', 'device_info')
        }),
        ('Status', {
            'fields': ('status', 'failure_reason')
        }),
        ('Timing', {
            'fields': ('login_timestamp', 'logout_timestamp', 'session_duration')
        })
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'resource_id', 'description', 'created_at']
    list_filter = ['action', 'resource_type', 'created_at']
    search_fields = ['user__email', 'action', 'resource_type', 'description']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Action Details', {
            'fields': ('action', 'resource_type', 'resource_id', 'description')
        }),
        ('Data Changes', {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AppFeature)
class AppFeatureAdmin(admin.ModelAdmin):
    list_display = ['feature_code', 'feature_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['feature_code', 'feature_name', 'description']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Feature Information', {
            'fields': ('feature_code', 'feature_name', 'description', 'is_active')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(UserPlatformAccess)
class UserPlatformAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'is_allowed', 'granted_by', 'granted_at']
    list_filter = ['platform', 'is_allowed', 'granted_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'granted_at', 'revoked_at']
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'platform', 'is_allowed')
        }),
        ('Management', {
            'fields': ('granted_by', 'granted_at', 'revoked_at')
        })
    )


@admin.register(AppAccessControl)
class AppAccessControlAdmin(admin.ModelAdmin):
    list_display = ['user', 'feature', 'is_allowed', 'granted_by', 'granted_at']
    list_filter = ['feature', 'is_allowed', 'granted_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'granted_at']
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'feature', 'is_allowed')
        }),
        ('Management', {
            'fields': ('granted_by', 'granted_at')
        })
    )


# Customize admin site
admin.site.site_header = "CredBuzz ERP Admin"
admin.site.site_title = "CredBuzz ERP"
admin.site.index_title = "ERP Administration"