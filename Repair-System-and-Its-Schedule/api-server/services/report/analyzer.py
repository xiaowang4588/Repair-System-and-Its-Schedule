"""
报告数据分析器 v2.0

专业级报告分析，包含：
  1. 周报分析（核心功能）- 详细到每一条记录
  2. 月报分析
  3. 学期报告分析
  4. 多维度对比分析
  5. 趋势预警分析
"""
import re
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from models import Repair
from peewee import fn

logger = logging.getLogger(__name__)


class ReportAnalyzer:
    """报告数据分析器"""

    def analyze(self, report_type: str, **kwargs) -> dict:
        """执行分析"""
        if report_type == 'weekly':
            week_number = kwargs.get('week_number', 0)
            return self._analyze_weekly(week_number)
        elif report_type == 'monthly':
            year = kwargs.get('year', datetime.now().year)
            month = kwargs.get('month', datetime.now().month)
            return self._analyze_monthly(year, month)
        else:
            semester = kwargs.get('semester', '')
            return self._analyze_semester(semester)

    # ============================================================
    # 周报分析（核心功能）
    # ============================================================

    def _analyze_weekly(self, week_number: int) -> dict:
        """周报分析 - 领导视角"""
        import services.admin_config as admin_config

        semester_config = admin_config.get_semester_config()
        start_date_str = semester_config.get('start_date', '')

        if not start_date_str:
            return {'error': '未设置学期开始日期，无法生成周报'}

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'error': '学期开始日期格式错误'}

        # 本周日期范围
        week_start = start_date + timedelta(weeks=week_number - 1)
        week_end = week_start + timedelta(days=6)
        today = datetime.now().date()

        # 上周日期范围
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start - timedelta(days=1)

        # 获取数据
        this_week_records = self._get_records_by_date_range(
            week_start.strftime('%Y-%m-%d'),
            week_end.strftime('%Y-%m-%d')
        )
        last_week_records = self._get_records_by_date_range(
            last_week_start.strftime('%Y-%m-%d'),
            last_week_end.strftime('%Y-%m-%d')
        )
        semester_records = self._get_semester_records(start_date_str)

        # 判断是否是当前周
        is_current_week = (week_start <= today <= week_end)

        return {
            'report_type': 'weekly',
            'week_number': week_number,
            'is_current_week': is_current_week,
            'date_range': {
                'start': week_start.strftime('%Y-%m-%d'),
                'end': week_end.strftime('%Y-%m-%d'),
                'label': f'第{week_number}周（{week_start.strftime("%m月%d日")} - {week_end.strftime("%m月%d日")}）'
            },
            # 核心指标
            'overview': self._get_week_overview(this_week_records, last_week_records),
            # 详细记录列表（领导看的）
            'records_detail': self._get_records_detail(this_week_records),
            # 按教室分组
            'repairs_by_classroom': self._get_repairs_by_classroom(this_week_records, semester_records),
            # 按楼栋分组
            'repairs_by_building': self._get_repairs_by_building(this_week_records),
            # 按故障类型分组
            'repairs_by_fault_type': self._get_repairs_by_fault_type(this_week_records),
            # 按处理人分组
            'repairs_by_handler': self._get_repairs_by_handler(this_week_records),
            # 按学院分组
            'repairs_by_college': self._get_repairs_by_college(this_week_records),
            # 按报修方式分组
            'repairs_by_method': self._get_repairs_by_method(this_week_records),
            # 按周几分组
            'repairs_by_weekday': self._get_repairs_by_weekday(this_week_records),
            # 周对比
            'week_comparison': self._get_week_comparison(this_week_records, last_week_records),
            # 故障分析
            'fault_analysis': self._analyze_faults(this_week_records),
            # 区域分析
            'area_analysis': self._analyze_areas(this_week_records, semester_records),
            # 时间分析
            'time_analysis': self._analyze_time(this_week_records),
            # 学院分析
            'college_analysis': self._analyze_colleges(this_week_records),
            # 处理效率分析
            'efficiency_analysis': self._analyze_efficiency(this_week_records),
            # 外聘教师分析
            'external_teacher_analysis': self._analyze_external_teachers(this_week_records),
            # 设备更换分析
            'device_replace_analysis': self._analyze_device_replace(this_week_records),
        }

    def _get_records_by_date_range(self, start_date: str, end_date: str) -> list:
        """获取日期范围内的报修记录"""
        records = Repair.select().where(
            (Repair.report_time >= start_date) &
            (Repair.report_time <= end_date + ' 23:59:59')
        ).order_by(Repair.report_time.desc())
        return [r.to_dict() for r in records]

    def _get_semester_records(self, start_date: str) -> list:
        """获取学期开始至今的所有记录"""
        records = Repair.select().where(
            Repair.report_time >= start_date
        ).order_by(Repair.report_time.desc())
        return [r.to_dict() for r in records]

    def _get_records_detail(self, records: list) -> list:
        """获取记录详细列表（领导看的）"""
        details = []
        for r in records:
            report_time = r.get('report_time', '')
            date_str = ''
            weekday_str = ''
            if report_time:
                try:
                    dt = datetime.strptime(report_time[:10], '%Y-%m-%d')
                    date_str = dt.strftime('%m/%d')
                    weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
                    weekday_str = weekday_map.get(dt.weekday(), '')
                except ValueError:
                    date_str = report_time[:10]

            details.append({
                'id': r.get('id', ''),
                'date': date_str,
                'weekday': weekday_str,
                'report_time': report_time,
                'classroom': r.get('classroom', ''),
                'fault_type': r.get('fault_type', ''),
                'fault_cause': r.get('fault_cause', ''),
                'status': r.get('status', ''),
                'reporter_name': r.get('reporter_name', ''),
                'reporter_college': r.get('reporter_college', ''),
                'is_external_teacher': r.get('is_external_teacher', False),
                'report_method': r.get('report_method', ''),
                'handler_name': r.get('handler_name', ''),
                'is_device_replaced': r.get('is_device_replaced', False),
                'device_replace_note': r.get('device_replace_note', ''),
                'solution': r.get('solution', ''),
                'completion_time': r.get('completion_time', ''),
                'notes': r.get('notes', ''),
            })
        return details

    def _get_week_overview(self, this_week: list, last_week: list) -> dict:
        """获取本周概览"""
        this_total = len(this_week)
        this_resolved = len([r for r in this_week if r.get('status') in ('已处理', '已解决')])
        this_pending = len([r for r in this_week if r.get('status') in ('未处理', '处理中')])
        this_processing = len([r for r in this_week if r.get('status') == '处理中'])
        this_unhandled = len([r for r in this_week if r.get('status') == '未处理'])
        this_rate = round(this_resolved / this_total * 100, 1) if this_total > 0 else 0

        last_total = len(last_week)
        last_resolved = len([r for r in last_week if r.get('status') in ('已处理', '已解决')])
        last_pending = len([r for r in last_week if r.get('status') in ('未处理', '处理中')])
        last_rate = round(last_resolved / last_total * 100, 1) if last_total > 0 else 0

        total_change = this_total - last_total
        total_change_rate = round(total_change / last_total * 100, 1) if last_total > 0 else (100 if this_total > 0 else 0)

        # 外聘教师数量
        external_count = len([r for r in this_week if r.get('is_external_teacher')])
        # 设备更换数量
        device_replace_count = len([r for r in this_week if r.get('is_device_replaced')])
        # 涉及教室数
        classrooms = set(r.get('classroom', '') for r in this_week if r.get('classroom'))
        # 涉及楼栋数
        buildings = set()
        for r in this_week:
            building = re.sub(r'\d+$', '', r.get('classroom', '')).strip()
            if building:
                buildings.add(building)
        # 涉及学院数
        colleges = set(r.get('reporter_college', '') for r in this_week if r.get('reporter_college'))

        return {
            'total_count': this_total,
            'resolved_count': this_resolved,
            'pending_count': this_pending,
            'processing_count': this_processing,
            'unhandled_count': this_unhandled,
            'resolved_rate': this_rate,
            'external_teacher_count': external_count,
            'device_replace_count': device_replace_count,
            'classroom_count': len(classrooms),
            'building_count': len(buildings),
            'college_count': len(colleges),
            'vs_last_week': {
                'last_total': last_total,
                'last_resolved': last_resolved,
                'last_pending': last_pending,
                'last_rate': last_rate,
                'total_change': total_change,
                'total_change_rate': total_change_rate,
                'resolved_change': this_resolved - last_resolved,
                'pending_change': this_pending - last_pending,
                'rate_change': round(this_rate - last_rate, 1),
            }
        }

    def _get_repairs_by_classroom(self, this_week: list, semester_records: list) -> dict:
        """按教室分组"""
        classroom_repairs = defaultdict(list)
        for r in this_week:
            classroom = r.get('classroom', '').strip()
            if classroom:
                report_time = r.get('report_time', '')
                date_str = ''
                weekday_str = ''
                if report_time:
                    try:
                        dt = datetime.strptime(report_time[:10], '%Y-%m-%d')
                        date_str = dt.strftime('%m/%d')
                        weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
                        weekday_str = weekday_map.get(dt.weekday(), '')
                    except ValueError:
                        date_str = report_time[:5]

                classroom_repairs[classroom].append({
                    'id': r.get('id', ''),
                    'date': date_str,
                    'weekday': weekday_str,
                    'fault_type': r.get('fault_type', ''),
                    'fault_cause': r.get('fault_cause', ''),
                    'status': r.get('status', ''),
                    'handler': r.get('handler_name', ''),
                    'reporter': r.get('reporter_name', ''),
                    'reporter_college': r.get('reporter_college', ''),
                    'is_external_teacher': r.get('is_external_teacher', False),
                    'report_method': r.get('report_method', ''),
                    'solution': r.get('solution', ''),
                    'is_device_replaced': r.get('is_device_replaced', False),
                })

        semester_classroom_count = defaultdict(int)
        for r in semester_records:
            classroom = r.get('classroom', '').strip()
            if classroom:
                semester_classroom_count[classroom] += 1

        result = {}
        sorted_classrooms = sorted(classroom_repairs.items(), key=lambda x: len(x[1]), reverse=True)

        for classroom, repairs in sorted_classrooms:
            semester_total = semester_classroom_count.get(classroom, 0)
            result[classroom] = {
                'count': len(repairs),
                'repairs': repairs,
                'semester_total': semester_total,
                'is_frequent': semester_total >= 5,
            }

        return result

    def _get_repairs_by_building(self, records: list) -> dict:
        """按楼栋分组"""
        building_repairs = defaultdict(list)
        for r in records:
            classroom = r.get('classroom', '')
            building = re.sub(r'\d+$', '', classroom).strip()
            if building:
                building_repairs[building].append(r)

        result = {}
        for building, repairs in sorted(building_repairs.items(), key=lambda x: len(x[1]), reverse=True):
            # 按故障类型统计
            fault_types = defaultdict(int)
            for r in repairs:
                ft = r.get('fault_type', '其他') or '其他'
                fault_types[ft] += 1

            # 按状态统计
            status_counts = defaultdict(int)
            for r in repairs:
                status_counts[r.get('status', '')] += 1

            result[building] = {
                'count': len(repairs),
                'fault_types': dict(fault_types),
                'status_counts': dict(status_counts),
            }

        return result

    def _get_repairs_by_fault_type(self, records: list) -> dict:
        """按故障类型分组"""
        fault_repairs = defaultdict(list)
        for r in records:
            ft = r.get('fault_type', '其他') or '其他'
            fault_repairs[ft].append(r)

        result = {}
        for ft, repairs in sorted(fault_repairs.items(), key=lambda x: len(x[1]), reverse=True):
            # 按楼栋统计
            buildings = defaultdict(int)
            for r in repairs:
                building = re.sub(r'\d+$', '', r.get('classroom', '')).strip()
                if building:
                    buildings[building] += 1

            # 主要故障原因
            causes = defaultdict(int)
            for r in repairs:
                cause = r.get('fault_cause', '').strip()
                if cause:
                    causes[cause[:20]] += 1

            result[ft] = {
                'count': len(repairs),
                'buildings': dict(buildings),
                'top_causes': dict(sorted(causes.items(), key=lambda x: x[1], reverse=True)[:5]),
            }

        return result

    def _get_repairs_by_handler(self, records: list) -> dict:
        """按处理人分组"""
        handler_repairs = defaultdict(list)
        for r in records:
            handler = r.get('handler_name', '').strip()
            if handler:
                handler_repairs[handler].append(r)

        result = {}
        for handler, repairs in sorted(handler_repairs.items(), key=lambda x: len(x[1]), reverse=True):
            resolved = len([r for r in repairs if r.get('status') in ('已处理', '已解决')])
            result[handler] = {
                'count': len(repairs),
                'resolved': resolved,
                'resolved_rate': round(resolved / len(repairs) * 100, 1) if repairs else 0,
            }

        return result

    def _get_repairs_by_college(self, records: list) -> dict:
        """按学院分组"""
        college_repairs = defaultdict(list)
        for r in records:
            college = r.get('reporter_college', '').strip()
            if college:
                college_repairs[college].append(r)

        result = {}
        for college, repairs in sorted(college_repairs.items(), key=lambda x: len(x[1]), reverse=True):
            external = len([r for r in repairs if r.get('is_external_teacher')])
            result[college] = {
                'count': len(repairs),
                'external_count': external,
            }

        return result

    def _get_repairs_by_method(self, records: list) -> dict:
        """按报修方式分组"""
        method_counts = defaultdict(int)
        for r in records:
            method = r.get('report_method', '').strip() or '未填写'
            method_counts[method] += 1
        return dict(sorted(method_counts.items(), key=lambda x: x[1], reverse=True))

    def _get_repairs_by_weekday(self, records: list) -> dict:
        """按周几分组"""
        weekday_repairs = defaultdict(list)
        weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}

        for r in records:
            report_time = r.get('report_time', '')
            if report_time:
                try:
                    dt = datetime.strptime(report_time[:10], '%Y-%m-%d')
                    weekday = weekday_map.get(dt.weekday(), '')
                    if weekday:
                        weekday_repairs[weekday].append(r)
                except ValueError:
                    pass

        result = {}
        for weekday in ['周一', '周二', '周三', '周四', '周五', '周六', '周日']:
            repairs = weekday_repairs.get(weekday, [])
            result[weekday] = {
                'count': len(repairs),
                'records': [{'classroom': r.get('classroom', ''), 'fault_type': r.get('fault_type', '')} for r in repairs],
            }

        return result

    def _get_week_comparison(self, this_week: list, last_week: list) -> dict:
        """周对比分析"""
        def _calc_change(this_val, last_val):
            change = this_val - last_val
            if last_val > 0:
                change_rate = round(change / last_val * 100, 1)
            else:
                change_rate = 100 if this_val > 0 else 0
            trend = '↑' if change > 0 else ('↓' if change < 0 else '-')
            return change, change_rate, trend

        # 整体对比
        this_total = len(this_week)
        this_resolved = len([r for r in this_week if r.get('status') in ('已处理', '已解决')])
        this_pending = len([r for r in this_week if r.get('status') in ('未处理', '处理中')])
        this_rate = round(this_resolved / this_total * 100, 1) if this_total > 0 else 0

        last_total = len(last_week)
        last_resolved = len([r for r in last_week if r.get('status') in ('已处理', '已解决')])
        last_pending = len([r for r in last_week if r.get('status') in ('未处理', '处理中')])
        last_rate = round(last_resolved / last_total * 100, 1) if last_total > 0 else 0

        total_change, total_rate, total_trend = _calc_change(this_total, last_total)
        resolved_change, resolved_rate, resolved_trend = _calc_change(this_resolved, last_resolved)
        pending_change, pending_rate, pending_trend = _calc_change(this_pending, last_pending)

        overview_table = [
            {'metric': '报修总量', 'this_week': this_total, 'last_week': last_total, 'change': total_change, 'change_rate': total_rate, 'trend': total_trend},
            {'metric': '已处理', 'this_week': this_resolved, 'last_week': last_resolved, 'change': resolved_change, 'change_rate': resolved_rate, 'trend': resolved_trend},
            {'metric': '待处理', 'this_week': this_pending, 'last_week': last_pending, 'change': pending_change, 'change_rate': pending_rate, 'trend': pending_trend},
            {'metric': '处理率(%)', 'this_week': this_rate, 'last_week': last_rate, 'change': round(this_rate - last_rate, 1), 'change_rate': 0, 'trend': '↑' if this_rate > last_rate else ('↓' if this_rate < last_rate else '-')},
        ]

        # 故障类型对比
        this_fault = defaultdict(int)
        for r in this_week:
            this_fault[r.get('fault_type', '其他') or '其他'] += 1

        last_fault = defaultdict(int)
        for r in last_week:
            last_fault[r.get('fault_type', '其他') or '其他'] += 1

        all_fault_types = sorted(set(list(this_fault.keys()) + list(last_fault.keys())))
        fault_type_comparison = []
        for ft in all_fault_types:
            this_val = this_fault.get(ft, 0)
            last_val = last_fault.get(ft, 0)
            change, _, trend = _calc_change(this_val, last_val)
            fault_type_comparison.append({
                'type': ft, 'this_week': this_val, 'last_week': last_val,
                'change': change, 'trend': trend, 'need_attention': change >= 2,
            })
        fault_type_comparison.sort(key=lambda x: x['this_week'], reverse=True)

        # 楼栋对比
        def _extract_building(classroom):
            return re.sub(r'\d+$', '', classroom).strip()

        this_building = defaultdict(int)
        for r in this_week:
            building = _extract_building(r.get('classroom', ''))
            if building:
                this_building[building] += 1

        last_building = defaultdict(int)
        for r in last_week:
            building = _extract_building(r.get('classroom', ''))
            if building:
                last_building[building] += 1

        all_buildings = sorted(set(list(this_building.keys()) + list(last_building.keys())))
        building_comparison = []
        for building in all_buildings:
            this_val = this_building.get(building, 0)
            last_val = last_building.get(building, 0)
            change, _, trend = _calc_change(this_val, last_val)
            building_comparison.append({
                'building': building, 'this_week': this_val, 'last_week': last_val,
                'change': change, 'trend': trend, 'need_attention': change >= 2,
            })
        building_comparison.sort(key=lambda x: x['this_week'], reverse=True)

        return {
            'overview_table': overview_table,
            'fault_type_comparison': fault_type_comparison,
            'building_comparison': building_comparison,
        }

    # ============================================================
    # 通用分析函数
    # ============================================================

    def _analyze_faults(self, records: list) -> dict:
        """故障分析"""
        type_distribution = defaultdict(int)
        for r in records:
            ft = r.get('fault_type', '其他') or '其他'
            type_distribution[ft] += 1

        type_distribution = dict(sorted(type_distribution.items(), key=lambda x: x[1], reverse=True))

        top_faults = []
        for ft, count in list(type_distribution.items())[:10]:
            ratio = round(count / len(records) * 100, 1) if records else 0
            causes = defaultdict(int)
            for r in records:
                if r.get('fault_type') == ft:
                    cause = r.get('fault_cause', '').strip()
                    if cause:
                        causes[cause[:20]] += 1
            top_cause = max(causes.items(), key=lambda x: x[1])[0] if causes else ''
            top_faults.append({'fault_type': ft, 'count': count, 'ratio': ratio, 'top_cause': top_cause})

        cause_summary = defaultdict(list)
        for r in records:
            ft = r.get('fault_type', '其他') or '其他'
            cause = r.get('fault_cause', '').strip()
            if cause and cause not in cause_summary[ft]:
                cause_summary[ft].append(cause)

        return {
            'type_distribution': type_distribution,
            'top_faults': top_faults,
            'cause_summary': dict(cause_summary),
        }

    def _analyze_areas(self, records: list, semester_records: list = None) -> dict:
        """区域分析"""
        if semester_records is None:
            semester_records = records

        building_distribution = defaultdict(int)
        for r in records:
            building = re.sub(r'\d+$', '', r.get('classroom', '')).strip()
            if building:
                building_distribution[building] += 1

        building_distribution = dict(sorted(building_distribution.items(), key=lambda x: x[1], reverse=True))

        floor_distribution = defaultdict(int)
        for r in records:
            classroom = r.get('classroom', '')
            match = re.search(r'(\d)', classroom)
            if match:
                floor = int(match.group(1))
                floor_distribution[f'{floor}楼'] += 1

        floor_distribution = dict(sorted(floor_distribution.items()))

        classroom_count = defaultdict(int)
        classroom_semester_count = defaultdict(int)

        for r in records:
            classroom = r.get('classroom', '').strip()
            if classroom:
                classroom_count[classroom] += 1

        for r in semester_records:
            classroom = r.get('classroom', '').strip()
            if classroom:
                classroom_semester_count[classroom] += 1

        top_classrooms = []
        for classroom, count in sorted(classroom_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            semester_total = classroom_semester_count.get(classroom, 0)
            top_classrooms.append({
                'classroom': classroom, 'count': count,
                'semester_total': semester_total, 'is_frequent': semester_total >= 5,
            })

        classroom_fault_types = defaultdict(lambda: defaultdict(int))
        for r in records:
            classroom = r.get('classroom', '').strip()
            ft = r.get('fault_type', '其他') or '其他'
            if classroom:
                classroom_fault_types[classroom][ft] += 1

        top_classroom_names = [c['classroom'] for c in top_classrooms]
        classroom_fault_types_result = {}
        for name in top_classroom_names:
            if name in classroom_fault_types:
                classroom_fault_types_result[name] = dict(classroom_fault_types[name])

        return {
            'building_distribution': building_distribution,
            'floor_distribution': floor_distribution,
            'top_classrooms': top_classrooms,
            'classroom_fault_types': classroom_fault_types_result,
        }

    def _analyze_time(self, records: list) -> dict:
        """时间分析"""
        weekday_distribution = defaultdict(int)
        for r in records:
            report_time = r.get('report_time', '')
            if report_time:
                try:
                    dt = datetime.strptime(report_time[:10], '%Y-%m-%d')
                    weekday = dt.weekday()
                    weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
                    weekday_distribution[weekday_map[weekday]] += 1
                except ValueError:
                    pass

        section_distribution = defaultdict(int)
        for r in records:
            report_time = r.get('report_time', '')
            if report_time and len(report_time) >= 16:
                try:
                    hour = int(report_time[11:13])
                    if 8 <= hour < 10:
                        section_distribution['1-2节'] += 1
                    elif 10 <= hour < 12:
                        section_distribution['3-4节'] += 1
                    elif 14 <= hour < 16:
                        section_distribution['5-6节'] += 1
                    elif 16 <= hour < 18:
                        section_distribution['7-8节'] += 1
                    elif 19 <= hour < 21:
                        section_distribution['9-10节'] += 1
                    else:
                        section_distribution['其他时段'] += 1
                except (ValueError, IndexError):
                    pass

        peak_weekday = max(weekday_distribution.items(), key=lambda x: x[1]) if weekday_distribution else ('', 0)
        peak_section = max(section_distribution.items(), key=lambda x: x[1]) if section_distribution else ('', 0)

        return {
            'weekday_distribution': dict(weekday_distribution),
            'section_distribution': dict(section_distribution),
            'peak_period': {
                'weekday': peak_weekday[0],
                'section': peak_section[0],
                'count': peak_section[1],
            }
        }

    def _analyze_colleges(self, records: list) -> dict:
        """学院分析"""
        college_distribution = defaultdict(int)
        external_count = 0

        for r in records:
            college = r.get('reporter_college', '').strip()
            if college:
                college_distribution[college] += 1
            if r.get('is_external_teacher'):
                external_count += 1

        college_distribution = dict(sorted(college_distribution.items(), key=lambda x: x[1], reverse=True))

        total = len(records)
        external_ratio = round(external_count / total * 100, 1) if total > 0 else 0

        return {
            'college_distribution': college_distribution,
            'external_teacher_count': external_count,
            'external_teacher_ratio': external_ratio,
        }

    def _analyze_efficiency(self, records: list) -> dict:
        """处理效率分析"""
        resolved = [r for r in records if r.get('status') in ('已处理', '已解决')]
        pending = [r for r in records if r.get('status') in ('未处理', '处理中')]

        # 已处理的平均处理时间
        process_days = []
        for r in resolved:
            created = r.get('created_at', '')
            updated = r.get('updated_at', '')
            if created and updated:
                try:
                    c = datetime.strptime(created[:10], '%Y-%m-%d')
                    u = datetime.strptime(updated[:10], '%Y-%m-%d')
                    days = (u - c).days
                    if days >= 0:
                        process_days.append(days)
                except ValueError:
                    pass

        avg_process_days = round(sum(process_days) / len(process_days), 1) if process_days else 0

        # 待处理中超过3天的
        old_pending = []
        for r in pending:
            created = r.get('created_at', '')
            if created:
                try:
                    c = datetime.strptime(created[:10], '%Y-%m-%d')
                    days = (datetime.now() - c).days
                    if days > 3:
                        old_pending.append({'id': r.get('id'), 'classroom': r.get('classroom'), 'days': days})
                except ValueError:
                    pass

        return {
            'resolved_count': len(resolved),
            'pending_count': len(pending),
            'avg_process_days': avg_process_days,
            'old_pending_count': len(old_pending),
            'old_pending_list': old_pending,
        }

    def _analyze_external_teachers(self, records: list) -> dict:
        """外聘教师分析"""
        external = [r for r in records if r.get('is_external_teacher')]
        internal = [r for r in records if not r.get('is_external_teacher')]

        # 外聘教师的故障类型
        ext_fault_types = defaultdict(int)
        for r in external:
            ext_fault_types[r.get('fault_type', '其他') or '其他'] += 1

        return {
            'external_count': len(external),
            'internal_count': len(internal),
            'external_ratio': round(len(external) / len(records) * 100, 1) if records else 0,
            'external_fault_types': dict(ext_fault_types),
        }

    def _analyze_device_replace(self, records: list) -> dict:
        """设备更换分析"""
        replaced = [r for r in records if r.get('is_device_replaced')]

        # 更换的教室
        replaced_classrooms = defaultdict(int)
        for r in replaced:
            replaced_classrooms[r.get('classroom', '')] += 1

        return {
            'replace_count': len(replaced),
            'replace_ratio': round(len(replaced) / len(records) * 100, 1) if records else 0,
            'replaced_classrooms': dict(replaced_classrooms),
            'replace_notes': [r.get('device_replace_note', '') for r in replaced if r.get('device_replace_note')],
        }

    # ============================================================
    # 月报分析
    # ============================================================

    def _analyze_monthly(self, year: int, month: int) -> dict:
        """月报分析"""
        start_date = f'{year}-{month:02d}-01'
        if month == 12:
            end_date = f'{year + 1}-01-01'
        else:
            end_date = f'{year}-{month + 1:02d}-01'

        records = Repair.select().where(
            (Repair.report_time >= start_date) &
            (Repair.report_time < end_date)
        ).order_by(Repair.report_time.desc())

        records_list = [r.to_dict() for r in records]

        if month == 1:
            last_year, last_month = year - 1, 12
        else:
            last_year, last_month = year, month - 1

        last_start = f'{last_year}-{last_month:02d}-01'
        last_end = start_date

        last_records = Repair.select().where(
            (Repair.report_time >= last_start) &
            (Repair.report_time < last_end)
        )
        last_records_list = [r.to_dict() for r in last_records]

        return {
            'report_type': 'monthly',
            'year': year,
            'month': month,
            'date_range': {
                'start': start_date,
                'end': f'{year}-{month:02d}-{self._get_days_in_month(year, month):02d}',
                'label': f'{year}年{month}月'
            },
            'overview': self._get_period_overview(records_list, last_records_list, '上月'),
            'records_detail': self._get_records_detail(records_list),
            'repairs_by_classroom': self._get_repairs_by_classroom(records_list, records_list),
            'repairs_by_building': self._get_repairs_by_building(records_list),
            'repairs_by_fault_type': self._get_repairs_by_fault_type(records_list),
            'repairs_by_handler': self._get_repairs_by_handler(records_list),
            'repairs_by_college': self._get_repairs_by_college(records_list),
            'fault_analysis': self._analyze_faults(records_list),
            'area_analysis': self._analyze_areas(records_list),
            'time_analysis': self._analyze_time(records_list),
            'college_analysis': self._analyze_colleges(records_list),
            'efficiency_analysis': self._analyze_efficiency(records_list),
            'external_teacher_analysis': self._analyze_external_teachers(records_list),
            'device_replace_analysis': self._analyze_device_replace(records_list),
        }

    def _get_days_in_month(self, year: int, month: int) -> int:
        """获取月份天数"""
        if month == 12:
            return 31
        from calendar import monthrange
        return monthrange(year, month)[1]

    # ============================================================
    # 学期报告分析
    # ============================================================

    def _analyze_semester(self, semester: str = '') -> dict:
        """学期报告分析"""
        import services.admin_config as admin_config

        semester_config = admin_config.get_semester_config()
        start_date_str = semester_config.get('start_date', '')

        if not start_date_str:
            return {'error': '未设置学期开始日期'}

        records = Repair.select().where(
            Repair.report_time >= start_date_str
        ).order_by(Repair.report_time.desc())

        records_list = [r.to_dict() for r in records]

        weekly_stats = defaultdict(int)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        for r in records_list:
            report_time = r.get('report_time', '')
            if report_time:
                try:
                    dt = datetime.strptime(report_time[:10], '%Y-%m-%d').date()
                    days_diff = (dt - start_date).days
                    if days_diff >= 0:
                        week_num = days_diff // 7 + 1
                        weekly_stats[f'第{week_num}周'] += 1
                except ValueError:
                    pass

        def _week_sort(item):
            try:
                return int(item[0].replace('第', '').replace('周', ''))
            except ValueError:
                return 0

        weekly_stats = dict(sorted(weekly_stats.items(), key=_week_sort))

        return {
            'report_type': 'semester',
            'semester': semester,
            'date_range': {
                'start': start_date_str,
                'end': datetime.now().strftime('%Y-%m-%d'),
                'label': semester or '本学期'
            },
            'overview': self._get_semester_overview(records_list),
            'records_detail': self._get_records_detail(records_list),
            'weekly_stats': weekly_stats,
            'repairs_by_classroom': self._get_repairs_by_classroom(records_list, records_list),
            'repairs_by_building': self._get_repairs_by_building(records_list),
            'repairs_by_fault_type': self._get_repairs_by_fault_type(records_list),
            'repairs_by_handler': self._get_repairs_by_handler(records_list),
            'repairs_by_college': self._get_repairs_by_college(records_list),
            'fault_analysis': self._analyze_faults(records_list),
            'area_analysis': self._analyze_areas(records_list),
            'time_analysis': self._analyze_time(records_list),
            'college_analysis': self._analyze_colleges(records_list),
            'efficiency_analysis': self._analyze_efficiency(records_list),
            'external_teacher_analysis': self._analyze_external_teachers(records_list),
            'device_replace_analysis': self._analyze_device_replace(records_list),
        }

    def _get_period_overview(self, this_period: list, last_period: list, last_label: str) -> dict:
        """获取时间段概览"""
        this_total = len(this_period)
        this_resolved = len([r for r in this_period if r.get('status') in ('已处理', '已解决')])
        this_pending = len([r for r in this_period if r.get('status') in ('未处理', '处理中')])
        this_rate = round(this_resolved / this_total * 100, 1) if this_total > 0 else 0

        last_total = len(last_period)

        total_change = this_total - last_total
        total_change_rate = round(total_change / last_total * 100, 1) if last_total > 0 else 0

        return {
            'total_count': this_total,
            'resolved_count': this_resolved,
            'pending_count': this_pending,
            'resolved_rate': this_rate,
            'vs_last_period': {
                'last_total': last_total,
                'total_change': total_change,
                'total_change_rate': total_change_rate,
                'last_label': last_label,
            }
        }

    def _get_semester_overview(self, records: list) -> dict:
        """获取学期概览"""
        total = len(records)
        resolved = len([r for r in records if r.get('status') in ('已处理', '已解决')])
        pending = len([r for r in records if r.get('status') in ('未处理', '处理中')])
        rate = round(resolved / total * 100, 1) if total > 0 else 0

        classrooms = set(r.get('classroom', '') for r in records if r.get('classroom'))
        buildings = set()
        for r in records:
            building = re.sub(r'\d+$', '', r.get('classroom', '')).strip()
            if building:
                buildings.add(building)

        colleges = set(r.get('reporter_college', '') for r in records if r.get('reporter_college'))

        return {
            'total_count': total,
            'resolved_count': resolved,
            'pending_count': pending,
            'resolved_rate': rate,
            'classroom_count': len(classrooms),
            'building_count': len(buildings),
            'college_count': len(colleges),
        }


# 创建全局实例
analyzer = ReportAnalyzer()
