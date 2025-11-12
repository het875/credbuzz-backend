"""
Encryption and decryption utilities for sensitive data.
Uses cryptography library for encryption.
"""
from cryptography.fernet import Fernet
from django.conf import settings
import hashlib
from django.contrib.auth.hashers import make_password, check_password


def get_cipher():
    """
    Get Fernet cipher instance for encryption/decryption.
    Uses the ENCRYPTION_KEY from Django settings.
    """
    encryption_key = settings.ENCRYPTION_KEY
    # Ensure the key is 32 bytes and base64 encoded
    key = hashlib.sha256(encryption_key.encode()).digest()
    # Fernet requires base64 encoded 32-byte key
    from base64 import urlsafe_b64encode
    safe_key = urlsafe_b64encode(key)
    return Fernet(safe_key)


def encrypt_data(data):
    """
    Encrypt sensitive data (like Aadhaar, bank account numbers).
    
    Args:
        data: String to encrypt
    
    Returns:
        Encrypted string
    """
    if not data:
        return None
    
    try:
        cipher = get_cipher()
        encrypted = cipher.encrypt(str(data).encode())
        return encrypted.decode()
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")


def decrypt_data(encrypted_data):
    """
    Decrypt sensitive data.
    
    Args:
        encrypted_data: Encrypted string
    
    Returns:
        Decrypted string
    """
    if not encrypted_data:
        return None
    
    try:
        cipher = get_cipher()
        decrypted = cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")


def hash_otp(otp):
    """
    Hash OTP code for secure storage.
    
    Args:
        otp: 6-digit OTP
    
    Returns:
        Hashed OTP
    """
    return make_password(otp)


def verify_otp(otp, hashed_otp):
    """
    Verify OTP against hashed OTP.
    
    Args:
        otp: 6-digit OTP to verify
        hashed_otp: Hashed OTP from database
    
    Returns:
        True if OTP matches, False otherwise
    """
    try:
        return check_password(otp, hashed_otp)
    except Exception:
        return False


def hash_password(password):
    """
    Hash password for secure storage.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return make_password(password)


def verify_password(password, hashed_password):
    """
    Verify password against hashed password.
    
    Args:
        password: Plain text password to verify
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return check_password(password, hashed_password)
    except Exception:
        return False


def hash_sensitive_field(data):
    """
    One-way hash for sensitive fields that don't need decryption.
    
    Args:
        data: Data to hash
    
    Returns:
        Hashed data
    """
    return hashlib.sha256(str(data).encode()).hexdigest()


def mask_aadhaar(aadhaar_encrypted):
    """
    Decrypt and mask Aadhaar for display (show only last 4 digits).
    
    Args:
        aadhaar_encrypted: Encrypted Aadhaar number
    
    Returns:
        Masked Aadhaar like "XXXX XXXX 1234"
    """
    try:
        decrypted = decrypt_data(aadhaar_encrypted)
        if decrypted and len(decrypted) >= 4:
            last_4 = decrypted[-4:]
            return f"XXXX XXXX {last_4}"
        return "XXXX XXXX XXXX"
    except Exception:
        return "XXXX XXXX XXXX"


def mask_account_number(account_number_encrypted):
    """
    Decrypt and mask account number for display (show only last 4 digits).
    
    Args:
        account_number_encrypted: Encrypted account number
    
    Returns:
        Masked account number like "XXXXXXXX1234"
    """
    try:
        decrypted = decrypt_data(account_number_encrypted)
        if decrypted and len(decrypted) >= 4:
            last_4 = decrypted[-4:]
            x_count = len(decrypted) - 4
            return f"{'X' * x_count}{last_4}"
        return "XXXXXXXXXXXX"
    except Exception:
        return "XXXXXXXXXXXX"
