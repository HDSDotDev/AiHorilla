# QUICK VERIFICATION CHECKLIST FOR ACCOUNTANT

## What You Need to Check

### ✅ Tax Calculation Formula

**Our Implementation:**
```
1. Total Basic Pay (semi-monthly) = Monthly Basic ÷ 2
2. Taxable Income = Total Basic - SSS - PhilHealth - Pag-IBIG
3. Apply Semi-Monthly Tax Bracket
```

**Does this match Sprout?** ⬜ YES ⬜ NO

---

### ✅ Semi-Monthly Tax Brackets

| Taxable Income | Tax Formula |
|----------------|-------------|
| ≤ ₱10,417 | ₱0 |
| ₱10,417 - ₱16,666 | (TI − ₱10,417) × 15% |
| ₱16,667 - ₱33,332 | ₱937.50 + (TI − ₱16,667) × 20% |
| ₱33,333 - ₱83,332 | ₱4,270.70 + (TI − ₱33,333) × 25% |
| ₱83,333 - ₱333,332 | ₱16,770.70 + (TI − ₱83,333) × 30% |
| Above ₱333,333 | ₱91,770.70 + (TI − ₱333,333) × 35% |

**Are these brackets correct?** ⬜ YES ⬜ NO

---

### ✅ Sample Calculation

**Employee:** Harvey Delos Santos  
**Monthly Basic:** ₱57,486.00

```
Half-Month Basic:     ₱28,743.00
Less: SSS            (₱1,125.00)
Less: PhilHealth     (₱1,437.15)
Less: Pag-IBIG         (₱100.00)
─────────────────────────────────
Taxable Income:       ₱26,080.85

Tax Bracket: ₱16,667 - ₱33,332 (20%)
Tax = ₱937.50 + (₱26,080.85 - ₱16,667) × 20%
Tax = ₱937.50 + ₱1,882.77
Tax = ₱2,820.27
```

**Does this match your Excel?** ⬜ YES ⬜ NO

**Does this match Sprout?** ⬜ YES ⬜ NO

---

### ⏳ Questions Needing Answers

1. **SSS MPF Contribution**
   - Should this be deducted from taxable income?
   - Currently: NOT deducted
   - Sprout does: ⬜ Deduct ⬜ Don't deduct

2. **Taxable Allowances**
   - Should allowances be included in "Total Basic Pay"?
   - Currently: YES (if marked as taxable)
   - Sprout does: ⬜ Include ⬜ Exclude

3. **13th Month Pay**
   - How is this handled in semi-monthly payroll?
   - Currently: Excluded from tax calculation
   - Sprout does: ⬜ Same ⬜ Different (explain): _____________

4. **Period 1 vs Period 2**
   - Should tax differ between 1st and 2nd half of month?
   - Currently: SAME (contributions deducted in both periods)
   - Sprout does:
     - ⬜ Same tax both periods
     - ⬜ Different (explain): _____________

5. **Other Deductions Before Tax**
   - Are there other items that should reduce taxable income?
   - Currently: Only SSS, PhilHealth, Pag-IBIG
   - Should also deduct: ___________________________

---

### 📋 What I Need From You

To verify the calculation is 100% correct, please provide:

1. **Sample Payslip from Sprout** showing:
   - Basic Salary
   - All deductions (SSS, PhilHealth, Pag-IBIG, etc.)
   - Taxable Income calculation
   - Withholding Tax amount
   - Net Pay

2. **Your Excel File** (already provided ✅)
   - Confirmed: Uses semi-monthly brackets
   - Confirmed: Deducts contributions before tax

3. **Any Special Cases:**
   - Employees with allowances
   - Employees with loans
   - Employees with different pay frequencies
   - Period 1 vs Period 2 examples

---

### 🎯 Expected Outcome

Once you verify, we should see:

✅ Nexus Tax = Sprout Tax (exact match)  
✅ Nexus Net Pay = Sprout Net Pay (exact match)  
✅ All deductions match line by line

---

### 📞 Next Step

Please review this and let us know:
1. ⬜ Tax calculation is CORRECT - matches Sprout exactly
2. ⬜ Tax calculation needs adjustment:
   - What's wrong: _________________________
   - What should change: ___________________

---

**Your Signature:** ___________________  
**Date:** ___________________  
**Status:** ⬜ Approved ⬜ Needs Changes
