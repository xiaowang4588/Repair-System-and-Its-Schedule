"""
智能建议生成器 v3.0

基于数据分析生成专业建议：
  1. 设备维护建议（含设备健康评分）
  2. 人员培训建议
  3. 流程优化建议
  4. 趋势预警建议
  5. 楼栋特征针对性建议
  6. 响应时效优化建议
  7. 工作负载调整建议
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ReportAdvisor:
    """智能建议生成器"""

    def generate(self, analysis: dict) -> List[Dict]:
        """基于分析结果生成建议（按优先级排序）"""
        advice = []

        if 'error' in analysis:
            return advice

        # 1. 设备健康度告警（新增 - 最高优先级）
        advice.extend(self._check_equipment_health(analysis))

        # 2. 高频故障教室（设备问题）
        advice.extend(self._check_frequent_classroom(analysis))

        # 3. 故障类型集中（培训需求）
        advice.extend(self._check_fault_concentration(analysis))

        # 4. 楼栋故障率偏高（区域问题）
        advice.extend(self._check_building_fault_rate(analysis))

        # 5. 楼栋特征问题（新增 - 针对性建议）
        advice.extend(self._check_building_profile(analysis))

        # 6. 待处理积压（流程问题）
        advice.extend(self._check_pending_backlog(analysis))

        # 7. 周报修量激增（趋势预警）
        if analysis.get('report_type') == 'weekly':
            advice.extend(self._check_week_change(analysis))
            advice.extend(self._check_multi_week_trend(analysis))

        # 8. 报修高峰时段（人员调配）
        advice.extend(self._check_peak_period(analysis))

        # 9. 重复故障（设备老化）
        advice.extend(self._check_repeated_faults(analysis))

        # 10. 外聘教师问题
        advice.extend(self._check_external_teachers(analysis))

        # 11. 设备更换建议
        advice.extend(self._check_device_replace(analysis))

        # 12. 处理效率问题
        advice.extend(self._check_efficiency(analysis))

        # 13. 响应时效瓶颈（新增）
        advice.extend(self._check_response_bottleneck(analysis))

        # 14. 工作负载均衡（新增）
        advice.extend(self._check_workload_balance(analysis))

        # 按优先级排序（优先级高的在前）
        advice.sort(key=lambda x: x.get('priority', 5), reverse=True)

        return advice

    # ============================================================
    # 新增检查方法
    # ============================================================

    def _check_equipment_health(self, analysis: dict) -> list:
        """检查设备健康度评分"""
        advice = []
        health = analysis.get('equipment_health', {})
        problems = health.get('this_week_problems', [])

        for item in problems[:5]:  # Top 5 问题教室
            classroom = item.get('classroom', '')
            score = item.get('health_score', 0)
            label = item.get('health_label', '')
            semester_count = item.get('semester_count', 0)
            repeat_faults = item.get('repeat_fault_types', [])

            repeat_desc = ''
            if repeat_faults:
                repeat_desc = '，重复故障：' + '、'.join(
                    [f"{f['type']}({f['count']}次)" for f in repeat_faults[:2]]
                )

            if score < 40:
                level = 'alert'
                priority = 10
                impact = 'high'
                action = f'建议立即对{classroom}进行全面设备检修，评估核心设备是否需要更换。'
            elif score < 60:
                level = 'warning'
                priority = 8
                impact = 'high'
                action = f'建议近期安排设备科对{classroom}进行专项检查，排查隐患设备。'
            else:
                level = 'info'
                priority = 6
                impact = 'medium'
                action = f'建议关注{classroom}的设备状态变化，做好预防性维护。'

            advice.append({
                'level': level,
                'priority': priority,
                'impact': impact,
                'category': '设备健康',
                'title': f'设备健康度[{label}]：{classroom}（评分{score}）',
                'content': f'{classroom}设备健康评分{score}分（{label}），学期累计报修{semester_count}次{repeat_desc}',
                'action': action,
            })

        # 整体健康度总结
        summary = health.get('summary', {})
        unhealthy_count = summary.get('unhealthy_count', 0)
        if unhealthy_count >= 3:
            advice.append({
                'level': 'warning',
                'priority': 7,
                'impact': 'medium',
                'category': '设备管理',
                'title': f'全校{unhealthy_count}间教室设备健康度偏低',
                'content': f'共有{unhealthy_count}间教室健康度评级为"警告"或"危险"，平均分{summary.get("avg_score", 0)}分',
                'action': '建议制定分批次的设备检修计划，优先处理评分最低的教室',
            })

        return advice

    def _check_building_profile(self, analysis: dict) -> list:
        """检查楼栋特征画像"""
        advice = []
        profile = analysis.get('building_profile', {})
        attention = profile.get('attention_buildings', [])
        profiles = profile.get('profiles', {})

        for building_name in attention:
            info = profiles.get(building_name, {})
            if not info:
                continue

            issues = []
            if info.get('external_vs_avg') == 'high':
                issues.append('外聘教师报修比例偏高')
            if info.get('replace_vs_avg') == 'high':
                issues.append('设备更换率偏高')
            if info.get('process_vs_avg') == 'high':
                issues.append('处理时效偏慢')
            if info.get('unhandled_count', 0) > 0:
                issues.append(f'有{info["unhandled_count"]}条未处理')

            typical_faults = info.get('typical_fault_label', '')

            advice.append({
                'level': 'warning',
                'priority': 7,
                'impact': 'medium',
                'category': '楼栋画像',
                'title': f'{building_name}多项指标异常',
                'content': f'{building_name}存在问题：{"、".join(issues)}。典型故障模式：{typical_faults}',
                'action': f'建议对{building_name}进行专项诊断：检查设备老化情况{"、加强外聘教师培训" if info.get("external_vs_avg") == "high" else ""}',
            })

        return advice

    def _check_multi_week_trend(self, analysis: dict) -> list:
        """检查多周趋势"""
        advice = []
        trend = analysis.get('multi_week_trend', {})
        acceleration = trend.get('acceleration_label', '')

        if '加速上升' in acceleration:
            weeks_data = trend.get('weeks', [])
            totals = [w['total'] for w in weeks_data]
            advice.append({
                'level': 'warning',
                'priority': 8,
                'impact': 'high',
                'category': '趋势预警',
                'title': '报修量呈加速上升趋势',
                'content': f'近{len(weeks_data)}周报修量分别为：{" → ".join([f"{w["week"]}({w["total"]}件)" for w in weeks_data])}，呈加速上升态势',
                'action': '建议排查近期设备是否集中进入老化期，或是否有新设备部署导致兼容问题',
            })
        elif '持续上升' in acceleration:
            weeks_data = trend.get('weeks', [])
            advice.append({
                'level': 'info',
                'priority': 5,
                'impact': 'medium',
                'category': '趋势预警',
                'title': '报修量呈持续上升趋势',
                'content': f'近{len(weeks_data)}周报修量持续上升，建议密切关注后续变化',
                'action': '建议加强对高频教室的巡检频率，预防故障集中爆发',
            })

        return advice

    def _check_response_bottleneck(self, analysis: dict) -> list:
        """检查响应时效瓶颈"""
        advice = []
        rtm = analysis.get('response_time_matrix', {})
        bottlenecks = rtm.get('bottlenecks', [])

        for bn in bottlenecks[:3]:
            advice.append({
                'level': 'warning' if bn['type'] == 'handler' else 'info',
                'priority': 6 if bn['type'] == 'handler' else 4,
                'impact': 'medium',
                'category': '时效优化',
                'title': f'响应瓶颈：{bn["name"]}',
                'content': bn['issue'],
                'action': bn['suggestion'],
            })

        return advice

    def _check_workload_balance(self, analysis: dict) -> list:
        """检查工作负载均衡"""
        advice = []
        workload = analysis.get('workload_analysis', {})
        handlers = workload.get('handlers', [])

        if not workload.get('is_balanced', True) and len(handlers) >= 2:
            busiest = handlers[0]
            most_free = handlers[-1]
            advice.append({
                'level': 'info',
                'priority': 5,
                'impact': 'medium',
                'category': '资源调配',
                'title': '处理人工作负载不均',
                'content': f'{busiest["handler"]}处理量最大（{busiest["semester_total"]}件），{most_free["handler"]}最少（{most_free["semester_total"]}件），差距{workload["load_range"]["max"] - workload["load_range"]["min"]}件',
                'action': f'建议适当调整任务分配，将{busiest["handler"]}的部分任务转给{most_free["handler"]}，平衡工作负载',
            })

        # 检查有积压的处理人
        for h in handlers:
            if h.get('pending', 0) >= 2:
                advice.append({
                    'level': 'info',
                    'priority': 4,
                    'impact': 'low',
                    'category': '任务跟进',
                    'title': f'{h["handler"]}有{h["pending"]}条待处理积压',
                    'content': f'{h["handler"]}当前有{h["pending"]}条工单未处理（学期累计{h["semester_total"]}件）',
                    'action': '建议及时跟进处理，避免影响教学秩序',
                })

        return advice

    # ============================================================
    # 原有检查方法（增强版 - 增加 priority 和 impact）
    # ============================================================

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

                # 使用设备健康评分增强建议
                health = analysis.get('equipment_health', {})
                health_scores = {h['classroom']: h for h in health.get('scores', [])}
                health_info = health_scores.get(classroom, {})

                priority = 7
                impact = 'medium'
                if health_info.get('health_score', 100) < 40:
                    priority = 9
                    impact = 'high'
                elif health_info.get('health_score', 100) < 60:
                    priority = 7
                    impact = 'high'

                advice.append({
                    'level': 'warning',
                    'priority': priority,
                    'impact': impact,
                    'category': '设备维护',
                    'title': f'高频故障教室：{classroom}',
                    'content': f'{classroom}本学期已报修{semester_total}次，本周{week_count}次，设备故障频率过高' +
                               (f'（健康评分：{health_info.get("health_score", "?")}）' if health_info else ''),
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
                    'priority': 5,
                    'impact': 'medium',
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
                    'priority': 6,
                    'impact': 'medium',
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
            priority = 9 if unhandled >= 3 else 6
            advice.append({
                'level': 'alert',
                'priority': priority,
                'impact': 'high',
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
                'priority': 7,
                'impact': 'high',
                'category': '趋势预警',
                'title': '报修量激增',
                'content': f'本周报修量较上周增长{total_change_rate:.1f}%（+{total_change}件），需关注',
                'action': '建议检查近期是否有设备老化集中爆发，或新学期设备使用不当问题',
            })

        rate_change = vs_last.get('rate_change', 0)
        if rate_change < -10:
            advice.append({
                'level': 'warning',
                'priority': 6,
                'impact': 'medium',
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
                'priority': 4,
                'impact': 'low',
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
                        'priority': 6,
                        'impact': 'medium',
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
                'priority': 5,
                'impact': 'medium',
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
                'priority': 6,
                'impact': 'high',
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
                'priority': 6,
                'impact': 'medium',
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
                'priority': 9,
                'impact': 'high',
                'category': '紧急处理',
                'title': '存在超时未处理工单',
                'content': f'有{old_pending}件工单超过3天未处理，涉及：{classrooms}',
                'action': '建议立即安排人员处理这些超时工单，避免影响教学',
            })

        return advice


# 创建全局实例
advisor = ReportAdvisor()
