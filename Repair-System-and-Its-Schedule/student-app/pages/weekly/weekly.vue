<template>
    <view class="page">
        <view class="container">
            <!-- 查询表单 -->
            <view class="card">
                <view class="card-title">一周课程表</view>
                <view class="form-group">
                    <text class="form-label">查询类型</text>
                    <view class="type-switch">
                        <view class="type-btn" :class="{ active: queryType === 'class' }" @click="queryType = 'class'">
                            按班级
                        </view>
                        <view class="type-btn" :class="{ active: queryType === 'teacher' }" @click="queryType = 'teacher'">
                            按教师
                        </view>
                    </view>
                </view>
                <view class="form-group">
                    <text class="form-label">{{ queryType === 'class' ? '班级名称' : '教师姓名' }}</text>
                    <input class="form-input" v-model="keyword" :placeholder="queryType === 'class' ? '例：2025级软件工程1班' : '例：张三'" />
                </view>
                <button class="btn-primary" @click="doQuery">📅 生成课表</button>
            </view>

            <!-- 课表结果 -->
            <view class="card" v-if="scheduleData && scheduleData.sections && scheduleData.sections.length > 0">
                <scroll-view scroll-x class="table-scroll">
                    <view class="table">
                        <!-- 表头 -->
                        <view class="table-header">
                            <view class="table-cell section-cell">节次</view>
                            <view class="table-cell" v-for="day in 7" :key="day">
                                {{ weekdayNames[day - 1] }}
                            </view>
                        </view>
                        <!-- 数据行 -->
                        <view class="table-row" v-for="section in scheduleData.sections" :key="section">
                            <view class="table-cell section-cell">{{ section }}</view>
                            <view class="table-cell" v-for="day in 7" :key="day">
                                <view class="course-block" v-for="(course, idx) in (scheduleData.weekly_data[day] || {})[section] || []" :key="idx">
                                    <text class="course-name">{{ course.course_name }}</text>
                                    <text class="course-teacher">{{ course.teacher }}</text>
                                    <text class="course-room">📍 {{ course.classroom }}</text>
                                </view>
                            </view>
                        </view>
                    </view>
                </scroll-view>
            </view>

            <!-- 空结果 -->
            <view class="card" v-else-if="queried">
                <view class="empty">
                    <text class="empty-icon">📭</text>
                    <text class="empty-text">未找到{{ queryType === 'class' ? '班级' : '教师' }}：{{ keyword }} 的课程</text>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
import { getWeeklySchedule } from '@/api/index.js'

export default {
    data() {
        return {
            queryType: 'class',
            keyword: '',
            scheduleData: null,
            queried: false,
            weekdayNames: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        }
    },
    methods: {
        async doQuery() {
            if (!this.keyword.trim()) {
                uni.showToast({
                    title: this.queryType === 'class' ? '请输入班级名称' : '请输入教师姓名',
                    icon: 'none'
                })
                return
            }

            uni.showLoading({ title: '查询中...' })
            try {
                const res = await getWeeklySchedule(this.keyword.trim(), this.queryType)
                if (res.status === 'ok') {
                    this.scheduleData = res.data
                    this.queried = true
                } else {
                    uni.showToast({ title: res.message, icon: 'none' })
                }
            } catch (e) {
                uni.showToast({ title: '查询失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
        }
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg); }
.container { padding: 24rpx; }

.card { background: var(--color-surface); border-radius: var(--radius-lg); padding: 28rpx; margin-bottom: 20rpx; box-shadow: var(--shadow-sm); border: 1rpx solid var(--color-border-light); }
.card-title { font-size: 30rpx; font-weight: 700; color: var(--color-text); margin-bottom: 24rpx; padding-bottom: 16rpx; border-bottom: 1rpx solid var(--color-divider); }

.form-group { margin-bottom: 24rpx; }
.form-label { font-size: 26rpx; color: var(--color-text-secondary); margin-bottom: 10rpx; display: block; font-weight: 500; }

.form-input { width: 100%; height: 88rpx; padding: 0 24rpx; border: 2rpx solid var(--color-border); border-radius: var(--radius-sm); font-size: 28rpx; color: var(--color-text); background: var(--color-bg-secondary); box-sizing: border-box; transition: all var(--transition-fast); }
.form-input:focus { border-color: var(--color-primary); background: var(--color-surface); box-shadow: 0 0 0 4rpx rgba(108,92,231,0.06); }

.type-switch { display: flex; gap: 12rpx; }
.type-btn { flex: 1; height: 80rpx; line-height: 80rpx; text-align: center; border: 2rpx solid var(--color-border); border-radius: var(--radius-sm); font-size: 28rpx; color: var(--color-text-secondary); background: var(--color-bg-secondary); transition: all var(--transition-fast); font-weight: 500; }
.type-btn.active { background: var(--color-primary-bg); color: var(--color-primary); border-color: var(--color-primary); font-weight: 600; }

.btn-primary { width: 100%; height: 88rpx; line-height: 88rpx; background: var(--color-primary-gradient); color: white; border: none; border-radius: var(--radius-md); font-size: 30rpx; font-weight: 600; box-shadow: 0 4rpx 16rpx rgba(108,92,231,0.25); transition: all var(--transition-fast); }
.btn-primary:active { transform: translateY(2rpx) scale(0.98); }

.table-scroll { width: 100%; }
.table { min-width: 900rpx; }
.table-header { display: flex; background: var(--color-primary-bg); border-bottom: 2rpx solid rgba(108,92,231,0.12); }
.table-row { display: flex; border-bottom: 1rpx solid var(--color-divider); }
.table-cell { flex: 1; padding: 14rpx 8rpx; font-size: 24rpx; color: var(--color-text-secondary); min-height: 100rpx; text-align: center; }
.section-cell { width: 120rpx; flex: none; background: var(--color-primary-bg); font-weight: 600; color: var(--color-primary); display: flex; align-items: center; justify-content: center; }

.course-block { background: linear-gradient(135deg, #F0EEFF 0%, #E4E0FF 100%); border-radius: var(--radius-xs); padding: 10rpx; margin-bottom: 8rpx; border-left: 4rpx solid var(--color-primary); text-align: left; }
.course-name { font-size: 24rpx; font-weight: 600; color: var(--color-text); display: block; }
.course-teacher { font-size: 22rpx; color: var(--color-primary); display: block; margin-top: 4rpx; }
.course-room { font-size: 22rpx; color: var(--color-text-tertiary); display: block; margin-top: 4rpx; }

.empty { display: flex; flex-direction: column; align-items: center; padding: 60rpx 0; }
.empty-icon { font-size: 80rpx; margin-bottom: 16rpx; opacity: 0.45; }
.empty-text { font-size: 26rpx; color: var(--color-text-tertiary); }
</style>
