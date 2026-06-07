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
            <view class="loading-area" v-if="!stats">
                <view class="spinner-ring"></view>
                <text>加载中...</text>
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
    background: var(--color-bg);
}

.container {
    padding: 24rpx;
}

/* ---- 统计卡片网格 ---- */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16rpx;
    margin-bottom: 24rpx;
}

.stat-card {
    border-radius: var(--radius-lg);
    padding: 36rpx 28rpx;
    text-align: center;
    color: white;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-md);
    transition: transform var(--transition-fast);
}
.stat-card:active {
    transform: scale(0.96);
}
/* 装饰圆 */
.stat-card::after {
    content: '';
    position: absolute;
    top: -24rpx;
    right: -24rpx;
    width: 100rpx;
    height: 100rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.12);
}

.stat-card:nth-child(1) {
    background: linear-gradient(135deg, #6C5CE7 0%, #8B7CF6 100%);
}
.stat-card:nth-child(2) {
    background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
}
.stat-card:nth-child(3) {
    background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
}
.stat-card:nth-child(4) {
    background: linear-gradient(135deg, #EC4899 0%, #F472B6 100%);
}

.stat-value {
    font-size: 52rpx;
    font-weight: 700;
    display: block;
    margin-bottom: 6rpx;
    position: relative;
    z-index: 1;
}

.stat-label {
    font-size: 24rpx;
    opacity: 0.88;
    position: relative;
    z-index: 1;
    font-weight: 500;
}

/* ---- 排行卡片 ---- */
.card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 28rpx;
    margin-bottom: 20rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
}

.card-title {
    font-size: 30rpx;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 8rpx;
    padding-bottom: 16rpx;
    border-bottom: 1rpx solid var(--color-divider);
}

.rank-list {
    margin-top: 8rpx;
}

.rank-item {
    display: flex;
    align-items: center;
    padding: 18rpx 0;
    border-bottom: 1rpx solid var(--color-divider);
    transition: background var(--transition-fast);
    border-radius: var(--radius-xs);
    margin: 0 -8rpx;
    padding-left: 8rpx;
    padding-right: 8rpx;
}
.rank-item:last-child {
    border-bottom: none;
}

.rank-num {
    width: 48rpx;
    height: 48rpx;
    border-radius: 50%;
    background: var(--color-bg-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24rpx;
    font-weight: 600;
    color: var(--color-text-secondary);
    margin-right: 16rpx;
    flex-shrink: 0;
}

.rank-num.gold {
    background: linear-gradient(135deg, #FCD34D, #F59E0B);
    color: white;
    box-shadow: 0 4rpx 12rpx rgba(245, 158, 11, 0.3);
}
.rank-num.silver {
    background: linear-gradient(135deg, #CBD5E1, #94A3B8);
    color: white;
    box-shadow: 0 4rpx 12rpx rgba(148, 163, 184, 0.3);
}
.rank-num.bronze {
    background: linear-gradient(135deg, #FED7AA, #F97316);
    color: white;
    box-shadow: 0 4rpx 12rpx rgba(249, 115, 22, 0.3);
}

.rank-name {
    flex: 1;
    font-size: 28rpx;
    color: var(--color-text);
    font-weight: 500;
}

.rank-value {
    font-size: 26rpx;
    color: var(--color-primary);
    font-weight: 600;
}

/* ---- 星期分布 ---- */
.day-list {
    margin-top: 8rpx;
}

.day-item {
    display: flex;
    align-items: center;
    padding: 14rpx 0;
}

.day-name {
    width: 72rpx;
    font-size: 26rpx;
    color: var(--color-text-secondary);
    font-weight: 500;
}

.day-bar {
    flex: 1;
    height: 28rpx;
    background: var(--color-bg);
    border-radius: 14rpx;
    margin: 0 16rpx;
    overflow: hidden;
}

.day-fill {
    height: 100%;
    background: var(--color-accent-gradient);
    border-radius: 14rpx;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    min-width: 0;
}

.day-count {
    width: 64rpx;
    text-align: right;
    font-size: 26rpx;
    color: var(--color-text);
    font-weight: 600;
}

/* ---- 加载动画 ---- */
.loading-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60rpx 0;
    gap: 12rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}
.spinner-ring {
    width: 48rpx;
    height: 48rpx;
    border: 3rpx solid var(--color-border);
    border-top: 3rpx solid var(--color-primary);
    border-radius: 50%;
    animation: stats-spin 0.7s linear infinite;
}
@keyframes stats-spin {
    to { transform: rotate(360deg); }
}
</style>
