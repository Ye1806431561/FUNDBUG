"""
验证脚本 - 步骤 4.2: API 路由集成验证
此脚本使用 TestClient 模拟真实请求，验证 API -> 数据库 -> 计算引擎 -> 数据采集的完整链路。
"""
import os
import sys
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.api.routes import router
from src.db.models import init_db
import config

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def run_verification():
    print("=== 步骤 4.2 API 路由验证开始 ===")
    
    # 1. 确保数据库已初始化
    init_db()
    print(f"✅ 数据库已就绪: {config.DATABASE_PATH}")

    # 清理旧数据以确保触发“新基金”逻辑
    import sqlite3
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_watchlist WHERE fund_code = '000001'")
    cursor.execute("DELETE FROM holdings WHERE fund_code = '000001'")
    cursor.execute("DELETE FROM funds WHERE fund_code = '000001'")
    conn.commit()
    conn.close()
    print("🧹 已清理 000001 的旧数据，确保测试『新基金同步抓取』逻辑。")

    # 2. 测试 POST /api/watchlist 添加 000001
    print("\n[测试 1] 添加基金 000001 (华夏成长) 到关注列表...")
    # 注意：这将触发真实的数据抓取，可能需要几秒钟
    response = client.post("/api/watchlist", json={"fund_code": "000001"})
    
    if response.status_code == 200:
        print(f"✅ 成功添加 000001. 结果: {response.json()}")
    else:
        print(f"❌ 添加失败: {response.status_code} - {response.text}")
        return

    # 3. 测试 GET /api/watchlist
    print("\n[测试 2] 获取关注列表...")
    response = client.get("/api/watchlist")
    if response.status_code == 200:
        watchlist = response.json()
        print(f"✅ 获取成功，当前关注数: {len(watchlist)}")
        for item in watchlist:
            print(f"   - {item['fund_code']}: {item['fund_name']}")
    else:
        print(f"❌ 获取失败: {response.status_code}")

    # 4. 测试 GET /api/estimates 获取估值数据
    print("\n[测试 3] 获取所有关注基金的实时估值 (含误差修正)...")
    # 这将触发计算引擎和实时行情抓取
    response = client.get("/api/estimates")
    if response.status_code == 200:
        estimates = response.json()
        print(f"✅ 获取成功，当前估值数: {len(estimates)}")
        for est in estimates:
            print(f"   基金: {est['fund_code']} ({est['fund_name']})")
            print(f"   预估净值: {est['estimated_nav']} (涨跌: {est['estimated_return']}%)")
            print(f"   是否修正: {est['is_corrected']} (EWA偏差: {est['ewa_bias']}%)")
            if est['is_corrected']:
                print(f"   修正后净值: {est['corrected_nav']}")
    else:
        print(f"❌ 获取失败: {response.status_code} - {response.text}")

    print("\n[说明] Swagger 文档验证")
    print("👉 由于 main.py (阶段 5) 尚未实现，目前无法直接通过 http://127.0.0.1:8000/docs 访问。")
    print("👉 但在后续 main.py 中集成此 router 后，Swagger 文档将自动生成。")
    
    print("\n=== 验证完成 ===")

if __name__ == "__main__":
    run_verification()
