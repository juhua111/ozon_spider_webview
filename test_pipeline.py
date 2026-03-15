#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 SQLitePipeline 的修改是否成功
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from pyapp.db.db import DB
    
    print("✅ SQLitePipeline 导入成功")
    print(f"📁 数据库路径: {DB().dbPath}")
    
    db = DB()
    db.init()

except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    print(f"\n📋 详细错误信息:")
    print(traceback.format_exc())