"""
KYC Verification Views
=======================
API views for KYC/Onboarding system with:
- OTP verification (email/phone)
- Identity proof submission (Aadhaar, PAN)
- Business details submission
- Verification images upload
- Bank details submission
- KYC submission and status
- Admin review endpoints
"""

import random
import string
from datetime import timedelta

from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import (
    OTPVerification, KYCApplication, IdentityProof, BusinessDetails,
    VerificationImages, BankDetails, KYCProgressTracker, KYCAuditLog,
    OTPType, KYCStatus, MegaStep, StepStatus, AuditAction
)
from .serializers import (
    OTPSendSerializer, OTPVerifySerializer, OTPResponseSerializer,
    AadhaarDetailsSerializer, AadhaarUploadSerializer,
    PANDetailsSerializer, PANUploadSerializer, IdentityProofSerializer,
    BusinessDetailsInputSerializer, BusinessDetailsSerializer,
    SelfieUploadSerializer, OfficePhotosUploadSerializer,
    AddressProofUploadSerializer, VerificationImagesSerializer,
    BankDetailsInputSerializer, BankDetailsSerializer,
    KYCApplicationStatusSerializer, KYCApplicationDetailSerializer,
    KYCApplicationAdminDetailSerializer, KYCAdminListSerializer,
    KYCStartSerializer, KYCSubmitSerializer, KYCReviewActionSerializer,
    KYCProgressSerializer, IdentityProofAdminSerializer, BankDetailsAdminSerializer
)
from .permissions import IsKYCOwner, IsKYCAdmin, CanAccessKYCStep


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def generate_otp(length=6):
    """Generate numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


# =============================================================================
# OTP VIEWS
# =============================================================================

class OTPSendView(APIView):
    """
    Send OTP for email or phone verification.
    
    POST /api/auth-user/send-otp/
    {
        "otp_type": "EMAIL" | "PHONE",
        "email": "user@example.com",  // Required for EMAIL
        "phone": "9876543210"          // Required for PHONE
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from users_auth.email_service import send_otp_email
        from django.conf import settings
        
        serializer = OTPSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        otp_type = serializer.validated_data['otp_type']
        
        # Invalidate any existing unused OTPs of same type
        OTPVerification.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False
        ).update(expires_at=timezone.now())
        
        # Generate new OTP using configured length
        otp_length = getattr(settings, 'OTP_LENGTH', 6)
        otp_code = generate_otp(length=otp_length)
        
        # Use configured expiry time
        otp_expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        expires_at = timezone.now() + timedelta(minutes=otp_expiry)
        
        otp = OTPVerification.objects.create(
            user=user,
            otp_type=otp_type,
            otp_code=otp_code,
            expires_at=expires_at,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send OTP via email if type is EMAIL
        email_sent = False
        if otp_type == OTPType.EMAIL:
            user_email = serializer.validated_data.get('email') or user.email
            user_name = user.first_name or user.email.split('@')[0]
            email_sent = send_otp_email(
                email=user_email,
                otp_code=otp_code,
                user_name=user_name
            )
        
        response_data = {
            'success': True,
            'message': f'OTP sent successfully to your {otp_type.lower()}.',
            'otp_id': str(otp.id),
            'expires_at': otp.expires_at.isoformat(),
            'expires_in_seconds': otp_expiry * 60,
        }
        
        # Add email delivery status
        if otp_type == OTPType.EMAIL:
            response_data['email_sent'] = email_sent
        
        # Development only - return OTP in response for testing
        # Remove this in production by setting DEBUG=False
        if settings.DEBUG:
            response_data['otp_code_dev'] = otp_code
        
        return Response(response_data, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    """
    Verify OTP code.
    
    POST /api/auth-user/verify-otp/
    {
        "otp_type": "EMAIL" | "PHONE",
        "otp_code": "123456"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        otp_type = serializer.validated_data['otp_type']
        otp_code = serializer.validated_data['otp_code']
        
        # Get the latest OTP for this user and type
        otp = OTPVerification.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False
        ).order_by('-created_at').first()
        
        if not otp:
            return Response({
                'success': False,
                'message': 'No pending OTP found. Please request a new OTP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, message = otp.verify(otp_code)
        
        if success:
            # Update KYC application verification status
            if hasattr(user, 'kyc_application'):
                kyc_app = user.kyc_application
                if otp_type == OTPType.EMAIL:
                    kyc_app.is_email_verified = True
                    kyc_app.email_verified_at = timezone.now()
                    kyc_app.save(update_fields=['is_email_verified', 'email_verified_at', 'updated_at'])
                elif otp_type == OTPType.PHONE:
                    kyc_app.is_phone_verified = True
                    kyc_app.phone_verified_at = timezone.now()
                    kyc_app.save(update_fields=['is_phone_verified', 'phone_verified_at', 'updated_at'])
            
            return Response({
                'success': True,
                'message': f'{otp_type.replace("_", " ").title()} verified successfully.',
                'verified_at': otp.verified_at.isoformat()
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': message,
            'remaining_attempts': max(0, otp.max_attempts - otp.attempts)
        }, status=status.HTTP_400_BAD_REQUEST)


class OTPResendView(APIView):
    """
    Resend OTP for email or phone verification.
    
    POST /api/auth-user/resend-otp/
    {
        "otp_type": "EMAIL" | "PHONE"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        otp_type = request.data.get('otp_type')
        
        if otp_type not in [choice[0] for choice in OTPType.choices]:
            return Response({
                'success': False,
                'message': f'Invalid OTP type. Must be one of: {", ".join([c[0] for c in OTPType.choices])}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Check for rate limiting (max 3 OTPs per 15 minutes)
        fifteen_min_ago = timezone.now() - timedelta(minutes=15)
        recent_otps = OTPVerification.objects.filter(
            user=user,
            otp_type=otp_type,
            created_at__gte=fifteen_min_ago
        ).count()
        
        if recent_otps >= 3:
            return Response({
                'success': False,
                'message': 'Too many OTP requests. Please wait before requesting a new OTP.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Invalidate existing OTPs
        OTPVerification.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False
        ).update(expires_at=timezone.now())
        
        # Generate new OTP
        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)
        
        otp = OTPVerification.objects.create(
            user=user,
            otp_type=otp_type,
            otp_code=otp_code,
            expires_at=expires_at,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        response_data = {
            'success': True,
            'message': f'OTP resent successfully to your {otp_type.lower()}.',
            'otp_id': str(otp.id),
            'expires_at': otp.expires_at.isoformat(),
            'expires_in_seconds': 600,
        }
        
        # Development only - remove in production
        if hasattr(request, 'is_test') or True:  # TODO: Remove True in production
            response_data['otp_code_dev'] = otp_code
        
        return Response(response_data, status=status.HTTP_200_OK)


# =============================================================================
# KYC STATUS VIEWS
# =============================================================================

class KYCStatusView(APIView):
    """
    Get current KYC status and progress.
    
    GET /api/kyc/status/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': True,
                'has_kyc': False,
                'message': 'No KYC application found. Start KYC to begin.'
            }, status=status.HTTP_200_OK)
        
        kyc_app = user.kyc_application
        serializer = KYCApplicationStatusSerializer(kyc_app, context={'request': request})
        
        return Response({
            'success': True,
            'has_kyc': True,
            'kyc': serializer.data
        }, status=status.HTTP_200_OK)


class KYCStartView(APIView):
    """
    Start or resume KYC process.
    
    POST /api/kyc/start/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Check if already has approved KYC
        if hasattr(user, 'kyc_application'):
            kyc_app = user.kyc_application
            if kyc_app.status == KYCStatus.APPROVED:
                return Response({
                    'success': False,
                    'message': 'KYC already approved.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Resume existing application
            if kyc_app.status == KYCStatus.NOT_STARTED:
                kyc_app.status = KYCStatus.IN_PROGRESS
                kyc_app.save(update_fields=['status', 'updated_at'])
            
            serializer = KYCApplicationDetailSerializer(kyc_app, context={'request': request})
            return Response({
                'success': True,
                'message': 'KYC application resumed.',
                'kyc': serializer.data
            }, status=status.HTTP_200_OK)
        
        # Create new application
        kyc_app = KYCApplication.objects.create(
            user=user,
            status=KYCStatus.IN_PROGRESS
        )
        
        serializer = KYCApplicationDetailSerializer(kyc_app, context={'request': request})
        return Response({
            'success': True,
            'message': 'KYC application started successfully.',
            'kyc': serializer.data
        }, status=status.HTTP_201_CREATED)


class KYCDetailView(APIView):
    """
    Get full KYC details.
    
    GET /api/kyc/detail/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'No KYC application found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        kyc_app = user.kyc_application
        serializer = KYCApplicationDetailSerializer(kyc_app, context={'request': request})
        
        return Response({
            'success': True,
            'kyc': serializer.data
        }, status=status.HTTP_200_OK)


# =============================================================================
# IDENTITY PROOF VIEWS
# =============================================================================

class AadhaarDetailsView(APIView):
    """
    Submit Aadhaar details.
    
    POST /api/kyc/identity/aadhaar/
    {
        "aadhaar_number": "123456789012",
        "aadhaar_name": "John Doe",
        "aadhaar_dob": "1990-01-15",
        "aadhaar_address": "Full address from Aadhaar"
    }
    
    GET /api/kyc/identity/aadhaar/
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'No KYC application found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        identity_proof = user.kyc_application.identity_proof
        serializer = IdentityProofSerializer(identity_proof, context={'request': request})
        
        return Response({
            'success': True,
            'aadhaar': {
                'aadhaar_masked': serializer.data.get('aadhaar_masked'),
                'aadhaar_name': serializer.data.get('aadhaar_name'),
                'aadhaar_dob': serializer.data.get('aadhaar_dob'),
                'aadhaar_address': serializer.data.get('aadhaar_address'),
                'is_complete': serializer.data.get('is_aadhaar_complete'),
                'is_verified': serializer.data.get('aadhaar_verified'),
            }
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'error': 'Please start KYC first.',
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'error': f'Cannot update Aadhaar details. KYC status: {kyc_app.status}',
                'message': f'Cannot update Aadhaar details. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AadhaarDetailsSerializer(data=request.data)
        if not serializer.is_valid():
            # Return validation errors in a clear format
            error_messages = []
            for field, errors in serializer.errors.items():
                for error in errors:
                    error_messages.append(f'{field}: {error}')
            return Response({
                'success': False,
                'error': '; '.join(error_messages),
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        identity_proof = kyc_app.identity_proof
        identity_proof.aadhaar_number = serializer.validated_data['aadhaar_number']
        identity_proof.aadhaar_name = serializer.validated_data['aadhaar_name']
        identity_proof.aadhaar_dob = serializer.validated_data['aadhaar_dob']
        identity_proof.aadhaar_address = serializer.validated_data.get('aadhaar_address', '')
        identity_proof.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=1).first()
        if progress:
            progress.complete(data_snapshot={
                'aadhaar_name': identity_proof.aadhaar_name,
                'aadhaar_dob': str(identity_proof.aadhaar_dob)
            })
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.STEP_COMPLETED,
            performed_by=user,
            remarks='Aadhaar details submitted',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Aadhaar details saved successfully.',
            'aadhaar_masked': identity_proof.aadhaar_masked
        }, status=status.HTTP_200_OK)


class AadhaarUploadView(APIView):
    """
    Upload Aadhaar images (front and back).
    
    POST /api/kyc/identity/aadhaar/upload/
    FormData:
        aadhaar_front_image: file
        aadhaar_back_image: file
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = []  # Using custom throttle below
    
    def get_throttles(self):
        """Apply KYC upload rate throttle."""
        from users_auth.throttling import KYCUploadThrottle
        return [KYCUploadThrottle()]
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot upload Aadhaar images. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AadhaarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identity_proof = kyc_app.identity_proof
        
        # Delete old images if exist
        if identity_proof.aadhaar_front_image:
            identity_proof.aadhaar_front_image.delete(save=False)
        if identity_proof.aadhaar_back_image:
            identity_proof.aadhaar_back_image.delete(save=False)
        
        identity_proof.aadhaar_front_image = serializer.validated_data['aadhaar_front_image']
        identity_proof.aadhaar_back_image = serializer.validated_data['aadhaar_back_image']
        identity_proof.aadhaar_submitted_at = timezone.now()
        identity_proof.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=2).first()
        if progress:
            progress.complete()
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.DOCUMENT_UPLOADED,
            performed_by=user,
            remarks='Aadhaar images uploaded',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Aadhaar images uploaded successfully.'
        }, status=status.HTTP_200_OK)


class PANDetailsView(APIView):
    """
    Submit PAN details.
    
    POST /api/kyc/identity/pan/
    {
        "pan_number": "ABCDE1234F",
        "pan_name": "John Doe",
        "pan_dob": "1990-01-15",
        "pan_father_name": "Father Name"
    }
    
    GET /api/kyc/identity/pan/
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'No KYC application found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        identity_proof = user.kyc_application.identity_proof
        serializer = IdentityProofSerializer(identity_proof, context={'request': request})
        
        return Response({
            'success': True,
            'pan': {
                'pan_masked': serializer.data.get('pan_masked'),
                'pan_name': serializer.data.get('pan_name'),
                'pan_dob': serializer.data.get('pan_dob'),
                'pan_father_name': serializer.data.get('pan_father_name'),
                'is_complete': serializer.data.get('is_pan_complete'),
                'is_verified': serializer.data.get('pan_verified'),
            }
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot update PAN details. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PANDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identity_proof = kyc_app.identity_proof
        identity_proof.pan_number = serializer.validated_data['pan_number']
        identity_proof.pan_name = serializer.validated_data['pan_name']
        identity_proof.pan_dob = serializer.validated_data['pan_dob']
        identity_proof.pan_father_name = serializer.validated_data.get('pan_father_name', '')
        identity_proof.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=3).first()
        if progress:
            progress.complete(data_snapshot={
                'pan_name': identity_proof.pan_name,
                'pan_dob': str(identity_proof.pan_dob)
            })
        
        # Update mega step if identity proof complete
        if identity_proof.is_aadhaar_complete:
            kyc_app.mega_step = MegaStep.SELFIE_AND_BUSINESS
            kyc_app.current_step = 5
            kyc_app.save(update_fields=['mega_step', 'current_step', 'updated_at'])
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.STEP_COMPLETED,
            performed_by=user,
            remarks='PAN details submitted',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'PAN details saved successfully.',
            'pan_masked': identity_proof.pan_masked
        }, status=status.HTTP_200_OK)


class PANUploadView(APIView):
    """
    Upload PAN image.
    
    POST /api/kyc/identity/pan/upload/
    FormData:
        pan_image: file
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = []  # Using custom throttle below
    
    def get_throttles(self):
        """Apply KYC upload rate throttle."""
        from users_auth.throttling import KYCUploadThrottle
        return [KYCUploadThrottle()]
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot upload PAN image. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PANUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identity_proof = kyc_app.identity_proof
        
        # Delete old image if exists
        if identity_proof.pan_image:
            identity_proof.pan_image.delete(save=False)
        
        identity_proof.pan_image = serializer.validated_data['pan_image']
        identity_proof.pan_submitted_at = timezone.now()
        identity_proof.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=4).first()
        if progress:
            progress.complete()
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.DOCUMENT_UPLOADED,
            performed_by=user,
            remarks='PAN image uploaded',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'PAN image uploaded successfully.'
        }, status=status.HTTP_200_OK)


# =============================================================================
# BUSINESS DETAILS VIEWS
# =============================================================================

class BusinessDetailsView(APIView):
    """
    Submit or get business details.
    
    POST/PUT /api/kyc/business/
    {
        "business_name": "My Business",
        "business_type": "Retail",
        "business_phone": "9876543210",
        "business_email": "business@example.com",
        "address_line_1": "123 Main Street",
        "address_line_2": "Near Park",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001"
    }
    
    GET /api/kyc/business/
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'No KYC application found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        business_details = user.kyc_application.business_details
        serializer = BusinessDetailsSerializer(business_details, context={'request': request})
        
        return Response({
            'success': True,
            'business': serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        return self._save_business_details(request)
    
    def put(self, request):
        return self._save_business_details(request)
    
    def _save_business_details(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot update business details. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = BusinessDetailsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        business_details = kyc_app.business_details
        
        # Update all fields
        for field, value in serializer.validated_data.items():
            setattr(business_details, field, value)
        
        business_details.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=5).first()
        if progress:
            progress.complete(data_snapshot={
                'business_name': business_details.business_name,
                'city': business_details.city,
                'pincode': business_details.pincode
            })
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.STEP_COMPLETED,
            performed_by=user,
            remarks='Business details submitted',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        response_serializer = BusinessDetailsSerializer(business_details, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Business details saved successfully.',
            'business': response_serializer.data
        }, status=status.HTTP_200_OK)


# =============================================================================
# VERIFICATION IMAGES VIEWS
# =============================================================================

class SelfieUploadView(APIView):
    """
    Upload selfie image.
    
    POST /api/kyc/verification/selfie/
    FormData:
        selfie_image: file
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = []  # Using custom throttle below
    
    def get_throttles(self):
        """Apply KYC upload rate throttle."""
        from users_auth.throttling import KYCUploadThrottle
        return [KYCUploadThrottle()]
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot upload selfie. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = SelfieUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verification_images = kyc_app.verification_images
        
        # Delete old image if exists
        if verification_images.selfie_image:
            verification_images.selfie_image.delete(save=False)
        
        verification_images.selfie_image = serializer.validated_data['selfie_image']
        verification_images.selfie_submitted_at = timezone.now()
        verification_images.save()
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.DOCUMENT_UPLOADED,
            performed_by=user,
            remarks='Selfie uploaded',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Selfie uploaded successfully.'
        }, status=status.HTTP_200_OK)


class OfficePhotosUploadView(APIView):
    """
    Upload office photos (sitting inside and door with name board).
    
    POST /api/kyc/verification/office/
    FormData:
        office_sitting_image: file
        office_door_image: file
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = []  # Using custom throttle below
    
    def get_throttles(self):
        """Apply KYC upload rate throttle."""
        from users_auth.throttling import KYCUploadThrottle
        return [KYCUploadThrottle()]
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot upload office photos. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = OfficePhotosUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verification_images = kyc_app.verification_images
        
        # Delete old images if exist
        if verification_images.office_sitting_image:
            verification_images.office_sitting_image.delete(save=False)
        if verification_images.office_door_image:
            verification_images.office_door_image.delete(save=False)
        
        verification_images.office_sitting_image = serializer.validated_data['office_sitting_image']
        verification_images.office_door_image = serializer.validated_data['office_door_image']
        verification_images.office_photos_submitted_at = timezone.now()
        verification_images.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=6).first()
        if progress:
            progress.complete()
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.DOCUMENT_UPLOADED,
            performed_by=user,
            remarks='Office photos uploaded',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Office photos uploaded successfully.'
        }, status=status.HTTP_200_OK)


class AddressProofUploadView(APIView):
    """
    Upload address proof (utility bill, rental agreement, etc.).
    
    POST /api/kyc/verification/address-proof/
    FormData:
        address_proof_image: file
        address_proof_type: string (e.g., "Utility Bill", "Rental Agreement")
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = []  # Using custom throttle below
    
    def get_throttles(self):
        """Apply KYC upload rate throttle."""
        from users_auth.throttling import KYCUploadThrottle
        return [KYCUploadThrottle()]
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot upload address proof. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AddressProofUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verification_images = kyc_app.verification_images
        
        # Delete old image if exists
        if verification_images.address_proof_image:
            verification_images.address_proof_image.delete(save=False)
        
        verification_images.address_proof_image = serializer.validated_data['address_proof_image']
        verification_images.address_proof_type = serializer.validated_data['address_proof_type']
        verification_images.address_proof_submitted_at = timezone.now()
        verification_images.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=7).first()
        if progress:
            progress.complete()
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.DOCUMENT_UPLOADED,
            performed_by=user,
            remarks=f'Address proof uploaded: {verification_images.address_proof_type}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Address proof uploaded successfully.'
        }, status=status.HTTP_200_OK)


class VerificationImagesView(APIView):
    """
    Get verification images status.
    
    GET /api/kyc/verification/
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'No KYC application found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        verification_images = user.kyc_application.verification_images
        serializer = VerificationImagesSerializer(verification_images, context={'request': request})
        
        return Response({
            'success': True,
            'verification_images': serializer.data
        }, status=status.HTTP_200_OK)


# =============================================================================
# BANK DETAILS VIEWS
# =============================================================================

class BankDetailsView(APIView):
    """
    Submit or get bank details.
    
    POST/PUT /api/kyc/bank/
    FormData:
        account_holder_name: string
        account_number: string
        confirm_account_number: string
        ifsc_code: string
        account_type: "SAVINGS" | "CURRENT"
        bank_name: string
        branch_name: string
        branch_address: string
        bank_document: file
    
    GET /api/kyc/bank/
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'No KYC application found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        bank_details = user.kyc_application.bank_details
        serializer = BankDetailsSerializer(bank_details, context={'request': request})
        
        return Response({
            'success': True,
            'bank': serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        return self._save_bank_details(request)
    
    def put(self, request):
        return self._save_bank_details(request)
    
    def _save_bank_details(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'Please start KYC first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot update bank details. KYC status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = BankDetailsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        bank_details = kyc_app.bank_details
        
        # Delete old document if exists and new one is being uploaded
        new_document = serializer.validated_data.get('bank_document')
        if new_document and bank_details.bank_document:
            bank_details.bank_document.delete(save=False)
        
        # Update fields
        bank_details.account_holder_name = serializer.validated_data['account_holder_name']
        bank_details.account_number = serializer.validated_data['account_number']
        bank_details.set_confirm_account_number(serializer.validated_data['confirm_account_number'])
        bank_details.ifsc_code = serializer.validated_data['ifsc_code'].upper()
        bank_details.account_type = serializer.validated_data['account_type']
        bank_details.bank_name = serializer.validated_data['bank_name']
        bank_details.branch_name = serializer.validated_data.get('branch_name', '')
        bank_details.branch_address = serializer.validated_data.get('branch_address', '')
        if new_document:
            bank_details.bank_document = new_document
        bank_details.save()
        
        # Update progress tracker
        progress = kyc_app.progress_steps.filter(step_number=8).first()
        if progress:
            progress.complete(data_snapshot={
                'bank_name': bank_details.bank_name,
                'ifsc_code': bank_details.ifsc_code
            })
        
        # Mark all steps completed
        kyc_app.mega_step = MegaStep.COMPLETED
        kyc_app.current_step = 8
        kyc_app.save(update_fields=['mega_step', 'current_step', 'updated_at'])
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.STEP_COMPLETED,
            performed_by=user,
            remarks='Bank details submitted',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        response_serializer = BankDetailsSerializer(bank_details, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Bank details saved successfully.',
            'bank': response_serializer.data
        }, status=status.HTTP_200_OK)


# =============================================================================
# KYC SUBMIT VIEW
# =============================================================================

class KYCSubmitView(APIView):
    """
    Submit KYC for review.
    
    POST /api/kyc/submit/
    """
    permission_classes = [IsAuthenticated, IsKYCOwner]
    
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'kyc_application'):
            return Response({
                'success': False,
                'message': 'No KYC application found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        kyc_app = user.kyc_application
        
        if kyc_app.status not in [KYCStatus.IN_PROGRESS, KYCStatus.RESUBMIT]:
            return Response({
                'success': False,
                'message': f'Cannot submit KYC with status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate all steps are complete
        errors = []
        
        if not kyc_app.identity_proof.is_complete:
            errors.append('Identity proof is incomplete.')
        
        if not kyc_app.business_details.is_complete:
            errors.append('Business details are incomplete.')
        
        if not kyc_app.verification_images.is_complete:
            errors.append('Verification images are incomplete.')
        
        if not kyc_app.bank_details.is_complete:
            errors.append('Bank details are incomplete.')
        
        if errors:
            return Response({
                'success': False,
                'message': 'KYC is incomplete.',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Submit KYC
        old_status = kyc_app.status
        kyc_app.status = KYCStatus.SUBMITTED
        kyc_app.submitted_at = timezone.now()
        kyc_app.save(update_fields=['status', 'submitted_at', 'updated_at'])
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.KYC_SUBMITTED,
            performed_by=user,
            old_status=old_status,
            new_status=KYCStatus.SUBMITTED,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'KYC submitted successfully for review.',
            'application_id': kyc_app.application_id,
            'status': kyc_app.status,
            'submitted_at': kyc_app.submitted_at.isoformat()
        }, status=status.HTTP_200_OK)


# =============================================================================
# ADMIN VIEWS
# =============================================================================

class KYCAdminListView(generics.ListAPIView):
    """
    List all KYC applications for admin.
    
    GET /api/kyc/admin/applications/
    Query params:
        status: Filter by status
        search: Search by email or application_id
    """
    permission_classes = [IsAuthenticated, IsKYCAdmin]
    serializer_class = KYCAdminListSerializer
    
    def get_queryset(self):
        queryset = KYCApplication.objects.filter(is_deleted=False).select_related('user')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(application_id__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__user_code__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Get counts by status
        from django.db.models import Count
        status_counts = KYCApplication.objects.filter(is_deleted=False).values('status').annotate(count=Count('id'))
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'status_summary': {item['status']: item['count'] for item in status_counts},
            'applications': serializer.data
        }, status=status.HTTP_200_OK)


class KYCAdminDetailView(APIView):
    """
    Get detailed KYC application for admin review.
    
    GET /api/kyc/admin/applications/<application_id>/
    """
    permission_classes = [IsAuthenticated, IsKYCAdmin]
    
    def get(self, request, application_id):
        kyc_app = get_object_or_404(
            KYCApplication.objects.select_related('user', 'reviewed_by')
                .prefetch_related('progress_steps', 'audit_logs'),
            application_id=application_id,
            is_deleted=False
        )
        
        serializer = KYCApplicationAdminDetailSerializer(kyc_app, context={'request': request})
        
        return Response({
            'success': True,
            'kyc': serializer.data
        }, status=status.HTTP_200_OK)


class KYCAdminReviewView(APIView):
    """
    Admin review actions: approve, reject, request resubmit.
    
    POST /api/kyc/admin/applications/<application_id>/review/
    {
        "action": "approve" | "reject" | "resubmit",
        "remarks": "Review remarks (required for reject/resubmit)"
    }
    """
    permission_classes = [IsAuthenticated, IsKYCAdmin]
    
    def post(self, request, application_id):
        kyc_app = get_object_or_404(
            KYCApplication,
            application_id=application_id,
            is_deleted=False
        )
        
        serializer = KYCReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        remarks = serializer.validated_data.get('remarks', '')
        
        old_status = kyc_app.status
        admin_user = request.user
        
        if action == 'approve':
            if kyc_app.status not in [KYCStatus.SUBMITTED, KYCStatus.UNDER_REVIEW]:
                return Response({
                    'success': False,
                    'message': f'Cannot approve KYC with status: {kyc_app.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            kyc_app.approve(admin_user, remarks)
            audit_action = AuditAction.ADMIN_APPROVED
            message = 'KYC approved successfully.'
            
        elif action == 'reject':
            if kyc_app.status not in [KYCStatus.SUBMITTED, KYCStatus.UNDER_REVIEW]:
                return Response({
                    'success': False,
                    'message': f'Cannot reject KYC with status: {kyc_app.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            kyc_app.reject(admin_user, remarks)
            audit_action = AuditAction.ADMIN_REJECTED
            message = 'KYC rejected.'
            
        elif action == 'resubmit':
            if kyc_app.status not in [KYCStatus.SUBMITTED, KYCStatus.UNDER_REVIEW]:
                return Response({
                    'success': False,
                    'message': f'Cannot request resubmit for KYC with status: {kyc_app.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            kyc_app.request_resubmit(admin_user, remarks)
            audit_action = AuditAction.RESUBMIT_REQUESTED
            message = 'Resubmission requested.'
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=audit_action,
            performed_by=admin_user,
            old_status=old_status,
            new_status=kyc_app.status,
            remarks=remarks,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': message,
            'application_id': kyc_app.application_id,
            'status': kyc_app.status
        }, status=status.HTTP_200_OK)


class KYCAdminStartReviewView(APIView):
    """
    Start reviewing a KYC application (changes status to UNDER_REVIEW).
    
    POST /api/kyc/admin/applications/<application_id>/start-review/
    """
    permission_classes = [IsAuthenticated, IsKYCAdmin]
    
    def post(self, request, application_id):
        kyc_app = get_object_or_404(
            KYCApplication,
            application_id=application_id,
            is_deleted=False
        )
        
        if kyc_app.status != KYCStatus.SUBMITTED:
            return Response({
                'success': False,
                'message': f'Cannot start review for KYC with status: {kyc_app.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = kyc_app.status
        kyc_app.start_review(request.user)
        
        # Log action
        KYCAuditLog.log_action(
            kyc_application=kyc_app,
            action=AuditAction.ADMIN_REVIEW,
            performed_by=request.user,
            old_status=old_status,
            new_status=KYCStatus.UNDER_REVIEW,
            remarks='Started review',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Review started.',
            'application_id': kyc_app.application_id,
            'status': kyc_app.status
        }, status=status.HTTP_200_OK)
