"""
Audit service for logging all system operations.
"""
from django.utils import timezone
from accounts.models import AuditTrail
from accounts.utils.code_generator import generate_unique_id


def log_audit_trail(
    action,
    resource_type,
    resource_id=None,
    resource_identifier=None,
    description=None,
    user_code=None,
    old_values=None,
    new_values=None,
    changed_fields=None,
    ip_address=None,
    user_agent=None,
    request_method=None,
    request_path=None
):
    """
    Create an audit trail record.
    
    Args:
        action: Action performed (create, update, delete, login, etc.)
        resource_type: Type of resource (UserAccount, Branch, etc.)
        resource_id: ID of the resource
        resource_identifier: Human-readable identifier (email, user_code, etc.)
        description: Human-readable description of the action
        user_code: User who performed the action
        old_values: Previous state of the resource
        new_values: New state of the resource
        changed_fields: List of changed fields
        ip_address: IP address of the request
        user_agent: User agent of the request
        request_method: HTTP method (GET, POST, PUT, DELETE)
        request_path: API endpoint path
    
    Returns:
        AuditTrail object
    """
    audit_id = generate_unique_id(prefix='AUDIT_')
    
    audit = AuditTrail.objects.create(
        id=audit_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_identifier=resource_identifier,
        description=description,
        user_code=user_code,
        old_values=old_values or {},
        new_values=new_values or {},
        changed_fields=changed_fields or [],
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
    )
    
    return audit


def log_user_action(
    action,
    user_code,
    description,
    old_values=None,
    new_values=None,
    changed_fields=None,
    ip_address=None,
    user_agent=None,
    request_method=None,
    request_path=None
):
    """
    Log an action on a user account.
    """
    return log_audit_trail(
        action=action,
        resource_type='UserAccount',
        resource_id=user_code.id if hasattr(user_code, 'id') else None,
        resource_identifier=user_code.user_code if hasattr(user_code, 'user_code') else str(user_code),
        description=description,
        user_code=user_code if not hasattr(user_code, 'id') else user_code,
        old_values=old_values,
        new_values=new_values,
        changed_fields=changed_fields,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
    )


def log_kyc_action(
    action,
    user_code,
    kyc_type,
    description,
    is_verified=None,
    ip_address=None,
    user_agent=None
):
    """
    Log a KYC-related action.
    """
    resource_type = f"{kyc_type}KYC"
    return log_audit_trail(
        action=action,
        resource_type=resource_type,
        resource_identifier=user_code.user_code if hasattr(user_code, 'user_code') else str(user_code),
        description=description,
        user_code=user_code if not hasattr(user_code, 'id') else user_code,
        new_values={'is_verified': is_verified},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_login_action(
    user_code,
    status,
    ip_address,
    user_agent,
    login_identifier,
    description='User login attempt'
):
    """
    Log a login attempt.
    """
    return log_audit_trail(
        action='login' if status == 'success' else 'login_failed',
        resource_type='LoginActivity',
        resource_identifier=login_identifier,
        description=description,
        user_code=user_code,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_access_control_action(
    action,
    user_code,
    resource_type,
    resource_id,
    description,
    admin_user=None,
    ip_address=None,
    user_agent=None
):
    """
    Log access control changes.
    """
    return log_audit_trail(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_identifier=user_code.user_code if hasattr(user_code, 'user_code') else str(user_code),
        description=description,
        user_code=admin_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
