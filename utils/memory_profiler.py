"""内存分析工具 - 用于追踪内存泄漏"""

import gc
import sys
import threading
import time
import tracemalloc
import logging
from typing import Optional, Dict, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class MemoryProfiler:
    """内存分析器 - 追踪内存使用和泄漏"""
    
    _instance: Optional['MemoryProfiler'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._snapshot_baseline = None
        self._interval = 10
    
    def start(self, interval: int = 10):
        """启动内存监控
        
        Args:
            interval: 输出间隔（秒）
        """
        if self._monitoring:
            return
        
        self._interval = interval
        self._monitoring = True
        self._stop_event.clear()
        
        # 启动 tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)  # 保存25帧调用栈
        
        # 保存基线快照
        self._snapshot_baseline = tracemalloc.take_snapshot()
        
        # 启动监控线程
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MemoryProfiler"
        )
        self._monitor_thread.start()
        logger.info(f"内存分析器已启动，每 {interval} 秒输出一次报告")
    
    def stop(self):
        """停止内存监控"""
        self._monitoring = False
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)
        tracemalloc.stop()
        logger.info("内存分析器已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            self._stop_event.wait(self._interval)
            if not self._stop_event.is_set():
                self._output_report()
    
    def _output_report(self):
        """输出内存报告"""
        try:
            # 强制GC
            gc.collect()
            
            # 清除 linecache 缓存，避免 tracemalloc 的开销影响结果
            import linecache
            linecache.clearcache()
            
            # 获取当前快照
            snapshot = tracemalloc.take_snapshot()
            
            # 过滤掉 tracemalloc 自身的内存和 linecache
            snapshot = snapshot.filter_traces((
                tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
                tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
                tracemalloc.Filter(False, tracemalloc.__file__),
                tracemalloc.Filter(False, "*linecache*"),
                tracemalloc.Filter(False, "*memory_profiler*"),
            ))
            
            # 按文件统计
            top_stats = snapshot.statistics('lineno')
            
            logger.info("=" * 60)
            logger.info("内存使用报告 (Top 15 by line)")
            logger.info("=" * 60)
            
            total_size = 0
            for stat in top_stats[:15]:
                total_size += stat.size
                logger.info(f"{stat.traceback.format()[0]}")
                logger.info(f"    大小: {stat.size / 1024:.1f} KB, 数量: {stat.count}")
            
            logger.info("-" * 60)
            logger.info(f"Top 15 总计: {total_size / 1024 / 1024:.2f} MB")
            
            # 与基线比较
            if self._snapshot_baseline:
                diff_stats = snapshot.compare_to(self._snapshot_baseline, 'lineno')
                
                # 只显示增长的
                growing = [s for s in diff_stats if s.size_diff > 0]
                growing.sort(key=lambda x: x.size_diff, reverse=True)
                
                if growing:
                    logger.info("")
                    logger.info("内存增长 Top 10 (相比启动时)")
                    logger.info("-" * 60)
                    for stat in growing[:10]:
                        logger.info(f"{stat.traceback.format()[0]}")
                        logger.info(f"    增长: +{stat.size_diff / 1024:.1f} KB, "
                                   f"数量变化: {stat.count_diff:+d}")
            
            # 对象统计
            self._output_object_stats()
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"内存报告生成失败: {e}")
    
    def _output_object_stats(self):
        """输出对象统计"""
        gc.collect()
        
        # 统计各类型对象数量
        type_counts: Dict[str, int] = Counter()
        type_sizes: Dict[str, int] = Counter()
        
        for obj in gc.get_objects():
            try:
                type_name = type(obj).__name__
                type_counts[type_name] += 1
                type_sizes[type_name] += sys.getsizeof(obj)
            except Exception:
                pass
        
        logger.info("")
        logger.info("对象数量 Top 10")
        logger.info("-" * 60)
        for type_name, count in type_counts.most_common(10):
            size = type_sizes[type_name]
            logger.info(f"  {type_name}: {count} 个, {size / 1024:.1f} KB")
        
        # 特别关注可能泄漏的类型
        suspicious_types = ['Thread', 'LogEntry', 'dict', 'list', 'str', 'Text', 'Container']
        logger.info("")
        logger.info("关注类型统计")
        logger.info("-" * 60)
        for type_name in suspicious_types:
            if type_name in type_counts:
                count = type_counts[type_name]
                size = type_sizes[type_name]
                logger.info(f"  {type_name}: {count} 个, {size / 1024:.1f} KB")
    
    def take_snapshot(self, label: str = ""):
        """手动获取快照并输出
        
        Args:
            label: 快照标签
        """
        logger.info(f"手动快照: {label}")
        self._output_report()


# 全局实例
_profiler: Optional[MemoryProfiler] = None


def start_memory_profiling(interval: int = 10):
    """启动内存分析
    
    Args:
        interval: 输出间隔（秒）
    """
    global _profiler
    _profiler = MemoryProfiler()
    _profiler.start(interval)


def stop_memory_profiling():
    """停止内存分析"""
    global _profiler
    if _profiler:
        _profiler.stop()


def take_memory_snapshot(label: str = ""):
    """手动获取内存快照
    
    Args:
        label: 快照标签
    """
    global _profiler
    if _profiler:
        _profiler.take_snapshot(label)
