# Test clean_company_name function
# Tests removal of 'code:' prefix from FlexiBee company names

def clean_company_name(company_str):
    """
    Remove 'code:' prefix from FlexiBee company name.
    FlexiBee returns: 'code:Company Name' -> we want: 'Company Name'
    """
    if not company_str:
        return ''
    company_str = str(company_str).strip()
    # Remove 'code:' prefix if present
    if company_str.startswith('code:'):
        return company_str[5:].strip()
    return company_str

print("=" * 70)
print("TESTING CLEAN_COMPANY_NAME FUNCTION")
print("=" * 70)

# Test cases
test_cases = [
    ("code:ABC Company s.r.o.", "ABC Company s.r.o."),
    ("code:XYZ Ltd", "XYZ Ltd"),
    ("Normal Company Name", "Normal Company Name"),
    ("", ""),
    ("code:", ""),
    ("  code:  Spaced Company  ", "Spaced Company"),
    (None, ""),
]

all_passed = True
for i, (input_val, expected) in enumerate(test_cases, 1):
    result = clean_company_name(input_val)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    if result != expected:
        all_passed = False
    print(f"\nTest {i}: {status}")
    print(f"  Input:    '{input_val}'")
    print(f"  Expected: '{expected}'")
    print(f"  Got:      '{result}'")

print("\n" + "=" * 70)
if all_passed:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 70)
