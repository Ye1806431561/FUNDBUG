from src.data.fund_list import get_fund_info, validate_fund_code

def verify():
    print("--- 验证 1: 已知基金代码 (000001) ---")
    info = get_fund_info("000001")
    if info:
        print(f"✅ 获取成功: {info}")
        if info['fund_name'] == "华夏成长混合":
             print("✅ 基金名称正确")
        else:
             print(f"⚠️ 基金名称可能已变更或不同: {info['fund_name']}")
    else:
        print("❌ 获取失败")

    print("\n--- 验证 2: 无效基金代码 (999999) ---")
    info_invalid = get_fund_info("999999")
    if info_invalid is None:
        print("✅ 返回 None (符合预期)")
    else:
        print(f"❌ 返回了结果: {info_invalid}")

    print("\n--- 验证 3: 代码校验函数 ---")
    is_valid_1 = validate_fund_code("000001")
    print(f"validate_fund_code('000001') -> {is_valid_1} [{'✅' if is_valid_1 else '❌'}]")
    
    is_valid_2 = validate_fund_code("abc")
    print(f"validate_fund_code('abc') -> {is_valid_2} [{'✅' if not is_valid_2 else '❌'}]")

if __name__ == "__main__":
    verify()
