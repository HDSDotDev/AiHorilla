"""
Payroll validation functions for country-specific requirements.

This module provides validation functions to ensure employees and system
configurations have all required data before payroll calculations.
"""
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_ph_employee_data(employee):
    """
    Validate that employee has all required Philippines tax/payroll data.
    
    Required fields for PH payroll:
    - TIN (Tax Identification Number)
    - SSS number
    - PhilHealth number
    - Pag-IBIG number
    - Philippines region assignment (for minimum wage/COLA)
    - Tax withholding status
    - Active employment contract with wage
    
    Args:
        employee (Employee): The employee to validate
        
    Raises:
        ValidationError: If any required field is missing or invalid
    """
    errors = []
    
    # Check if employee has work information
    if not hasattr(employee, 'employee_work_info'):
        errors.append("Employee work information not found")
    
    # Validate TIN (Tax Identification Number)
    tin_field = getattr(employee, 'tin', None) or getattr(employee, 'employee_tin', None)
    if not tin_field:
        errors.append("TIN (Tax Identification Number) is required for Philippines payroll")
    
    # Validate SSS number
    sss_field = getattr(employee, 'sss_number', None) or getattr(employee, 'employee_sss', None)
    if not sss_field:
        errors.append("SSS number is required for Philippines payroll")
    
    # Validate PhilHealth number
    philhealth_field = getattr(employee, 'philhealth_number', None) or getattr(employee, 'employee_philhealth', None)
    if not philhealth_field:
        errors.append("PhilHealth number is required for Philippines payroll")
    
    # Validate Pag-IBIG number
    pagibig_field = getattr(employee, 'pagibig_number', None) or getattr(employee, 'employee_pagibig', None)
    if not pagibig_field:
        errors.append("Pag-IBIG number is required for Philippines payroll")
    
    # Validate region assignment (for minimum wage/COLA calculations)
    region_field = getattr(employee, 'ph_region', None) or getattr(employee, 'philippines_region', None)
    if not region_field:
        errors.append("Philippines region is required for minimum wage and COLA calculations")
        logger.error(f"Employee {employee.id} missing Philippines region assignment - BLOCKING payroll")
    
    # Validate tax withholding status
    tax_status_field = getattr(employee, 'ph_tax_status', None) or getattr(employee, 'philippines_tax_status', None)
    if not tax_status_field:
        errors.append("Tax withholding status is required for accurate tax calculation")
        logger.error(f"Employee {employee.id} missing Philippines tax withholding status - BLOCKING payroll")
    
    # Validate active contract with basic salary
    try:
        from payroll.models.models import Contract
        active_contract = Contract.objects.filter(
            employee_id=employee,
            contract_status='active'
        ).first()
        
        if not active_contract:
            errors.append("No active employment contract found")
        elif not hasattr(active_contract, 'wage') or not active_contract.wage or active_contract.wage <= 0:
            errors.append("Basic salary/wage not configured in employment contract")
    except Exception as e:
        logger.error(f"Error checking contract for employee {employee.id}: {e}", exc_info=True)
        errors.append("Unable to verify employment contract")
    
    # Raise validation error if any critical issues found
    if errors:
        error_message = "; ".join(errors)
        logger.warning(f"PH payroll validation failed for employee {employee.id}: {error_message}")
        raise ValidationError(error_message)
    
    logger.debug(f"Employee {employee.id} passed PH payroll data validation")


def validate_ph_system_data():
    """
    Validate that Philippines payroll system has all required master data configured.
    
    Required master data:
    - Active SSS contribution tables
    - Active PhilHealth contribution tables
    - Active Pag-IBIG contribution tables
    - Active Philippines tax brackets
    
    Raises:
        ValidationError: If any required master data is missing
    """
    errors = []
    
    # Check SSS contribution tables
    try:
        from payroll.models.country_models import PhilippinesSSSContribution
        # Check for any SSS records (no is_active field on this model)
        if not PhilippinesSSSContribution.objects.exists():
            errors.append("No SSS contribution tables configured")
    except ImportError:
        logger.warning("PhilippinesSSSContribution model not found - skipping SSS validation")
    except Exception as e:
        logger.error(f"Error checking SSS tables: {e}")
        errors.append("Unable to verify SSS contribution tables")
    
    # Check PhilHealth contribution tables
    try:
        from payroll.models.country_models import PhilippinesPhilHealthContribution
        if not PhilippinesPhilHealthContribution.objects.exists():
            errors.append("No PhilHealth contribution tables configured")
    except ImportError:
        logger.warning("PhilippinesPhilHealthContribution model not found - skipping PhilHealth validation")
    except Exception as e:
        logger.error(f"Error checking PhilHealth tables: {e}")
        errors.append("Unable to verify PhilHealth contribution tables")
    
    # Check Pag-IBIG contribution tables
    try:
        from payroll.models.country_models import PhilippinesPagIbigContribution
        if not PhilippinesPagIbigContribution.objects.exists():
            errors.append("No Pag-IBIG contribution tables configured")
    except ImportError:
        logger.warning("PhilippinesPagIbigContribution model not found - skipping Pag-IBIG validation")
    except Exception as e:
        logger.error(f"Error checking Pag-IBIG tables: {e}")
        errors.append("Unable to verify Pag-IBIG contribution tables")
    
    # Check tax brackets
    try:
        from payroll.models.country_models import PhilippinesTaxBracket
        if not PhilippinesTaxBracket.objects.exists():
            errors.append("No Philippines tax brackets configured")
    except ImportError:
        logger.warning("PhilippinesTaxBracket model not found - skipping tax bracket validation")
    except Exception as e:
        logger.error(f"Error checking tax brackets: {e}")
        errors.append("Unable to verify Philippines tax brackets")
    
    # Raise validation error if any critical issues found
    if errors:
        error_message = "; ".join(errors)
        logger.critical(f"Philippines payroll system validation failed: {error_message}")
        raise ValidationError(error_message)
    
    logger.info("Philippines payroll system master data validation passed")


def validate_date_range(start_date, end_date):
    """
    Validate payroll date range.
    
    Args:
        start_date (date): Period start date
        end_date (date): Period end date
        
    Raises:
        ValidationError: If dates are invalid
    """
    from datetime import date
    
    if not start_date or not end_date:
        raise ValidationError("Start date and end date are required")
    
    if start_date > end_date:
        raise ValidationError(f"Start date ({start_date}) cannot be after end date ({end_date})")
    
    if end_date > date.today():
        raise ValidationError(f"End date ({end_date}) cannot be in the future")
    
    # Check if date range is reasonable (not more than 1 year)
    days_diff = (end_date - start_date).days
    if days_diff > 366:
        logger.warning(f"Payroll date range is unusually long: {days_diff} days")
