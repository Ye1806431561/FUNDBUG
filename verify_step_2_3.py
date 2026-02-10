
import sys
import os
import pandas as pd
from src.data.realtime import get_realtime_quotes

def verify_step_2_3():
    print("--- Verifying Step 2.3: Realtime Quotes ---")
    
    # Test valid codes
    # 000001: Ping An Bank
    # 600519: Kweichow Moutai
    # 300750: CATL
    codes = ["000001", "600519", "300750"]
    print(f"Fetching quotes for: {codes}")
    
    try:
        df = get_realtime_quotes(codes)
        
        if df.empty:
            print("❌ Error: Returned DataFrame is empty!")
            return
            
        print(f"✅ Successfully fetched {len(df)} quotes.")
        print(df)
        
        # Check specific columns
        required_cols = ["stock_code", "name", "current_price", "change_percent"]
        for col in required_cols:
            if col not in df.columns:
                print(f"❌ Error: Missing column '{col}'")
                return
        print("✅ Column structure correct.")
        
        # Check values
        for _, row in df.iterrows():
            price = row['current_price']
            change = row['change_percent']
            name = row['name']
            code = row['stock_code']
            
            if not isinstance(price, (int, float)) or price <= 0:
                print(f"❌ Error: Invalid price for {code} ({name}): {price}")
            else:
                print(f"✅ Price for {code} ({name}) is valid: {price}")
                
            if not isinstance(change, (int, float)):
                 print(f"❌ Error: Invalid change_percent for {code}: {change}")
            elif abs(change) > 20: # 20% limit (A-shares usually 10% or 20%)
                 print(f"⚠️ Warning: Large change_percent for {code}: {change}% (Could be correct if volatile)")
            else:
                 print(f"✅ Change percent for {code} is reasonable: {change}%")

        # Test invalid code
        invalid_code = "999999"
        print(f"\nTesting invalid code: {invalid_code}")
        df_invalid = get_realtime_quotes([invalid_code])
        if df_invalid.empty:
            print(f"✅ Correctly returned empty DataFrame for invalid code.")
        else:
            print(f"❌ Error: Should return empty for invalid code, got: {df_invalid}")

    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_step_2_3()
