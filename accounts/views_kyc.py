"""
KYC (Know Your Customer) verification APIs.
Handles Aadhaar, PAN, Business, and Bank verification.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from accounts.models import (
    UserAccount, AadhaarKYC, PANKYC, BusinessDetails, BankDetails,
    OTPRecord, AuditTrail
)
from accounts.serializers import (
    AadhaarKYCSerializer, PANKYCSerializer, BusinessDetailsSerializer,
    BankDetailsSerializer
)
from accounts.utils.code_generator import generate_unique_id
from accounts.services.kyc_service import KYCService
from accounts.services.audit_service import log_user_action
from accounts.permissions import IsActiveUser, IsNotBlocked


class AadhaarKYCViewSet(viewsets.ViewSet):
    """
    Aadhaar KYC verification endpoints.
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsNotBlocked]
    
    @action(detail=False, methods=['post'])
    def submit_aadhaar(self, request):
        """
        POST /api/v1/kyc/aadhaar/submit
        Submit Aadhaar information for verification.
        """
        try:
            user = request.user
            
            aadhaar_number = request.data.get('aadhaar_number')
            aadhaar_name = request.data.get('name')
            aadhaar_dob = request.data.get('dob')
            aadhaar_gender = request.data.get('gender')
            
            if not all([aadhaar_number, aadhaar_name, aadhaar_dob, aadhaar_gender]):
                return Response(
                    {'error': 'All required fields (aadhaar_number, name, dob, gender) must be provided.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if Aadhaar already submitted
            if AadhaarKYC.objects.filter(user_code=user).exists():
                return Response(
                    {'error': 'Aadhaar KYC already submitted for this user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create or update Aadhaar KYC record
            aadhaar_id = generate_unique_id()
            aadhaar_kyc = AadhaarKYC.objects.create(
                id=aadhaar_id,
                user_code=user,
                aadhaar_number_encrypted=KYCService.encrypt_field(aadhaar_number),
                aadhaar_name=aadhaar_name,
                aadhaar_dob=aadhaar_dob,
                aadhaar_gender=aadhaar_gender,
                aadhaar_address=request.data.get('address', ''),
                verification_method='manual'
            )
            
            # Update user KYC tracking
            user.kyc_verification_step = max(user.kyc_verification_step, 1)
            user.save()
            
            # Log audit
            log_user_action(
                action='kyc_submit',
                user_code=user,
                description=f'Aadhaar KYC submitted',
                resource_type='AadhaarKYC',
                resource_id=aadhaar_id,
                ip_address=self._get_client_ip(request)
            )
            
            serializer = AadhaarKYCSerializer(aadhaar_kyc)
            return Response({
                'message': 'Aadhaar KYC submitted successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_aadhaar_status(self, request):
        """
        GET /api/v1/kyc/aadhaar/status
        Get Aadhaar KYC verification status.
        """
        try:
            user = request.user
            aadhaar_kyc = AadhaarKYC.objects.filter(user_code=user).first()
            
            if not aadhaar_kyc:
                return Response(
                    {'status': 'not_submitted', 'message': 'Aadhaar KYC not submitted yet.'},
                    status=status.HTTP_200_OK
                )
            
            serializer = AadhaarKYCSerializer(aadhaar_kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PANKYCViewSet(viewsets.ViewSet):
    """
    PAN KYC verification endpoints.
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsNotBlocked]
    
    @action(detail=False, methods=['post'])
    def submit_pan(self, request):
        """
        POST /api/v1/kyc/pan/submit
        Submit PAN information for verification.
        """
        try:
            user = request.user
            
            pan_number = request.data.get('pan_number')
            pan_name = request.data.get('name')
            pan_dob = request.data.get('dob')
            
            if not all([pan_number, pan_name, pan_dob]):
                return Response(
                    {'error': 'All required fields (pan_number, name, dob) must be provided.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if PAN already submitted
            if PANKYC.objects.filter(user_code=user).exists():
                return Response(
                    {'error': 'PAN KYC already submitted for this user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create PAN KYC record
            pan_id = generate_unique_id()
            pan_kyc = PANKYC.objects.create(
                id=pan_id,
                user_code=user,
                pan_number=pan_number,
                pan_name=pan_name,
                pan_father_name=request.data.get('father_name', ''),
                pan_dob=pan_dob,
                verification_method='manual'
            )
            
            # Update user KYC tracking
            user.kyc_verification_step = max(user.kyc_verification_step, 2)
            user.save()
            
            # Log audit
            log_user_action(
                action='kyc_submit',
                user_code=user,
                description=f'PAN KYC submitted',
                resource_type='PANKYC',
                resource_id=pan_id,
                ip_address=self._get_client_ip(request)
            )
            
            serializer = PANKYCSerializer(pan_kyc)
            return Response({
                'message': 'PAN KYC submitted successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_pan_status(self, request):
        """
        GET /api/v1/kyc/pan/status
        Get PAN KYC verification status.
        """
        try:
            user = request.user
            pan_kyc = PANKYC.objects.filter(user_code=user).first()
            
            if not pan_kyc:
                return Response(
                    {'status': 'not_submitted', 'message': 'PAN KYC not submitted yet.'},
                    status=status.HTTP_200_OK
                )
            
            serializer = PANKYCSerializer(pan_kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BusinessKYCViewSet(viewsets.ViewSet):
    """
    Business details verification endpoints.
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsNotBlocked]
    
    @action(detail=False, methods=['post'])
    def submit_business(self, request):
        """
        POST /api/v1/kyc/business/submit
        Submit business information for verification.
        """
        try:
            user = request.user
            
            business_name = request.data.get('business_name')
            business_type = request.data.get('business_type')
            
            if not all([business_name, business_type]):
                return Response(
                    {'error': 'business_name and business_type are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if business details already submitted
            if BusinessDetails.objects.filter(user_code=user).exists():
                return Response(
                    {'error': 'Business details already submitted for this user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            business_id = generate_unique_id()
            business = BusinessDetails.objects.create(
                id=business_id,
                user_code=user,
                business_name=business_name,
                business_type=business_type,
                business_registration_number=request.data.get('registration_number', ''),
                business_address_line1=request.data.get('address_line1', ''),
                business_address_line2=request.data.get('address_line2', ''),
                city=request.data.get('city', ''),
                state=request.data.get('state', ''),
                pincode=request.data.get('pincode', ''),
                business_phone=request.data.get('phone', ''),
                business_email=request.data.get('email', '')
            )
            
            # Update user KYC tracking
            user.kyc_verification_step = max(user.kyc_verification_step, 3)
            user.save()
            
            # Log audit
            log_user_action(
                action='kyc_submit',
                user_code=user,
                description=f'Business KYC submitted for {business_name}',
                resource_type='BusinessDetails',
                resource_id=business_id,
                ip_address=self._get_client_ip(request)
            )
            
            serializer = BusinessDetailsSerializer(business)
            return Response({
                'message': 'Business details submitted successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_business_status(self, request):
        """
        GET /api/v1/kyc/business/status
        Get business verification status.
        """
        try:
            user = request.user
            business = BusinessDetails.objects.filter(user_code=user).first()
            
            if not business:
                return Response(
                    {'status': 'not_submitted', 'message': 'Business details not submitted yet.'},
                    status=status.HTTP_200_OK
                )
            
            serializer = BusinessDetailsSerializer(business)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BankKYCViewSet(viewsets.ViewSet):
    """
    Bank details verification endpoints.
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsNotBlocked]
    
    @action(detail=False, methods=['post'])
    def submit_bank(self, request):
        """
        POST /api/v1/kyc/bank/submit
        Submit bank information for verification.
        """
        try:
            user = request.user
            
            account_holder = request.data.get('account_holder_name')
            account_number = request.data.get('account_number')
            ifsc_code = request.data.get('ifsc_code')
            account_type = request.data.get('account_type')
            
            if not all([account_holder, account_number, ifsc_code, account_type]):
                return Response(
                    {'error': 'All required fields must be provided.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if bank details already submitted
            if BankDetails.objects.filter(user_code=user).exists():
                return Response(
                    {'error': 'Bank details already submitted for this user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            bank_id = generate_unique_id()
            bank = BankDetails.objects.create(
                id=bank_id,
                user_code=user,
                account_holder_name=account_holder,
                account_number_encrypted=KYCService.encrypt_field(account_number),
                account_number_last4=account_number[-4:],
                ifsc_code=ifsc_code,
                account_type=account_type,
                bank_name=request.data.get('bank_name', ''),
                branch_name=request.data.get('branch_name', '')
            )
            
            # Update user KYC tracking
            user.kyc_verification_step = max(user.kyc_verification_step, 4)
            user.is_kyc_complete = True
            user.save()
            
            # Log audit
            log_user_action(
                action='kyc_submit',
                user_code=user,
                description=f'Bank KYC submitted - {bank_name}',
                resource_type='BankDetails',
                resource_id=bank_id,
                ip_address=self._get_client_ip(request)
            )
            
            serializer = BankDetailsSerializer(bank)
            return Response({
                'message': 'Bank details submitted successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_bank_status(self, request):
        """
        GET /api/v1/kyc/bank/status
        Get bank verification status.
        """
        try:
            user = request.user
            bank = BankDetails.objects.filter(user_code=user).first()
            
            if not bank:
                return Response(
                    {'status': 'not_submitted', 'message': 'Bank details not submitted yet.'},
                    status=status.HTTP_200_OK
                )
            
            serializer = BankDetailsSerializer(bank)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class KYCStatusViewSet(viewsets.ViewSet):
    """
    Overall KYC status and completion endpoints.
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsNotBlocked]
    
    @action(detail=False, methods=['get'])
    def get_kyc_status(self, request):
        """
        GET /api/v1/kyc/status
        Get overall KYC verification status.
        """
        try:
            user = request.user
            
            # Check each KYC component
            aadhaar_submitted = AadhaarKYC.objects.filter(user_code=user).exists()
            pan_submitted = PANKYC.objects.filter(user_code=user).exists()
            business_submitted = BusinessDetails.objects.filter(user_code=user).exists()
            bank_submitted = BankDetails.objects.filter(user_code=user).exists()
            
            aadhaar_verified = AadhaarKYC.objects.filter(user_code=user, is_verified=True).exists()
            pan_verified = PANKYC.objects.filter(user_code=user, is_verified=True).exists()
            business_verified = BusinessDetails.objects.filter(user_code=user, is_verified=True).exists()
            bank_verified = BankDetails.objects.filter(user_code=user, is_verified=True).exists()
            
            kyc_data = {
                'user_code': user.user_code,
                'kyc_complete': user.is_kyc_complete,
                'kyc_step': user.kyc_verification_step,
                'aadhaar': {
                    'submitted': aadhaar_submitted,
                    'verified': aadhaar_verified
                },
                'pan': {
                    'submitted': pan_submitted,
                    'verified': pan_verified
                },
                'business': {
                    'submitted': business_submitted,
                    'verified': business_verified
                },
                'bank': {
                    'submitted': bank_submitted,
                    'verified': bank_verified
                },
                'all_verified': all([aadhaar_verified, pan_verified, business_verified, bank_verified])
            }
            
            return Response(kyc_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
