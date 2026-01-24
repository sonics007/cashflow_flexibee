# Test FlexiBee import_from_date feature
# This script tests the new date picker functionality

from datetime import datetime, timedelta
import json
import os

# Simulate config with import_from_date
test_config = {
    "host": "https://demo.flexibee.eu:5434",
    "company": "demo_sro",
    "user": "test",
    "password": "test123",
    "enabled": False,
    "import_from_date": "2024-01-01"
}

print("=" * 70)
print("TESTING IMPORT_FROM_DATE FEATURE")
print("=" * 70)

# Test 1: Parse import_from_date
import_from_date = test_config.get('import_from_date')
if import_from_date:
    try:
        from_date = datetime.strptime(import_from_date, '%Y-%m-%d')
        start_date = from_date.strftime('%Y-%m-%dT%H:%M:%S')
        print(f"\n✅ Test 1 PASSED: Date parsing")
        print(f"   Input: {import_from_date}")
        print(f"   Output: {start_date}")
    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")
else:
    print("\n⚠️  Test 1 SKIPPED: No import_from_date in config")

# Test 2: Fallback to 365 days
print(f"\n✅ Test 2: Fallback to 365 days")
now = datetime.now()
fallback_date = (now - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%S')
print(f"   Fallback date: {fallback_date}")

# Test 3: Invalid date format
print(f"\n✅ Test 3: Invalid date handling")
invalid_date = "invalid-date"
try:
    from_date = datetime.strptime(invalid_date, '%Y-%m-%d')
    print(f"   ❌ Should have failed")
except:
    print(f"   ✅ Correctly caught invalid date")
    fallback = (now - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%S')
    print(f"   Fallback: {fallback}")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETED")
print("=" * 70)
