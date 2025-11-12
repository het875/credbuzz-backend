"""
Validators for PAN, Aadhaar, IFSC, mobile numbers, and other fields.
"""
import re
from django.core.exceptions import ValidationError
import phonenumbers
from phonenumbers import NumberParseException


def validate_pan(pan_number):
    """
    Validate PAN format: ABCDE1234F (5 letters, 4 numbers, 1 letter).
    """
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    if not re.match(pan_pattern, pan_number.upper()):
        raise ValidationError(
            "Invalid PAN format. Expected format: ABCDE1234F "
            "(5 uppercase letters, 4 digits, 1 uppercase letter)"
        )


def validate_aadhaar(aadhaar_number):
    """
    Validate Aadhaar number format (12 digits).
    Uses Verhoeff algorithm for checksum validation.
    """
    aadhaar_str = str(aadhaar_number).strip()
    
    # Check if it's 12 digits
    if not re.match(r'^\d{12}$', aadhaar_str):
        raise ValidationError(
            "Invalid Aadhaar format. Aadhaar must be 12 digits."
        )
    
    # Verhoeff algorithm for checksum validation
    if not verhoeff_check(aadhaar_str):
        raise ValidationError(
            "Invalid Aadhaar checksum. Please verify your Aadhaar number."
        )


def validate_ifsc(ifsc_code):
    """
    Validate IFSC code format: ABCD0123456 (4 letters, 0, 6 alphanumeric).
    """
    ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    if not re.match(ifsc_pattern, ifsc_code.upper()):
        raise ValidationError(
            "Invalid IFSC format. Expected format: ABCD0123456 "
            "(4 uppercase letters, 0, 6 alphanumeric)"
        )


def validate_indian_mobile(mobile_number):
    """
    Validate Indian mobile number format.
    Accepts: +91XXXXXXXXXX or 91XXXXXXXXXX or XXXXXXXXXX
    """
    try:
        # Try to parse as Indian number
        parsed = phonenumbers.parse(mobile_number, "IN")
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError(
                "Invalid Indian mobile number. Please enter a valid 10-digit number."
            )
    except NumberParseException:
        raise ValidationError(
            "Invalid mobile number format. Expected Indian number with country code +91."
        )


def validate_pincode(pincode):
    """
    Validate Indian pincode format (6 digits).
    """
    if not re.match(r'^\d{6}$', str(pincode)):
        raise ValidationError(
            "Invalid pincode. Pincode must be 6 digits."
        )


def validate_email_format(email):
    """
    Validate email format.
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format.")


def validate_password_strength(password):
    """
    Validate password strength.
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit.")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character.")
    
    if errors:
        raise ValidationError(errors)


def verhoeff_check(number_str):
    """
    Verhoeff algorithm for checksum validation (used for Aadhaar).
    
    Args:
        number_str: 12-digit string including check digit
    
    Returns:
        True if checksum is valid, False otherwise
    """
    # Multiplication table for Verhoeff algorithm
    mult_table = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]
    
    # Permutation table for Verhoeff algorithm
    perm_table = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]
    
    # Inverse table
    inv_table = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
    
    try:
        digits = [int(d) for d in number_str]
        c = 0
        
        for i, d in enumerate(reversed(digits)):
            c = mult_table[c][perm_table[(i + 1) % 8][d]]
        
        return c == 0
    except (ValueError, IndexError):
        return False


def validate_account_number_format(account_number):
    """
    Basic account number validation (9-18 digits).
    """
    if not re.match(r'^\d{9,18}$', str(account_number)):
        raise ValidationError(
            "Invalid account number. Account number must be 9-18 digits."
        )


def validate_user_code_format(user_code):
    """
    Validate user code format (6 alphanumeric uppercase).
    """
    if not re.match(r'^[A-Z0-9]{6}$', user_code.upper()):
        raise ValidationError(
            "Invalid user code format. Must be 6 alphanumeric characters (A-Z, 0-9)."
        )


def validate_branch_code_format(branch_code):
    """
    Validate branch code format (5 alphanumeric uppercase).
    """
    if not re.match(r'^[A-Z0-9]{5}$', branch_code.upper()):
        raise ValidationError(
            "Invalid branch code format. Must be 5 alphanumeric characters (A-Z, 0-9)."
        )


def validate_feature_code_format(feature_code):
    """
    Validate feature code format (4 alphanumeric uppercase).
    """
    if not re.match(r'^[A-Z0-9]{4}$', feature_code.upper()):
        raise ValidationError(
            "Invalid feature code format. Must be 4 alphanumeric characters (A-Z, 0-9)."
        )
