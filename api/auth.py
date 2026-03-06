import functools

def auth_required(func):
    '''登录验证装饰器'''
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # 1. 首先检查本地标记
        if not getattr(self, '_is_authenticated', False):
            print(f"警告: 未经身份验证尝试调用接口 {func.__name__}")
            return {"success": False, "message": "请先登录以访问此功能", "code": 401}
            
        # 2. 调用在线验证逻辑（仅当 self 具有 check_token_valid 属性时，例如在 API 类中）
        if hasattr(self, 'check_token_valid'):
            if not self.check_token_valid():
                print(f"警告: Token 已失效，拒绝访问接口 {func.__name__}")
                return {"success": False, "message": "登录已过期，请重新登录", "code": 401}
                
        return func(self, *args, **kwargs)
    return wrapper
