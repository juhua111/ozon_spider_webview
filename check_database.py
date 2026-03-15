#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''检查数据库中的商品数据'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from pyapp.config.config import Config
from pyapp.db.sql.db import DB
from api.db.sql.models import PPXStorageVar
from loguru import logger
from sqlalchemy import text

def check_database():
    '''检查数据库中的商品数据'''
    logger.add("check_database.log", level="INFO")
    
    logger.info("开始检查数据库...")
    
    try:
        # 初始化配置
        config = Config()
        config.init()
        
        # 初始化数据库
        db = DB()
        db.init()
        
        # 获取数据库会话
        dbSession = DB.session()
        
        # 查询表结构
        logger.info("查询ppx_storage_var表的字段结构:")
        stmt = text('PRAGMA table_info(ppx_storage_var);')
        res = dbSession.execute(stmt)
        columns = res.all()
        for column in columns:
            logger.info(f"字段名: {column[1]}, 类型: {column[2]}")
        
    except Exception as e:
        logger.error(f"❌ 数据库检查失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
    finally:
        if 'dbSession' in locals():
            dbSession.close()

if __name__ == "__main__":
    check_database()