#!/usr/bin/env python
"""Complete analysis of Sprout's two-period payroll for Joseph Sy"""

print("="*70)
print("SPROUT PAYROLL ANALYSIS - JOSEPH SY (Harvey Delos Santos)")
print("="*70)

# PERIOD 1 DATA
p1_basic = 28943
p1_parking = 400  # Not shown on payslip but in gross
p1_gross_shown = 29343
p1_tax = 3392.70
p1_net = 25950.30

# PERIOD 2 DATA  
p2_basic = 28943
p2_laundry = 500  # Non-taxable
p2_meal = 3000  # TAXABLE
p2_rice = 2000  # Non-taxable
p2_gross_shown = 34443
p2_sss = 1000
p2_sss_mpf = 750
p2_phil = 1447.15
p2_pag = 200
p2_tax = 2713.27
p2_net = 28332.58

# YTD FIGURES
p1_ytd_taxable_gross = 519342.65
p1_ytd_tax = 58346.43
p1_ytd_sss = 15750

p2_ytd_taxable_gross = 544888.50
p2_ytd_tax = 61059.70
p2_ytd_sss = 17500

print("\nPERIOD 1 (Sep 29 - Oct 13, 2025) - 15 days")
print("-"*70)
print(f"Basic Pay:              ₱{p1_basic:>10,.2f}")
print(f"Parking (hidden):       ₱{p1_parking:>10,.2f}")
print(f"Gross on payslip:       ₱{p1_gross_shown:>10,.2f}")
print(f"")
print(f"SSS:                    ₱{0:>10,.2f}  (DEFERRED)")
print(f"PhilHealth:             ₱{0:>10,.2f}  (DEFERRED)")
print(f"Pag-IBIG:               ₱{0:>10,.2f}  (DEFERRED)")
print(f"Withholding Tax:        ₱{p1_tax:>10,.2f}")
print(f"Net Pay:                ₱{p1_net:>10,.2f}")

print("\nPERIOD 2 (Oct 14 - Oct 28, 2025) - 15 days")
print("-"*70)
print(f"Basic Pay:              ₱{p2_basic:>10,.2f}")
print(f"Laundry (non-taxable):  ₱{p2_laundry:>10,.2f}")
print(f"Meal (TAXABLE):         ₱{p2_meal:>10,.2f}")
print(f"Rice (non-taxable):     ₱{p2_rice:>10,.2f}")
print(f"Gross on payslip:       ₱{p2_gross_shown:>10,.2f}")
print(f"")
print(f"SSS Employee:           ₱{p2_sss:>10,.2f}")
print(f"SSS MPF:                ₱{p2_sss_mpf:>10,.2f}")
print(f"SSS Total:              ₱{p2_sss + p2_sss_mpf:>10,.2f}  (Catching up P1)")
print(f"PhilHealth:             ₱{p2_phil:>10,.2f}  (Normal monthly)")
print(f"Pag-IBIG:               ₱{p2_pag:>10,.2f}  (DOUBLE)")
print(f"Withholding Tax:        ₱{p2_tax:>10,.2f}")
print(f"Net Pay:                ₱{p2_net:>10,.2f}")

print("\n" + "="*70)
print("MONTHLY TOTALS")
print("="*70)

total_basic = p1_basic + p2_basic
total_allowances_taxable = p2_meal  # Only meal is taxable
total_allowances_nontaxable = p2_laundry + p2_rice
total_gross = p1_basic + p2_basic + p2_meal + p2_laundry + p2_rice
total_sss = p2_sss + p2_sss_mpf
total_phil = p2_phil
total_pag = p2_pag
total_tax = p1_tax + p2_tax
total_net = p1_net + p2_net

print(f"Basic Pay (2 periods):          ₱{total_basic:>10,.2f}")
print(f"Taxable Allowances:             ₱{total_allowances_taxable:>10,.2f}")
print(f"Non-taxable Allowances:         ₱{total_allowances_nontaxable:>10,.2f}")
print(f"Total Gross:                    ₱{total_gross:>10,.2f}")
print(f"")
print(f"SSS (Total for month):          ₱{total_sss:>10,.2f}")
print(f"PhilHealth (for month):         ₱{total_phil:>10,.2f}")
print(f"Pag-IBIG (Total for month):     ₱{total_pag:>10,.2f}")
print(f"Withholding Tax (for month):    ₱{total_tax:>10,.2f}")
print(f"")
print(f"NET PAY (for month):            ₱{total_net:>10,.2f}")

print("\n" + "="*70)
print("KEY INSIGHTS")
print("="*70)

# YTD ANALYSIS
ytd_increase_taxable = p2_ytd_taxable_gross - p1_ytd_taxable_gross
ytd_increase_tax = p2_ytd_tax - p1_ytd_tax
ytd_increase_sss = p2_ytd_sss - p1_ytd_sss

print(f"\nYTD Changes from Period 1 to Period 2:")
print(f"  Taxable Gross increase:  ₱{ytd_increase_taxable:,.2f}")
print(f"  Tax increase:            ₱{ytd_increase_tax:,.2f}")
print(f"  SSS increase:            ₱{ytd_increase_sss:,.2f}")

