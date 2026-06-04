"""
报告 HTML 模板生成器

生成可在浏览器中预览的 HTML 报告
"""
from datetime import datetime


def generate_html_report(analysis: dict, advice: list) -> str:
    """
    生成 HTML 格式的报告
    :param analysis: 分析结果
    :param advice: 建议列表
    :return: HTML 字符串
    """
    report_type = analysis.get('report_type', '')
    date_range = analysis.get('date_range', {})
    overview = analysis.get('overview', {})

    # 根据报告类型生成不同内容
    if report_type == 'weekly':
        content = _generate_weekly_content(analysis, advice)
    elif report_type == 'monthly':
        content = _generate_monthly_content(analysis, advice)
    else:
        content = _generate_semester_content(analysis, advice)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>运维{_get_report_type_name(report_type)} - {date_range.get('label', '')}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 24px;
        }}
        .report-header h1 {{
            font-size: 28px;
            margin-bottom: 8px;
        }}
        .report-header h2 {{
            font-size: 20px;
            font-weight: normal;
            opacity: 0.9;
        }}
        .report-header .time {{
            font-size: 14px;
            opacity: 0.7;
            margin-top: 12px;
        }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #667eea;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }}
        .kpi-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .kpi-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .kpi-card .label {{
            font-size: 14px;
            color: #666;
            margin-top: 4px;
        }}
        .kpi-card .change {{
            font-size: 13px;
            margin-top: 8px;
        }}
        .kpi-card .change.up {{ color: #e74c3c; }}
        .kpi-card .change.down {{ color: #27ae60; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}
        .classroom-group {{
            margin-bottom: 20px;
            border: 1px solid #eee;
            border-radius: 8px;
            overflow: hidden;
        }}
        .classroom-header {{
            background: #f8f9fa;
            padding: 12px 16px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .classroom-header .count {{
            color: #667eea;
        }}
        .classroom-header .semester {{
            font-size: 13px;
            color: #666;
        }}
        .classroom-body {{
            padding: 0;
        }}
        .classroom-body table {{
            margin: 0;
        }}
        .chart-container {{
            height: 350px;
            margin: 16px 0;
        }}
        .advice-item {{
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .advice-item.alert {{
            background: #fff5f5;
            border-color: #e74c3c;
        }}
        .advice-item.warning {{
            background: #fffaf0;
            border-color: #f39c12;
        }}
        .advice-item.info {{
            background: #f0f7ff;
            border-color: #3498db;
        }}
        .advice-item .title {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .advice-item .content {{
            color: #555;
        }}
        .advice-item .action {{
            margin-top: 8px;
            font-size: 13px;
            color: #888;
        }}
        .trend-up {{ color: #e74c3c; }}
        .trend-down {{ color: #27ae60; }}
        .trend-flat {{ color: #95a5a6; }}
        @media print {{
            body {{ background: white; }}
            .container {{ padding: 0; }}
            .section {{ box-shadow: none; border: 1px solid #eee; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1>重庆移通学院綦江校区</h1>
            <h2>多媒体设备运维{_get_report_type_name(report_type)}</h2>
            <div class="time">{date_range.get('label', '')} | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>

        {content}
    </div>
</body>
</html>"""


def _generate_weekly_content(analysis: dict, advice: list) -> str:
    """生成周报内容"""
    overview = analysis.get('overview', {})
    vs_last = overview.get('vs_last_week', {})
    repairs_by_classroom = analysis.get('repairs_by_classroom', {})
    comparison = analysis.get('week_comparison', {})
    fault = analysis.get('fault_analysis', {})
    area = analysis.get('area_analysis', {})
    time_analysis = analysis.get('time_analysis', {})
    college = analysis.get('college_analysis', {})

    # 变化趋势
    total_change = vs_last.get('total_change', 0)
    total_rate = vs_last.get('total_change_rate', 0)
    trend_class = 'up' if total_change > 0 else ('down' if total_change < 0 else 'flat')
    trend_arrow = '↑' if total_change > 0 else ('↓' if total_change < 0 else '-')

    rate_change = vs_last.get('rate_change', 0)
    rate_class = 'up' if rate_change > 0 else ('down' if rate_change < 0 else 'flat')

    # 教室明细 HTML
    classroom_html = ''
    for classroom, info in repairs_by_classroom.items():
        count = info.get('count', 0)
        semester_total = info.get('semester_total', 0)
        is_frequent = info.get('is_frequent', False)
        frequent_badge = '<span class="badge badge-warning">⚠️ 高频</span>' if is_frequent else ''

        rows_html = ''
        for r in info.get('repairs', []):
            status_class = 'badge-success' if r.get('status') in ('已处理', '已解决') else 'badge-warning'
            rows_html += f"""
            <tr>
                <td>{r.get('date', '')}</td>
                <td>{r.get('weekday', '')}</td>
                <td>{r.get('fault_type', '')}</td>
                <td>{r.get('fault_cause', '')}</td>
                <td><span class="badge {status_class}">{r.get('status', '')}</span></td>
                <td>{r.get('handler', '')}</td>
                <td>{r.get('reporter', '')}</td>
            </tr>"""

        classroom_html += f"""
        <div class="classroom-group">
            <div class="classroom-header">
                <span>📍 {classroom} <span class="count">本周{count}次</span></span>
                <span class="semester">学期累计{semester_total}次 {frequent_badge}</span>
            </div>
            <div class="classroom-body">
                <table>
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>星期</th>
                            <th>故障类型</th>
                            <th>故障原因</th>
                            <th>状态</th>
                            <th>处理人</th>
                            <th>报修人</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>"""

    # 周对比表格
    comparison_rows = ''
    for item in comparison.get('overview_table', []):
        trend = item.get('trend', '-')
        trend_cls = 'trend-up' if trend == '↑' else ('trend-down' if trend == '↓' else 'trend-flat')
        comparison_rows += f"""
        <tr>
            <td>{item.get('metric', '')}</td>
            <td>{item.get('this_week', '')}</td>
            <td>{item.get('last_week', '')}</td>
            <td>{item.get('change', '')}</td>
            <td class="{trend_cls}">{trend}</td>
        </tr>"""

    # 故障类型对比
    fault_comparison_rows = ''
    for item in comparison.get('fault_type_comparison', []):
        need_attention = '⚠️' if item.get('need_attention') else ''
        fault_comparison_rows += f"""
        <tr>
            <td>{item.get('type', '')}</td>
            <td>{item.get('this_week', '')}</td>
            <td>{item.get('last_week', '')}</td>
            <td>{item.get('change', '')}</td>
            <td>{item.get('trend', '')} {need_attention}</td>
        </tr>"""

    # 楼栋对比
    building_comparison_rows = ''
    for item in comparison.get('building_comparison', []):
        need_attention = '⚠️' if item.get('need_attention') else ''
        building_comparison_rows += f"""
        <tr>
            <td>{item.get('building', '')}</td>
            <td>{item.get('this_week', '')}</td>
            <td>{item.get('last_week', '')}</td>
            <td>{item.get('change', '')}</td>
            <td>{item.get('trend', '')} {need_attention}</td>
        </tr>"""

    # 故障类型分布饼图数据
    type_dist = fault.get('type_distribution', {})
    pie_data = str([{'value': v, 'name': k} for k, v in type_dist.items()])

    # 楼栋分布柱状图数据
    building_dist = area.get('building_distribution', {})
    bar_categories = str(list(building_dist.keys()))
    bar_data = str(list(building_dist.values()))

    # 周几分布
    weekday_dist = time_analysis.get('weekday_distribution', {})
    weekday_order = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_data = [weekday_dist.get(d, 0) for d in weekday_order]

    # 建议 HTML
    advice_html = ''
    for item in advice:
        level = item.get('level', 'info')
        advice_html += f"""
        <div class="advice-item {level}">
            <div class="title">{_get_level_icon(level)} {item.get('title', '')}</div>
            <div class="content">{item.get('content', '')}</div>
            <div class="action">💡 {item.get('action', '')}</div>
        </div>"""

    return f"""
    <!-- 一、本周概览 -->
    <div class="section">
        <div class="section-title">一、本周概览</div>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="value">{overview.get('total_count', 0)}</div>
                <div class="label">报修总量</div>
                <div class="change {trend_class}">{trend_arrow} {abs(total_change)}件 ({total_rate}%)</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('resolved_count', 0)}</div>
                <div class="label">已处理</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('pending_count', 0)}</div>
                <div class="label">待处理</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('resolved_rate', 0)}%</div>
                <div class="label">处理率</div>
                <div class="change {rate_class}">较上周 {rate_change:+.1f}%</div>
            </div>
        </div>
    </div>

    <!-- 二、本周报修明细 -->
    <div class="section">
        <div class="section-title">二、本周报修明细</div>
        {classroom_html if classroom_html else '<p style="color:#999">本周暂无报修记录</p>'}
    </div>

    <!-- 三、周对比分析 -->
    <div class="section">
        <div class="section-title">三、周对比分析</div>

        <h4 style="margin-bottom: 12px;">3.1 整体对比</h4>
        <table>
            <thead>
                <tr>
                    <th>指标</th>
                    <th>本周</th>
                    <th>上周</th>
                    <th>变化</th>
                    <th>趋势</th>
                </tr>
            </thead>
            <tbody>
                {comparison_rows}
            </tbody>
        </table>

        <h4 style="margin: 24px 0 12px;">3.2 故障类型对比</h4>
        <table>
            <thead>
                <tr>
                    <th>故障类型</th>
                    <th>本周</th>
                    <th>上周</th>
                    <th>变化</th>
                    <th>趋势</th>
                </tr>
            </thead>
            <tbody>
                {fault_comparison_rows}
            </tbody>
        </table>

        <h4 style="margin: 24px 0 12px;">3.3 楼栋对比</h4>
        <table>
            <thead>
                <tr>
                    <th>楼栋</th>
                    <th>本周</th>
                    <th>上周</th>
                    <th>变化</th>
                    <th>趋势</th>
                </tr>
            </thead>
            <tbody>
                {building_comparison_rows}
            </tbody>
        </table>
    </div>

    <!-- 四、故障分析 -->
    <div class="section">
        <div class="section-title">四、故障分析</div>
        <div class="chart-container" id="faultChart"></div>
    </div>

    <!-- 五、区域分析 -->
    <div class="section">
        <div class="section-title">五、区域分析</div>
        <div class="chart-container" id="buildingChart"></div>
    </div>

    <!-- 六、时间分析 -->
    <div class="section">
        <div class="section-title">六、时间分析</div>
        <div class="chart-container" id="weekdayChart"></div>
    </div>

    <!-- 七、智能建议 -->
    <div class="section">
        <div class="section-title">七、智能建议</div>
        {advice_html if advice_html else '<p style="color:#999">暂无建议</p>'}
    </div>

    <script>
        // 故障类型饼图
        var faultChart = echarts.init(document.getElementById('faultChart'));
        faultChart.setOption({{
            title: {{ text: '故障类型分布', left: 'center' }},
            tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}}件 ({{d}}%)' }},
            series: [{{
                type: 'pie',
                radius: '60%',
                data: {pie_data},
                emphasis: {{
                    itemStyle: {{
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }}
                }}
            }}]
        }});

        // 楼栋柱状图
        var buildingChart = echarts.init(document.getElementById('buildingChart'));
        buildingChart.setOption({{
            title: {{ text: '楼栋报修分布', left: 'center' }},
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: {bar_categories} }},
            yAxis: {{ type: 'value', name: '数量' }},
            series: [{{
                type: 'bar',
                data: {bar_data},
                itemStyle: {{
                    color: '#667eea',
                    borderRadius: [4, 4, 0, 0]
                }}
            }}]
        }});

        // 周几分布柱状图
        var weekdayChart = echarts.init(document.getElementById('weekdayChart'));
        weekdayChart.setOption({{
            title: {{ text: '周几报修分布', left: 'center' }},
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: {str(weekday_order)} }},
            yAxis: {{ type: 'value', name: '数量' }},
            series: [{{
                type: 'bar',
                data: {str(weekday_data)},
                itemStyle: {{
                    color: '#764ba2',
                    borderRadius: [4, 4, 0, 0]
                }}
            }}]
        }});

        // 响应式
        window.addEventListener('resize', function() {{
            faultChart.resize();
            buildingChart.resize();
            weekdayChart.resize();
        }});
    </script>
"""


def _generate_monthly_content(analysis: dict, advice: list) -> str:
    """生成月报内容（简化版，结构类似周报）"""
    # 月报结构与周报类似，但没有教室明细和周对比
    overview = analysis.get('overview', {})
    fault = analysis.get('fault_analysis', {})
    area = analysis.get('area_analysis', {})
    time_analysis = analysis.get('time_analysis', {})

    # 建议 HTML
    advice_html = ''
    for item in advice:
        level = item.get('level', 'info')
        advice_html += f"""
        <div class="advice-item {level}">
            <div class="title">{_get_level_icon(level)} {item.get('title', '')}</div>
            <div class="content">{item.get('content', '')}</div>
            <div class="action">💡 {item.get('action', '')}</div>
        </div>"""

    return f"""
    <div class="section">
        <div class="section-title">一、本月概览</div>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="value">{overview.get('total_count', 0)}</div>
                <div class="label">报修总量</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('resolved_count', 0)}</div>
                <div class="label">已处理</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('pending_count', 0)}</div>
                <div class="label">待处理</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('resolved_rate', 0)}%</div>
                <div class="label">处理率</div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">二、智能建议</div>
        {advice_html if advice_html else '<p style="color:#999">暂无建议</p>'}
    </div>
"""


def _generate_semester_content(analysis: dict, advice: list) -> str:
    """生成学期报告内容"""
    overview = analysis.get('overview', {})
    weekly_stats = analysis.get('weekly_stats', {})

    # 周趋势图数据
    weeks = list(weekly_stats.keys())
    counts = list(weekly_stats.values())

    # 建议 HTML
    advice_html = ''
    for item in advice:
        level = item.get('level', 'info')
        advice_html += f"""
        <div class="advice-item {level}">
            <div class="title">{_get_level_icon(level)} {item.get('title', '')}</div>
            <div class="content">{item.get('content', '')}</div>
            <div class="action">💡 {item.get('action', '')}</div>
        </div>"""

    return f"""
    <div class="section">
        <div class="section-title">一、学期概览</div>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="value">{overview.get('total_count', 0)}</div>
                <div class="label">报修总量</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('resolved_count', 0)}</div>
                <div class="label">已处理</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('classroom_count', 0)}</div>
                <div class="label">涉及教室</div>
            </div>
            <div class="kpi-card">
                <div class="value">{overview.get('building_count', 0)}</div>
                <div class="label">涉及楼栋</div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">二、周趋势</div>
        <div class="chart-container" id="trendChart"></div>
    </div>

    <div class="section">
        <div class="section-title">三、智能建议</div>
        {advice_html if advice_html else '<p style="color:#999">暂无建议</p>'}
    </div>

    <script>
        var trendChart = echarts.init(document.getElementById('trendChart'));
        trendChart.setOption({{
            title: {{ text: '每周报修趋势', left: 'center' }},
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: {str(weeks)}, axisLabel: {{ rotate: 45 }} }},
            yAxis: {{ type: 'value', name: '数量' }},
            series: [{{
                type: 'line',
                data: {str(counts)},
                smooth: true,
                areaStyle: {{ opacity: 0.3 }},
                itemStyle: {{ color: '#667eea' }}
            }}]
        }});

        window.addEventListener('resize', function() {{
            trendChart.resize();
        }});
    </script>
"""


def _get_report_type_name(report_type: str) -> str:
    """获取报告类型中文名"""
    names = {
        'weekly': '周报',
        'monthly': '月报',
        'semester': '学期报告',
    }
    return names.get(report_type, '报告')


def _get_level_icon(level: str) -> str:
    """获取建议级别图标"""
    icons = {
        'alert': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️',
    }
    return icons.get(level, 'ℹ️')
