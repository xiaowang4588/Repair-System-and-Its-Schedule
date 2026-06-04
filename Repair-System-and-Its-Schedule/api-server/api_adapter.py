"""
青果教务系统 API 适配器
对接青果教务管理系统，获取课表数据并转换为标准 DataFrame。

支持两种认证方式：
  1. 账号密码登录（推荐，自动维护会话）
  2. 手动提供 Cookie（备用，需要定期更新）

API 信息：
  - 地址：POST /jwglxt/cdjy/cdjy_cxSfkfyuy.html?gnmkdm=N2155
  - 认证：VPN 网关 + 教务系统登录
  - 分页：每页15条，需翻页获取全部
"""
import sys
import io
import re
import time
import logging
import pandas as pd
import requests
from data_source import DataSource
import config

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

# 常量
API_BASE_URL = "https://http-10-252-6-31-80.vpn.cqytxy.edu.cn"
API_PATH = "/jwglxt/cdjy/cdjy_cxSfkfyuy.html"
API_PARAMS = {"gnmkdm": "N2155"}
LOGIN_PATH = "/jwglxt/xtgl/login_slogin.html"


class QingguoSession:
    """
    管理与青果教务系统的认证会话。
    支持两种认证方式：
      1. 账号密码登录（自动维护会话，推荐）
      2. 手动提供 Cookie（备用）
    """

    def __init__(self, base_url: str, username: str = "", password: str = "",
                 webvpn_token: str = "", jsessionid: str = ""):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.webvpn_token = webvpn_token
        self._manual_jsessionid = jsessionid

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
        })

        # 设置 VPN 令牌
        if webvpn_token:
            self.session.cookies.set('webvpn-token', webvpn_token,
                                     domain='http-10-252-6-31-80.vpn.cqytxy.edu.cn')

        self._logged_in = False
        self._last_login_time = 0
        self._login_ttl = 7200  # 2小时后重新登录

    def ensure_authenticated(self) -> bool:
        """确保已认证，优先用账号密码登录，备用 Cookie"""
        # 如果有账号密码，优先使用登录方式
        if self.username and self.password:
            if not self._logged_in or (time.time() - self._last_login_time > self._login_ttl):
                return self._login()
            return True

        # 备用：使用手动提供的 Cookie
        if self.webvpn_token:
            if self._manual_jsessionid:
                self.session.cookies.set('JSESSIONID', self._manual_jsessionid,
                                         domain='http-10-252-6-31-80.vpn.cqytxy.edu.cn')
            return True

        return False

    def _login(self) -> bool:
        """使用账号密码登录教务系统"""
        try:
            logger.info(f"正在登录教务系统，账号: {self.username}")

            # 第一步：访问登录页面，获取 csrftoken
            login_url = self.base_url + LOGIN_PATH
            resp = self.session.get(login_url, verify=False, timeout=15, allow_redirects=True)

            if resp.status_code != 200:
                logger.error(f"访问登录页面失败: {resp.status_code}")
                return False

            # 提取 csrftoken
            csrftoken = self._extract_csrftoken(resp.text)
            if not csrftoken:
                logger.warning("未找到 csrftoken，尝试不带 token 登录")

            # 第二步：提交登录表单
            login_data = {
                'yhm': self.username,
                'mm': self.password,
            }
            if csrftoken:
                login_data['csrftoken'] = csrftoken

            resp = self.session.post(login_url, data=login_data, verify=False, timeout=15, allow_redirects=True)

            # 判断登录是否成功
            if 'index_initMenu' in resp.text or 'index_initMenu' in resp.url:
                self._logged_in = True
                self._last_login_time = time.time()
                logger.info("教务系统登录成功")
                return True
            elif '用户名或密码' in resp.text or '密码错误' in resp.text:
                logger.error("登录失败：用户名或密码错误")
                return False
            elif '验证码' in resp.text:
                logger.error("登录失败：需要验证码（暂不支持）")
                return False
            else:
                # 检查是否跳转到了主页
                if '/xtgl/index_initMenu' in resp.url:
                    self._logged_in = True
                    self._last_login_time = time.time()
                    logger.info("教务系统登录成功（通过重定向判断）")
                    return True
                logger.warning(f"登录结果不确定，当前URL: {resp.url}")
                # 尝试访问主页验证
                return self._verify_login()

        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False

    def _verify_login(self) -> bool:
        """验证是否已登录"""
        try:
            resp = self.session.get(
                self.base_url + '/jwglxt/xtgl/index_initMenu.html',
                verify=False, timeout=10, allow_redirects=False
            )
            if resp.status_code == 200:
                self._logged_in = True
                self._last_login_time = time.time()
                return True
        except Exception:
            pass
        return False

    def _extract_csrftoken(self, html: str) -> str:
        """从登录页面提取 csrftoken"""
        patterns = [
            r'name="csrftoken"\s+value="([^"]+)"',
            r'csrftoken["\s:=]+["\']([a-f0-9]+)["\']',
            r'<input[^>]*name="csrftoken"[^>]*value="([^"]+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return ""

    def get(self, url: str, **kwargs):
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 30)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 30)
        return self.session.post(url, **kwargs)


