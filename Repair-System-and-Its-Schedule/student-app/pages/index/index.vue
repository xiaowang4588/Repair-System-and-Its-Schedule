<template>
    <view class="page">
        <!-- 快捷操作入口 -->
        <view class="section-card">
            <view class="section-title">快捷操作</view>
            <view class="quick-grid">
                <view class="quick-item" @click="switchTo('/pages/repair/repair')">
                    <view class="quick-icon-wrap" style="background:#EEF2FF;">
                        <text class="quick-icon">&#x1f527;</text>
                    </view>
                    <text class="quick-text">提交报修</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/repair/list')">
                    <view class="quick-icon-wrap" style="background:#FEF3C7;">
                        <text class="quick-icon">&#x1f4cb;</text>
                    </view>
                    <text class="quick-text">全部记录</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/course/schedule')">
                    <view class="quick-icon-wrap" style="background:#DCFCE7;">
                        <text class="quick-icon">&#x1f4c5;</text>
                    </view>
                    <text class="quick-text">课表查询</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/empty/empty')">
                    <view class="quick-icon-wrap" style="background:#F3E8FF;">
                        <text class="quick-icon">&#x1f3eb;</text>
                    </view>
                    <text class="quick-text">空教室</text>
                </view>
                <view class="quick-item" @click="switchTo('/pages/guide/index')">
                    <view class="quick-icon-wrap" style="background:#FFF7ED;">
                        <text class="quick-icon">&#x1f4da;</text>
                    </view>
                    <text class="quick-text">防坑指南</text>
                </view>
            </view>
        </view>

        <!-- 报修动态 -->
        <view class="section-card">
            <view class="section-title">
                <text>报修动态</text>
                <text class="section-sub">最新报修</text>
            </view>
            <view v-if="recentList.length === 0" class="empty-tip">暂无报修记录</view>
            <view v-for="item in recentList" :key="item.id" class="record-item">
                <view class="record-left">
                    <view class="record-title">{{ item.classroom || '未知位置' }}</view>
                    <view class="record-desc">{{ item.fault_type || '' }}</view>
                </view>
                <view class="record-right">
                    <view class="record-status" :class="statusClass(item.status)">
                        {{ item.status || '未知' }}
                    </view>
                    <view class="record-time">{{ formatTime(item.report_time) }}</view>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
import { request } from '../../api/index.js'

export default {
    data() {
        return {
            recentList: []
        }
    },
    onLoad() {
        // 检查登录状态
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        this.loadRecentRepairs()
    },
    onShow() {
        // 每次显示页面刷新数据
        const token = uni.getStorageSync('student_token')
        if (token) {
            this.loadRecentRepairs()
        }
    },
    methods: {
        // 获取最新5条报修动态
        async loadRecentRepairs() {
            try {
                const res = await request('/api/repair/list', { page: 1, page_size: 5 })
                if (res && res.status === 'ok') {
                    this.recentList = res.records || []
                }
            } catch (e) {
                console.error('获取报修动态失败:', e)
            }
        },
        // 状态样式类映射
        statusClass(status) {
            if (status === '未处理') return 'status-pending'
            if (status === '处理中') return 'status-processing'
            if (status === '已处理' || status === '已解决') return 'status-resolved'
            return 'status-pending'
        },
        // 时间格式化（report_time 是字符串如 "2024-01-15 10:30"）
        formatTime(t) {
            if (!t) return ''
            // 取月-日 时:分 部分
            const parts = t.split(' ')
            if (parts.length >= 2) {
                const datePart = parts[0] // 2024-01-15
                const timePart = parts[1] // 10:30
                const md = datePart.substring(5) // 01-15
                return `${md} ${timePart.substring(0, 5)}`
            }
            return t
        },
        // 跳转到报修记录
        goToList(filter) {
            uni.navigateTo({ url: '/pages/repair/list' })
        },
        // Tab页跳转
        switchTo(url) {
            uni.switchTab({ url })
        },
        // 普通页跳转
        navigateTo(url) {
            uni.navigateTo({ url })
        }
    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: #F5F7FA;
    padding: 20rpx;
}

/* 通用卡片 */
.section-card {
    background: #fff;
    border-radius: 16rpx;
    padding: 24rpx;
    margin-bottom: 16rpx;
}

.section-title {
    font-size: 30rpx;
    font-weight: 600;
    color: #1F2937;
    margin-bottom: 20rpx;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.section-sub {
    font-size: 22rpx;
    font-weight: 400;
    color: #9CA3AF;
}

/* 快捷入口 */
.quick-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12rpx;
}

.quick-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16rpx 0;
    border-radius: 12rpx;
    transition: all 0.15s;
}

.quick-item:active {
    transform: scale(0.95);
    background: #F5F7FA;
}

.quick-icon-wrap {
    width: 88rpx;
    height: 88rpx;
    border-radius: 20rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10rpx;
}

.quick-icon { font-size: 40rpx; }

.quick-text {
    font-size: 22rpx;
    color: #6B7280;
}

/* 报修记录列表 */
.record-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16rpx 0;
    border-bottom: 1rpx solid #F3F4F6;
}

.record-item:last-child { border-bottom: none; }

.record-left {
    flex: 1;
    margin-right: 16rpx;
}

.record-title {
    font-size: 28rpx;
    font-weight: 600;
    color: #1F2937;
    margin-bottom: 4rpx;
}

.record-desc {
    font-size: 22rpx;
    color: #9CA3AF;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.record-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    flex-shrink: 0;
}

.record-status {
    font-size: 20rpx;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;
    margin-bottom: 6rpx;
    font-weight: 500;
}

.status-pending {
    background: #FEF3C7;
    color: #D97706;
}

.status-processing {
    background: #DBEAFE;
    color: #2563EB;
}

.status-resolved {
    background: #DCFCE7;
    color: #16A34A;
}

.record-time {
    font-size: 20rpx;
    color: #9CA3AF;
}

.empty-tip {
    text-align: center;
    padding: 40rpx 0;
    font-size: 26rpx;
    color: #9CA3AF;
}
</style>
