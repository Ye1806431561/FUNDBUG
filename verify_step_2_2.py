
# Script to manually verify Step 2.2
from src.data.holdings import save_fund_holdings
from src.db.models import init_db
from src.db.crud import get_latest_holdings
import os

# Initialize real DB
init_db()

fund_code = "000001"
print(f"--- Verifying Step 2.2 for Fund {fund_code} ---")

# Ensure fund exists in table (constraint)
from src.data.fund_list import save_fund_info
save_fund_info(fund_code)

print(f"Fetching and saving holdings...")
success = save_fund_holdings(fund_code)

if success:
    print("✅ save_fund_holdings returned True")
    
    # Verify in DB
    holdings = get_latest_holdings(fund_code)
    if holdings:
        print(f"✅ Found {len(holdings)} holdings in DB")
        print("Sample:", holdings[0])
    else:
        print("❌ No holdings found in DB after save!")
else:
    print("❌ save_fund_holdings returned False")
