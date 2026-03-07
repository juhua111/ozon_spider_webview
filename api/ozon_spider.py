# -*- coding: utf-8 -*-
"""
Created on 2025-03-14 14:39:25
---------
@summary:
---------
@author: Administrator
"""

import feapder
from DrissionPage import ChromiumPage,ChromiumOptions
from feapder import Request,Response,Item,UpdateItem
from feapder.utils.log import log
import re
from datetime import datetime
import threading
import json
import random
from DrissionPage.common import make_session_ele
from DrissionPage._elements.session_element import SessionElement
from DrissionPage.errors import ElementNotFoundError


import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class OzonProduct:
    """Ozon商品数据模型"""
    sku: int
    name: str
    current_price: str
    original_price: str
    discount: str
    rating: str
    review_count: str
    product_url: str
    image_urls: List[str]
    is_in_cart: bool
    cart_quantity: int
    is_favorite: bool
    is_adult: bool
    tracking_key: str
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, indent=2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class OzonProductParser:
    """Ozon商品卡片解析器"""
    
    def __init__(self, json_data: Dict):
        self.data = json_data
        self.product: Optional[OzonProduct] = None
    
    def _extract_price_info(self) -> tuple:
        """提取价格信息"""
        price_info = {}
        
        for item in self.data.get('mainState', []):
            if item.get('type') == 'priceV2':
                prices = item['priceV2']['price']
                for price in prices:
                    if price['textStyle'] == 'PRICE':
                        price_info['current_price'] = price['text']
                    elif price['textStyle'] == 'ORIGINAL_PRICE':
                        price_info['original_price'] = price['text']
                
                price_info['discount'] = item['priceV2'].get('discount', '')
                break
        
        return (
            price_info.get('current_price', ''),
            price_info.get('original_price', ''),
            price_info.get('discount', '')
        )
    
    def _extract_name(self) -> str:
        """提取商品名称"""
        for item in self.data.get('mainState', []):
            if item.get('type') == 'textAtom' and item.get('id') == 'name':
                return item['textAtom'].get('text', '')
        return ''
    
    def _extract_rating_info(self) -> tuple:
        """提取评分和评论数"""
        rating = ''
        review_count = ''
        
        for item in self.data.get('mainState', []):
            if item.get('type') == 'labelList':
                items = item['labelList'].get('items', [])
                for label in items:
                    # 优化星级获取方式：优先根据 titleColor: "textPremium" 判断，通常带有这个属性的是星级
                    if label.get('titleColor') == 'textPremium':
                        rating = label.get('title', '').strip()
                    elif 'star' in label.get('icon', {}).get('image', '').lower():
                        rating = label.get('title', '').strip()
                    elif 'dialog' in label.get('icon', {}).get('image', '').lower():
                        review_count = label.get('title', '').strip()
        
        return rating, review_count
    
    def _extract_images(self) -> List[str]:
        """提取图片链接并清理空格"""
        image_urls = []
        
        items = self.data.get('tileImage', {}).get('items', [])
        for item in items:
            if item.get('type') == 'image':
                link = item['image'].get('link', '').strip()
                if link:
                    image_urls.append(link)
        
        return image_urls
    
    def _extract_product_url(self) -> str:
        """提取商品详情页链接"""
        link = self.data.get('action', {}).get('link', '')
        # 如果需要完整的URL，可以拼接域名
        if link and not link.startswith('http'):
            link = f"https://www.ozon.ru{link}"
        return link
    
    def _extract_cart_info(self) -> tuple:
        """提取购物车信息"""
        cart_button = self.data.get('multiButton', {}).get('ozonButton', {})
        
        if cart_button.get('type') == 'addToCart':
            cart_data = cart_button['addToCart']
            return (
                cart_data.get('inCartQuantity', 0) > 0,
                cart_data.get('inCartQuantity', 0)
            )
        
        return False, 0
    
    def _extract_favorite_info(self) -> bool:
        """提取收藏状态"""
        buttons = self.data.get('topRightButtons', [])
        for btn in buttons:
            if btn.get('type') == 'favoriteProductMoleculeV2':
                return btn['favoriteProductMoleculeV2'].get('isFav', False)
        return False
    
    def parse(self) -> OzonProduct:
        """解析商品数据"""
        current_price, original_price, discount = self._extract_price_info()
        name = self._extract_name()
        rating, review_count = self._extract_rating_info()
        image_urls = self._extract_images()
        product_url = self._extract_product_url()
        is_in_cart, cart_quantity = self._extract_cart_info()
        is_favorite = self._extract_favorite_info()
        
        self.product = OzonProduct(
            sku=self.data.get('sku', 0),
            name=name,
            current_price=current_price,
            original_price=original_price,
            discount=discount,
            rating=rating,
            review_count=review_count,
            product_url=product_url,
            image_urls=image_urls,
            is_in_cart=is_in_cart,
            cart_quantity=cart_quantity,
            is_favorite=is_favorite,
            is_adult=self.data.get('isAdult', False),
            tracking_key=self.data.get('trackingInfo', {}).get('click', {}).get('key', '')
        )
        
        return self.product


