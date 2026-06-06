"""
抽象数据源层
定义统一的数据源接口，支持 Excel 和 API 两种实现。
所有数据源都输出相同的 pandas DataFrame（9列），下游代码无需改动。

配置优先级：config.json > 环境变量 > 默认值
"""
import os
import logging
import pandas as pd
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源抽象基类"""

    REQUIRED_COLS = [
        "星期几", "上课节次", "上课地点", "课程名称",
        "姓名", "教工号", "开课学院", "教学班组成", "上课时间"
    ]

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """
        加载课表数据，返回 DataFrame。
        返回的 DataFrame 必须包含以下列：
          星期几, 上课节次, 上课地点, 课程名称, 姓名, 教工号, 开课学院, 教学班组成, 上课时间
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查当前数据源是否可用"""
        pass

    def get_source_name(self) -> str:
        """数据源名称，用于日志"""
        return self.__class__.__name__


class ExcelDataSource(DataSource):
    """从本地 Excel 文件读取数据的数据源"""

    def __init__(self, excel_path: str, sheet_name: str = "Sheet1"):
        self.excel_path = excel_path
        self.sheet_name = sheet_name

    def is_available(self) -> bool:
        """检查数据源是否可用"""
        if not self.excel_path:
            return False
        return os.path.exists(self.excel_path)

    def load(self) -> pd.DataFrame:
        """加载 Excel 数据，文件不存在时抛出异常（让调用方知道加载失败）"""
        if not self.excel_path:
            logger.info("Excel 文件未配置，返回空数据")
            return pd.DataFrame(columns=self.REQUIRED_COLS)
        if not os.path.exists(self.excel_path):
            raise FileNotFoundError(f"Excel 文件不存在: {self.excel_path}")

        df = pd.read_excel(self.excel_path, sheet_name=self.sheet_name, header=0)
        df.columns = df.columns.str.strip()

        # 验证必需列是否存在
        missing_cols = [col for col in self.REQUIRED_COLS if col not in df.columns]
        if missing_cols:
            logger.warning(f"Excel 文件缺少必需列: {', '.join(missing_cols)}")
            # 对于缺少的列，填充空值
            for col in missing_cols:
                df[col] = ''

        for col in self.REQUIRED_COLS:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
        return df


def create_data_source() -> DataSource:
    """
    工厂函数：根据 config.json 创建对应的数据源。
    优先读取 config.json，不存在则读取环境变量。
    """
    import services.admin_config as admin_config
    import config

    ds_config = admin_config.get_datasource_config()
    ds_type = ds_config.get('type', 'excel')

    if ds_type == 'api':
        from datasource.api_adapter import QingguoDataSource
        api_conf = ds_config.get('api', {})
        return QingguoDataSource(
            base_url=api_conf.get('base_url', '') or config.QINGGUO_BASE_URL,
            username=api_conf.get('username', '') or config.QINGGUO_USERNAME,
            password=api_conf.get('password', '') or config.QINGGUO_PASSWORD,
            webvpn_token=api_conf.get('webvpn_token', '') or config.QINGGUO_WEBVPN_TOKEN,
            jsessionid=api_conf.get('jsessionid', '') or config.QINGGUO_JSESSIONID,
        )
    else:
        # Excel 模式：从 config.json 获取当前文件路径
        excel_path = admin_config.get_current_excel_path()
        if not excel_path:
            # 没有配置文件，返回空路径（系统启动后教师端上传）
            logger.info("未配置 Excel 文件，系统将以空数据启动，等待教师端上传课表")
            excel_path = ""
        return ExcelDataSource(excel_path, config.EXCEL_SHEET)
