"""
时间相关工具函数
从 app.py 提取，消除 repair_manager.py 对 app.py 的循环依赖。
"""
import datetime
import pytz

# 课程节次时间表
CLASS_PERIODS = [
    (datetime.time(8, 0), datetime.time(9, 40), "1-2节"),
    (datetime.time(10, 5), datetime.time(11, 45), "3-4节"),
    (datetime.time(14, 0), datetime.time(15, 40), "5-6节"),
    (datetime.time(16, 5), datetime.time(17, 45), "7-8节"),
    (datetime.time(19, 0), datetime.time(20, 40), "9-10节"),
    (datetime.time(20, 50), datetime.time(22, 30), "11-12节")
]
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')


def get_current_beijing_time():
    """获取当前北京时间"""
    return datetime.datetime.now(SHANGHAI_TZ)


def get_auto_time_info():
    """获取当前时间、节次信息"""
    now = get_current_beijing_time()
    weekday = now.weekday() + 1
    current_section = None
    next_section = None
    countdown = 0

    for start, end, section in CLASS_PERIODS:
        if start <= now.time() <= end:
            current_section = section
            end_dt = SHANGHAI_TZ.localize(datetime.datetime.combine(now.date(), end))
            countdown = int((end_dt - now).total_seconds() // 60)
            break

    if not current_section:
        min_diff = None
        next_section_info = None
        today = now.date()
        for start, end, section in CLASS_PERIODS:
            start_dt = SHANGHAI_TZ.localize(datetime.datetime.combine(today, start))
            if start_dt > now:
                diff = (start_dt - now).total_seconds() // 60
                if min_diff is None or diff < min_diff:
                    min_diff = diff
                    next_section_info = (section, diff)
        if not next_section_info:
            days_until_monday = (7 - weekday) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = today + datetime.timedelta(days=days_until_monday)
            first_start = SHANGHAI_TZ.localize(
                datetime.datetime.combine(next_monday, CLASS_PERIODS[0][0])
            )
            diff = (first_start - now).total_seconds() // 60
            next_section_info = (CLASS_PERIODS[0][2], diff)
        next_section = next_section_info[0]
        countdown = -int(next_section_info[1])

    return {
        "weekday": weekday,
        "weekday_name": WEEKDAY_NAMES[weekday - 1],
        "current_section": current_section,
        "next_section": next_section,
        "countdown": countdown,
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