def clean_price_text(price_text: str) -> Dict:
    """
    清理价格文本，提取数字和货币符号
    
    示例: "269 ₽" -> {'amount': 269, 'currency': '₽', 'raw': '269 ₽'}
    """
    # 移除窄空格和其他空白字符
    cleaned = re.sub(r'[\u2009\s]+', '', price_text)
    
    # 提取数字
    amount_match = re.search(r'(\d+)', cleaned)
    amount = int(amount_match.group(1)) if amount_match else 0
    
    # 提取货币符号
    currency_match = re.search(r'[₽$€£¥]', cleaned)
    currency = currency_match.group(0) if currency_match else ''
    
    return {
        'amount': amount,
        'currency': currency,
        'raw': price_text
    }


def clean_review_count(review_text: str) -> int:
    """
    清理评论数文本，提取数字
    
    示例: "2 459 отзывов" -> 2459
    """
    # 移除空格和非数字字符
    cleaned = re.sub(r'[\u2009\s]+', '', review_text)
    number_match = re.search(r'(\d+)', cleaned)
    
    return int(number_match.group(1)) if number_match else 0


def extract_all_products_from_list(json_list: List[Dict]) -> List[Dict]:
    """
    从商品列表中提取所有商品信息
    
    适用于解析搜索结果页的多个商品卡片
    """
    products = []
    
    for item in json_list:
        parser = OzonProductParser(item)
        product = parser.parse()
        
        # 添加额外的清理数据
        product_dict = product.to_dict()
        product_dict['current_price_clean'] = clean_price_text(product.current_price)
        product_dict['original_price_clean'] = clean_price_text(product.original_price)
        product_dict['review_count_clean'] = clean_review_count(product.review_count)
        
        products.append(product_dict)
    
    return products

def cyrillic_to_latin(text):
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ы': 'y', 'э': 'e', 'ю': 'yu',
        'я': 'ya', ' ': '-'
    }
    return ''.join(mapping.get(c.lower(), c) for c in text)

def get_shops():
    from curl_cffi import requests
    with open('result.json', 'r', encoding='utf-8') as f:
        result = json.load(f)
    items = result['sections'][0]['items']
    shop_ids = []
    for item in items:
        id = item['key']
        text = item['title']['text']
        text = cyrillic_to_latin(text.lower())
        shop_ids.append(f'{id}')
    return shop_ids

js_script = '''
(async () => {
    const url = 'product_url&__rr=1';
    const options = {
    method: 'GET',
    headers: {
        accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        pragma: 'no-cache',
        priority: 'u=1, i',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0',
    }
    };

    try {
        const response = await fetch(url, options);
        const contentType = response.headers.get('content-type');
        if (!response.ok) {
            return {'error': `HTTP error! status: ${response.status}`};
        }
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        return {'error': error.message};
    }
})()
'''


