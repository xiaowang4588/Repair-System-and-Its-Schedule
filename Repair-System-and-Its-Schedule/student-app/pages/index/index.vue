<template>
    <view class="page">
        <!-- 顶部欢迎横幅 -->
        <view class="welcome-banner">
            <view class="welcome-left">
                <text class="welcome-hi">Hi，{{ studentName || '同学' }}</text>
                <text class="welcome-sub">今天有什么设备需要报修吗？</text>
            </view>
            <view class="welcome-avatar" @click="goProfile">
                <text class="avatar-text">{{ studentName ? studentName[0] : '?' }}</text>
            </view>
        </view>

        <!-- 快捷操作 -->
        <view class="section-card">
            <view class="section-title">快捷操作</view>
            <view class="quick-grid">
                <view class="quick-item" @click="switchTo('/pages/repair/repair')">
                    <view class="quick-icon-wrap bg-blue">
                        <text class="quick-icon">&#x1f527;</text>
                    </view>
                    <text class="quick-text">提交报修</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/repair/list')">
                    <view class="quick-icon-wrap bg-amber">
                        <text class="quick-icon">&#x1f4cb;</text>
                    </view>
                    <text class="quick-text">全部记录</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/course/schedule')">
                    <view class="quick-icon-wrap bg-green">
                        <text class="quick-icon">&#x1f4c5;</text>
                    </view>
                    <text class="quick-text">课表查询</text>
                </view>
                <view class="quick-item" @click="switchTo('/pages/guide/index')">
                    <view class="quick-icon-wrap bg-orange">
                        <text class="quick-icon">&#x1f4da;</text>
                    </view>
                    <text class="quick-text">防坑指南</text>
                </view>
            </view>
        </view>

        <!-- 最新报修动态 -->
        <view class="section-card">
            <view class="section-header">
                <view class="section-title">报修动态</view>
                <text class="section-link" @click="goToList">查看全部</text>
            </view>

            <view v-if="recentList.length === 0" class="empty-state">
                <text class="empty-icon">&#x1f4ed;</text>
                <text class="empty-text">暂无报修记录</text>
            </view>

            <view v-for="item in recentList" :key="item.id" class="record-item">
                <view class="record-dot" :class="statusDotClass(item.status)"></view>
                <view class="record-body">
                    <view class="record-top">
                        <text class="record-title">{{ item.classroom || '未知位置' }}</text>
                        <view class="record-status" :class="statusClass(item.status)">
                            {{ item.status || '未知' }}
                        </view>
                    </view>
                    <view class="record-bottom">
                        <text class="record-type">{{ item.fault_type || '' }}</text>
                        <text class="record-time">{{ formatTime(item.report_time) }}</text>
                    </view>
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
            studentName: '',
            recentList: []
        }
    },
    onLoad() {
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadRecentRepairs()
    },
    onShow() {
        const token = uni.getStorageSync('student_token')
        if (token) {
            this.studentName = uni.getStorageSync('student_name') || ''
            this.loadRecentRepairs()
        }
    },
    methods: {
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
        statusClass(status) {
            if (status === '未处理') return 'status-pending'
            if (status === '处理中') return 'status-processing'
            if (status === '已处理' || status === '已解决') return 'status-resolved'
            return 'status-pending'
        },
        statusDotClass(status) {
            if (status === '未处理') return 'dot-pending'
            if (status === '处理中') return 'dot-processing'
            return 'dot-resolved'
        },
        formatTime(t) {
            if (!t) return ''
            const parts = t.split(' ')
            if (parts.length >= 2) {
                return parts[0].substring(5) + ' ' + parts[1].substring(0, 5)
            }
            return t
        },
        goToList() { uni.navigateTo({ url: '/pages/repair/list' }) },
        goProfile() { uni.switchTab({ url: '/pages/profile/profile' }) },
        switchTo(url) { uni.switchTab({ url }) },
        navigateTo(url) { uni.navigateTo({ url }) }
    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: #F0F4FF;
}

/* 欢迎横幅 */
.welcome-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 48rpx 32rpx 56rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 0 0 40rpx 40rpx;
}

.welcome-left {
    flex: 1;
}

.welcome-hi {
    font-size: 38rpx;
    font-weight: 700;
    color: white;
    display: block;
    margin-bottom: 8rpx;
}

.welcome-sub {
    font-size: 26rpx;
    color: rgba(255, 255, 255, 0.8);
    display: block;
}

.welcome-avatar {
    width: 88rpx;
    height: 88rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 24rpx;
}

.avatar-text {
    font-size: 36rpx;
    font-weight: 700;
    color: white;
}

/* 卡片 */
.section-card {
    background: white;
    border-radius: 20rpx;
    padding: 28rpx;
    margin: -20rpx 24rpx 20rpx;
    position: relative;
    box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;
}

.section-title {
    font-size: 30rpx;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 20rpx;
}

.section-header .section-title {
    margin-bottom: 0;
}

.section-link {
    font-size: 24rpx;
    color: #667eea;
    font-weight: 500;
}

/* 快捷入口 */
.quick-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16rpx;
}

.quick-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20rpx 0;
    border-radius: 16rpx;
    transition: all 0.15s;
}

.quick-item:active {
    transform: scale(0.93);
}

.quick-icon-wrap {
    width: 96rpx;
    height: 96rpx;
    border-radius: 24rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12rpx;
}

.bg-blue { background: linear-gradient(135deg, #DBEAFE, #BFDBFE); }
.bg-amber { background: linear-gradient(135deg, #FEF3C7, #FDE68A); }
.bg-green { background: linear-gradient(135deg, #DCFCE7, #BBF7D0); }
.bg-orange { background: linear-gradient(135deg, #FFEDD5, #FED7AA); }

.quick-icon { font-size: 44rpx; }

.quick-text {
    font-size: 22rpx;
    color: #64748B;
    font-weight: 500;
}

/* 报修动态列表 */
.record-item {
    display: flex;
    align-items: flex-start;
    padding: 20rpx 0;
    border-bottom: 1rpx solid #F1F5F9;
}

.record-item:last-child {
    border-bottom: none;
    padding-bottom: 4rpx;
}

.record-dot {
    width: 16rpx;
    height: 16rpx;
    border-radius: 50%;
    margin-top: 10rpx;
    margin-right: 20rpx;
    flex-shrink: 0;
}

.dot-pending { background: #F59E0B; }
.dot-processing { background: #3B82F6; }
.dot-resolved { background: #10B981; }

.record-body {
    flex: 1;
    min-width: 0;
}

.record-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8rpx;
}

.record-title {
    font-size: 28rpx;
    font-weight: 600;
    color: #1E293B;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.record-status {
    font-size: 20rpx;
    padding: 4rpx 14rpx;
    border-radius: 8rpx;
    font-weight: 600;
    flex-shrink: 0;
    margin-left: 12rpx;
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

.record-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.record-type {
    font-size: 24rpx;
    color: #94A3B8;
}

.record-time {
    font-size: 22rpx;
    color: #CBD5E1;
}

/* 空状态 */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48rpx 0;
}

.empty-icon {
    font-size: 64rpx;
    margin-bottom: 16rpx;
    opacity: 0.5;
}

.empty-text {
    font-size: 26rpx;
    color: #94A3B8;
}
</style>
