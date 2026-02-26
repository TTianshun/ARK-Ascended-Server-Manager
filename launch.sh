#!/bin/bash
# ARK: Survival Ascended Server Manager 启动脚本
# 直接运行: bash launch.sh 或 ./launch.sh

cd "$(dirname "$0")"
python src/ark_asa_manager/__main__.py
