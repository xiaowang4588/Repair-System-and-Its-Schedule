<template>
    <view class="page">
        <view class="container">
            <!-- 统计卡片 -->
            <view class="stats-grid" v-if="stats">
                <view class="stat-card">
                    <text class="stat-value">{{ stats.total_courses }}</text>
                    <text class="stat-label">总课程数</text>
                </view>
                <view class="stat-card">
                    <text class="stat-value">{{ stats.total_teachers }}</text>
                    <text class="stat-label">教师总数</text>
                </view>
                <view class="stat-card">
                    <text class="stat-value">{{ stats.total_classrooms }}</text>
                    <text class="stat-label">教室总数</text>
                </view>
                <view class="stat-card">
                    <text class="stat-value">{{ stats.total_colleges }}</text>
                    <text class="stat-label">开课学院</text>
                </view>
            </view>

            <!-- 教师排行 -->
            <view class="card" v-if="stats && stats.top_teachers">
                <view class="card-title">👨‍🏫 授课量 Top 10 教师</view>
                <view class="rank-list">
                    <view class="rank-item" v-for="(count, name, index) in stats.top_teachers" :key="name">
                        <view class="rank-num" :class="{ gold: index === 0, silver: index === 1, bronze: index === 2 }">
                            {{ index + 1 }}
                        </view>
                        <text class="rank-name">{{ name }}</text>
                        <text class="rank-value">{{ count }} 节</text>
                    </view>
                </view>
            </view>

            <!-- 教室排行 -->
            <view class="card" v-if="stats && stats.top_classrooms">
                <view class="card-title">🏫 使用率 Top 10 教室</view>
                <view class="rank-list">
                    <view class="rank-item" v-for="(count, room, index) in stats.top_classrooms" :key="room">
                        <view class="rank-num" :class="{ gold: index === 0, silver: index === 1, bronze: index === 2 }">
                            {{ index + 1 }}
                        </view>
                        <text class="rank-name">{{ room }}</text>
                        <text class="rank-value">{{ count }} 次</text>
                    </view>
                </view>
            </view>

            <!-- 星期分布 -->
            <view class="card" v-if="stats && stats.courses_per_day">
                <view class="card-title">📅 各星期课程分布</view>
                <view class="day-list">
                    <view class="day-item" v-for="(count, day) in stats.courses_per_day" :key="day">
                        <text class="day-name">{{ weekdayNames[day - 1] || day }}</text>
                        <view class="day-bar">
                            <view class="day-fill" :style="{ width: getBarWidth(count) }"></view>
                        </view>
                        <text class="day-count">{{ count }}</text>
                    </view>
                </view>
            </view>

            <!-- 加载中 -->
            <view class="loading" v-if="!stats">
                加载中...
            </view>
        </view>
    </view>
</template>

<script>
import { getStats } from '@/api/index.js'

export default {
    data() {
        return {
            stats: null,
            weekdayNames: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            maxDayCount: 0
        }
    },
    onLoad() {
        this.loadStats()
    },
    methods: {
        async loadStats() {
            try {
                const res = await getStats()
                if (res.status === 'ok') {
                    this.stats = res.data
                    // 计算最大值用于进度条
                    if (res.data.courses_per_day) {
                        this.maxDayCount = Math.max(...Object.values(res.data.courses_per_day))
                    }
                }
            } catch (e) {
                console.error('获取统计失败:', e)
            }
        },
        getBarWidth(count) {
            if (this.maxDayCount === 0) return '0%'
            return (count / this.maxDayCount * 100) + '%'
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

.stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16rpx;
    margin-bottom: 24rpx;
}

.stat-card {
    background: #4F7CFF;
    border-radius: 16rpx;
    padding: 32rpx;
    text-align: center;
    color: white;
}

.stat-card:nth-child(2) {
    background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.stat-card:nth-child(3) {
    background: linear-gradient(135deg, #fa8c16 0%, #d46b08 100%);
}

.stat-card:nth-child(4) {
    background: linear-gradient(135deg, #eb2f96 0%, #c41d7f 100%);
}

.stat-value {
    font-size: 48rpx;
    font-weight: 700;
    display: block;
    margin-bottom: 8rpx;
}

.stat-label {
    font-size: 24rpx;
    opacity: 0.9;
}

.rank-list {
    margin-top: 16rpx;
}

.rank-item {
    display: flex;
    align-items: center;
    padding: 20rpx 0;
    border-bottom: 1rpx solid #f5f5f5;
}

.rank-item:last-child {
    border-bottom: none;
}

.rank-num {
    width: 48rpx;
    height: 48rpx;
    border-radius: 50%;
    background: #F5F7FA;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24rpx;
    font-weight: 600;
    color: #666;
    margin-right: 16rpx;
}

.rank-num.gold {
    background: linear-gradient(135deg, #ffd700, #ffaa00);
    color: white;
}

.rank-num.silver {
    background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
    color: white;
}

.rank-num.bronze {
    background: linear-gradient(135deg, #cd7f32, #b06020);
    color: white;
}

.rank-name {
    flex: 1;
    font-size: 28rpx;
    color: #333;
}

.rank-value {
    font-size: 28rpx;
    color: #4F7CFF;
    font-weight: 600;
}

.day-list {
    margin-top: 16rpx;
}

.day-item {
    display: flex;
    align-items: center;
    padding: 16rpx 0;
}

.day-name {
    width: 80rpx;
    font-size: 26rpx;
    color: #666;
}

.day-bar {
    flex: 1;
    height: 32rpx;
    background: #F5F7FA;
    border-radius: 16rpx;
    margin: 0 16rpx;
    overflow: hidden;
}

.day-fill {
    height: 100%;
    background: #4F7CFF;
    border-radius: 16rpx;
    transition: width 0.3s;
}

.day-count {
    width: 80rpx;
    text-align: right;
    font-size: 26rpx;
    color: #333;
    font-weight: 600;
}
</style>