class QingguoDataSource(DataSource):
    """
    青果教务系统数据源。
    通过 API 获取课表数据，转换为标准 DataFrame。
    """

    def __init__(self, base_url: str = "", username: str = "", password: str = "",
                 webvpn_token: str = "", jsessionid: str = "",
                 schedule_url: str = "", semester_id: str = "",
                 use_scraper: bool = False, headless: bool = True):
        self.base_url = base_url or API_BASE_URL
        self.session = QingguoSession(
            base_url=self.base_url,
            username=username,
            password=password,
            webvpn_token=webvpn_token,
            jsessionid=jsessionid,
        )

    def is_available(self) -> bool:
        return self.session.ensure_authenticated()

    def get_source_name(self) -> str:
        return "青果教务系统"

    def load(self) -> pd.DataFrame:
        """从青果系统获取全部课表数据，转换为标准 DataFrame"""
        if not self.session.ensure_authenticated():
            raise RuntimeError("无法登录教务系统，请检查账号密码或 VPN 令牌")

        logger.info("开始从青果系统获取数据...")
        all_items = self._fetch_all_items()

        if not all_items:
            raise RuntimeError("无法从青果系统获取数据")

        df = self._normalize_to_dataframe(all_items)
        logger.info(f"数据获取完成，共 {len(df)} 条记录")
        return df

    def _fetch_all_items(self) -> list:
        """翻页获取全部数据"""
        all_items = []
        page = 1
        page_size = 500

        while True:
            logger.info(f"正在获取第 {page} 页数据...")
            items = self._fetch_page(page, page_size)
            if not items:
                break
            all_items.extend(items)
            logger.info(f"第 {page} 页获取 {len(items)} 条，累计 {len(all_items)} 条")

            if len(items) < page_size:
                break
            page += 1
            time.sleep(0.5)

        return all_items

    def _fetch_page(self, page: int, page_size: int) -> list:
        """获取单页数据"""
        data = {
            'doType': 'query',
            'gnmkdm': 'N2155',
            'xqh_id': config.QINGGUO_XQH_ID or 'C67E548C4B4553FFE0530100007F06AD',
            'xnm': config.QINGGUO_XNM or '2025',
            'xqm': config.QINGGUO_XQM or '12',
            'cdlb_id': '', 'cdejlb_id': '', 'qszws': '', 'jszws': '',
            'cdmc': '', 'lh': '', 'jyfs': '0', 'cdjylx': '', 'sfbhkc': '',
            'zcd': '', 'xqj': '', 'jcd': '',
            '_search': 'false',
            'nd': str(int(time.time() * 1000)),
            'queryModel.showCount': str(page_size),
            'queryModel.currentPage': str(page),
            'queryModel.sortName': 'cdbh',
            'queryModel.sortOrder': 'asc',
            'time': '2',
        }

        try:
            url = f"{self.base_url}{API_PATH}"
            resp = self.session.post(url, data=data, params=API_PARAMS)
            resp.raise_for_status()
            result = resp.json()
            if isinstance(result, dict):
                return result.get('items', [])
            return []
        except Exception as e:
            logger.error(f"获取第 {page} 页数据失败: {e}")
            return []

    def _normalize_to_dataframe(self, items: list) -> pd.DataFrame:
        """将 API 返回的教室数据转换为标准 DataFrame"""
        records = []
        for item in items:
            cdmc = item.get('cdmc', '')
            jxlmc = item.get('jxlmc', '')
            cdlbmc = item.get('cdlbmc', '')
            kszws = item.get('kszws1', '0')
            xqmc = item.get('xqmc', '')

            full_classroom = f"{jxlmc}{cdmc}" if jxlmc and cdmc else cdmc

            records.append({
                '星期几': '',
                '上课节次': '',
                '上课地点': full_classroom,
                '课程名称': '',
                '姓名': '',
                '教工号': '',
                '开课学院': '',
                '教学班组成': '',
                '上课时间': '',
                '_教室类型': cdlbmc,
                '_楼栋': jxlmc,
                '_座位数': kszws,
                '_校区': xqmc,
            })

        return pd.DataFrame(records)

    def query_empty_classrooms(self, weekday: str, sections: list, week: str = '') -> list:
        """查询指定时间的空教室"""
        if not self.session.ensure_authenticated():
            return []

        results = []
        for section in sections:
            data = {
                'doType': 'query',
                'gnmkdm': 'N2155',
                'xqh_id': config.QINGGUO_XQH_ID or 'C67E548C4B4553FFE0530100007F06AD',
                'xnm': config.QINGGUO_XNM or '2025',
                'xqm': config.QINGGUO_XQM or '12',
                'cdlb_id': '', 'cdejlb_id': '', 'qszws': '', 'jszws': '',
                'cdmc': '', 'lh': '', 'jyfs': '0', 'cdjylx': '', 'sfbhkc': '',
                'zcd': week, 'xqj': weekday, 'jcd': section,
                '_search': 'false',
                'nd': str(int(time.time() * 1000)),
                'queryModel.showCount': '500',
                'queryModel.currentPage': '1',
                'queryModel.sortName': 'cdbh',
                'queryModel.sortOrder': 'asc',
                'time': '2',
            }

            try:
                url = f"{self.base_url}{API_PATH}"
                resp = self.session.post(url, data=data, params=API_PARAMS)
                resp.raise_for_status()
                result = resp.json()
                if isinstance(result, dict):
                    items = result.get('items', [])
                    for item in items:
                        cdmc = item.get('cdmc', '')
                        jxlmc = item.get('jxlmc', '')
                        results.append({
                            'classroom': f"{jxlmc}{cdmc}" if jxlmc and cdmc else cdmc,
                            'building': jxlmc,
                            'classroom_type': item.get('cdlbmc', ''),
                            'sections_available': [section],
                            'sections_occupied': [],
                        })
            except Exception as e:
                logger.error(f"查询空教室失败: {e}")

        return results
