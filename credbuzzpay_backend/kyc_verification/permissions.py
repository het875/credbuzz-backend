"""
KYC Verification Permissions
=============================
Custom permissions for KYC/Onboarding system with:
- KYC owner validation
- Admin access control
- Step-by-step access validation
"""

from rest_framework.permissions import BasePermission


class IsKYCOwner(BasePermission):
    """
    Permission to check if user owns the KYC application.
    Allows access only if the user has an associated KYC application.
    """
    message = 'You do not have a KYC application.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # Check if the KYC application belongs to the user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'kyc_application'):
            return obj.kyc_application.user == request.user
        return False


class IsKYCAdmin(BasePermission):
    """
    Permission for KYC admin access.
    Allows access to super admins and users with KYC admin role.
    """
    message = 'You do not have admin access for KYC management.'
    
    ADMIN_ROLES = ['SUPER_ADMIN', 'ADMIN', 'DEVELOPER', 'super_admin', 'admin', 'kyc_admin', 'kyc_reviewer']
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check user role directly (custom User model)
        user_role = getattr(request.user, 'user_role', None)
        if user_role and user_role.upper() in [r.upper() for r in self.ADMIN_ROLES]:
            return True
        
        # Check RBAC permissions if available
        if hasattr(request.user, 'user_roles'):
            user_roles = request.user.user_roles.filter(is_active=True).select_related('role')
            for user_role in user_roles:
                role_name = user_role.role.name.lower()
                if role_name in [r.lower() for r in self.ADMIN_ROLES]:
                    return True
                
                # Check for KYC-related features
                if hasattr(user_role.role, 'role_features'):
                    features = user_role.role.role_features.filter(
                        is_active=True,
                        feature__app_name='kyc_verification'
                    ).select_related('feature')
                    
                    for rf in features:
                        if rf.can_view or rf.can_create or rf.can_edit:
                            return True
        
        return False


class CanAccessKYCStep(BasePermission):
    """
    Permission to check if user can access a specific KYC step.
    Ensures steps are accessed in order.
    """
    message = 'You cannot access this step yet. Please complete previous steps first.'
    
    # Step order mapping
    STEP_ORDER = {
        'aadhaar_details': 1,
        'aadhaar_upload': 2,
        'pan_details': 3,
        'pan_upload': 4,
        'business_details': 5,
        'verification_images': 6,
        'address_proof': 7,
        'bank_details': 8,
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'kyc_application'):
            return True  # Will be handled by view
        
        kyc_app = request.user.kyc_application
        
        # Allow access during IN_PROGRESS or RESUBMIT status
        from .models import KYCStatus
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return False
        
        # Get step name from view
        step_name = getattr(view, 'kyc_step_name', None)
        if not step_name or step_name not in self.STEP_ORDER:
            return True  # No specific step validation needed
        
        required_step = self.STEP_ORDER[step_name]
        
        # For resubmission, allow access to all steps
        if kyc_app.status == KYCStatus.RESUBMIT:
            return True
        
        # Check if previous steps are complete
        if required_step > 1:
            completed_steps = kyc_app.progress_steps.filter(
                status='COMPLETED',
                step_number__lt=required_step
            ).count()
            
            # Must complete at least step - 1 previous steps
            if completed_steps < required_step - 1:
                return False
        
        return True


class IsEmailVerified(BasePermission):
    """
    Permission to check if user's email is verified for KYC.
    """
    message = 'Please verify your email before proceeding with KYC.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'kyc_application'):
            return request.user.kyc_application.is_email_verified
        
        # If no KYC application, allow access (will be created)
        return True


class IsPhoneVerified(BasePermission):
    """
    Permission to check if user's phone is verified for KYC.
    """
    message = 'Please verify your phone number before proceeding with KYC.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'kyc_application'):
            return request.user.kyc_application.is_phone_verified
        
        # If no KYC application, allow access (will be created)
        return True


class IsBothVerified(BasePermission):
    """
    Permission to check if both email and phone are verified.
    """
    message = 'Please verify both email and phone before proceeding.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'kyc_application'):
            kyc_app = request.user.kyc_application
            return kyc_app.is_email_verified and kyc_app.is_phone_verified
        
        # If no KYC application, allow access (will be created)
        return True


class CanSubmitKYC(BasePermission):
    """
    Permission to check if KYC can be submitted.
    Validates all steps are complete.
    """
    message = 'Please complete all KYC steps before submitting.'
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'kyc_application'):
            return False
        
        kyc_app = request.user.kyc_application
        
        # Check completion percentage
        if kyc_app.completion_percentage < 100:
            return False
        
        # Validate all components are complete
        if not kyc_app.identity_proof.is_complete:
            return False
        
        if not kyc_app.business_details.is_complete:
            return False
        
        if not kyc_app.verification_images.is_complete:
            return False
        
        if not kyc_app.bank_details.is_complete:
            return False
        
        return True


class CanReviewKYC(BasePermission):
    """
    Permission for reviewing specific KYC application.
    Admin must have review capability.
    """
    message = 'You do not have permission to review this KYC application.'
    
    def has_permission(self, request, view):
        return IsKYCAdmin().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        # Check if KYC is in reviewable status
        from .models import KYCStatus
        
        if hasattr(obj, 'status'):
            return obj.status in [KYCStatus.SUBMITTED, KYCStatus.UNDER_REVIEW]
        
        return False
