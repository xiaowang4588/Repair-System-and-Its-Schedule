<template>
    <view class="page">
        <!-- 顶部欢迎横幅 -->
        <view class="welcome-banner">
            <view class="welcome-left">
                <text class="welcome-hi">{{ studentName || '同学' }}</text>
                <text class="welcome-sub">今天有什么设备需要报修吗</text>
            </view>
            <view class="welcome-avatar" @click="goProfile">
                <text class="avatar-text">{{ studentName ? studentName[0] : '?' }}</text>
            </view>
        </view>

        <!-- 快捷操作 -->
        <view class="section-card quick-card">
            <view class="quick-grid">
                <view class="quick-item" @click="switchTo('/pages/repair/repair')">
                    <view class="qi qi-green">
                        <view class="qi-icon">
                            <view class="icon-wrench"></view>
                        </view>
                    </view>
                    <text class="qi-text">提交报修</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/repair/list')">
                    <view class="qi qi-slate">
                        <view class="qi-icon">
                            <view class="icon-list"></view>
                        </view>
                    </view>
                    <text class="qi-text">全部记录</text>
                </view>
                <view class="quick-item" @click="navigateTo('/pages/course/schedule')">
                    <view class="qi qi-blue">
                        <view class="qi-icon">
                            <view class="icon-calendar"></view>
                        </view>
                    </view>
                    <text class="qi-text">课表查询</text>
                </view>
                <view class="quick-item" @click="switchTo('/pages/guide/index')">
                    <view class="qi qi-amber">
                        <view class="qi-icon">
                            <view class="icon-book"></view>
                        </view>
                    </view>
                    <text class="qi-text">防坑指南</text>
                </view>
            </view>
        </view>

        <!-- 最新报修动态 -->
        <view class="section-card">
            <view class="section-header">
                <text class="section-title">最近报修</text>
                <text class="section-link" @click="goToList">全部</text>
            </view>

            <view v-if="recentList.length === 0" class="empty-state">
                <view class="empty-circle">
                    <view class="icon-inbox"></view>
                </view>
                <text class="empty-text">暂无报修记录</text>
                <text class="empty-hint">点击上方「提交报修」开始</text>
            </view>

            <view v-for="(item, idx) in recentList" :key="item.id" class="record-item"
                  :class="{ 'record-last': idx === recentList.length - 1 }">
                <view class="record-left">
                    <view class="record-dot" :class="dotClass(item.status)"></view>
                    <view class="record-body">
                        <text class="record-title">{{ item.classroom || '未知位置' }}</text>
                        <text class="record-desc">{{ item.fault_type || '' }} · {{ formatTime(item.report_time) }}</text>
                    </view>
                </view>
                <view class="record-tag" :class="tagClass(item.status)">{{ item.status }}</view>
            </view>
        </view>

        <!-- 底部留白 -->
        <view style="height: 40rpx;"></view>
    </view>
</template>

<script>
import { request } from '../../api/index.js'

