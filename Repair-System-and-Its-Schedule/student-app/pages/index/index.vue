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

            <!-- 加载骨架 -->
            <view v-if="loadingRepairs" class="loading-area">
                <view class="spinner"></view>
                <text class="loading-text">加载中...</text>
            </view>

            <view v-else-if="recentList.length === 0" class="empty-state">
                <text class="empty-icon">&#x1f4ed;</text>
                <text class="empty-text">暂无报修记录</text>
            </view>

            <view v-if="!loadingRepairs" v-for="item in recentList" :key="item.id" class="record-item">
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
            recentList: [],
            loadingRepairs: false
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
        // 每次显示时检查 token 是否还有效（防止服务器重启后旧 token 失效）
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadRecentRepairs()
    },
    methods: {
        async loadRecentRepairs() {
            this.loadingRepairs = true
            try {
                const res = await request('/api/repair/list', { page: 1, page_size: 5 })
                if (res && res.status === 'ok') {
                    this.recentList = res.records || []
                }
            } catch (e) {
                console.error('获取报修动态失败:', e)
            } finally {
                this.loadingRepairs = false
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
    background: var(--color-bg);
    padding-bottom: 24rpx;
}

/* ---- 欢迎横幅（渐变 + 装饰圆）---- */
.welcome-banner {
    background: var(--color-primary-gradient);
    padding: 56rpx 32rpx 72rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 0 0 40rpx 40rpx;
    position: relative;
    overflow: hidden;
}
/* 装饰光斑 */
.welcome-banner::before {
    content: '';
    position: absolute;
    top: -80rpx;
    right: -60rpx;
    width: 240rpx;
    height: 240rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
}
.welcome-banner::after {
    content: '';
    position: absolute;
    bottom: -40rpx;
    left: 20%;
    width: 160rpx;
    height: 160rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.04);
}

.welcome-left {
    flex: 1;
    position: relative;
    z-index: 1;
}

.welcome-hi {
    font-size: 40rpx;
    font-weight: 700;
    color: white;
    display: block;
    margin-bottom: 6rpx;
    letter-spacing: 1rpx;
}

.welcome-sub {
    font-size: 26rpx;
    color: rgba(255, 255, 255, 0.75);
    display: block;
}

.welcome-avatar {
    width: 88rpx;
    height: 88rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(10rpx);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 24rpx;
    position: relative;
    z-index: 1;
    border: 2rpx solid rgba(255, 255, 255, 0.25);
    transition: transform var(--transition-fast);
}
.welcome-avatar:active {
    transform: scale(0.92);
}

.avatar-text {
    font-size: 36rpx;
    font-weight: 700;
    color: white;
}

/* ---- 快捷入口卡片 ---- */
.section-card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 28rpx;
    margin: -24rpx 24rpx 20rpx;
    position: relative;
    box-shadow: var(--shadow-md);
    border: 1rpx solid var(--color-border-light);
    animation: fadeInUp 0.4s ease both;
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
    color: var(--color-text);
    margin-bottom: 20rpx;
}

.section-header .section-title {
    margin-bottom: 0;
}

.section-link {
    font-size: 24rpx;
    color: var(--color-primary);
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 4rpx;
}
.section-link::after {
    content: '\203A';
    font-size: 28rpx;
}

/* ---- 快捷入口网格 ---- */
.quick-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12rpx;
}

.quick-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20rpx 8rpx;
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    position: relative;
}
.quick-item:active {
    transform: scale(0.93);
    background: var(--color-bg-secondary);
}

.quick-icon-wrap {
    width: 96rpx;
    height: 96rpx;
    border-radius: 26rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12rpx;
    transition: transform var(--transition-fast);
}
.quick-item:active .quick-icon-wrap {
    transform: scale(0.9);
}

.bg-blue   { background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); }
.bg-amber  { background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); }
.bg-green  { background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%); }
.bg-orange { background: linear-gradient(135deg, #FFEDD5 0%, #FED7AA 100%); }

.quick-icon { font-size: 44rpx; }

.quick-text {
    font-size: 22rpx;
    color: var(--color-text-secondary);
    font-weight: 500;
}

/* ---- 报修动态列表 ---- */
.record-item {
    display: flex;
    align-items: flex-start;
    padding: 20rpx 0;
    border-bottom: 1rpx solid var(--color-divider);
    transition: background var(--transition-fast);
    border-radius: var(--radius-xs);
    margin: 0 -8rpx;
    padding-left: 8rpx;
    padding-right: 8rpx;
}
.record-item:active {
    background: var(--color-bg-secondary);
}
.record-item:last-child {
    border-bottom: none;
    padding-bottom: 4rpx;
}

.record-dot {
    width: 14rpx;
    height: 14rpx;
    border-radius: 50%;
    margin-top: 10rpx;
    margin-right: 18rpx;
    flex-shrink: 0;
    position: relative;
}
/* 发光脉冲 */
.record-dot::after {
    content: '';
    position: absolute;
    inset: -4rpx;
    border-radius: 50%;
    opacity: 0.3;
}
.dot-pending {
    background: var(--color-warning);
    box-shadow: 0 0 10rpx rgba(245, 158, 11, 0.35);
}
.dot-processing {
    background: var(--color-info);
    box-shadow: 0 0 10rpx rgba(59, 130, 246, 0.35);
}
.dot-resolved {
    background: var(--color-success);
    box-shadow: 0 0 10rpx rgba(16, 185, 129, 0.35);
}

.record-body {
    flex: 1;
    min-width: 0;
}

.record-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6rpx;
}

.record-title {
    font-size: 28rpx;
    font-weight: 600;
    color: var(--color-text);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.record-status {
    font-size: 20rpx;
    padding: 4rpx 14rpx;
    border-radius: var(--radius-xs);
    font-weight: 600;
    flex-shrink: 0;
    margin-left: 12rpx;
    letter-spacing: 0.5rpx;
}

.status-pending {
    background: var(--color-warning-bg);
    color: #D97706;
}
.status-processing {
    background: var(--color-info-bg);
    color: #2563EB;
}
.status-resolved {
    background: var(--color-success-bg);
    color: var(--color-success);
}

.record-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.record-type {
    font-size: 24rpx;
    color: var(--color-text-tertiary);
}

.record-time {
    font-size: 22rpx;
    color: var(--color-text-placeholder);
}

/* ---- 加载动画 ---- */
.loading-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60rpx 0;
}
.spinner {
    width: 44rpx;
    height: 44rpx;
    border: 3rpx solid var(--color-border);
    border-top: 3rpx solid var(--color-primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    margin-bottom: 16rpx;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
.loading-text {
    font-size: 24rpx;
    color: var(--color-text-tertiary);
}

/* ---- 空状态 ---- */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48rpx 0;
}
.empty-state .empty-icon {
    font-size: 64rpx;
    margin-bottom: 16rpx;
    opacity: 0.45;
}
.empty-state .empty-text {
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}
</style>
