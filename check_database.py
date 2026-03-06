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
        
        # 查询总商品数量
        total_count = dbSession.query(PPXStorageVar).count()
        logger.info(f"总商品数量: {total_count}")
        
        # 查询前20个商品
        logger.info("前20个商品:")
        products = dbSession.query(PPXStorageVar).limit(20).all()
        for idx, product in enumerate(products):
            logger.info(f"{idx+1}. SKU: {product.sku}, 价格: {product.price}, 星级: {product.star}, 状态: {product.status}")
        
        # 查询价格范围
        logger.info("价格统计:")
        prices = dbSession.query(PPXStorageVar.price).all()
        price_list = [p[0] for p in prices if p[0] is not None]
        
        if price_list:
            min_price = min(price_list)
            max_price = max(price_list)
            avg_price = sum(price_list) / len(price_list)
            logger.info(f"价格范围: 最小 {min_price}, 最大 {max_price}, 平均 {avg_price:.2f}")
        
        logger.info("✅ 数据库检查完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库检查失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
    finally:
        if 'dbSession' in locals():
            dbSession.close()

if __name__ == "__main__":
    check_database()