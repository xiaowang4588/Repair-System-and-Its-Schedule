<template>
    <view class="page">
        <!-- 查询表单 -->
        <view class="container">
            <view class="card">
                <view class="card-title">按时间 + 教室查询</view>
                <view class="form-group">
                    <text class="form-label">星期几</text>
                    <picker :range="weekdayOptions" range-key="label" @change="onWeekdayChange">
                        <view class="form-select">
                            {{ weekdayOptions[weekdayIndex].label }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group">
                    <text class="form-label">上课节次</text>
                    <picker :range="sectionOptions" range-key="label" @change="onSectionChange">
                        <view class="form-select">
                            {{ sectionOptions[sectionIndex].label }}
                            <text class="arrow">▼</text>
                        </view>
                    </picker>
                </view>
                <view class="form-group">
                    <text class="form-label">教室关键词</text>
                    <input class="form-input" v-model="classroom" placeholder="例：405 或 贤者楼" />
                </view>
                <button class="btn-primary" @click="doQuery">🔍 查询</button>
            </view>

            <!-- 查询结果 -->
            <view class="card" v-if="results.length > 0">
                <view class="result-count">
                    共找到 <text class="count-num">{{ results.length }}</text> 条结果
                </view>
                <view class="result-list">
                    <view class="result-item" v-for="(item, index) in results" :key="index">
                        <view class="result-header">
                            <text class="result-name">{{ item.course_name }}</text>
                            <text class="copy-btn" @click="copyInfo(item)">复制</text>
                        </view>
                        <view class="result-row">
                            <text class="result-label">👨‍🏫 教师</text>
                            <text class="result-value">{{ item.teacher }}（{{ item.teacher_id }}）</text>
                        </view>
                        <view class="result-row">
                            <text class="result-label">🏛️ 学院</text>
                            <text class="result-value">{{ item.college }}</text>
                        </view>
                        <view class="result-row">
                            <text class="result-label">👥 班级</text>
                            <text class="result-value">{{ item.class }}</text>
                        </view>
                        <view class="result-row">
                            <text class="result-label">🕐 时间</text>
                            <text class="result-value">{{ item.time }}</text>
                        </view>
                        <view class="result-row">
                            <text class="result-label">📍 地点</text>
                            <text class="result-value">{{ item.classroom }}</text>
                        </view>
                    </view>
                </view>
            </view>

            <!-- 空结果 -->
            <view class="card" v-else-if="queried">
                <view class="empty">
                    <text class="empty-icon">📭</text>
                    <text class="empty-text">暂无匹配课程，请调整查询条件</text>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
import { queryCourses, getTime } from '@/api/index.js'

export default {
    data() {
        return {
            weekdayIndex: 0,
            sectionIndex: 0,
            classroom: '',
            results: [],
            queried: false,
            weekdayOptions: [
                { label: '周一（1）', value: '1' },
                { label: '周二（2）', value: '2' },
                { label: '周三（3）', value: '3' },
                { label: '周四（4）', value: '4' },
                { label: '周五（5）', value: '5' },
                { label: '周六（6）', value: '6' },
                { label: '周日（7）', value: '7' }
            ],
            sectionOptions: [
                { label: '1-2节（08:00-09:40）', value: '1-2节' },
                { label: '3-4节（10:05-11:45）', value: '3-4节' },
                { label: '5-6节（14:00-15:40）', value: '5-6节' },
                { label: '7-8节（16:05-17:45）', value: '7-8节' },
                { label: '9-10节（19:00-20:40）', value: '9-10节' },
                { label: '11-12节（20:50-22:30）', value: '11-12节' }
            ]
        }
    },
    onLoad() {
        this.initTime()
    },
    methods: {
        async initTime() {
            try {
                const res = await getTime()
                if (res.status === 'ok') {
                    const weekday = res.data.weekday
                    const index = this.weekdayOptions.findIndex(opt => opt.value === String(weekday))
                    if (index >= 0) this.weekdayIndex = index

                    if (res.data.current_section) {
                        const sectionIndex = this.sectionOptions.findIndex(opt => opt.value === res.data.current_section)
                        if (sectionIndex >= 0) this.sectionIndex = sectionIndex
                    }
                }
            } catch (e) {
                console.error('获取时间失败:', e)
            }
        },
        onWeekdayChange(e) {
            this.weekdayIndex = e.detail.value
        },
        onSectionChange(e) {
            this.sectionIndex = e.detail.value
        },
        async doQuery() {
            if (!this.classroom.trim()) {
                uni.showToast({ title: '请输入教室关键词', icon: 'none' })
                return
            }

            uni.showLoading({ title: '查询中...' })
            try {
                const res = await queryCourses({
                    day_of_week: this.weekdayOptions[this.weekdayIndex].value,
                    section: this.sectionOptions[this.sectionIndex].value,
                    classroom: this.classroom.trim()
                })

                if (res.status === 'ok') {
                    this.results = res.data
                    this.queried = true
                } else {
                    uni.showToast({ title: res.message, icon: 'none' })
                }
            } catch (e) {
                uni.showToast({ title: '查询失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
        },
        copyInfo(item) {
            const text = `课程名称：${item.course_name}\n授课教师：${item.teacher}（${item.teacher_id}）\n开课学院：${item.college}\n授课班级：${item.class}\n上课时间：${item.time}\n上课地点：${item.classroom}`
            uni.setClipboardData({
                data: text,
                success: () => {
                    uni.showToast({ title: '已复制', icon: 'success' })
                }
            })
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

.form-select { display: flex; justify-content: space-between; align-items: center; width: 100%; height: 88rpx; padding: 0 24rpx; border: 2rpx solid var(--color-border); border-radius: var(--radius-sm); font-size: 28rpx; color: var(--color-text); background: var(--color-bg-secondary); box-sizing: border-box; }
.arrow { font-size: 20rpx; color: var(--color-text-tertiary); }

.form-input { width: 100%; height: 88rpx; padding: 0 24rpx; border: 2rpx solid var(--color-border); border-radius: var(--radius-sm); font-size: 28rpx; color: var(--color-text); background: var(--color-bg-secondary); box-sizing: border-box; transition: all var(--transition-fast); }
.form-input:focus { border-color: var(--color-primary); background: var(--color-surface); box-shadow: 0 0 0 4rpx rgba(108,92,231,0.06); }

.btn-primary { width: 100%; height: 88rpx; line-height: 88rpx; background: var(--color-primary-gradient); color: white; border: none; border-radius: var(--radius-md); font-size: 30rpx; font-weight: 600; box-shadow: 0 4rpx 16rpx rgba(108,92,231,0.25); transition: all var(--transition-fast); }
.btn-primary:active { transform: translateY(2rpx) scale(0.98); }

.result-count { font-size: 28rpx; color: var(--color-text-secondary); margin-bottom: 24rpx; }
.count-num { color: var(--color-primary); font-weight: 700; font-size: 32rpx; }

.result-item { padding: 24rpx 0; border-bottom: 1rpx solid var(--color-divider); }
.result-item:last-child { border-bottom: none; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.result-name { font-size: 32rpx; font-weight: 700; color: var(--color-text); flex: 1; }
.copy-btn { padding: 8rpx 22rpx; background: var(--color-accent-gradient); color: white; border-radius: var(--radius-xs); font-size: 24rpx; flex-shrink: 0; font-weight: 500; box-shadow: 0 2rpx 8rpx rgba(79,124,255,0.2); transition: all var(--transition-fast); }
.copy-btn:active { transform: scale(0.93); }

.result-row { display: flex; align-items: flex-start; padding: 8rpx 0; font-size: 26rpx; }
.result-label { width: 120rpx; color: var(--color-text-tertiary); flex-shrink: 0; }
.result-value { flex: 1; color: var(--color-text-secondary); }

.empty { display: flex; flex-direction: column; align-items: center; padding: 60rpx 0; }
.empty-icon { font-size: 80rpx; margin-bottom: 16rpx; opacity: 0.45; }
.empty-text { font-size: 26rpx; color: var(--color-text-tertiary); }
</style>
