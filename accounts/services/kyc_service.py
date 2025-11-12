"""
KYC (Know Your Customer) service for verification operations.
"""
from django.utils import timezone
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
import os


class KYCService:
    """
    Service for KYC verification operations.
    """
    
    # Encryption key (should be from environment in production)
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-encryption-key-change-in-production')
    
    @staticmethod
    def encrypt_field(data):
        """
        Encrypt sensitive field data.
        """
        try:
            cipher = Fernet(KYCService.ENCRYPTION_KEY.encode() if isinstance(KYCService.ENCRYPTION_KEY, str) else KYCService.ENCRYPTION_KEY)
            if isinstance(data, str):
                data = data.encode()
            encrypted = cipher.encrypt(data)
            return encrypted.decode()
        except Exception as e:
            raise ValidationError(f"Encryption error: {str(e)}")
    
    @staticmethod
    def decrypt_field(encrypted_data):
        """
        Decrypt sensitive field data.
        """
        try:
            cipher = Fernet(KYCService.ENCRYPTION_KEY.encode() if isinstance(KYCService.ENCRYPTION_KEY, str) else KYCService.ENCRYPTION_KEY)
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()
            decrypted = cipher.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            raise ValidationError(f"Decryption error: {str(e)}")
    
    @staticmethod
    def validate_aadhaar(aadhaar_number):
        """
        Validate Aadhaar number format.
        """
        if not aadhaar_number:
            raise ValidationError("Aadhaar number is required.")
        
        # Remove spaces and convert to string
        aadhaar = str(aadhaar_number).replace(" ", "")
        
        # Aadhaar should be 12 digits
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            raise ValidationError("Aadhaar number must be 12 digits.")
        
        return aadhaar
    
    @staticmethod
    def validate_pan(pan_number):
        """
        Validate PAN format.
        """
        if not pan_number:
            raise ValidationError("PAN number is required.")
        
        pan = str(pan_number).upper().replace(" ", "")
        
        # PAN should be 10 characters: 5 letters, 4 numbers, 1 letter
        if len(pan) != 10:
            raise ValidationError("PAN number must be 10 characters.")
        
        # Check format: AAAAA9999A
        if not (pan[:5].isalpha() and pan[5:9].isdigit() and pan[9].isalpha()):
            raise ValidationError("PAN format is invalid.")
        
        return pan
    
    @staticmethod
    def validate_ifsc(ifsc_code):
        """
        Validate IFSC code format.
        """
        if not ifsc_code:
            raise ValidationError("IFSC code is required.")
        
        ifsc = str(ifsc_code).upper().replace(" ", "")
        
        # IFSC should be 11 characters: 4 letters, 0 (zero), 6 alphanumeric
        if len(ifsc) != 11:
            raise ValidationError("IFSC code must be 11 characters.")
        
        if not ifsc[:4].isalpha() or ifsc[4] != '0' or not ifsc[5:].isalnum():
            raise ValidationError("IFSC format is invalid.")
        
        return ifsc
    
    @staticmethod
    def validate_account_number(account_number):
        """
        Validate bank account number format.
        """
        if not account_number:
            raise ValidationError("Account number is required.")
        
        account = str(account_number).replace(" ", "")
        
        # Account number should be 9-18 digits
        if not account.isdigit() or len(account) < 9 or len(account) > 18:
            raise ValidationError("Account number must be between 9-18 digits.")
        
        return account
    
    @staticmethod
    def get_kyc_completion_percentage(user):
        """
        Calculate KYC completion percentage for a user.
        """
        from accounts.models import AadhaarKYC, PANKYC, BusinessDetails, BankDetails
        
        completion_score = 0
        total_components = 4
        
        if AadhaarKYC.objects.filter(user_code=user).exists():
            completion_score += 1
        
        if PANKYC.objects.filter(user_code=user).exists():
            completion_score += 1
        
        if BusinessDetails.objects.filter(user_code=user).exists():
            completion_score += 1
        
        if BankDetails.objects.filter(user_code=user).exists():
            completion_score += 1
        
        return (completion_score / total_components) * 100
    
    @staticmethod
    def is_kyc_fully_verified(user):
        """
        Check if user's KYC is fully verified.
        """
        from accounts.models import AadhaarKYC, PANKYC, BusinessDetails, BankDetails
        
        aadhaar_verified = AadhaarKYC.objects.filter(
            user_code=user,
            is_verified=True
        ).exists()
        
        pan_verified = PANKYC.objects.filter(
            user_code=user,
            is_verified=True
        ).exists()
        
        business_verified = BusinessDetails.objects.filter(
            user_code=user,
            is_verified=True
        ).exists()
        
        bank_verified = BankDetails.objects.filter(
            user_code=user,
            is_verified=True
        ).exists()
        
        return all([aadhaar_verified, pan_verified, business_verified, bank_verified])
    
    @staticmethod
    def mark_kyc_complete(user):
        """
        Mark user's KYC as complete if all components are verified.
        """
        if KYCService.is_kyc_fully_verified(user):
            user.is_kyc_complete = True
            user.kyc_verification_step = 4
            user.save()
            return True
        return False
