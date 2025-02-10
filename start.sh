#!/bin/bash

# 设置Python路径
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# 启动PyService Web管理界面
streamlit run src/ui/main.py