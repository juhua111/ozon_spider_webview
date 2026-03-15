#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Author: 潘高
LastEditors: 潘高
Date: 2022-03-21 16:54:23
LastEditTime: 2025-12-06 14:17:59
Description: 配置文件
usage:
    from pyapp.config.config import Config
    print(Config.rootDir)
'''

import getpass
import os
import platform
import sys


class Config:
    '''配置文件'''

    ##
    # 程序基础配置信息
    ##
    appName = 'OzonSpider'  # 应用名称
    appNameEN = 'OzonSpider'    # 应用名称-英文（用于生成缓存文件夹，必须是英文）
    appVersion = "V1.3"  # 应用版本号
    appDeveloper = "CJH"  # 应用开发者
    appBlogs = ""  # 个人博客
    appPackage = 'vip.cjh.ozonspider'    # 应用包名，用于在本地电脑生成 vip.pangao.ozonspider 唯一文件夹
    appUpdateUrl = ''    # 获取程序更新信息 https://api.github.com/repos/pangao1990/ozon_spider_webview/releases/latest
    appISSID = '2DE4B734-33D5-B84E-EF0C-5270F4966A62'    # Inno Setup 打包唯一编号。在执行 pnpm run init 之前，请设置为空，程序会自动生成唯一编号，生成后请勿修改！！！

    ##
    # 系统配置信息（不需要修改，可以自动获取）
    ##
    cpuArch = platform.processor()    # 本机CPU架构
    appSystem = platform.system()    # 本机系统类型
    appIsMacOS = appSystem == 'Darwin'    # 是否为macOS系统
    codeDir = sys.path[0].replace('base_library.zip', '')    # 代码根目录，一般情况下，也是程序所在的绝对目录（但在build:pure打包成的独立exe程序中，codeDir是执行代码的缓存根目录，而非程序所在的绝对目录）
    staticDir = os.path.join(codeDir, 'static')    # 代码根目录下的static文件夹的绝对路径
    appDataDir = ''    # 电脑上可持久使用的隐藏目录
    downloadDir = ''    # 电脑上的下载目录

    ##
    # 其他配置信息
    ##
    devPort = '5173'    # 开发环境中的前端页面端口
    devEnv = True    # 是否为开发环境，不需要手动更改，在程序运行的时候自动判断
    ifCoverDB = True    # 是否覆盖电脑上存储的数据库，默认不覆盖。只有在变更数据库密码或者数据库改动非常大，不得已的情况下才建议覆盖数据库
    typeDB = 'sql'    # 数据库类型，目前支持: json, sql
    pwDB = b'W5bjZVQ-Q19mwDeK7qZ2pUDVkS0_TABQBMt3fIUFkko='    # 数据库密码，typeDB=json时有效。若要重置密码，请在执行 pnpm run init 之前，设置为空，程序会自动生成密码，生成后请勿修改！！！

    ##
    # Casdoor 配置信息
    ##
    casdoor_endpoint = "http://66.154.108.88:8000/" # 例如: http://casdoor.example.com
    casdoor_client_id = "187f29dc62ee588829e2"
    casdoor_client_secret = "a7930b214c819506c4486eeff89fbb96f0029c08"
    casdoor_certificate = """-----BEGIN CERTIFICATE-----
MIIE1zCCAr+gAwIBAgIDAeJAMA0GCSqGSIb3DQEBCwUAMCUxDTALBgNVBAoTBHVz
ZXIxFDASBgNVBAMMC2NlcnRfdjdnMW5lMB4XDTI2MDMwNjE1NTYzMFoXDTQ2MDMw
NjE1NTYzMFowJTENMAsGA1UEChMEdXNlcjEUMBIGA1UEAwwLY2VydF92N2cxbmUw
ggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQC+KC/hY2lmzggja56WpWBk
M1j97fER1cTfVz7t66oi/6/OpER57GVz6wS2gEKcK2j7WQh2uDK3+PEXDonmhhQB
6GmG8cidPXrZtwCRvm2tb2hTpv+GumcWVh6+wdWc4bprwiIHrXz2AKIIR4+xVf56
xLyWYZUx+4Ng6mfpz/sZ33znAg58xsixtgti9INLd+geBD8qDOpFy++73/bb3sD+
HrB48lq3FVUa9WzU+QQYG9clnaLpzTu/Cj27K+7wn8UNWjNEkaWyDAM7RZFSdZLe
7d/CEJfGZVnTqtGlyKu86Jx+yZ8cE0ndj6Hx0bdI4Iggx4Qb9sBY5TXNNjnXXXwq
KH+wc9/ybeSk63uJVHqDc/z03oRz2OKHJG1kgt5rOYZ7ZS4027XqA6NzQlgzdEh3
GYeRMGUcoD8vMKHM8la4P2eUKj/NbsDLDGqpmwLbX/AK5Hf6JVP268/RxCZFLk+l
6Q8Layy2D8ng9bCZcBin1Uulg7vwS1fvxDCtV4VrpGGdnCIYD8KUZ4+xqhjQ+uq0
6ZQGvkyp4F7tYm9EjGtCL0KqgdWIHIT8USgsdpcWCfD4krBuQlnN4KDcoVmwJ6IJ
OqX/lI4vE8mXxqHXny1Bcd4x6z0YPBYFnip2yDdzeS/CNC1zQE7FB2aJhRgD2a4l
O+chw2ttFVRTWZK1G8o/aQIDAQABoxAwDjAMBgNVHRMBAf8EAjAAMA0GCSqGSIb3
DQEBCwUAA4ICAQCanC1uhx4k7Kq4L3nCkijs9z938coVyWgna6Xjyu2cGtmlWM4u
+eDorRWQoFDpdl7nRU01a+BEz4xCMVIGNtKklOdPxuqEoq6VF4IaS9efP2rwgd9B
7nR/E+NlbmDjEZynb87pVAVdoA42yXyNDdRKsDMOJPtM6jDMUHH+qQeSwKJQgS8v
I6NikXC4+WzY85QieMJRWWfdLxK27kGThwOzMbo5CKq8o5ChAtwlIvDLN0uzYtrw
u/5EfWieXL3cN8S5vbliCTUVWDRlgzdM2lHeIDT4aVktsgUiFbTgbSmZfOHFQ60b
SC+jy0zFqOXMEpVWbIYd+JOhuQsJUppLef8f2tQW0LPwPAj+CR6lGt27OXNzo/2h
028uKz0Z9UOUqV9xi2BgTLLRFbi0lfj1Z60Dmr0Ykeu4Le3hJsBscUBoVzH3Ybnr
ci59DhidZ1qkDGa39Ue7Pz9RECACXY8HuqNZVjDdc7cEeIuoQH5vIBg5sqUsYjRg
oDGhdeUddy80fQV1f3HnDUKZ9EZ1d4ikirisLFHgCxlDuBkgH5adhwjUWBxrZM4a
VUrlkAH9vF0Z3v1ZXBSsXJNyNn2QDf42OqmNLmwTiIj+aMd11eGaxZbxpMQ2avQb
OTFloX5cVL/6Ln+EEHstrIsfZTUohWfVyvBiICFnet6opDtevgVMZ1hyjg==
-----END CERTIFICATE-----""" # 证书内容
    casdoor_org_name = "user"
    casdoor_application_name = "ozon_spider"
    casdoor_redirect_url = "http://localhost:5173/index.html" # 登录回调地址 (显式指向 index.html 以避免 404 错误)

    ##
    # 函数
    ##
    def init(self):
        '''初始化'''
        # 获取电脑上的目录
        self.getDir()

    def getDir(self):
        '''获取电脑上的目录'''
        if Config.appSystem == 'Darwin':
            # Mac系统
            user = getpass.getuser()
            downloadDir = os.path.join('/', 'Users', user, 'Downloads')
            appDataDir = os.path.join('/', 'Users', user, 'Library', 'Application Support', Config.appPackage+'.'+Config.appNameEN)
        elif Config.appSystem == 'Windows':
            # win系统
            downloadDir = os.path.join(os.getenv('USERPROFILE'), 'Downloads')
            appDataDir = os.path.join(os.getenv('APPDATA'), Config.appPackage+'.'+Config.appNameEN)
        elif Config.appSystem == 'Linux':
            # linux系统
            downloadDir = os.path.join(os.getenv('HOME'), 'Downloads')
            appDataDir = os.path.join(os.getenv('HOME'), '.'+Config.appPackage+'.'+Config.appNameEN)
        if not os.path.isdir(appDataDir):
            os.mkdir(appDataDir)
        Config.appDataDir = appDataDir    # 电脑上可持久使用的隐藏目录
        Config.downloadDir = downloadDir    # 电脑上的下载目录
