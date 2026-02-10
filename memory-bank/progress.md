# FUNDBUG 开发进度记录

> 此文档记录开发过程，供后续开发者参考。

---

## 2026-02-09 - 步骤 0.1: 创建项目目录结构 ✅

### 完成内容

创建了完整的模块化项目结构：

```
FUNDBUG/
├── src/                    # 源代码目录
│   ├── __init__.py         # 包标识
│   ├── data/               # 数据采集层
│   │   └── __init__.py
│   ├── engine/             # 计算引擎层
│   │   └── __init__.py
│   ├── api/                # API 服务层
│   │   └── __init__.py
│   ├── db/                 # 数据库层
│   │   └── __init__.py
│   └── utils/              # 公共工具
│       └── __init__.py
├── frontend/               # 前端目录
│   └── index.html          # 占位文件
├── data/                   # SQLite 数据库目录
│   └── .gitkeep
├── config.py               # 配置文件 (已包含所有常量)
└── main.py                 # 主入口文件 (占位)
```

### 关键决策

1. **config.py 已预填充配置** - 包含 DATABASE_PATH, API_HOST/PORT, UPDATE_INTERVAL_SECONDS(60), DATA_RETENTION_DAYS(7), EWA_ALPHA(0.3)
2. **每个模块都有 `__init__.py`** - 确保 Python 包结构正确
3. **data/ 目录独立于 src/data/** - 前者存放 SQLite 文件，后者存放数据采集代码

### 验证结果

```bash
$ find src -name "__init__.py" | wc -l
6  ✅

$ ls config.py main.py frontend/ data/
config.py  main.py  data/  frontend/  ✅
```

---

## 下一步

- [ ] 步骤 0.2: 创建 requirements.txt
