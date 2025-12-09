"""
Management command to create initial bill categories and billers.
"""

from django.core.management.base import BaseCommand
from bill_pay.models import BillCategory, Biller


class Command(BaseCommand):
    help = 'Create initial bill categories and sample billers'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Electricity', 'code': 'ELECTRICITY', 'icon': 'Zap', 'display_order': 1},
            {'name': 'Gas', 'code': 'GAS', 'icon': 'Flame', 'display_order': 2},
            {'name': 'Water', 'code': 'WATER', 'icon': 'Droplet', 'display_order': 3},
            {'name': 'Mobile Prepaid', 'code': 'MOBILE_PREPAID', 'icon': 'Smartphone', 'display_order': 4},
            {'name': 'Mobile Postpaid', 'code': 'MOBILE_POSTPAID', 'icon': 'Phone', 'display_order': 5},
            {'name': 'DTH', 'code': 'DTH', 'icon': 'Tv', 'display_order': 6},
            {'name': 'Broadband', 'code': 'BROADBAND', 'icon': 'Wifi', 'display_order': 7},
            {'name': 'Landline', 'code': 'LANDLINE', 'icon': 'Phone', 'display_order': 8},
            {'name': 'Insurance', 'code': 'INSURANCE', 'icon': 'Shield', 'display_order': 9},
            {'name': 'Credit Card', 'code': 'CREDIT_CARD', 'icon': 'CreditCard', 'display_order': 10},
            {'name': 'Loan EMI', 'code': 'LOAN_EMI', 'icon': 'Landmark', 'display_order': 11},
            {'name': 'Municipal Tax', 'code': 'MUNICIPAL_TAX', 'icon': 'Building2', 'display_order': 12},
        ]
        
        created_categories = 0
        for cat_data in categories_data:
            cat, created = BillCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )
            if created:
                created_categories += 1
                self.stdout.write(f"Created category: {cat.name}")
        
        # Create sample billers
        billers_data = [
            # Electricity
            {'category_code': 'ELECTRICITY', 'name': 'Adani Electricity Mumbai', 'code': 'ADANI_ELEC_MUM', 'is_featured': True},
            {'category_code': 'ELECTRICITY', 'name': 'BEST Undertaking', 'code': 'BEST_MUM', 'is_featured': True},
            {'category_code': 'ELECTRICITY', 'name': 'Tata Power Mumbai', 'code': 'TATA_POWER_MUM', 'is_featured': True},
            {'category_code': 'ELECTRICITY', 'name': 'MSEDCL Maharashtra', 'code': 'MSEDCL', 'is_featured': False},
            {'category_code': 'ELECTRICITY', 'name': 'BSES Rajdhani Delhi', 'code': 'BSES_RAJ', 'is_featured': False},
            {'category_code': 'ELECTRICITY', 'name': 'BSES Yamuna Delhi', 'code': 'BSES_YAM', 'is_featured': False},
            
            # Gas
            {'category_code': 'GAS', 'name': 'Mahanagar Gas Limited', 'code': 'MGL', 'is_featured': True},
            {'category_code': 'GAS', 'name': 'Indraprastha Gas Limited', 'code': 'IGL', 'is_featured': True},
            {'category_code': 'GAS', 'name': 'Adani Total Gas', 'code': 'ADANI_GAS', 'is_featured': False},
            
            # Water
            {'category_code': 'WATER', 'name': 'MCGM Water Department', 'code': 'MCGM_WATER', 'is_featured': True},
            {'category_code': 'WATER', 'name': 'Delhi Jal Board', 'code': 'DJB', 'is_featured': False},
            
            # Mobile Postpaid
            {'category_code': 'MOBILE_POSTPAID', 'name': 'Jio Postpaid', 'code': 'JIO_POST', 'is_featured': True},
            {'category_code': 'MOBILE_POSTPAID', 'name': 'Airtel Postpaid', 'code': 'AIRTEL_POST', 'is_featured': True},
            {'category_code': 'MOBILE_POSTPAID', 'name': 'Vi Postpaid', 'code': 'VI_POST', 'is_featured': True},
            {'category_code': 'MOBILE_POSTPAID', 'name': 'BSNL Postpaid', 'code': 'BSNL_POST', 'is_featured': False},
            
            # DTH
            {'category_code': 'DTH', 'name': 'Tata Play', 'code': 'TATA_PLAY', 'is_featured': True},
            {'category_code': 'DTH', 'name': 'Airtel Digital TV', 'code': 'AIRTEL_DTH', 'is_featured': True},
            {'category_code': 'DTH', 'name': 'Dish TV', 'code': 'DISH_TV', 'is_featured': False},
            {'category_code': 'DTH', 'name': 'Sun Direct', 'code': 'SUN_DIRECT', 'is_featured': False},
            
            # Broadband
            {'category_code': 'BROADBAND', 'name': 'Jio Fiber', 'code': 'JIO_FIBER', 'is_featured': True},
            {'category_code': 'BROADBAND', 'name': 'Airtel Xstream Fiber', 'code': 'AIRTEL_FIBER', 'is_featured': True},
            {'category_code': 'BROADBAND', 'name': 'ACT Fibernet', 'code': 'ACT_FIBER', 'is_featured': False},
            {'category_code': 'BROADBAND', 'name': 'BSNL Broadband', 'code': 'BSNL_BB', 'is_featured': False},
            
            # Insurance
            {'category_code': 'INSURANCE', 'name': 'LIC of India', 'code': 'LIC', 'is_featured': True},
            {'category_code': 'INSURANCE', 'name': 'ICICI Prudential Life', 'code': 'ICICI_PRUD', 'is_featured': False},
            {'category_code': 'INSURANCE', 'name': 'HDFC Life Insurance', 'code': 'HDFC_LIFE', 'is_featured': False},
            {'category_code': 'INSURANCE', 'name': 'SBI Life Insurance', 'code': 'SBI_LIFE', 'is_featured': False},
            
            # Credit Card
            {'category_code': 'CREDIT_CARD', 'name': 'HDFC Bank Credit Card', 'code': 'HDFC_CC', 'is_featured': True},
            {'category_code': 'CREDIT_CARD', 'name': 'ICICI Bank Credit Card', 'code': 'ICICI_CC', 'is_featured': True},
            {'category_code': 'CREDIT_CARD', 'name': 'SBI Card', 'code': 'SBI_CC', 'is_featured': True},
            {'category_code': 'CREDIT_CARD', 'name': 'Axis Bank Credit Card', 'code': 'AXIS_CC', 'is_featured': False},
            {'category_code': 'CREDIT_CARD', 'name': 'Kotak Credit Card', 'code': 'KOTAK_CC', 'is_featured': False},
        ]
        
        created_billers = 0
        for biller_data in billers_data:
            category_code = biller_data.pop('category_code')
            try:
                category = BillCategory.objects.get(code=category_code)
                biller, created = Biller.objects.get_or_create(
                    code=biller_data['code'],
                    defaults={**biller_data, 'category': category}
                )
                if created:
                    created_billers += 1
                    self.stdout.write(f"Created biller: {biller.name}")
            except BillCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Category not found: {category_code}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nCreated {created_categories} categories and {created_billers} billers"))
