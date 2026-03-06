#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''测试 Casdoor SDK 初始化和证书配置'''

from pyapp.config.config import Config
from casdoor import CasdoorSDK
from loguru import logger

# 配置日志
logger.add("test_casdoor.log", level="INFO")

def test_sdk_init():
    '''测试 SDK 初始化'''
    logger.info("开始测试 Casdoor SDK 初始化...")
    
    try:
        sdk = CasdoorSDK(
            endpoint=Config.casdoor_endpoint,
            client_id=Config.casdoor_client_id,
            client_secret=Config.casdoor_client_secret,
            certificate=Config.casdoor_certificate,
            org_name=Config.casdoor_org_name,
            application_name=Config.casdoor_application_name
        )
        logger.info("✅ Casdoor SDK 初始化成功")
        get_oauth_token = sdk.get_oauth_token()
        logger.info(f"获取到的 OAuth Token: {get_oauth_token}")
        
        # 验证证书格式
        logger.info(f"证书类型: {type(Config.casdoor_certificate)}")
        logger.info(f"证书长度: {len(Config.casdoor_certificate)} 字符")
        logger.info(f"证书前缀: {repr(Config.casdoor_certificate[:50])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Casdoor SDK 初始化失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def test_token_verify(code):
    '''测试 Token 验证'''
    logger.info(f"开始测试 Token 验证: {code[:10]}...")
    
    try:
        sdk = CasdoorSDK(
            endpoint=Config.casdoor_endpoint,
            client_id=Config.casdoor_client_id,
            client_secret=Config.casdoor_client_secret,
            certificate=Config.casdoor_certificate,
            org_name=Config.casdoor_org_name,
            application_name=Config.casdoor_application_name
        )
        token = sdk.get_oauth_token(username='juhua1',password='Qq123123')
        print(token)
        token = token['access_token']
        user_info = sdk.parse_jwt_token(token)
        logger.info(f"✅ Token 验证成功，用户信息: {user_info}")
        return True 
        
    except Exception as e:
        logger.error(f"❌ Token 验证失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImNlcnRfdjdnMW5lIiwidHlwIjoiSldUIn0.eyJvd25lciI6InVzZXIiLCJuYW1lIjoianVodWExIiwiY3JlYXRlZFRpbWUiOiIyMDI2LTAzLTAzVDIzOjQ5OjQxKzA4OjAwIiwidXBkYXRlZFRpbWUiOiIyMDI2LTAzLTA2VDE1OjI0OjA1WiIsImRlbGV0ZWRUaW1lIjoiMjAyNi0wMy0wNFQwMTozMjoxNiswODowMCIsImlkIjoiMmEyM2FjMmItNTRhZC00ZTY5LTliMjgtZjYxZTYwYzBiZDNmIiwidHlwZSI6Im5vcm1hbC11c2VyIiwicGFzc3dvcmQiOiIiLCJwYXNzd29yZFNhbHQiOiJlOTY4YWQ5YWIwNTQwYWQwNDJhMiIsInBhc3N3b3JkVHlwZSI6ImJjcnlwdCIsImRpc3BsYXlOYW1lIjoiTmV3IFVzZXIgLSBiZzNveXoiLCJmaXJzdE5hbWUiOiIiLCJsYXN0TmFtZSI6IiIsImF2YXRhciI6Imh0dHBzOi8vY2RuLmNhc2Jpbi5vcmcvaW1nL2Nhc2Jpbi5zdmciLCJhdmF0YXJUeXBlIjoiIiwicGVybWFuZW50QXZhdGFyIjoiIiwiZW1haWwiOiJiZzNveXpAZXhhbXBsZS5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInBob25lIjoiOTI2MzEwMjU5MjIiLCJjb3VudHJ5Q29kZSI6IkNOIiwicmVnaW9uIjoiIiwibG9jYXRpb24iOiIiLCJhZGRyZXNzIjpbXSwiYWZmaWxpYXRpb24iOiJFeGFtcGxlIEluYy4iLCJ0aXRsZSI6IiIsImlkQ2FyZFR5cGUiOiIiLCJpZENhcmQiOiIiLCJob21lcGFnZSI6IiIsImJpbyI6IiIsImxhbmd1YWdlIjoiIiwiZ2VuZGVyIjoiIiwiYmlydGhkYXkiOiIiLCJlZHVjYXRpb24iOiIiLCJzY29yZSI6MCwia2FybWEiOjAsInJhbmtpbmciOjEsImlzRGVmYXVsdEF2YXRhciI6ZmFsc2UsImlzT25saW5lIjpmYWxzZSwiaXNBZG1pbiI6ZmFsc2UsImlzRm9yYmlkZGVuIjpmYWxzZSwiaXNEZWxldGVkIjpmYWxzZSwic2lnbnVwQXBwbGljYXRpb24iOiJvem9uX3NwaWRlciIsImhhc2giOiIiLCJwcmVIYXNoIjoiIiwicmVnaXN0ZXJUeXBlIjoiQWRkIFVzZXIiLCJyZWdpc3RlclNvdXJjZSI6ImJ1aWx0LWluL2FkbWluIiwiYWNjZXNzS2V5IjoiIiwiYWNjZXNzU2VjcmV0IjoiIiwiZ2l0aHViIjoiIiwiZ29vZ2xlIjoiIiwicXEiOiIiLCJ3ZWNoYXQiOiIiLCJmYWNlYm9vayI6IiIsImRpbmd0YWxrIjoiIiwid2VpYm8iOiIiLCJnaXRlZSI6IiIsImxpbmtlZGluIjoiIiwid2Vjb20iOiIiLCJsYXJrIjoiIiwiZ2l0bGFiIjoiIiwiY3JlYXRlZElwIjoiIiwibGFzdFNpZ25pblRpbWUiOiIiLCJsYXN0U2lnbmluSXAiOiIiLCJwcmVmZXJyZWRNZmFUeXBlIjoiIiwicmVjb3ZlcnlDb2RlcyI6bnVsbCwidG90cFNlY3JldCI6IiIsIm1mYVBob25lRW5hYmxlZCI6ZmFsc2UsIm1mYUVtYWlsRW5hYmxlZCI6ZmFsc2UsImxkYXAiOiIiLCJwcm9wZXJ0aWVzIjp7fSwicm9sZXMiOltdLCJwZXJtaXNzaW9ucyI6W10sImdyb3VwcyI6W10sImxhc3RTaWduaW5Xcm9uZ1RpbWUiOiIiLCJzaWduaW5Xcm9uZ1RpbWVzIjowLCJtYW5hZ2VkQWNjb3VudHMiOm51bGwsInRva2VuVHlwZSI6ImFjY2Vzcy10b2tlbiIsInRhZyI6InN0YWZmIiwic2NvcGUiOiJyZWFkIiwiYXpwIjoiMTg3ZjI5ZGM2MmVlNTg4ODI5ZTIiLCJzaWduaW5NZXRob2QiOiJQYXNzd29yZCIsImlzcyI6Imh0dHA6Ly82Ni4xNTQuMTA4Ljg4OjgwMDAiLCJzdWIiOiIyYTIzYWMyYi01NGFkLTRlNjktOWIyOC1mNjFlNjBjMGJkM2YiLCJhdWQiOlsiMTg3ZjI5ZGM2MmVlNTg4ODI5ZTIiXSwiZXhwIjoxNzczNDI1MDE0LCJuYmYiOjE3NzI4MjAyMTQsImlhdCI6MTc3MjgyMDIxNCwianRpIjoiYWRtaW4vNGVhMjI1YTMtODIwZS00N2JmLWE5YjktYmJkNDJlNDAzYTRlIn0.VwnRnePEXRZixnKafk_3TNEybg5K6Cwk3d05_j0cPus_qd2tzmzTn5SNYlsSQmF4k_JkTDlEJ7DV_IwKQHtQiE_nSBd--EV161ZN0mR7vCIbRphniyNhYcKTOYxElT8WM_uKlZc-7RxmItGxwMBSpleIjOrTt86nIpAtmAhY-lhf6vGvXcOJEze_AX_71sdw1xNJnfu1Qa1r1NdzZ8R9e-HihjC3AYe63OCIQ3wu8st9oKY6WOcPycfzsm12w3a9-GhDPR902K6b4Eu3b8Q3_8Ay53GxVoW1QRVCZKrym3IV1kqV7FxEapIqwxo50-gpxM3UdQ6CjxvrHSOf41EAYCfrLKE5Um9L_f3pH-qbVMJYJaJMjrDIBkpp7Wl6kO_W61Q2IWw3lY78ey0754-ThJYRzAYuZXtGtiyyDOBIIK-BC1-oZqBjbT-CaGuGbEl4b8SUuGG9fVCSRlMmx6jITalCjJpcHW9WWtUDnMrg2moLRJkFucNYoX-ivoIoNhsBXWnc2hGYiKE4ChZApGtTvQ_9c7y_AhWs1dDg-hpBYxXLF2hbtcmHUS0msXjijvXtzO6XKlc5xSUteG3UiU7dzhr71HCQzoVUCLzFO8MHLPAK3SN9axoRfDjNXqX_bShFKSUejeC08lvoBXurKCN-WIctVjEzKFfECVhOFj2bnyA'

    #用证书验证token
    import jwt
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.x509 import load_pem_x509_certificate
    public_key = load_pem_x509_certificate(Config.casdoor_certificate.encode(), default_backend()).public_key()
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    expected_audience = Config.casdoor_client_id  # 替换为实际的 audience
    
    payload = jwt.decode(
        token, 
        key=pem_public_key, 
        algorithms=["RS256"],
        audience=expected_audience  # 指定预期的 audience
    )
    logger.info("✅ Token 验证成功")