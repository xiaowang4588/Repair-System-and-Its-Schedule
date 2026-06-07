"""
增强缓存管理器
支持 TTL 过期、文件修改时间检测、后台刷新、降级兜底。
"""
import threading
import time
import logging
import os
from typing import Optional
import pandas as pd

import config
from datasource.empty_classroom_query import create_query_system

logger = logging.getLogger(__name__)


class CacheManager:
    """
    增强缓存，支持：
    - TTL 过期（适用于 API 数据源）
    - 文件修改时间检测（适用于 Excel 数据源，向后兼容）
    - 后台刷新（在 TTL 到期前主动更新）
    - 降级兜底（刷新失败时继续提供旧数据）
    """

    def __init__(self, data_source, ttl_seconds: int = None,
                 background_refresh: bool = None,
                 fallback_to_stale: bool = None):
        self._data_source = data_source
        self._ttl = ttl_seconds if ttl_seconds is not None else config.CACHE_TTL_SECONDS
        self._background_refresh = background_refresh if background_refresh is not None else config.CACHE_BACKGROUND_REFRESH
        self._fallback_to_stale = fallback_to_stale if fallback_to_stale is not None else config.CACHE_FALLBACK_TO_STALE

        self._df: Optional[pd.DataFrame] = None
        self._query_system = None
        self._lock = threading.RLock()  # 可重入锁，避免 get_query_system 内调用 get_df 时死锁
        self._last_load_time: float = 0
        self._last_error: Optional[str] = None

        # Excel 数据源：记录文件修改时间
        self._file_mtime: float = 0

        # Bug5 修复: 请求路径的冷却时间，避免 _last_load_time=0 时每次请求都触发重载
        self._last_fail_time: float = 0
        self._fail_cooldown: float = 5.0  # 失败后 5 秒内不再重试

        # 后台异步重载状态
        self._async_reloading: bool = False
        self._async_reload_started: float = 0
        self._async_reload_result: Optional[bool] = None
        self._async_lock = threading.Lock()

        # 初始加载
        self._load_data()

        # 启动后台刷新线程
        if self._background_refresh:
            self._start_background_refresh()

    def _is_expired(self) -> bool:
        """检查缓存是否过期"""
        # TTL 检查
        if time.time() - self._last_load_time > self._ttl:
            return True

        # Excel 数据源：检查文件修改时间
        if hasattr(self._data_source, 'excel_path'):
            try:
                mtime = os.path.getmtime(self._data_source.excel_path)
                if mtime > self._file_mtime:
                    return True
            except OSError:
                # Bug7 修复: 文件不存在时视为过期（而非静默忽略）
                return True

        return False

    def _load_data(self, raise_on_error: bool = False) -> bool:
        """
        从数据源加载最新数据
        :param raise_on_error: 是否在失败时抛出异常（用于后台刷新线程的退避机制）
        """
        try:
            df = self._data_source.load()

            # Bug4 修复: 对 Excel 数据源增加重试（Windows 文件锁场景）
            if hasattr(self._data_source, 'excel_path') and self._data_source.excel_path:
                if df.empty and os.path.exists(self._data_source.excel_path):
                    # 文件存在但读出来是空的，可能是文件锁，重试
                    for retry in range(3):
                        time.sleep(0.5)
                        df = self._data_source.load()
                        if not df.empty:
                            break

            # 如果是空 DataFrame，添加必需的列
            if df.empty and '星期几' not in df.columns:
                df = pd.DataFrame(columns=[
                    '星期几', '上课节次', '上课地点', '课程名称',
                    '姓名', '教工号', '开课学院', '教学班组成', '上课时间'
                ])

            # 验证必需列是否存在
            required_cols = ['星期几', '上课节次', '上课地点', '课程名称', '姓名', '教工号']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"数据源缺少必需列: {', '.join(missing_cols)}")

            # 添加小写索引列（从原 app.py DataCache 提取，保持完全一致）
            df["_weekday_str"] = df["星期几"].astype(str).str.strip()
            df["_section_lower"] = df["上课节次"].astype(str).str.lower()
            df["_classroom_lower"] = df["上课地点"].astype(str).str.lower()
            df["_course_lower"] = df["课程名称"].astype(str).str.lower()
            df["_teacher_lower"] = df["姓名"].astype(str).str.lower()
            df["_teacher_id_lower"] = df["教工号"].astype(str).str.lower()

            self._df = df
            self._last_load_time = time.time()
            self._last_error = None
            self._last_fail_time = 0  # 成功后重置失败时间

            # 记录 Excel 文件修改时间
            if hasattr(self._data_source, 'excel_path') and self._data_source.excel_path:
                try:
                    self._file_mtime = os.path.getmtime(self._data_source.excel_path)
                except OSError:
                    pass

            # 重建空教室查询系统
            self._query_system = create_query_system(self._df)

            logger.info(f"数据加载成功 [来源: {self._data_source.get_source_name()}], "
                        f"记录数: {len(df)}")
            return True

        except Exception as e:
            self._last_error = str(e)
            self._last_fail_time = time.time()  # 记录失败时间
            logger.error(f"数据加载失败: {e}")
            if self._df is None:
                self._df = pd.DataFrame(columns=[
                    '星期几', '上课节次', '上课地点', '课程名称',
                    '姓名', '教工号', '开课学院', '教学班组成', '上课时间',
                    '_weekday_str', '_section_lower', '_classroom_lower',
                    '_course_lower', '_teacher_lower', '_teacher_id_lower'
                ])
            if raise_on_error:
                raise
            return False

    def get_df(self) -> pd.DataFrame:
        """获取缓存的 DataFrame，过期时自动刷新"""
        with self._lock:
            # Bug5 修复: 失败冷却期内不重试，避免每次请求都触发失败的加载
            now = time.time()
            need_reload = self._is_expired() or self._df is None
            in_cooldown = (self._last_fail_time > 0 and
                           now - self._last_fail_time < self._fail_cooldown)

            if need_reload and not in_cooldown:
                if self._fallback_to_stale and self._df is not None:
                    # 有旧数据时，尝试刷新但失败则继续使用旧数据
                    try:
                        self._load_data(raise_on_error=True)
                    except Exception:
                        logger.warning("刷新失败，继续使用旧数据")
                else:
                    # 无旧数据时，必须加载成功
                    self._load_data(raise_on_error=False)
            return self._df.copy() if self._df is not None else pd.DataFrame()

    def get_query_system(self):
        """获取空教室查询系统"""
        with self._lock:
            if self._is_expired():
                self.get_df()
            return self._query_system

    def reload(self) -> bool:
        """
        强制重新加载。
        Bug3 修复: 先创建新数据源成功后再替换，失败时保留旧数据源。
        返回 True 表示加载成功，False 表示失败。
        """
        with self._lock:
            # 先尝试创建新数据源
            try:
                from datasource.data_source import create_data_source
                new_source = create_data_source()
            except Exception as e:
                logger.warning(f"重新创建数据源失败: {e}")
                # Bug3: 创建失败时，仍然用旧数据源尝试加载，但返回失败状态
                self._last_load_time = 0
                self._file_mtime = 0
                self._load_data(raise_on_error=False)
                return False

            # 创建成功，替换数据源
            self._data_source = new_source
            self._last_load_time = 0
            self._file_mtime = 0
            success = self._load_data(raise_on_error=False)
            return success

    def reload_async(self) -> bool:
        """
        在后台线程中异步重新加载数据（先创建新数据源，再加载）。
        返回 True 表示后台线程已启动，False 表示已有重载在进行中。
        使用 get_processing_status() 轮询进度。
        """
        with self._async_lock:
            if self._async_reloading:
                logger.info("后台重载已在进行中，跳过")
                return False
            self._async_reloading = True
            self._async_reload_started = time.time()
            self._async_reload_result = None

        def _bg_reload():
            try:
                # 先尝试创建新数据源（与 reload() 逻辑一致）
                try:
                    from datasource.data_source import create_data_source
                    new_source = create_data_source()
                    with self._lock:
                        self._data_source = new_source
                        self._last_load_time = 0
                        self._file_mtime = 0
                except Exception as e:
                    logger.warning(f"后台重载: 创建新数据源失败 ({e})，使用旧数据源")

                self._load_data(raise_on_error=False)
                with self._async_lock:
                    self._async_reload_result = True
            except Exception as e:
                logger.error(f"后台重载异常: {e}")
                with self._async_lock:
                    self._async_reload_result = False
            finally:
                with self._async_lock:
                    self._async_reloading = False

        thread = threading.Thread(target=_bg_reload, daemon=True, name="cache-bg-reload")
        thread.start()
        logger.info("后台重载已启动")
        return True

    def get_processing_status(self) -> dict:
        """返回后台处理状态（供前端轮询）"""
        with self._async_lock:
            status = {
                "ready": not self._async_reloading,
                "processing": self._async_reloading,
                "started_at": self._async_reload_started,
                "elapsed_seconds": round(time.time() - self._async_reload_started, 1) if self._async_reloading else 0,
            }
        with self._lock:
            status["records"] = len(self._df) if self._df is not None else 0
            status["last_error"] = self._last_error
            status["source_available"] = self._data_source.is_available()
        return status

    def get_status(self) -> dict:
        """返回缓存状态，用于监控"""
        # Bug9 修复: 加锁访问共享状态
        with self._lock:
            result = {
                "source": self._data_source.get_source_name(),
                "records": len(self._df) if self._df is not None else 0,
                "last_load": self._last_load_time,
                "ttl": self._ttl,
                "expired": self._is_expired(),
                "last_error": self._last_error,
                "source_available": self._data_source.is_available(),
            }
        # 附加异步重载状态
        with self._async_lock:
            result["async_reloading"] = self._async_reloading
        return result

    def test_connection(self) -> bool:
        """测试数据源连接是否正常"""
        with self._lock:
            try:
                if not self._data_source.is_available():
                    return False

                # 如果缓存中已有数据，直接返回成功（避免重复读文件）
                if self._df is not None and not self._df.empty:
                    return True

                # 缓存为空，尝试加载（带重试，兼容 Windows 文件锁）
                for attempt in range(3):
                    try:
                        df = self._data_source.load()
                        if df is not None and not df.empty:
                            return True
                    except Exception:
                        pass
                    if attempt < 2:
                        time.sleep(0.5)

                return False
            except Exception as e:
                logger.error(f"连接测试失败: {e}")
                return False

    def _start_background_refresh(self):
        """启动后台守护线程，在 TTL 到期前主动刷新，支持指数退避"""
        INITIAL_BACKOFF = 1
        MAX_BACKOFF = 60
        MAX_CONSECUTIVE_FAILS = 10

        def refresh_loop():
            consecutive_fails = 0
            backoff = INITIAL_BACKOFF

            while True:
                time.sleep(self._ttl * 0.8)
                try:
                    logger.info("后台刷新触发")
                    with self._lock:
                        self._load_data(raise_on_error=True)
                    if consecutive_fails > 0:
                        logger.info(f"后台刷新恢复正常，连续失败 {consecutive_fails} 次后恢复")
                    consecutive_fails = 0
                    backoff = INITIAL_BACKOFF
                except Exception as e:
                    consecutive_fails += 1
                    logger.error(f"后台刷新失败 (连续第{consecutive_fails}次): {e}")

                    if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                        logger.warning(f"后台刷新连续失败 {consecutive_fails} 次，数据源可能不可用")

                    backoff = min(backoff * 2, MAX_BACKOFF)
                    logger.info(f"后台刷新退避 {backoff} 秒后重试")
                    time.sleep(backoff)

        t = threading.Thread(target=refresh_loop, daemon=True)
        t.start()
