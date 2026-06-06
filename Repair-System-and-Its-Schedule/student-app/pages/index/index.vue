<template>
    <view class="page">
        <!-- 欢迎横幅 -->
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
            <text class="section-title">快捷操作</text>
            <view class="quick-grid">
                <view class="quick-item" @click="switchTo('/pages/repair/repair')">
                    <view class="qi-wrap bg-green"><text class="qi-icon">&#x1f527;</text></view>
                    <text class="qi-text">提交报修</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/repair/list')">
                    <view class="qi-wrap bg-blue"><text class="qi-icon">&#x1f4cb;</text></view>
                    <text class="qi-text">全部记录</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/course/schedule')">
                    <view class="qi-wrap bg-orange"><text class="qi-icon">&#x1f4c5;</text></view>
                    <text class="qi-text">课表查询</text>
                </view>
                <view class="quick-item" @click="switchTo('/pages/guide/index')">
                    <view class="qi-wrap bg-amber"><text class="qi-icon">&#x1f4da;</text></view>
                    <text class="qi-text">防坑指南</text>
                </view>
            </view>
        </view>

        <!-- 报修动态 -->
        <view class="section-card">
            <view class="section-header">
                <text class="section-title">报修动态</text>
                <text class="section-link" @click="goToList">查看全部</text>
            </view>

            <view v-if="recentList.length === 0" class="empty-state">
                <text class="empty-icon">&#x1f4ed;</text>
                <text class="empty-text">暂无报修记录</text>
            </view>

            <view v-for="item in recentList" :key="item.id" class="record-item">
                <view class="record-dot" :class="dotClass(item.status)"></view>
                <view class="record-body">
                    <view class="record-top">
                        <text class="record-title">{{ item.classroom || '未知位置' }}</text>
                        <view class="record-tag" :class="tagClass(item.status)">{{ item.status }}</view>
                    </view>
                    <view class="record-bottom">
                        <text class="record-type">{{ item.fault_type }}</text>
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
    data() { return { studentName: '', recentList: [] } },
    onLoad() {
        const token = uni.getStorageSync('student_token')
        if (!token) { uni.reLaunch({ url: '/pages/login/login' }); return }
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadRecentRepairs()
    },
    onShow() {
        if (uni.getStorageSync('student_token')) {
            this.studentName = uni.getStorageSync('student_name') || ''
            this.loadRecentRepairs()
        }
    },
    methods: {
        async loadRecentRepairs() {
            try {
                const res = await request('/api/repair/list', { page: 1, page_size: 5 })
                if (res && res.status === 'ok') this.recentList = res.records || []
            } catch (e) { console.error(e) }
        },
        dotClass(s) { return s === '未处理' ? 'dot-warn' : s === '处理中' ? 'dot-info' : 'dot-ok' },
        tagClass(s) { return s === '未处理' ? 'tag-warn' : s === '处理中' ? 'tag-info' : 'tag-ok' },
        formatTime(t) {
            if (!t) return ''
            const p = t.split(' ')
            return p.length >= 2 ? p[0].substring(5) + ' ' + p[1].substring(0, 5) : t
        },
        goToList() { uni.navigateTo({ url: '/pages/repair/list' }) },
        goProfile() { uni.switchTab({ url: '/pages/profile/profile' }) },
        switchTo(url) { uni.switchTab({ url }) },
        navigateTo(url) { uni.navigateTo({ url }) }
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #F7FAF8; }

/* 欢迎横幅 */
.welcome-banner {
    background: #5BBF8A;
    padding: 48rpx 32rpx 60rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 0 0 36rpx 36rpx;
}

.welcome-left { flex: 1; }
.welcome-hi { font-size: 36rpx; font-weight: 700; color: white; display: block; margin-bottom: 6rpx; }
.welcome-sub { font-size: 26rpx; color: rgba(255,255,255,0.85); display: block; }

.welcome-avatar {
    width: 84rpx; height: 84rpx; border-radius: 50%;
    background: rgba(255,255,255,0.25);
    display: flex; align-items: center; justify-content: center;
}
.avatar-text { font-size: 34rpx; font-weight: 700; color: white; }

/* 卡片 */
.section-card {
    background: white;
    border-radius: 20rpx;
    padding: 28rpx;
    margin: -24rpx 24rpx 20rpx;
    position: relative;
    box-shadow: 0 2rpx 16rpx rgba(0,0,0,0.03);
}

.section-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 16rpx;
}

.section-title { font-size: 30rpx; font-weight: 700; color: #2D3436; margin-bottom: 20rpx; }
.section-header .section-title { margin-bottom: 0; }
.section-link { font-size: 24rpx; color: #5BBF8A; font-weight: 500; }

/* 快捷入口 */
.quick-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16rpx; }

.quick-item {
    display: flex; flex-direction: column; align-items: center;
    padding: 16rpx 0; border-radius: 16rpx;
}
.quick-item:active { transform: scale(0.93); }

.qi-wrap {
    width: 92rpx; height: 92rpx; border-radius: 22rpx;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 10rpx;
}

.bg-green { background: #E8F5EE; }
.bg-blue { background: #E3F2FD; }
.bg-orange { background: #FFF3E0; }
.bg-amber { background: #FFF8E1; }

.qi-icon { font-size: 42rpx; }
.qi-text { font-size: 22rpx; color: #636E72; font-weight: 500; }

/* 报修动态 */
.record-item {
    display: flex; align-items: flex-start;
    padding: 18rpx 0;
    border-bottom: 1rpx solid #F1F5F1;
}
.record-item:last-child { border-bottom: none; padding-bottom: 4rpx; }

.record-dot {
    width: 14rpx; height: 14rpx; border-radius: 50%;
    margin-top: 10rpx; margin-right: 18rpx; flex-shrink: 0;
}
.dot-warn { background: #FDCB6E; }
.dot-info { background: #74B9FF; }
.dot-ok { background: #55EFC4; }

.record-body { flex: 1; min-width: 0; }

.record-top {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 6rpx;
}
.record-title {
    font-size: 28rpx; font-weight: 600; color: #2D3436;
    flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.record-tag {
    font-size: 20rpx; padding: 4rpx 14rpx; border-radius: 8rpx;
    font-weight: 600; flex-shrink: 0; margin-left: 12rpx;
}
.tag-warn { background: #FFF3E0; color: #E17055; }
.tag-info { background: #E3F2FD; color: #0984E3; }
.tag-ok { background: #E8F5EE; color: #00B894; }

.record-bottom { display: flex; justify-content: space-between; align-items: center; }
.record-type { font-size: 24rpx; color: #A0A8AB; }
.record-time { font-size: 22rpx; color: #B2BEC3; }

.empty-state { display: flex; flex-direction: column; align-items: center; padding: 48rpx 0; }
.empty-icon { font-size: 60rpx; margin-bottom: 12rpx; opacity: 0.4; }
.empty-text { font-size: 26rpx; color: #A0A8AB; }
</style>