export default {
    data() {
        return { studentName: '', recentList: [] }
    },
    onLoad() {
        const token = uni.getStorageSync('student_token')
        if (!token) { uni.reLaunch({ url: '/pages/login/login' }); return }
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadRecentRepairs()
    },
    onShow() {
        if (!uni.getStorageSync('student_token')) {
            uni.reLaunch({ url: '/pages/login/login' }); return
        }
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadRecentRepairs()
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
.page { min-height: 100vh; background: #F5F6F8; }

/* ===== 欢迎横幅 ===== */
.welcome-banner {
    background: #3D5A3E;
    padding: 52rpx 36rpx 64rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 0 0 44rpx 44rpx;
    position: relative;
    overflow: hidden;
}
.welcome-banner::after {
    content: '';
    position: absolute;
    top: -60rpx;
    right: -40rpx;
    width: 240rpx;
    height: 240rpx;
    border-radius: 50%;
    background: rgba(255,255,255,0.06);
}
.welcome-left { flex: 1; position: relative; z-index: 1; }
.welcome-hi { font-size: 40rpx; font-weight: 700; color: #fff; display: block; margin-bottom: 8rpx; letter-spacing: 1rpx; }
.welcome-sub { font-size: 24rpx; color: rgba(255,255,255,0.65); display: block; }
.welcome-avatar {
    width: 80rpx; height: 80rpx; border-radius: 50%;
    background: rgba(255,255,255,0.15);
    border: 2rpx solid rgba(255,255,255,0.2);
    display: flex; align-items: center; justify-content: center;
    position: relative; z-index: 1;
}
.avatar-text { font-size: 32rpx; font-weight: 600; color: rgba(255,255,255,0.9); }

/* ===== 卡片 ===== */
.section-card {
    background: #fff;
    border-radius: 24rpx;
    padding: 28rpx;
    margin: -28rpx 24rpx 20rpx;
    position: relative;
    box-shadow: 0 1rpx 3rpx rgba(0,0,0,0.04), 0 8rpx 24rpx rgba(0,0,0,0.03);
}
.quick-card { margin-top: -32rpx; }

.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.section-title { font-size: 30rpx; font-weight: 700; color: #1A1D1F; letter-spacing: 0.5rpx; }
.section-link { font-size: 24rpx; color: #3D5A3E; font-weight: 600; }

/* ===== 快捷入口 ===== */
.quick-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8rpx; }
.quick-item { display: flex; flex-direction: column; align-items: center; padding: 20rpx 0; }
.quick-item:active { transform: scale(0.94); transition: transform 0.1s; }

.qi {
    width: 96rpx; height: 96rpx; border-radius: 28rpx;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 14rpx; position: relative;
}
.qi-green { background: #E8F2E9; }
.qi-slate { background: #EEEFF2; }
.qi-blue { background: #E6EFFE; }
.qi-amber { background: #FFF3E0; }

.qi-icon { width: 40rpx; height: 40rpx; position: relative; }

/* ===== 纯 CSS 图标 ===== */
.icon-wrench {
    width: 28rpx; height: 28rpx;
    border: 4rpx solid #3D5A3E;
    border-radius: 50%;
    position: relative;
}
.icon-wrench::after {
    content: ''; position: absolute;
    bottom: -14rpx; right: -14rpx;
    width: 20rpx; height: 6rpx;
    background: #3D5A3E;
    border-radius: 3rpx;
    transform: rotate(45deg);
}

.icon-list {
    width: 28rpx; height: 24rpx;
    border: 3rpx solid #6B7280;
    border-radius: 4rpx;
    position: relative;
}
.icon-list::before {
    content: ''; position: absolute;
    top: 4rpx; left: 4rpx; right: 4rpx;
    height: 2rpx; background: #6B7280;
    box-shadow: 0 7rpx 0 #6B7280, 0 14rpx 0 #6B7280;
}

.icon-calendar {
    width: 28rpx; height: 26rpx;
    border: 3rpx solid #4A6FA5;
    border-radius: 5rpx;
    position: relative;
}
.icon-calendar::before {
    content: ''; position: absolute;
    top: -6rpx; left: 5rpx;
    width: 3rpx; height: 10rpx;
    background: #4A6FA5;
    box-shadow: 13rpx 0 0 #4A6FA5;
}
.icon-calendar::after {
    content: ''; position: absolute;
    top: 8rpx; left: 5rpx; right: 5rpx;
    height: 2rpx; background: #4A6FA5;
}

.icon-book {
    width: 26rpx; height: 24rpx;
    border: 3rpx solid #B8860B;
    border-radius: 0 5rpx 5rpx 0;
    position: relative;
}
.icon-book::before {
    content: ''; position: absolute;
    left: -3rpx; top: 0; bottom: 0;
    width: 3rpx; background: #B8860B;
}
.icon-book::after {
    content: ''; position: absolute;
    top: 5rpx; left: 5rpx; right: 3rpx;
    height: 2rpx; background: #B8860B;
    box-shadow: 0 5rpx 0 #B8860B;
}

.qi-text { font-size: 22rpx; color: #6B7280; font-weight: 500; letter-spacing: 0.3rpx; }

/* ===== 报修记录列表 ===== */
.record-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 22rpx 0;
    border-bottom: 1rpx solid #F3F4F6;
}
.record-last { border-bottom: none; padding-bottom: 4rpx; }

.record-left { display: flex; align-items: flex-start; flex: 1; min-width: 0; }

.record-dot {
    width: 14rpx; height: 14rpx; border-radius: 50%;
    margin-top: 10rpx; margin-right: 18rpx; flex-shrink: 0;
}
.dot-warn { background: #F59E0B; box-shadow: 0 0 0 4rpx rgba(245,158,11,0.15); }
.dot-info { background: #3B82F6; box-shadow: 0 0 0 4rpx rgba(59,130,246,0.15); }
.dot-ok { background: #10B981; box-shadow: 0 0 0 4rpx rgba(16,185,129,0.15); }

.record-body { flex: 1; min-width: 0; }
.record-title { font-size: 28rpx; font-weight: 600; color: #1A1D1F; display: block; margin-bottom: 4rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.record-desc { font-size: 22rpx; color: #9CA3AF; display: block; }

.record-tag {
    font-size: 20rpx; padding: 5rpx 14rpx; border-radius: 8rpx;
    font-weight: 600; flex-shrink: 0; margin-left: 12rpx;
}
.tag-warn { background: #FEF3C7; color: #B45309; }
.tag-info { background: #DBEAFE; color: #1D4ED8; }
.tag-ok { background: #D1FAE5; color: #047857; }

/* ===== 空状态 ===== */
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 56rpx 0; }
.empty-circle {
    width: 100rpx; height: 100rpx; border-radius: 50%;
    background: #F3F4F6; display: flex; align-items: center; justify-content: center;
    margin-bottom: 20rpx;
}
.icon-inbox {
    width: 40rpx; height: 32rpx;
    border: 3rpx solid #9CA3AF;
    border-radius: 4rpx;
    position: relative;
}
.icon-inbox::before {
    content: ''; position: absolute;
    top: -8rpx; left: 3rpx; right: 3rpx;
    height: 8rpx;
    border: 3rpx solid #9CA3AF;
    border-bottom: none;
    border-radius: 4rpx 4rpx 0 0;
}
.empty-text { font-size: 28rpx; color: #6B7280; font-weight: 500; margin-bottom: 8rpx; }
.empty-hint { font-size: 22rpx; color: #9CA3AF; }
</style>
