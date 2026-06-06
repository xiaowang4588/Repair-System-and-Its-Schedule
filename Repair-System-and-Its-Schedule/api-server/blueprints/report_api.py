"""
报告API Blueprint

包含：
  1. 周报/月报/学期报告数据接口
  2. 报告预览接口
  3. 报告导出接口（Excel/PDF/HTML）
"""
from flask import Blueprint, request, jsonify, send_file
from functools import wraps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 创建 Blueprint
report_bp = Blueprint('report', __name__)

# 这些变量会在注册时从 app 传入
_admin_required = None


def init_blueprint(admin_required_decorator):
    """初始化 Blueprint 的依赖"""
    global _admin_required
    _admin_required = admin_required_decorator


def report_auth_required(f):
    """报告接口认证装饰器（延迟初始化，支持 query 参数 token）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request as req

        # 如果请求中有 token 参数，尝试验证（HMAC Token）
        token = req.args.get('token', '')
        if token and not req.headers.get('Authorization'):
            try:
                from flask import current_app
                from utils.token_utils import verify_admin_token
                result = verify_admin_token(token, current_app.secret_key)
                if result.get('valid'):
                    return f(*args, **kwargs)
            except Exception:
                pass

        if _admin_required:
            return _admin_required(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated


@report_bp.route('/api/report/weekly', methods=['GET'])
@report_auth_required
def api_report_weekly():
    """获取周报数据"""
    try:
        from services.report.analyzer import analyzer
        from services.report.advisor import advisor

        week_number = request.args.get('week', 0, type=int)

        if not week_number:
            from services.admin_config import get_current_week
            week_number = get_current_week()

        if week_number <= 0:
            return jsonify({'status': 'error', 'message': '未设置学期开始日期或周次无效'}), 400

        # 执行分析
        analysis = analyzer.analyze('weekly', week_number=week_number)

        if 'error' in analysis:
            return jsonify({'status': 'error', 'message': analysis['error']}), 400

        # 生成建议
        advice = advisor.generate(analysis)

        return jsonify({
            'status': 'ok',
            'data': {
                **analysis,
                'advice': advice,
            }
        })

    except Exception as e:
        logger.error(f"生成周报失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@report_bp.route('/api/report/monthly', methods=['GET'])
@report_auth_required
def api_report_monthly():
    """获取月报数据"""
    try:
        from services.report.analyzer import analyzer
        from services.report.advisor import advisor

        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)

        # 执行分析
        analysis = analyzer.analyze('monthly', year=year, month=month)

        if 'error' in analysis:
            return jsonify({'status': 'error', 'message': analysis['error']}), 400

        # 生成建议
        advice = advisor.generate(analysis)

        return jsonify({
            'status': 'ok',
            'data': {
                **analysis,
                'advice': advice,
            }
        })

    except Exception as e:
        logger.error(f"生成月报失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@report_bp.route('/api/report/semester', methods=['GET'])
@report_auth_required
def api_report_semester():
    """获取学期报告数据"""
    try:
        from services.report.analyzer import analyzer
        from services.report.advisor import advisor

        semester = request.args.get('semester', '')

        # 执行分析
        analysis = analyzer.analyze('semester', semester=semester)

        if 'error' in analysis:
            return jsonify({'status': 'error', 'message': analysis['error']}), 400

        # 生成建议
        advice = advisor.generate(analysis)

        return jsonify({
            'status': 'ok',
            'data': {
                **analysis,
                'advice': advice,
            }
        })

    except Exception as e:
        logger.error(f"生成学期报告失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@report_bp.route('/api/report/preview', methods=['GET'])
@report_auth_required
def api_report_preview():
    """预览报告（返回 HTML）"""
    try:
        from services.report.analyzer import analyzer
        from services.report.advisor import advisor
        from services.report.html_template import generate_html_report

        report_type = request.args.get('type', 'weekly')
        week_number = request.args.get('week', 0, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        semester = request.args.get('semester', '')

        # 执行分析
        if report_type == 'weekly':
            if not week_number:
                from services.admin_config import get_current_week
                week_number = get_current_week()
            analysis = analyzer.analyze('weekly', week_number=week_number)
        elif report_type == 'monthly':
            analysis = analyzer.analyze('monthly', year=year, month=month)
        else:
            analysis = analyzer.analyze('semester', semester=semester)

        if 'error' in analysis:
            return jsonify({'status': 'error', 'message': analysis['error']}), 400

        # 生成建议
        advice = advisor.generate(analysis)

        # 生成 HTML
        html = generate_html_report(analysis, advice)

        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

    except Exception as e:
        logger.error(f"预览报告失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@report_bp.route('/api/report/export/excel', methods=['GET'])
@report_auth_required
def api_report_export_excel():
    """导出 Excel 报告"""
    try:
        from services.report.analyzer import analyzer
        from services.report.advisor import advisor
        from services.report.renderer import renderer

        report_type = request.args.get('type', 'weekly')
        week_number = request.args.get('week', 0, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        semester = request.args.get('semester', '')

        # 执行分析
        if report_type == 'weekly':
            if not week_number:
                from services.admin_config import get_current_week
                week_number = get_current_week()
            analysis = analyzer.analyze('weekly', week_number=week_number)
        elif report_type == 'monthly':
            analysis = analyzer.analyze('monthly', year=year, month=month)
        else:
            analysis = analyzer.analyze('semester', semester=semester)

        if 'error' in analysis:
            return jsonify({'status': 'error', 'message': analysis['error']}), 400

        # 生成建议
        advice = advisor.generate(analysis)

        # 渲染 Excel
        buffer = renderer.render_excel(analysis, advice)

        # 生成文件名
        date_range = analysis.get('date_range', {})
        label = date_range.get('label', '').replace('（', '(').replace('）', ')')
        filename = f"运维{renderer._get_type_name(report_type)}_{label}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"导出 Excel 报告失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@report_bp.route('/api/report/export/word', methods=['GET'])
@report_auth_required
def api_report_export_word():
    """导出 Word 报告"""
    try:
        from services.report.analyzer import analyzer
        from services.report.advisor import advisor
        from services.report.renderer import renderer

        report_type = request.args.get('type', 'weekly')
        week_number = request.args.get('week', 0, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        semester = request.args.get('semester', '')

        # 执行分析
        if report_type == 'weekly':
            if not week_number:
                from services.admin_config import get_current_week
                week_number = get_current_week()
            analysis = analyzer.analyze('weekly', week_number=week_number)
        elif report_type == 'monthly':
            analysis = analyzer.analyze('monthly', year=year, month=month)
        else:
            analysis = analyzer.analyze('semester', semester=semester)

        if 'error' in analysis:
            return jsonify({'status': 'error', 'message': analysis['error']}), 400

        # 生成建议
        advice = advisor.generate(analysis)

        # 渲染 Word
        buffer = renderer.render_word(analysis, advice)

        # 生成文件名
        date_range = analysis.get('date_range', {})
        label = date_range.get('label', '').replace('（', '(').replace('）', ')')
        filename = f"运维{renderer._get_type_name(report_type)}_{label}_{datetime.now().strftime('%Y%m%d')}.docx"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        logger.error(f"导出 Word 报告失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@report_bp.route('/api/report/weeks', methods=['GET'])
@report_auth_required
def api_report_weeks():
    """获取可用的周次列表"""
    try:
        from services.admin_config import get_current_week, get_semester_config

        current_week = get_current_week()
        semester_config = get_semester_config()
        start_date = semester_config.get('start_date', '')

        weeks = []
        if start_date and current_week > 0:
            from datetime import timedelta
            start = datetime.strptime(start_date, '%Y-%m-%d')

            for w in range(1, current_week + 1):
                week_start = start + timedelta(weeks=w - 1)
                week_end = week_start + timedelta(days=6)
                weeks.append({
                    'week_number': w,
                    'label': f'第{w}周',
                    'date_range': f"{week_start.strftime('%m.%d')} - {week_end.strftime('%m.%d')}",
                })

        return jsonify({
            'status': 'ok',
            'data': {
                'current_week': current_week,
                'start_date': start_date,
                'weeks': weeks,
            }
        })

    except Exception as e:
        logger.error(f"获取周次列表失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
