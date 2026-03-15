#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
测试comment_count字段是否正常工作
'''

from cgitb import text
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api.db.sql.orm import ORM
    from api.db.sql.models import PPXStorageVar
    from pyapp.db.sql.db import DB
    from pyapp.config.config import Config
    
    print("✅ 模块导入成功")
    
    # 初始化配置和数据库
    config = Config()
    config.init()
    db = DB()
    db.init()
    
    print("✅ 数据库初始化成功")
    
    # 测试ORM查询
    orm = ORM()
    print("✅ ORM初始化成功")
    
    # 查询数据
    data = orm.query_data(limit=5)
    print(f"✅ 查询到 {len(data)} 条数据")
    
    if data:
        print("📋 数据详情:")
        for item in data:
            print(f"  SKU: {item.get('sku', 'N/A')}")
            print(f"  价格: {item.get('price', 'N/A')}")
            print(f"  评分: {item.get('star', 'N/A')}")
            print(f"  评价数量: {item.get('comment_count', 'N/A')}")
            print(f"  状态: {item.get('status', 'N/A')}")
            print()
        
        # 检查comment_count字段是否存在
        if 'comment_count' in data[0]:
            print("✅ comment_count字段存在")
            # 检查是否有评价数量数据
            has_comment_count = any(item.get('comment_count', 0) > 0 for item in data)
            if has_comment_count:
                print("✅ 发现包含评价数量的数据")
            else:
                print("⚠️  所有数据的评价数量都是0或None")
        else:
            print("❌ comment_count字段不存在")
            
    else:
        print("⚠️  未查询到数据")
    
    # 测试直接查询模型
    dbSession = DB.session()
    try:
        # 查询前几条数据
        result = dbSession.execute(
            text("SELECT sku, price, star, status, comment_count FROM ppx_storage_var LIMIT 3")
        )
        print("🔍 直接SQL查询结果:")
        for row in result:
            print(f"  {row}")
    finally:
        dbSession.close()
        
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    print(f"\n📋 详细错误信息:")
    print(traceback.format_exc())