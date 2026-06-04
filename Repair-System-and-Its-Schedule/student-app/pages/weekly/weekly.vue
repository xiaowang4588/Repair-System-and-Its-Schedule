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
.page {
    min-height: 100vh;
    background: #F5F7FA;
}

.container {
    padding: 24rpx;
}

.type-switch {
    display: flex;
    gap: 16rpx;
}

.type-btn {
    flex: 1;
    height: 80rpx;
    line-height: 80rpx;
    text-align: center;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    color: #666;
    background: white;
}

.type-btn.active {
    background: #4F7CFF;
    color: white;
    border-color: #4F7CFF;
}

.table-scroll {
    width: 100%;
}

.table {
    min-width: 900rpx;
}

.table-header {
    display: flex;
    background: #fafafa;
    border-bottom: 1rpx solid #f0f0f0;
}

.table-row {
    display: flex;
    border-bottom: 1rpx solid #f5f5f5;
}

.table-cell {
    flex: 1;
    padding: 16rpx 8rpx;
    font-size: 24rpx;
    color: #555;
    min-height: 100rpx;
    text-align: center;
}

.section-cell {
    width: 120rpx;
    flex: none;
    background: #f0f5ff;
    font-weight: 600;
    color: #333;
    display: flex;
    align-items: center;
    justify-content: center;
}

.course-block {
    background: linear-gradient(135deg, #e8f0fe 0%, #d4e4fc 100%);
    border-radius: 8rpx;
    padding: 12rpx;
    margin-bottom: 8rpx;
    border-left: 4rpx solid #4F7CFF;
    text-align: left;
}

.course-name {
    font-size: 24rpx;
    font-weight: 600;
    color: #333;
    display: block;
}

.course-teacher {
    font-size: 22rpx;
    color: #666;
    display: block;
    margin-top: 4rpx;
}

.course-room {
    font-size: 22rpx;
    color: #666;
    display: block;
    margin-top: 4rpx;
}
</style>
