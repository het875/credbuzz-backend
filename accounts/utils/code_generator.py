"""
Code generators for user_code, branch_code, feature_code, and other ID generation.
"""
import random
import string
import uuid
from django.utils import timezone
from accounts.models import UserAccount, Branch, AppFeature


def generate_random_code(length=6, include_letters=True, include_numbers=True):
    """
    Generate a random alphanumeric code.
    
    Args:
        length: Length of the code
        include_letters: Include uppercase letters
        include_numbers: Include digits
    
    Returns:
        Random alphanumeric string
    """
    characters = ''
    if include_letters:
        characters += string.ascii_uppercase
    if include_numbers:
        characters += string.digits
    
    return ''.join(random.choice(characters) for _ in range(length))


def generate_unique_user_code(length=6):
    """
    Generate a unique 6-character user code (A-Z + 0-9).
    Format example: AAB1T1, 5X9K2L
    """
    max_attempts = 10
    for _ in range(max_attempts):
        code = generate_random_code(length=length)
        if not UserAccount.objects.filter(user_code=code).exists():
            return code
    
    raise ValueError("Could not generate unique user code after max attempts")


def generate_unique_branch_code(length=5):
    """
    Generate a unique 5-character branch code (A-Z + 0-9).
    Format example: AAB14, XY9ZK
    """
    max_attempts = 10
    for _ in range(max_attempts):
        code = generate_random_code(length=length)
        if not Branch.objects.filter(branch_code=code).exists():
            return code
    
    raise ValueError("Could not generate unique branch code after max attempts")


def generate_unique_feature_code(length=4):
    """
    Generate a unique 4-character feature code (A-Z + 0-9).
    Format example: PAY1, RPT2, USR3
    """
    max_attempts = 10
    for _ in range(max_attempts):
        code = generate_random_code(length=length)
        if not AppFeature.objects.filter(feature_code=code).exists():
            return code
    
    raise ValueError("Could not generate unique feature code after max attempts")


def generate_unique_id(prefix='', length=16):
    """
    Generate a unique ID for models with CharField primary key.
    
    Args:
        prefix: Optional prefix for the ID
        length: Total length of ID (including prefix)
    
    Returns:
        Unique identifier string
    """
    if prefix:
        remaining_length = length - len(prefix)
        unique_part = uuid.uuid4().hex[:remaining_length]
        return f"{prefix}{unique_part}"
    else:
        return uuid.uuid4().hex[:length]


def generate_otp(length=6):
    """
    Generate a 6-digit OTP.
    """
    return ''.join(random.choice(string.digits) for _ in range(length))
