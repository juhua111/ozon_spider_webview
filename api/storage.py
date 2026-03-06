#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Author: 潘高
LastEditors: 潘高
Date: 2023-03-25 19:39:03
LastEditTime: 2024-12-17 14:06:00
Description: 操作存储在数据库中的数据
usage: 调用window.pywebview.api.storage.<methodname>(<parameters>)从Javascript执行
'''

from api.db.orm import ORM
from api.auth import auth_required


class Storage():
    '''存储类'''

    orm = ORM()    # 操作数据库类

    @auth_required
    def storage_get(self, sku, limit=30,page=1):
        '''获取产品信息'''
        return self.orm.getStorageVar(sku, limit,page)

    @auth_required
    def storage_set(self, sku, price, star, status=0):
        '''设置产品信息'''
        self.orm.setStorageVar(sku, price, star, status)

    @auth_required
    def storage_get_all(self, limit=30,page=1):
        '''获取所有产品信息'''
        return self.orm.getAllStorageVars(limit,page)

    @auth_required
    def storage_update(self, sku, price, star, status=0):
        '''更新产品信息'''
        self.orm.setStorageVar(sku, price, star, status)

    @auth_required
    def storage_insert(self, sku, price, star, status=0):
        '''插入产品信息'''
        return self.orm.insertStorageVar(sku, price, star, status)

    @auth_required
    def storage_delete(self, sku):
        '''删除产品信息'''
        return self.orm.deleteStorageVar(sku)

    @auth_required
    def storage_search(self, keyword, limit=30,page=1):
        '''搜索产品信息'''
        return self.orm.searchStorageVars(keyword, limit,page)
    
    # 配置相关接口
    @auth_required
    def config_get(self, key):
        '''获取配置变量'''
        return self.orm.getConfigVar(key)

    @auth_required
    def config_set(self, key, value):
        '''设置配置变量'''
        return self.orm.setConfigVar(key, value)

    @auth_required
    def config_get_all(self):
        '''获取所有配置变量'''
        return self.orm.getAllConfigVars()

    @auth_required
    def config_delete(self, key):
        '''删除配置变量'''
        return self.orm.deleteConfigVar(key)
