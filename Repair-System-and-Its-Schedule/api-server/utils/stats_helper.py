"""
统计相关工具函数
从 repair_manager.py 提取，消除重复代码。
"""
import re
from datetime import datetime, timedelta


def filter_by_range(records: list, range_type: str) -> list:
    """按时间范围筛选记录"""
    now = datetime.now()
    if range_type == 'week':
        week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        return [r for r in records if r.get('report_time', '') >= week_start]
    elif range_type == 'month':
        month_start = now.strftime('%Y-%m-01')
        return [r for r in records if r.get('report_time', '') >= month_start]
    return records


def count_dict(records: list, key: str, top: int = 0) -> dict:
    """统计字段频次"""
    d = {}
    for r in records:
        v = str(r.get(key, '')).strip()
        if v:
            d[v] = d.get(v, 0) + 1
    d = dict(sorted(d.items(), key=lambda x: x[1], reverse=True))
    if top > 0:
        d = dict(list(d.items())[:top])
    return d


def trend_data(records: list, range_type: str) -> dict:
    """生成趋势数据（O(N+D) 单次遍历，替代 O(N×D) 逐天全量扫描）"""
    now = datetime.now()
    trend = {}
    if range_type == 'week':
        # 初始化 7 天
        for i in range(7):
            d = (now - timedelta(days=6 - i)).strftime('%Y-%m-%d')
            trend[d] = 0
        # 单次遍历累加
        for r in records:
            rt = r.get('report_time', '')[:10]
            if rt in trend:
                trend[rt] += 1
    elif range_type == 'month':
        # 初始化 30 天
        for i in range(30):
            d = (now - timedelta(days=29 - i)).strftime('%Y-%m-%d')
            trend[d] = 0
        # 单次遍历累加
        for r in records:
            rt = r.get('report_time', '')[:10]
            if rt in trend:
                trend[rt] += 1
    else:
        # 按教学周聚合
        import services.admin_config as admin_config
        semester_config = admin_config.get_semester_config()
        start_date_str = semester_config.get('start_date', '')
        current_week = admin_config.get_current_week()
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        if start_date:
            for r in records:
                rt = r.get('report_time', '')[:10]
                if rt:
                    try:
                        dt = datetime.strptime(rt, '%Y-%m-%d').date()
                        days_diff = (dt - start_date).days
                        if days_diff >= 0:
                            week_num = days_diff // 7 + 1
                            if week_num <= current_week:
                                key = f"第{week_num}周"
                                trend[key] = trend.get(key, 0) + 1
                    except ValueError:
                        pass
            for w in range(1, current_week + 1):
                key = f"第{w}周"
                if key not in trend:
                    trend[key] = 0
        def _wk_sort(item):
            try:
                return int(item[0].replace('第', '').replace('周', ''))
            except ValueError:
                return 0
        trend = dict(sorted(trend.items(), key=_wk_sort))
    return trend


def avg_process_days(records: list) -> float:
    """计算平均处理天数"""
    days = []
    for r in records:
        if r.get('status') in ('已处理', '已解决') and r.get('created_at') and r.get('updated_at'):
            try:
                c = datetime.strptime(r['created_at'][:10], '%Y-%m-%d')
                u = datetime.strptime(r['updated_at'][:10], '%Y-%m-%d')
                d = (u - c).days
                if d >= 0:
                    days.append(d)
            except ValueError:
                pass
    return round(sum(days) / len(days), 1) if days else 0


def extract_building(classroom: str) -> str:
    """从教室名称提取楼栋"""
    return re.sub(r'\d+$', '', classroom).strip()