# Check if YTD matches our period amounts
print(f"\nVerification (should match Period 2 amounts):")
print(f"  YTD taxable increase ₱{ytd_increase_taxable:,.2f} vs P2 basic+meal ₱{p2_basic + p2_meal:,.2f}")
match_gross = abs(ytd_increase_taxable - (p2_basic + p2_meal)) < 1
print(f"    Match: {'✓ YES' if match_gross else '✗ NO'}")

print(f"  YTD tax increase ₱{ytd_increase_tax:,.2f} vs P2 tax ₱{p2_tax:,.2f}")
match_tax = abs(ytd_increase_tax - p2_tax) < 1
print(f"    Match: {'✓ YES' if match_tax else '✗ NO'}")

print(f"  YTD SSS increase ₱{ytd_increase_sss:,.2f} vs P2 SSS ₱{p2_sss + p2_sss_mpf:,.2f}")
match_sss = abs(ytd_increase_sss - (p2_sss + p2_sss_mpf)) < 1
print(f"    Match: {'✓ YES' if match_sss else '✗ NO'}")

# TAX CALCULATION REVERSE ENGINEERING
print("\n" + "="*70)
print("TAX CALCULATION ANALYSIS")
print("="*70)

monthly_basic = 57886
monthly_meal = 3000
monthly_comp = monthly_basic + monthly_meal

print(f"\nMonthly Compensation:")
print(f"  Basic:                ₱{monthly_basic:,.2f}")
print(f"  Meal Allowance:       ₱{monthly_meal:,.2f}")
print(f"  Total:                ₱{monthly_comp:,.2f}")

# Standard BIR calculation
annual_comp = monthly_comp * 12
monthly_contrib = 1125 + 1447.15 + 100  # Normal amounts
annual_contrib = monthly_contrib * 12
taxable_annual = annual_comp - annual_contrib

print(f"\nStandard BIR Calculation:")
print(f"  Annual compensation:  ₱{annual_comp:,.2f}")
print(f"  Annual contributions: ₱{annual_contrib:,.2f}")
print(f"  Taxable annual:       ₱{taxable_annual:,.2f}")

# 20% bracket
base_tax = 50000
excess = taxable_annual - 400000
annual_tax_standard = base_tax + (excess * 0.20)
monthly_tax_standard = annual_tax_standard / 12

print(f"  Annual tax (20%):     ₱{annual_tax_standard:,.2f}")
print(f"  Monthly tax:          ₱{monthly_tax_standard:,.2f}")

# What Sprout shows
total_tax_sprout = p1_tax + p2_tax
print(f"\nSprout Total Tax:       ₱{total_tax_sprout:,.2f}")
print(f"Standard BIR Tax:       ₱{monthly_tax_standard:,.2f}")
print(f"Difference:             ₱{monthly_tax_standard - total_tax_sprout:,.2f} ({((monthly_tax_standard - total_tax_sprout)/monthly_tax_standard * 100):.1f}% lower in Sprout)")

# Reverse engineer what taxable income Sprout used
sprout_annual_tax = total_tax_sprout * 12
sprout_excess_tax = sprout_annual_tax - base_tax
sprout_excess_income = sprout_excess_tax / 0.20
sprout_taxable_annual = 400000 + sprout_excess_income
sprout_implied_contrib = annual_comp - sprout_taxable_annual
sprout_implied_monthly_contrib = sprout_implied_contrib / 12

print(f"\nReverse Engineering Sprout's Calculation:")
print(f"  Sprout annual tax:            ₱{sprout_annual_tax:,.2f}")
print(f"  Implied taxable annual:       ₱{sprout_taxable_annual:,.2f}")
print(f"  Implied annual deductions:    ₱{sprout_implied_contrib:,.2f}")
print(f"  Implied monthly deductions:   ₱{sprout_implied_monthly_contrib:,.2f}")
print(f"")
print(f"  Actual monthly contributions: ₱{monthly_contrib:,.2f}")
print(f"  Extra 'phantom' deduction:    ₱{sprout_implied_monthly_contrib - monthly_contrib:,.2f}")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print(f"""
Sprout uses a tax calculation method that results in LOWER withholding:
  • Standard BIR method: ₱{monthly_tax_standard:,.2f}/month
  • Sprout method:        ₱{total_tax_sprout:,.2f}/month
  • Savings:              ₱{monthly_tax_standard - total_tax_sprout:,.2f}/month ({((monthly_tax_standard - total_tax_sprout)/monthly_tax_standard * 100):.1f}% less)

This appears to be achieved through ₱{sprout_implied_monthly_contrib - monthly_contrib:,.2f}/month in
additional deductions from taxable income beyond standard SSS/PhilHealth/Pag-IBIG.

Possible explanations:
  • 13th month pro-rata accrual (₱{monthly_basic/12:,.2f}/month)
  • De minimis benefits treatment
  • Custom BIR-approved tax tables
  • Year-to-date cumulative method

For Horilla implementation, we will use STANDARD BIR method which is:
  ✓ More conservative (protects from under-withholding penalties)
  ✓ Clearly documented in BIR TRAIN Law
  ✓ Any excess refunded at year-end via Form 2316
""")
