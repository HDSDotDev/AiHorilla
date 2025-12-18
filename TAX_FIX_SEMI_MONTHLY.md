# PHILIPPINES TAX CALCULATION - CORRECTED TO MATCH SPROUT

## Issue Identified by Accountant

The accountant clarified that Sprout uses **SEMI-MONTHLY tax tables directly** for each payroll period, NOT an annualized approach divided by 12/24.

## Previous (INCORRECT) Method

### Old Approach:
1. Annualize monthly income (× 12)
2. Apply personal exemption (₱50,000) + dependent exemptions (₱25,000 each)
3. Use ANNUAL tax brackets
4. Divide annual tax by 12 to get monthly tax
5. Divide by 2 for semi-monthly

### Old Annual Tax Brackets:
| Annual Income | Base Tax | Rate |
|---------------|----------|------|
| ₱0 - ₱250,000 | ₱0 | 0% |
| ₱250,001 - ₱400,000 | ₱0 | 15% |
| ₱400,001 - ₱800,000 | ₱22,500 | 20% |
| ₱800,001 - ₱2,000,000 | ₱102,500 | 25% |
| ₱2,000,001 - ₱8,000,000 | ₱402,500 | 30% |
| Above ₱8,000,000 | ₱2,202,500 | 35% |

## New (CORRECT) Method - Accountant Approved

### New Approach (Sprout-Compatible):
1. Calculate Total Basic Pay for the semi-monthly period
2. **Deduct SSS, PhilHealth, Pag-IBIG contributions = Taxable Income**
3. **Apply SEMI-MONTHLY tax brackets directly** (NO annualization)
4. **NO exemptions** (personal or dependent)

### New Semi-Monthly Tax Brackets:
| Taxable Income (Semi-Monthly) | Tax Formula |
|-------------------------------|-------------|
| ≤ ₱10,417 | ₱0 |
| ₱10,417 - ₱16,666 | (TI − ₱10,417) × 15% |
| ₱16,667 - ₱33,332 | ₱937.50 + (TI − ₱16,667) × 20% |
| ₱33,333 - ₱83,332 | ₱4,270.70 + (TI − ₱33,333) × 25% |
| ₱83,333 - ₱333,332 | ₱16,770.70 + (TI − ₱83,333) × 30% |
| Above ₱333,333 | ₱91,770.70 + (TI − ₱333,333) × 35% |

## Excel Formula (from Accountant)

```excel
=IFS(
 AE5<=10417, 0,
 AE5<=16666, (AE5-10417)*15%,
 AE5<=33332, (AE5-16667)*20% + 937.5,
 AE5<=83332, (AE5-33333)*25% + 4270.7,
 AE5<=333332, (AE5-83333)*30% + 16770.7,
 AE5>333333, (AE5-333333)*35% + 91770.7
)
```

Where `AE5 = Taxable Income` (Total Basic − SSS − PhilHealth − Pag-IBIG − MPF)

## Calculation Flow

### Step-by-Step:
```
1. Monthly Gross → ₱57,486.00
   ↓
2. Half-Month Basic → ₱28,743.00
   ↓
3. Deductions BEFORE Tax:
   - SSS → ₱1,125.00
   - PhilHealth → ₱1,437.15
   - Pag-IBIG → ₱100.00
   ↓
4. Taxable Income = ₱28,743.00 - ₱2,662.15 = ₱26,080.85
   ↓
5. Apply Semi-Monthly Bracket (₱16,667 - ₱33,332):
   Tax = ₱937.50 + (₱26,080.85 - ₱16,667) × 20%
   Tax = ₱937.50 + (₱9,413.85 × 0.20)
   Tax = ₱937.50 + ₱1,882.77
   Tax = ₱2,820.27
```

## Code Changes Made

### 1. Updated Tax Brackets
**File:** `populate_ph_deductions.py`

Changed from annual brackets to semi-monthly brackets:
```python
tax_brackets = [
    (0, 10417, 0, 0),
    (10417, 16666, 0, 15),
    (16667, 33332, 937.50, 20),
    (33333, 83332, 4270.70, 25),
    (83333, 333332, 16770.70, 30),
    (333333, 999999999, 91770.70, 35),
]
```

### 2. Created New Tax Calculation Function
**File:** `payroll/methods/philippines_payroll.py`

Added `calculate_semimonthly_withholding_tax()`:
- Takes total basic pay and contributions as parameters
- Deducts contributions from basic pay to get taxable income
- Applies semi-monthly brackets using IFS logic
- Returns tax amount, taxable income, bracket used

### 3. Updated Main Payroll Function
**File:** `payroll/methods/philippines_payroll.py`

Modified `philippines_payroll_calculation()`:
- Removed annualization logic
- Removed personal/dependent exemptions
- Calls new semi-monthly tax function
- Passes actual contributions being deducted in the period

## Key Differences

| Aspect | Old Method | New Method |
|--------|-----------|------------|
| **Tax Basis** | Annual income ÷ 12 | Semi-monthly direct |
| **Exemptions** | ₱50,000 personal + ₱25,000/dependent | None |
| **Deductions** | Complex annualized calculation | Simple: Basic − Contributions |
| **Brackets** | Annual (6 brackets) | Semi-monthly (6 brackets) |
| **13th Month** | Included in calculation | Excluded (separate) |

## Testing

Run the test script to validate:
```bash
python test_semi_monthly_tax.py
```

Expected output for ₱57,486 monthly salary:
- Half-Month Basic: ₱28,743.00
- Taxable Income: ₱26,080.85
- Withholding Tax: ₱2,820.27
- Bracket: ₱16,667 - ₱33,332 (20%)

## Next Steps

1. ✅ Update tax brackets in database
2. ✅ Test with sample payroll
3. ⏳ Compare with actual Sprout payslips
4. ⏳ Verify Period 1 vs Period 2 behavior
5. ⏳ Deploy to production

## References

- BIR Revenue Regulations implementing TRAIN Law
- Philippines Tax Tables (Semi-Monthly Withholding)
- Accountant's Excel calculation model
- Sprout Payroll system documentation
