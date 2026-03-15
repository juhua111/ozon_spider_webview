from feapder.pipelines import BasePipeline
from typing import Dict, List, Tuple
from api.db.sql.models import PPXStorageVar
from pyapp.db.sql.db import DB
from sqlalchemy.dialects.sqlite import insert
import logging
import time

logger = logging.getLogger(__name__)

class Pipeline(BasePipeline):
    """
    pipeline 是单线程的，批量保存数据的操作，不建议在这里写网络请求代码，如下载图片等
    """

    def __init__(self, batch_size=100):
        """
        初始化 pipeline
        Args:
            batch_size: 批量提交的数据量，默认100条
        """
        self.batch_size = batch_size
        self.buffer = []  # 添加缓冲区

    def save_items(self, table, items: List[Dict]) -> bool:
        """
        保存数据 - 批量处理版本
        """
        if not items:
            return True

        # 如果是 ppx_storage_var 表，使用专用处理
        if table == "ppx_storage_var":
            return self._save_ppx_storage_var(items)
        else:
            # 其他表使用通用处理（可以根据需要扩展）
            return self._save_generic(table, items)

    def _save_ppx_storage_var(self, items: List[Dict]) -> bool:
        """
        专门处理 ppx_storage_var 表的批量 upsert
        """
        dbSession = None
        try:
            # 过滤和预处理数据
            valid_items = []
            skipped_items = []
            
            for item in items:
                # 提取数据
                sku = item.get('sku')
                price = item.get('price')
                star = item.get('star', 0.0)
                comment_count = item.get('comment_count', 0)
                
                # 数据验证
                if not sku:
                    skipped_items.append(f"SKU为空: {item}")
                    continue
                    
                if price is None or price == '':
                    skipped_items.append(f"价格无效 (SKU: {sku}): {price}")
                    continue
                
                # 处理 comment_count 字段
                if comment_count == '' or comment_count is None:
                    comment_count = 0
                else:
                    try:
                        comment_count = int(comment_count)
                    except (ValueError, TypeError):
                        logger.warning(f"comment_count转换失败 (SKU: {sku}): {comment_count}，使用默认值0")
                        comment_count = 0
                
                # 处理 star 字段
                if star == '' or star is None:
                    star = 0.0
                else:
                    try:
                        star = float(star)
                    except (ValueError, TypeError):
                        logger.warning(f"star转换失败 (SKU: {sku}): {star}，使用默认值0.0")
                        star = 0.0
                
                # 处理 price
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    skipped_items.append(f"价格转换失败 (SKU: {sku}): {price}")
                    continue
                
                valid_items.append({
                    'sku': sku,
                    'price': price,
                    'star': star,
                    'comment_count': comment_count,
                    'status': 0
                })
            
            # 记录跳过的数据
            if skipped_items:
                logger.warning(f"跳过了 {len(skipped_items)} 条无效数据: {skipped_items[:5]}...")
            
            if not valid_items:
                logger.warning("没有有效数据需要保存")
                return True
            
            # 批量 upsert 操作
            dbSession = DB.session()
            
            # 使用 SQLAlchemy 的批量插入
            for i in range(0, len(valid_items), self.batch_size):
                batch = valid_items[i:i + self.batch_size]
                
                # 构建 upsert 语句
                stmt = insert(PPXStorageVar).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['sku'],
                    set_={
                        'price': stmt.excluded.price,
                        'star': stmt.excluded.star,
                        'status': stmt.excluded.status
                    }
                )
                
                dbSession.execute(stmt)
                
                # 记录成功的数据
                for item in batch:
                    api = item.get('api')
                    if api and hasattr(api, 'log_message'):
                        api.log_message(f'成功处理数据: {item["sku"]}', 'info')
            
            # 提交事务
            dbSession.commit()
            
            logger.info(f"成功保存 {len(valid_items)} 条数据到 ppx_storage_var，跳过 {len(skipped_items)} 条")
            return True
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}", exc_info=True)
            if dbSession:
                dbSession.rollback()
            return False
            
        finally:
            if dbSession:
                dbSession.close()

    def _save_generic(self, table: str, items: List[Dict]) -> bool:
        """
        通用保存方法（可以根据需要扩展）
        """
        # TODO: 根据需要实现其他表的保存逻辑
        logger.info(f"通用保存方法 - 表: {table}, 数据量: {len(items)}")
        return True


# 增强版本：带缓冲区的 pipeline，可以累积数据再批量提交
class BufferedPipeline(Pipeline):
    """
    带缓冲区的 pipeline，可以累积数据再批量提交
    """
    
    def __init__(self, batch_size=100, flush_interval=10):
        """
        Args:
            batch_size: 批量提交的数据量
            flush_interval: 即使没达到batch_size，每隔多少秒强制提交一次
        """
        super().__init__(batch_size)
        self.flush_interval = flush_interval
        self.buffer = []
        self.last_flush_time = time.time()
        
    def save_items(self, table, items: List[Dict]) -> bool:
        """
        将数据加入缓冲区，达到条件时批量提交
        """
        if table != "ppx_storage_var":
            return super().save_items(table, items)
        
        self.buffer.extend(items)
        
        # 检查是否需要刷新缓冲区
        should_flush = (
            len(self.buffer) >= self.batch_size or 
            time.time() - self.last_flush_time >= self.flush_interval
        )
        
        if should_flush and self.buffer:
            result = self._save_ppx_storage_var(self.buffer)
            if result:
                self.buffer = []  # 清空缓冲区
                self.last_flush_time = time.time()
            return result
        
        return True
    
    def flush(self):
        """强制刷新缓冲区"""
        if self.buffer:
            return self._save_ppx_storage_var(self.buffer)
        return True
    
    def close(self):
        """关闭时刷新剩余数据"""
        self.flush()