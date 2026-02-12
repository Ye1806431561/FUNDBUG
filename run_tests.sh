#!/bin/bash
# 一键运行所有测试的脚本

echo "Running all tests with PYTHONPATH=."
PYTHONPATH=. .venv/bin/pytest tests/ -v