class OzonSpider(feapder.AirSpider):

    __custom_setting__ = dict(
        ITEM_PIPELINES = [
            "api.pipline.BufferedPipeline"
        ],
        LOG_LEVEL = "INFO"
    )

    def __init__(self,base_url,browser:ChromiumPage,finish_event,max_page=820, api=None, end_callback=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.end_callback = end_callback
        self.lock = threading.Lock()
        self.session_id = random.random()

        #页面0产品 计数器
        self.zero_product_count = 0
        
        # 全局数据统计
        self.global_products_found = 0
        self.global_products_added = 0
        self.global_products_skipped = 0
        
        self.base_url = base_url
        self.browser = browser
        self.max_page = max_page
        self._finish_event = finish_event
        self.api = api
        self.tab = self.browser.new_tab()

        self.tab.listen.start('https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2')  
        self.tab.get(base_url)
        res = self.tab.listen.wait(count=1)
        prev_page = res.response.body.get('prevPage')
        #获取search_page_state
        if prev_page:
            self.search_page_state = prev_page.split('search_page_state=')[-1].split('&')[0]
        else:
            self.search_page_state = ''
 

        # self.tab = self.browser.new_tab('https://www.ozon.ru/seller/123huang-3048138/?1=1&layout_container=default&paginator_token=3618992')
        self.tab.wait(5)
        



    def start_requests(self):
        base_url = self.base_url
        #判断url是否有参数
        if '?' in base_url:
            url = '{}&layout_container=default&layout_page_index={}&opened=type&page={}&search_page_state={}'
        else:
            url = '{}?layout_container=default&layout_page_index={}&opened=type&page={}&search_page_state={}'
        urls = [url.format(base_url,page,page,self.search_page_state) for page in range(1,self.max_page)]
        # urls = [url.format(base_url,page) for page in range(1,2)]
        # urls = ['https://www.ozon.ru/highlight/tovary-iz-kitaya-935133/?category=14500&currency_price=200.000%3B116479.000&abt_att=1&layout_container=default&page=820']
        for i in urls:
            yield feapder.Request(i,pageNum=i.split('=')[-1],priority=urls.index(i))

    def parse(self, request, response):
        # 初始化计数器，防止变量未绑定错误

        add_product_count = 0
        
        # 添加详细的统计信息
        page_products_found = 0
        page_products_added = 0
        page_products_skipped = 0
        
        try:
            page = request.pageNum
            tab: SessionElement = response.tab
            data = tab.s_ele('@id^state-tileGridDesktop')
            data = json.loads(data.attr('data-state'))
            products = data['items']
            page_products_found = len(products)
            log.info(f'第{page}页发现{page_products_found}个商品')
            add_product_count += page_products_found
            add_num = 0
            for product in products:
                parser = OzonProductParser(product)
                product = parser.parse()
                
                # 添加额外的清理数据
                product_dict = product.to_dict()
                product_dict['current_price_clean'] = clean_price_text(product.current_price)
                product_dict['original_price_clean'] = clean_price_text(product.original_price)
                product_dict['review_count_clean'] = clean_review_count(product.review_count)
                item = Item()
                item.table_name = 'ppx_storage_var'
                item.sku = product_dict['sku']
                if item.sku == 0 or item.sku == '':
                    page_products_skipped += 1
                    continue
                item.sku = str(item.sku)
                item.category = 'default'
                item.title = product_dict['name']

                item.price = product_dict['current_price_clean']['amount']
                # 处理 star 字段为空的情况
                item.star = 0.0  # 默认值为 0.0
                item.api = self.api
                
                rating = product_dict['rating']
                if rating and rating != '':
                    try:
                        # 尝试将星级转换为浮点数
                        item.star = float(rating)
                    except (ValueError, TypeError):
                        # 如果转换失败，保持默认值 0.0
                        log.warning(f'无法将星级 "{rating}" 转换为浮点数')

                item.update_time = datetime.now()
                add_num += 1
                page_products_added += 1
                yield item  
            log.info(f'第{page}页添加{page_products_added}个商品，跳过{page_products_skipped}个无效商品')
            log.info(f'页面数据统计: 发现{page_products_found}个 → 添加{page_products_added}个 → 跳过{page_products_skipped}个')
            
            # 更新全局统计
            self.global_products_found += page_products_found
            self.global_products_added += page_products_added
            self.global_products_skipped += page_products_skipped
        except ElementNotFoundError:
            log.error(f'第{page}页元素未找到')
        except Exception as e:
            log.error(e)
            log.error(f'第{page}页失败')
        finally:
            if add_product_count == 0:
                self.zero_product_count += 1
                if self.zero_product_count > 5:
                    log.error(f'第{page}页连续5页无商品，停止爬虫')
                    self.stop_spider()
            self.tab.wait(2)

    def download_midware(self, request):
        
        # 1. 初始状态检查
        current_session = self.session_id
        
        # 检查是否需要同步页面状态（如果 session_id 已被其他线程更新）
        product_url = request.url.replace(self.base_url, self.tab.url)

        result = self.tab.run_js(js_script.replace('product_url', product_url), as_expr=True)
        
        # 2. 检查结果是否异常：不是 dict 或者 dict 中包含 error (如 403)
        is_bad_result = isinstance(result, dict)
        if type(result) == dict:
            is_bad_result = result.get('error') == 'HTTP error! status: 403'
        if is_bad_result:
            with self.lock:
                # 双重检查 session_id，避免重复刷新
                if self.session_id == current_session:
                    log.warning(f"[{current_session}] 检测到异常返回或人机验证: {result}，正在刷新页面并重试...")
                    self.tab.refresh()
                    self.tab.wait(5)
                    self.session_id = random.random()
                    log.info(f"页面已刷新，新 session_id: {self.session_id}")
                
                # 刷新后重新获取
                product_url = request.url.replace(self.base_url, self.tab.url)
                result = self.tab.run_js(js_script.replace('product_url', product_url), as_expr=True)

        # 3. 准备返回内容，确保传给 make_session_ele 的是字符串
        if isinstance(result, dict):
            content = json.dumps(result, ensure_ascii=False)
            response = Response.from_text(content)
        else:
            content = str(result)
            response = Response.from_text(content)
            
        # 确保 response.tab 获取的是解析后的页面对象
        try:
            response.tab: SessionElement = make_session_ele(content)
        except Exception as e:
            log.error(f"解析页面对象失败: {e}, content: {content[:100]}...")
            # 如果解析失败，创建一个空的元素避免后续 parse 崩溃
            response.tab = make_session_ele("<html></html>")
            
        return request, response

    def end_callback(self):
        # 爬虫结束时触发事件
        log.info(f'=== 爬虫任务完成 ===')
        log.info(f'全局数据统计:')
        log.info(f'  总发现商品数量: {self.global_products_found}')
        log.info(f'  总添加商品数量: {self.global_products_added}')
        log.info(f'  总跳过商品数量: {self.global_products_skipped}')
        log.info(f'  数据有效率: {self.global_products_added / self.global_products_found:.2%}')
        
        if self._finish_event:
            self._finish_event.set()
        
        if self.tab:
            try:
                self.tab.close()
            except:
                pass


if __name__ == "__main__":
    import schedule
    import time
    def run_spider():
        shop_ids = get_shops()
        print(len(shop_ids))
        all_category = {}
        for shop_id in shop_ids:
            all_category[shop_id] = f"https://www.ozon.ru/seller/{shop_id}/?1=1"

        co = ChromiumOptions()

        co.set_user_data_path(r"D:\browser data")
        co.set_browser_path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
        co.no_imgs(True)
        co.headless(False)
        co.set_local_port(59600)
        browser = ChromiumPage(co)

        status = False
        for category,base_url in all_category.items():
                
            finish_event = threading.Event()
            print(base_url)
            OzonSpider(base_url=base_url,category=category,browser=browser,finish_event=finish_event,max_page=820,thread_count=3).start()
            finish_event.wait()

        browser.quit()
    
    run_spider()