#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Author: 潘高
LastEditors: 潘高
Date: 2022-03-21 17:01:39
LastEditTime: 2024-09-08 20:28:48
Description: 业务层API，供前端JS调用
usage: 在Javascript中调用window.pywebview.api.<methodname>(<parameters>)
'''

from api.storage import Storage
from api.system import System
from api.ozon_spider import OzonSpider
from DrissionPage import ChromiumPage,ChromiumOptions
import threading
from api.db.orm import ORM
from pyapp.config.config import Config
from casdoor import CasdoorSDK
from api.auth import auth_required
import requests
from loguru import logger


class API(System, Storage):
    '''业务层API，供前端JS调用'''
    
    def __init__(self):
        self.orm = ORM()
        # 身份验证状态
        self._is_authenticated = False # 初始状态设为 False，避免前端过早判断登录
        self._user_info = None
        self._current_token = None # 存储当前有效的 Token
        self._last_auth_check = 0  # 上次在线验证时间
        self._used_codes = {}      # 已处理过的授权码缓存 {code: result}
        
        # 首先初始化 Casdoor SDK
        try:
            self.casdoor_sdk = CasdoorSDK(
                endpoint=Config.casdoor_endpoint,
                client_id=Config.casdoor_client_id,
                client_secret=Config.casdoor_client_secret,
                certificate=Config.casdoor_certificate,
                org_name=Config.casdoor_org_name,
                application_name=Config.casdoor_application_name
            )
        except Exception as e:
            logger.info(f"Casdoor SDK 初始化失败: {e}")
            self.casdoor_sdk = None
        
        # 程序启动时，检查并加载数据库中已有的 Token - 优化为直接获取避免重复验证
        try:
            token = self.orm.getConfigVar('casdoor_token')
            if token:
                logger.info(f"[DEBUG] 程序启动时发现数据库中的 Token")
                # 直接设置 Token 到内存中，不立即验证，避免与前端重复验证
                self._current_token = token
                # 尝试解码用户信息，但不验证签名（因为 SDK 可能无法解析）
                try:
                    import jwt
                    user_info = jwt.decode(token, options={"verify_signature": False})
                    self._is_authenticated = True
                    self._user_info = user_info
                    logger.info(f"[DEBUG] Token 解析成功，用户: {user_info.get('name', '未知用户')}")
                except Exception as e:
                    logger.info(f"[DEBUG] Token 解析失败（程序启动时忽略）: {e}")
                    # 即使解析失败，Token 仍然可能有效，设置为已认证状态
                    self._is_authenticated = True
        except Exception as e:
            logger.info(f"[DEBUG] 初始化时加载 Token 失败（数据库可能尚未初始化）: {e}")
        
        # 爬虫状态
        self.spider_status = 'idle'  # idle: 空闲, running: 运行中, finished: 已完成
        self.spider_info = ''        # 爬虫信息
        self.spider = None           # 爬虫实例
        self.browser = None
        
        # 日志记录
        self.spider_logs = []
    
    def get_casdoor_signin_url(self):
        '''获取 Casdoor 登录地址 - 手动拼凑以避免 SDK 内部请求 7001 端口超时'''
        import urllib.parse
        try:
            # 基础端点确保以 / 结尾
            endpoint = Config.casdoor_endpoint.rstrip('/')
            
            # 手动拼凑 OAuth2 授权链接
            params = {
                "client_id": Config.casdoor_client_id,
                "response_type": "code",
                "redirect_uri": Config.casdoor_redirect_url,
                "scope": "read",
                "state": Config.casdoor_application_name # 或者其他标识符
            }
            query_string = urllib.parse.urlencode(params)
            auth_url = f"{endpoint}/login/oauth/authorize?{query_string}"
            return auth_url
        except Exception as e:
            logger.info(f"拼凑登录地址失败: {e}")
            return ""

    def verify_casdoor_token(self, token):
        '''验证 Casdoor Token 并获取用户信息'''
        if not self.casdoor_sdk:
            return {"success": False, "message": "Casdoor SDK 未初始化"}
        try:
            user_info = self.casdoor_sdk.parse_jwt_token(token)
            # logger.info(f"Casdoor SDK 解析 Token 成功，用户信息: {user_info}")
            self._is_authenticated = True
            self._user_info = user_info
            self._current_token = token # 缓存 Token
            return {"success": True, "user": user_info}
        except Exception as e:
            # 如果 SDK 解析失败（可能是证书没配），尝试手动解码（不校验签名）
            logger.error(f"Casdoor SDK 解析 Token 失败: {e}")
            return {"success": False, "message": str(e)}

    def get_user_by_code(self, code):
        '''通过授权码获取用户信息'''
        import requests
        import time
        
        logger.info(f"[DEBUG] 开始处理授权码: {code}")
        
        # 1. 授权码防重逻辑：如果 10 秒内处理过同一个 code，直接返回结果
        if code in self._used_codes:
            cache_time, result = self._used_codes[code]
            if time.time() - cache_time < 10:
                logger.info(f"[DEBUG] 授权码 {code} 命中缓存，直接返回")
                return result
        
        # 2. 优先检查是否已有有效的 Token（包括内存中的和数据库中的）
        if self._current_token:
            logger.info(f"[DEBUG] 内存中已有有效 Token，验证其有效性")
            try:
                result = self.verify_casdoor_token(self._current_token)
                if result["success"]:
                    if self.check_token_valid():
                        logger.info(f"[DEBUG] 内存中的 Token 验证成功，直接使用，不创建新 Token")
                        # 确保返回结果包含 token 字段，以便前端处理
                        result["token"] = self._current_token
                        return result
                    else:
                        logger.info(f"[DEBUG] 内存中的 Token 在线验证失败")
                else:
                    logger.info(f"[DEBUG] 内存中的 Token 验证失败")
            except Exception as e:
                logger.info(f"[DEBUG] Token 验证过程异常: {e}")
        else:
            token = self.orm.getConfigVar('casdoor_token')
            if token:
                logger.info(f"[DEBUG] 发现数据库中的 Token，验证其有效性")
                try:
                    result = self.verify_casdoor_token(token)
                    if result["success"]:
                        if self.check_token_valid():
                            logger.info(f"[DEBUG] 数据库中的 Token 验证成功，直接使用，不创建新 Token")
                            # 确保返回结果包含 token 字段，以便前端处理
                            result["token"] = token
                            return result
                        else:
                            logger.info(f"[DEBUG] 数据库中的 Token 在线验证失败")
                    else:
                        logger.info(f"[DEBUG] 数据库中的 Token 验证失败")
                except Exception as e:
                    logger.info(f"[DEBUG] Token 验证过程异常: {e}")
        
        # 3. 只有在没有有效 Token 的情况下才会换取新 Token
        logger.info(f"[DEBUG] 没有有效的 Token，开始换取新 Token")
        
        if not self.casdoor_sdk:
            logger.info("[DEBUG] Casdoor SDK 未初始化，尝试重新初始化...")
            try:
                self.casdoor_sdk = CasdoorSDK(
                    endpoint=Config.casdoor_endpoint,
                    client_id=Config.casdoor_client_id,
                    client_secret=Config.casdoor_client_secret,
                    certificate=Config.casdoor_certificate,
                    org_name=Config.casdoor_org_name,
                    application_name=Config.casdoor_application_name
                )
            except Exception as e:
                logger.info(f"[DEBUG] Casdoor SDK 重新初始化失败: {e}")
                return {"success": False, "message": "Casdoor SDK 初始化失败"}
                
        try:
            # 4. 交换 Token
            endpoint = Config.casdoor_endpoint.rstrip('/')
            token_url = f"{endpoint}/api/login/oauth/access_token"
            payload = {
                "grant_type": "authorization_code",
                "client_id": Config.casdoor_client_id,
                "client_secret": Config.casdoor_client_secret,
                "code": code
            }
            
            logger.info(f"[DEBUG] 正在向 Casdoor 交换 Token: {token_url}")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # 设置较短的超时时间，防止挂起
            response = requests.post(token_url, data=payload, timeout=5, verify=False)
            logger.info(f"[DEBUG] Casdoor 响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                return {"success": False, "message": f"服务器返回错误: {response.status_code}"}
                
            data = response.json()
            if "access_token" not in data:
                logger.info(f"[DEBUG] 获取 Token 失败，返回数据: {data}")
                return {"success": False, "message": data.get("error_description") or data.get("message") or "获取 Token 失败"}
            
            new_token = data["access_token"]
            logger.info("[DEBUG] 成功获取新 Token，开始解析用户信息...")
            
            # 5. 解析并保存状态
            try:
                user_info = self.casdoor_sdk.parse_jwt_token(new_token)
            except:
                import jwt
                user_info = jwt.decode(new_token, options={"verify_signature": False})
            
            self._is_authenticated = True
            self._user_info = user_info
            self._current_token = new_token
            self._last_auth_check = time.time() # 刚登录完，重置验证时间
            
            final_result = {"success": True, "user": user_info, "token": new_token}
            logger.info(f"[DEBUG] 登录流程成功完成: {user_info.get('name')}")
            
            # 保存新 Token 到数据库
            self.orm.setConfigVar('casdoor_token', new_token)
            
            # 记录到已使用列表
            self._used_codes[code] = (time.time(), final_result)
            return final_result
            
        except Exception as e:
            import traceback
            logger.info(f"[DEBUG] 处理登录回调异常: {str(e)}")
            traceback.print_exc()
            return {"success": False, "message": str(e)}

    def check_token_valid(self):
        '''在线验证 Token 有效性，增加严格的频率限制（每 60 秒最多验证一次）'''
        import time
        token = self._current_token
        if not token:
            logger.info("[DEBUG] 没有有效的 Token，无法验证")
            return False
        if self._is_authenticated and (time.time() - self._last_auth_check < 60):
            return True
        elif self._is_authenticated and (time.time() - self._last_auth_check >= 60):
            logger.info("[DEBUG] 距离上次验证超过 60 秒，开始新的验证")
            #使用 PyJWT 自动验证过期（推荐） 使用签名验证
            import jwt
            from cryptography.x509 import load_pem_x509_certificate
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            try:
                public_key = load_pem_x509_certificate(Config.casdoor_certificate.encode(), default_backend()).public_key()
                pem_public_key = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                expected_audience = Config.casdoor_client_id  # 替换为实际的 audience
                jwt.decode(
                    token, 
                    key=pem_public_key, 
                    algorithms=["RS256"],
                    audience=expected_audience  # 指定预期的 audience
                )
                self._is_authenticated = True
                self._last_auth_check = time.time()
                logger.info("[DEBUG] Token 验证通过，更新状态")
                return True
            except jwt.ExpiredSignatureError:
                logger.info("[DEBUG] Token 已过期")
                self._is_authenticated = False
                return False
            except jwt.InvalidTokenError:
                logger.info("[DEBUG] Token 无效")
                self._is_authenticated = False
                return False
        
    def get_casdoor_signout_url(self, id_token=None):
        '''获取 Casdoor 注销地址，支持传入 id_token_hint'''
        import urllib.parse
        try:
            endpoint = Config.casdoor_endpoint.rstrip('/')
            params = {
                "client_id": Config.casdoor_client_id,
                "post_logout_redirect_uri": Config.casdoor_redirect_url,
                "state": Config.casdoor_application_name
            }
            # 如果传入了 token，作为 id_token_hint 传递给 Casdoor
            # 许多 OIDC 服务（包括 Casdoor）需要这个参数来确保安全注销
            if id_token:
                params["id_token_hint"] = id_token
                
            query_string = urllib.parse.urlencode(params)
            signout_url = f"{endpoint}/api/logout?{query_string}"
            return signout_url
        except Exception as e:
            logger.info(f"拼凑注销地址失败: {e}")
            return ""

    def get_casdoor_token(self):
        '''从数据库获取 Casdoor Token'''
        token = self.orm.getConfigVar('casdoor_token')
        return {"success": True, "token": token}
        
    def set_casdoor_token(self, token):
        '''将 Casdoor Token 保存到数据库'''
        result = self.orm.setConfigVar('casdoor_token', token)
        return {"success": result}
        
    def delete_casdoor_token(self):
        '''从数据库删除 Casdoor Token'''
        try:
            self.orm.deleteConfigVar('casdoor_token')
            return {"success": True}
        except Exception as e:
            logger.info(f"删除 Token 失败: {e}")
            return {"success": False, "message": str(e)}
            
    def logout(self):
        '''注销登录，清理本地认证状态'''
        # 此时不需要在后端用 requests 发 POST，因为 Casdoor 的注销主要是通过浏览器清除 Cookie 
        # 我们只要把本地状态设为 False 即可
        self._is_authenticated = False
        self._user_info = None
        self._current_token = None
        self._last_auth_check = 0
        # 同时删除数据库中的 Token
        self.delete_casdoor_token()
        logger.info("[DEBUG] 后端本地认证状态已清理")
        return {"success": True}

    def setWindow(self, window):
        '''获取窗口实例'''
        System._window = window

    @auth_required
    def get_spider_status(self):
        '''获取爬虫状态'''
        return {
            'status': self.spider_status,
            'info': self.spider_info
        }
    
    @auth_required
    def log_message(self, message, level='info'):
        '''记录日志消息'''
        import datetime
        log_entry = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'message': message
        }
        self.spider_logs.append(log_entry)
        # 限制日志数量，避免内存溢出
        if len(self.spider_logs) > 500:
            self.spider_logs = self.spider_logs[-200:]
        return True
    
    @auth_required
    def get_spider_logs(self):
        '''获取爬虫日志'''
        return self.spider_logs
    
    @auth_required
    def clear_logs(self):
        '''清空爬虫日志'''
        self.spider_logs = []
        return True
    
    @auth_required
    def start_spider(self, base_url):
        '''启动爬虫'''
        # 从配置表获取配置
        browser_path = self.orm.getConfigVar('browserPath')
        browser_user_data_path = self.orm.getConfigVar('browserUserDataPath')
        
        # 验证浏览器配置
        if not browser_path or not browser_user_data_path:
            if not browser_path:
                self.log_message('请指定浏览器路径', 'error')
            if not browser_user_data_path:
                self.log_message('请指定浏览器用户数据路径', 'error')
            self.spider_status = 'idle'
            self.spider_info = '浏览器配置不完整，无法启动爬虫'
            return False
            
        co = ChromiumOptions()

        # 使用配置表的配置
        co.set_user_data_path(browser_user_data_path)
        self.log_message(f'使用浏览器用户数据路径: {browser_user_data_path}', 'info')
        
        co.set_browser_path(browser_path)
        self.log_message(f'使用浏览器路径: {browser_path}', 'info')
        
        co.no_imgs(True)
        self.browser = ChromiumPage(co)


        self.spider_status = 'running'
        self.spider_info = '正在启动爬虫...'
        self.spider_logs = []  # 清空历史日志
        self.log_message(f'爬虫启动', 'info')
        
        finish_event = threading.Event()
        
        def run_spider():
            try:
                self.log_message('正在初始化浏览器实例...', 'info')
                self.spider = OzonSpider(base_url, self.browser, finish_event, 820, api=self, end_callback=self.spider_end_callback, thread_count=1)  # 默认爬取820页，传递API实例
                self.log_message('爬虫实例创建成功', 'info')
                self.spider.start()
                self.spider_info = '正在爬取中...'
                
                self.log_message('爬虫开始运行...', 'info')
                self.spider._finish_event.wait()
                
                self.spider_status = 'finished'
                self.spider_info = '爬虫任务完成！'
                self.log_message('爬虫任务完成', 'success')
                    
            except Exception as e:
                self.spider_status = 'idle'
                error_msg = f'爬虫出错: {str(e)}'
                self.spider_info = error_msg
                self.log_message(error_msg, 'error')
                
        # 启动爬虫线程
        thread = threading.Thread(target=run_spider, daemon=True)
        thread.start()
        
        return True

    def spider_end_callback(self):
        self.spider_status = 'finished'
        self.spider_info = '爬虫任务完成！'
        self.log_message('爬虫任务完成', 'success')
    
    @auth_required
    def stop_spider(self):
        '''停止爬虫'''
        if self.spider:
            self.spider.stop_spider()
        if self.browser:
            self.browser.close()
        self.spider_status = 'idle'
        self.spider_info = '爬虫已停止'
        self.log_message('爬虫已停止', 'info')
        return True

    @auth_required
    def test_browser_config(self, browser_path, user_data_path):
        '''测试浏览器配置 - 直接打开浏览器进程'''
        import subprocess
        try:
            # 使用 subprocess 直接启动浏览器进程，不进行任何控制
            # --user-data-dir 是 Chrome/Edge 的标准参数
            cmd = f'"{browser_path}" --user-data-dir="{user_data_path}"'
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception as e:
            logger.info(f'测试浏览器启动失败: {str(e)}')
            return False


    @auth_required
    def search_data(self, sku=None, limit=30, filters=None):
        '''查询数据'''
        #使用orm查询数据
        orm = ORM()
        if sku:
            data = orm.query_data(sku=sku, limit=limit, filters=filters)
        else:
            data = orm.query_data(limit=limit, filters=filters)
        return data
    
    @auth_required
    def get_data_count(self, sku=None, filters=None):
        '''获取数据总数量'''
        # 使用ORM查询总数据量
        orm = ORM()
        if sku:
            count = orm.query_count(sku=sku, filters=filters)
        else:
            count = orm.query_count(filters=filters)
        return count
    
    @auth_required
    def delete_filtered_data(self, filters=None):
        '''删除当前筛选后的数据'''
        try:
            # 使用ORM删除数据
            orm = ORM()
            # 先查询符合条件的数据
            data = orm.query_data(limit=None, filters=filters)
            deleted_count = 0
            
            for item in data:
                # 逐个删除数据
                if orm.deleteStorageVar(item['sku']):
                    deleted_count += 1
            
            return {'success': True, 'deletedCount': deleted_count}
        except Exception as e:
            logger.info(f'删除数据失败: {str(e)}')
            return {'success': False, 'message': str(e)}
    
    @auth_required
    def export_data(self, filters=None):
        '''导出数据为CSV文件，并修改导出数据的状态'''
        import csv
        import os
        from datetime import datetime
        
        try:
            # 使用ORM查询数据
            orm = ORM()
            data = orm.query_data(limit=None, filters=filters)
            
            # 生成筛选项文字描述
            filter_description = []
            if filters:
                if filters.get('status') is not None:
                    filter_description.append(f'状态_{filters["status"]}')
                if filters.get('minPrice') is not None:
                    filter_description.append(f'最低价_{filters["minPrice"]}')
                if filters.get('maxPrice') is not None:
                    filter_description.append(f'最高价_{filters["maxPrice"]}')
                if filters.get('minStar') is not None:
                    filter_description.append(f'最低星_{filters["minStar"]}')
                if filters.get('maxStar') is not None:
                    filter_description.append(f'最高星_{filters["maxStar"]}')
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filter_part = '_'.join(filter_description)
            if filter_part:
                filename = f'ozon_products_{filter_part}_{timestamp}.csv'
            else:
                filename = f'ozon_products_{timestamp}.csv'
            
            # 保存到软件根目录
            filepath = os.path.join(os.getcwd(), filename)
            
            # 写入CSV文件
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['sku', 'price', 'star', 'status', 'created_at', 'updated_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for item in data:
                    # 只写入我们需要的字段，过滤掉其他字段（如id）
                    filtered_item = {k: v for k, v in item.items() if k in fieldnames}
                    writer.writerow(filtered_item)
            
            # 修改导出数据的状态
            for item in data:
                orm.update_status(item['sku'], 1)  # 假设导出后状态变为1
            
            return {'success': True, 'filePath': filepath}
        except Exception as e:
            logger.info(f'导出数据失败: {str(e)}')
            return {'success': False, 'message': str(e)}