"""
智能建议生成器 v2.0

基于数据分析生成专业建议：
  1. 设备维护建议
  2. 人员培训建议
  3. 流程优化建议
  4. 趋势预警建议
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ReportAdvisor:
    """智能建议生成器"""

    def generate(self, analysis: dict) -> List[Dict]:
        """基于分析结果生成建议"""
        advice = []

        if 'error' in analysis:
            return advice

        # 1. 高频故障教室（设备问题）
        advice.extend(self._check_frequent_classroom(analysis))

        # 2. 故障类型集中（培训需求）
        advice.extend(self._check_fault_concentration(analysis))

        # 3. 楼栋故障率偏高（区域问题）
        advice.extend(self._check_building_fault_rate(analysis))

        # 4. 待处理积压（流程问题）
        advice.extend(self._check_pending_backlog(analysis))

        # 5. 周报修量激增（趋势预警）
        if analysis.get('report_type') == 'weekly':
            advice.extend(self._check_week_change(analysis))

        # 6. 报修高峰时段（人员调配）
        advice.extend(self._check_peak_period(analysis))

        # 7. 重复故障（设备老化）
        advice.extend(self._check_repeated_faults(analysis))

        # 8. 外聘教师问题
        advice.extend(self._check_external_teachers(analysis))

        # 9. 设备更换建议
        advice.extend(self._check_device_replace(analysis))

        # 10. 处理效率问题
        advice.extend(self._check_efficiency(analysis))

        return advice

    def _check_frequent_classroom(self, analysis: dict) -> list:
        """检查高频故障教室"""
        advice = []
        area = analysis.get('area_analysis', {})
        top_classrooms = area.get('top_classrooms', [])

        for c in top_classrooms:
            if c.get('is_frequent', False):
                classroom = c.get('classroom', '')
                semester_total = c.get('semester_total', 0)
                week_count = c.get('count', 0)

                advice.append({
                    'level': 'warning',
                    'category': '设备维护',
                    'title': f'高频故障教室：{classroom}',
                    'content': f'{classroom}本学期已报修{semester_total}次，本周{week_count}次，设备故障频率过高',
                    'action': f'建议安排设备科对{classroom}进行全面检查，评估是否需要更换老化设备',
                })

        return advice

    def _check_fault_concentration(self, analysis: dict) -> list:
        """检查故障类型集中度"""
        advice = []
        fault = analysis.get('fault_analysis', {})
        type_dist = fault.get('type_distribution', {})

        if not type_dist:
            return advice

        total = sum(type_dist.values())
        if total == 0:
            return advice

        for ft, count in type_dist.items():
            ratio = count / total * 100
            if ratio > 30:
                advice.append({
                    'level': 'info',
                    'category': '培训需求',
                    'title': f'{ft}故障占比偏高',
                    'content': f'{ft}故障本周{count}次，占比{ratio:.1f}%，是主要故障类型',
                    'action': f'建议组织{ft}设备使用培训，提高教师正确使用设备的意识',
                })

        return advice

    def _check_building_fault_rate(self, analysis: dict) -> list:
        """检查楼栋故障率"""
        advice = []
        area = analysis.get('area_analysis', {})
        building_dist = area.get('building_distribution', {})

        if not building_dist:
            return advice

        total = sum(building_dist.values())
        if total == 0:
            return advice

        for building, count in building_dist.items():
            ratio = count / total * 100
            if ratio > 40:
                advice.append({
                    'level': 'warning',
                    'category': '区域排查',
                    'title': f'{building}故障率偏高',
                    'content': f'{building}本周报修{count}次，占比{ratio:.1f}%，明显高于其他楼栋',
                    'action': f'建议对{building}的多媒体设备进行专项排查，找出问题根源',
                })

        return advice

    def _check_pending_backlog(self, analysis: dict) -> list:
        """检查待处理积压"""
        advice = []
        overview = analysis.get('overview', {})
        pending_count = overview.get('pending_count', 0)
        unhandled = overview.get('unhandled_count', 0)

        if pending_count > 5:
            advice.append({
                'level': 'alert',
                'category': '流程优化',
                'title': '待处理工单积压',
                'content': f'当前待处理{pending_count}件（未处理{unhandled}件），可能影响教学秩序',
                'action': '建议增派维修人员，优先处理超过2天的待处理工单',
            })

        return advice

    def _check_week_change(self, analysis: dict) -> list:
        """检查周报修量变化"""
        advice = []
        overview = analysis.get('overview', {})
        vs_last = overview.get('vs_last_week', {})

        total_change_rate = vs_last.get('total_change_rate', 0)
        total_change = vs_last.get('total_change', 0)

        if total_change_rate > 30 and total_change >= 3:
            advice.append({
                'level': 'warning',
                'category': '趋势预警',
                'title': '报修量激增',
                'content': f'本周报修量较上周增长{total_change_rate:.1f}%（+{total_change}件），需关注',
                'action': '建议检查近期是否有设备老化集中爆发，或新学期设备使用不当问题',
            })

        rate_change = vs_last.get('rate_change', 0)
        if rate_change < -10:
            advice.append({
                'level': 'warning',
                'category': '效率预警',
                'title': '处理率明显下降',
                'content': f'本周处理率较上周下降{abs(rate_change):.1f}%，处理效率降低',
                'action': '建议排查处理流程是否受阻，及时调配人力资源',
            })

        return advice

    def _check_peak_period(self, analysis: dict) -> list:
        """检查报修高峰"""
        advice = []
        time_analysis = analysis.get('time_analysis', {})
        peak = time_analysis.get('peak_period', {})

        weekday = peak.get('weekday', '')
        section = peak.get('section', '')
        count = peak.get('count', 0)

        if count > 5:
            advice.append({
                'level': 'info',
                'category': '人员调配',
                'title': '报修高峰时段',
                'content': f'{weekday}{section}报修量最高（{count}次），是报修高峰期',
                'action': f'建议在{weekday}{section}安排专人值班，提高响应速度',
            })

        return advice

    def _check_repeated_faults(self, analysis: dict) -> list:
        """检查重复故障"""
        advice = []
        by_classroom = analysis.get('repairs_by_classroom', {})

        for classroom, info in by_classroom.items():
            repairs = info.get('repairs', [])

            fault_type_count = {}
            for r in repairs:
                ft = r.get('fault_type', '')
                if ft:
                    fault_type_count[ft] = fault_type_count.get(ft, 0) + 1

            for ft, count in fault_type_count.items():
                if count >= 2:
                    advice.append({
                        'level': 'warning',
                        'category': '设备问题',
                        'title': f'{classroom}{ft}重复故障',
                        'content': f'{classroom}本周{ft}故障{count}次，存在设备隐患',
                        'action': f'建议重点检查{classroom}的{ft}设备，可能存在硬件故障',
                    })

        return advice

    def _check_external_teachers(self, analysis: dict) -> list:
        """检查外聘教师问题"""
        advice = []
        ext_analysis = analysis.get('external_teacher_analysis', {})

        external_count = ext_analysis.get('external_count', 0)
        external_ratio = ext_analysis.get('external_ratio', 0)
        total = external_count + ext_analysis.get('internal_count', 0)

        if external_ratio > 30 and total > 5:
            advice.append({
                'level': 'info',
                'category': '使用培训',
                'title': '外聘教师报修比例偏高',
                'content': f'外聘教师报修{external_count}件，占比{external_ratio}%，高于平均水平',
                'action': '建议针对外聘教师开展设备使用培训，或在教室张贴操作指南',
            })

        return advice

    def _check_device_replace(self, analysis: dict) -> list:
        """检查设备更换"""
        advice = []
        replace_analysis = analysis.get('device_replace_analysis', {})

        replace_count = replace_analysis.get('replace_count', 0)
        if replace_count > 3:
            replaced_classrooms = replace_analysis.get('replaced_classrooms', {})
            classrooms = '、'.join(list(replaced_classrooms.keys())[:3])

            advice.append({
                'level': 'warning',
                'category': '设备采购',
                'title': '设备更换频繁',
                'content': f'本周设备更换{replace_count}次，涉及教室：{classrooms}',
                'action': '建议统计更换设备清单，评估是否需要批量采购新设备',
            })

        return advice

    def _check_efficiency(self, analysis: dict) -> list:
        """检查处理效率"""
        advice = []
        eff = analysis.get('efficiency_analysis', {})

        avg_days = eff.get('avg_process_days', 0)
        old_pending = eff.get('old_pending_count', 0)

        if avg_days > 2:
            advice.append({
                'level': 'warning',
                'category': '效率提升',
                'title': '平均处理时间偏长',
                'content': f'已处理工单平均处理时间{avg_days}天，超过2天标准',
                'action': '建议优化处理流程，提高维修人员响应速度',
            })

        if old_pending > 0:
            old_list = eff.get('old_pending_list', [])
            classrooms = '、'.join([r.get('classroom', '') for r in old_list[:3]])

            advice.append({
                'level': 'alert',
                'category': '紧急处理',
                'title': '存在超时未处理工单',
                'content': f'有{old_pending}件工单超过3天未处理，涉及：{classrooms}',
                'action': '建议立即安排人员处理这些超时工单，避免影响教学',
            })

        return advice


# 创建全局实例
advisor = ReportAdvisor()
