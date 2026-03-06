#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Author: 潘高
LastEditors: 潘高
Date: 2023-03-12 20:08:30
LastEditTime: 2025-06-24 09:20:27
Description: 操作数据库类 - sql
usage:
    from api.db.sql.orm import ORM

    orm = ORM()    # 操作数据库类
    author = self.orm.getStorageVar('author')    # 获取储存变量
    print('author', author)
'''

from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.sqlite import insert

from api.db.sql.models import PPXStorageVar, PPXConfigVar
from pyapp.db.sql.db import DB


class ORM:
    '''操作数据库类'''

    def getConfigVar(self, key):
        '''获取配置变量'''
        dbSession = DB.session()
        try:
            with dbSession.begin():
                stmt = select(PPXConfigVar).where(PPXConfigVar.key == key)
                result = dbSession.execute(stmt)
                config = result.scalar_one_or_none()
                if config:
                    return config.value
                else:
                    return None
        finally:
            dbSession.close()

    def setConfigVar(self, key, value):
        '''设置配置变量'''
        try:
            dbSession = DB.session()
            with dbSession.begin():
                # 检查是否已存在该配置变量
                stmt = select(PPXConfigVar).where(PPXConfigVar.key == key)
                result = dbSession.execute(stmt)
                config = result.scalar_one_or_none()
                
                if config:
                    # 更新配置变量
                    stmt = update(PPXConfigVar).where(PPXConfigVar.key == key).values(value=value)
                else:
                    # 插入新配置变量
                    stmt = insert(PPXConfigVar).values(key=key, value=value)
                
                dbSession.execute(stmt)
            dbSession.close()
            return True
        except Exception as e:
            print('setConfigVar error:', e)
            return False

    def getAllConfigVars(self):
        '''获取所有配置变量'''
        dbSession = DB.session()
        try:
            with dbSession.begin():
                stmt = select(PPXConfigVar)
                result = dbSession.execute(stmt)
                return {row[0].key: row[0].value for row in result}
        finally:
            dbSession.close()

    def deleteConfigVar(self, key):
        '''删除配置变量'''
        try:
            dbSession = DB.session()
            with dbSession.begin():
                stmt = delete(PPXConfigVar).where(PPXConfigVar.key == key)
                dbSession.execute(stmt)
            dbSession.close()
            return True
        except Exception as e:
            print('deleteConfigVar error:', e)
            return False

    def insertStorageVar(self, sku, price, star, status=0):
        '''插入储存变量'''
        try:
            dbSession = DB.session()
            with dbSession.begin():
                data = {'sku': sku, 'price': price, 'star': star, 'status': status}
                stmt = insert(PPXStorageVar).values(**data)
                dbSession.execute(stmt)
            dbSession.close()
            return True
        except Exception as e:
            print('insertStorageVar error:', e)
            return False

    def getAllStorageVars(self, limit=30,page=1):
        '''获取所有储存变量'''
        dbSession = DB.session()
        try:
            with dbSession.begin():
                stmt = select(PPXStorageVar).limit(limit).offset((page-1)*limit)
                result = dbSession.execute(stmt)
                return [row[0].toDict() for row in result]
        finally:
            dbSession.close()

    def deleteStorageVar(self, sku):
        '''删除储存变量'''
        try:
            dbSession = DB.session()
            with dbSession.begin():
                stmt = delete(PPXStorageVar).where(PPXStorageVar.sku == sku)
                dbSession.execute(stmt)
            dbSession.close()
            return True
        except Exception as e:
            print('deleteStorageVar error:', e)
            return False
            
    def update_status(self, sku, status):
        '''更新产品状态'''
        try:
            dbSession = DB.session()
            with dbSession.begin():
                stmt = update(PPXStorageVar).where(PPXStorageVar.sku == sku).values(status=status)
                dbSession.execute(stmt)
            dbSession.close()
            return True
        except Exception as e:
            print('update_status error:', e)
            return False

    def query_count(self, sku=None, filters=None):
        '''查询数据总数量'''
        dbSession = DB.session()
        try:
            with dbSession.begin():
                stmt = select(func.count(PPXStorageVar.id))
                if sku:
                    stmt = stmt.where(PPXStorageVar.sku == sku)
                if filters:
                    if filters.get('status') is not None:
                        stmt = stmt.where(PPXStorageVar.status == filters['status'])
                    if filters.get('minPrice') is not None:
                        stmt = stmt.where(PPXStorageVar.price >= filters['minPrice'])
                    if filters.get('maxPrice') is not None:
                        stmt = stmt.where(PPXStorageVar.price <= filters['maxPrice'])
                    if filters.get('minStar') is not None:
                        stmt = stmt.where(PPXStorageVar.star >= filters['minStar'])
                    if filters.get('maxStar') is not None:
                        stmt = stmt.where(PPXStorageVar.star <= filters['maxStar'])
                result = dbSession.execute(stmt)
                return result.scalar()
        finally:
            dbSession.close()
            
    def query_data(self, sku=None, limit=30, page=1, filters=None):
        '''查询数据'''
        dbSession = DB.session()
        try:
            with dbSession.begin():
                stmt = select(PPXStorageVar)
                if sku:
                    stmt = stmt.where(PPXStorageVar.sku == sku)
                if filters:
                    if filters.get('status') is not None:
                        stmt = stmt.where(PPXStorageVar.status == filters['status'])
                    if filters.get('minPrice') is not None:
                        stmt = stmt.where(PPXStorageVar.price >= filters['minPrice'])
                    if filters.get('maxPrice') is not None:
                        stmt = stmt.where(PPXStorageVar.price <= filters['maxPrice'])
                    if filters.get('minStar') is not None:
                        stmt = stmt.where(PPXStorageVar.star >= filters['minStar'])
                    if filters.get('maxStar') is not None:
                        stmt = stmt.where(PPXStorageVar.star <= filters['maxStar'])
                if limit is not None:
                    stmt = stmt.limit(limit).offset((page-1)*limit)
                result = dbSession.execute(stmt)
                return [row[0].toDict() for row in result]
        finally:
            dbSession.close()
