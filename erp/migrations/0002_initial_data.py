"""
Create initial data for ERP system
Branches, App Features, and Master Super Admin
"""
from django.db import migrations
from django.contrib.auth import get_user_model
from django.utils import timezone


def create_initial_data(apps, schema_editor):
    """Create initial branches, features, and master admin."""
    
    # Get models
    Branch = apps.get_model('erp', 'Branch')
    AppFeature = apps.get_model('erp', 'AppFeature')
    UserAccount = apps.get_model('erp', 'UserAccount')
    
    # Create default branch
    main_branch, created = Branch.objects.get_or_create(
        branch_code='MAIN001',
        defaults={
            'id': 'BRANCH001',
            'branch_name': 'Main Branch',
            'address_line1': 'Head Office Building',
            'address_line2': 'Business District',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'country': 'India',
            'pincode': '400001',
            'phone': '9876543210',
            'email': 'main@credbuzz.com',
            'manager_name': 'Branch Manager',
            'is_active': True
        }
    )
    
    # Create additional branches
    branches_data = [
        {
            'id': 'BRANCH002',
            'branch_code': 'DEL001',
            'branch_name': 'Delhi Branch',
            'address_line1': 'Commercial Complex',
            'city': 'New Delhi',
            'state': 'Delhi',
            'pincode': '110001',
            'phone': '9876543211',
            'email': 'delhi@credbuzz.com'
        },
        {
            'id': 'BRANCH003', 
            'branch_code': 'BLR001',
            'branch_name': 'Bangalore Branch',
            'address_line1': 'Tech Park',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'pincode': '560001',
            'phone': '9876543212',
            'email': 'bangalore@credbuzz.com'
        }
    ]
    
    for branch_data in branches_data:
        Branch.objects.get_or_create(
            branch_code=branch_data['branch_code'],
            defaults={
                **branch_data,
                'address_line2': '',
                'country': 'India',
                'manager_name': 'Branch Manager',
                'is_active': True
            }
        )
    
    # Create app features
    features_data = [
        {
            'feature_code': 'USER_MANAGEMENT',
            'feature_name': 'User Management',
            'description': 'Create, update, and manage user accounts'
        },
        {
            'feature_code': 'KYC_MANAGEMENT',
            'feature_name': 'KYC Management',
            'description': 'Handle KYC verification processes'
        },
        {
            'feature_code': 'BUSINESS_MANAGEMENT',
            'feature_name': 'Business Management',
            'description': 'Manage business details and verification'
        },
        {
            'feature_code': 'FINANCIAL_SERVICES',
            'feature_name': 'Financial Services',
            'description': 'Credit card bill payments and financial transactions'
        },
        {
            'feature_code': 'REPORTING',
            'feature_name': 'Reporting & Analytics',
            'description': 'Generate reports and view analytics'
        },
        {
            'feature_code': 'AUDIT_TRAIL',
            'feature_name': 'Audit Trail',
            'description': 'View system audit logs and user activities'
        },
        {
            'feature_code': 'BRANCH_MANAGEMENT',
            'feature_name': 'Branch Management',
            'description': 'Manage branch operations and assignments'
        },
        {
            'feature_code': 'ROLE_MANAGEMENT',
            'feature_name': 'Role Management',
            'description': 'Assign roles and permissions to users'
        }
    ]
    
    for feature_data in features_data:
        AppFeature.objects.get_or_create(
            feature_code=feature_data['feature_code'],
            defaults={
                'id': f"FEAT_{feature_data['feature_code'][:8]}",
                'feature_name': feature_data['feature_name'],
                'description': feature_data['description'],
                'is_active': True
            }
        )
    
    # Create master superadmin (optional - can be created via command)
    # This is commented out as it should be created via management command
    # with proper password handling
    
    print("Initial data created successfully:")
    print(f"- {Branch.objects.count()} branches")
    print(f"- {AppFeature.objects.count()} app features")


def reverse_initial_data(apps, schema_editor):
    """Remove initial data."""
    Branch = apps.get_model('erp', 'Branch')
    AppFeature = apps.get_model('erp', 'AppFeature')
    
    # Don't delete all data as it might affect existing records
    # This is intentionally left minimal
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_data, 
            reverse_initial_data
        ),
    ]