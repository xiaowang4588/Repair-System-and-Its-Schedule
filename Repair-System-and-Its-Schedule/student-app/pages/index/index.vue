<template>
    <view class="page">
        <!-- 欢迎横幅 -->
        <view class="banner">
            <view class="banner-content">
                <text class="banner-hi">{{ studentName || '同学' }}</text>
                <text class="banner-sub">今天有什么设备需要报修吗</text>
            </view>
            <view class="banner-avatar" @click="goProfile">
                <view class="avatar-outer">
                    <view class="avatar-inner">
                        <text class="avatar-text">{{ studentName ? studentName[0] : '?' }}</text>
                    </view>
                </view>
            </view>
        </view>

        <!-- 快捷操作 - 双层嵌套卡片 -->
        <view class="card-outer">
            <view class="card-inner">
                <view class="quick-row">
                    <view class="quick-item" @click="switchTo('/pages/repair/repair')">
                        <view class="qi-shell qi-green">
                            <view class="qi-core">
                                <view class="ico-wrench"></view>
                            </view>
                        </view>
                        <text class="qi-label">提交报修</text>
                    </view>
                    <view class="quick-item" @click="navigateTo('/pages/repair/list')">
                        <view class="qi-shell qi-slate">
                            <view class="qi-core">
                                <view class="ico-list"></view>
                            </view>
                        </view>
                        <text class="qi-label">全部记录</text>
                    </view>
                    <view class="quick-item" @click="navigateTo('/pages/course/schedule')">
                        <view class="qi-shell qi-blue">
                            <view class="qi-core">
                                <view class="ico-calendar"></view>
                            </view>
                        </view>
                        <text class="qi-label">课表查询</text>
                    </view>
                    <view class="quick-item" @click="switchTo('/pages/guide/index')">
                        <view class="qi-shell qi-warm">
                            <view class="qi-core">
                                <view class="ico-book"></view>
                            </view>
                        </view>
                        <text class="qi-label">防坑指南</text>
                    </view>
                </view>
            </view>
        </view>

        <!-- 最新报修 - 双层嵌套卡片 -->
        <view class="card-outer">
            <view class="card-inner">
                <view class="section-head">
                    <text class="section-title">最近报修</text>
                    <text class="section-link" @click="goToList">全部</text>
                </view>

                <view v-if="recentList.length === 0" class="empty-area">
                    <view class="empty-shell">
                        <view class="empty-core">
                            <view class="ico-inbox"></view>
                        </view>
                    </view>
                    <text class="empty-main">暂无报修记录</text>
                    <text class="empty-sub">点击上方「提交报修」开始</text>
                </view>

                <view v-for="(item, idx) in recentList" :key="item.id" class="feed-item"
                      :class="{ last: idx === recentList.length - 1 }">
                    <view class="feed-dot" :class="dotCls(item.status)"></view>
                    <view class="feed-body">
                        <text class="feed-title">{{ item.classroom || '未知位置' }}</text>
                        <text class="feed-desc">{{ item.fault_type || '' }} · {{ fmtTime(item.report_time) }}</text>
                    </view>
                    <view class="feed-tag" :class="tagCls(item.status)">{{ item.status }}</view>
                </view>
            </view>
        </view>

        <view style="height: 40rpx;"></view>
    </view>
</template>

<script>
import { request } from '../../api/index.js'

export default {
    data() { return { studentName: '', recentList: [] } },
    onLoad() {
        if (!uni.getStorageSync('student_token')) { uni.reLaunch({ url: '/pages/login/login' }); return }
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadData()
    },
    onShow() {
        if (!uni.getStorageSync('student_token')) { uni.reLaunch({ url: '/pages/login/login' }); return }
        this.studentName = uni.getStorageSync('student_name') || ''
        this.loadData()
    },
    methods: {
        async loadData() {
            try {
                const res = await request('/api/repair/list', { page: 1, page_size: 5 })
                if (res && res.status === 'ok') this.recentList = res.records || []
            } catch (e) { console.error(e) }
        },
        dotCls(s) { return s === '未处理' ? 'dw' : s === '处理中' ? 'di' : 'do' },
        tagCls(s) { return s === '未处理' ? 'tw' : s === '处理中' ? 'ti' : 'to' },
        fmtTime(t) {
            if (!t) return ''
            const p = t.split(' ')
            return p.length >= 2 ? p[0].substring(5) + ' ' + p[1].substring(0, 5) : t
        },
        goToList() { uni.navigateTo({ url: '/pages/repair/list' }) },
        goProfile() { uni.switchTab({ url: '/pages/profile/profile' }) },
        switchTo(u) { uni.switchTab({ url: u }) },
        navigateTo(u) { uni.navigateTo({ url: u }) }
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #F2F3F5; }

/* ===== 横幅 ===== */
.banner {
    background: #1A1D1F;
    padding: 56rpx 36rpx 72rpx;
    border-radius: 0 0 48rpx 48rpx;
    display: flex; justify-content: space-between; align-items: center;
    position: relative; overflow: hidden;
}
.banner::before {
    content: ''; position: absolute; top: -120rpx; right: -80rpx;
    width: 360rpx; height: 360rpx; border-radius: 50%;
    background: rgba(255,255,255,0.03);
}
.banner-content { position: relative; z-index: 1; }
.banner-hi { font-size: 42rpx; font-weight: 800; color: #fff; display: block; margin-bottom: 8rpx; letter-spacing: 1rpx; }
.banner-sub { font-size: 24rpx; color: rgba(255,255,255,0.5); display: block; }
.banner-avatar { position: relative; z-index: 1; }
.avatar-outer {
    width: 88rpx; height: 88rpx; border-radius: 50%;
    background: rgba(255,255,255,0.08);
    border: 1rpx solid rgba(255,255,255,0.1);
    padding: 6rpx;
}
.avatar-inner {
    width: 100%; height: 100%; border-radius: 50%;
    background: rgba(255,255,255,0.1);
    display: flex; align-items: center; justify-content: center;
}
.avatar-text { font-size: 32rpx; font-weight: 700; color: rgba(255,255,255,0.85); }

/* ===== 双层嵌套卡片 ===== */
.card-outer {
    background: rgba(0,0,0,0.025);
    border: 1rpx solid rgba(0,0,0,0.04);
    border-radius: 28rpx;
    padding: 8rpx;
    margin: -32rpx 20rpx 20rpx;
    position: relative;
}
.card-inner {
    background: #fff;
    border-radius: 22rpx;
    padding: 28rpx;
    box-shadow: inset 0 1rpx 1rpx rgba(255,255,255,0.8), 0 2rpx 12rpx rgba(0,0,0,0.03);
}

/* ===== 快捷入口 ===== */
.quick-row { display: flex; justify-content: space-between; }
.quick-item { display: flex; flex-direction: column; align-items: center; width: 25%; }
.quick-item:active { transform: scale(0.94); transition: transform 0.1s; }

.qi-shell {
    width: 100rpx; height: 100rpx; border-radius: 28rpx;
    background: rgba(0,0,0,0.025);
    border: 1rpx solid rgba(0,0,0,0.04);
    padding: 8rpx; margin-bottom: 14rpx;
}
.qi-core {
    width: 100%; height: 100%; border-radius: 22rpx;
    display: flex; align-items: center; justify-content: center;
    box-shadow: inset 0 1rpx 1rpx rgba(255,255,255,0.6);
}
.qi-green .qi-core { background: #EDF5EE; }
.qi-slate .qi-core { background: #EEEFF1; }
.qi-blue .qi-core { background: #EAF0FB; }
.qi-warm .qi-core { background: #FFF5EB; }

.qi-label { font-size: 20rpx; color: #6B7280; font-weight: 500; letter-spacing: 0.5rpx; }

/* ===== CSS 图标 ===== */
.ico-wrench { width: 28rpx; height: 28rpx; border: 3rpx solid #3D5A3E; border-radius: 50%; position: relative; }
.ico-wrench::after { content: ''; position: absolute; bottom: -12rpx; right: -12rpx; width: 18rpx; height: 5rpx; background: #3D5A3E; border-radius: 3rpx; transform: rotate(45deg); }
.ico-list { width: 26rpx; height: 22rpx; border: 3rpx solid #6B7280; border-radius: 4rpx; position: relative; }
.ico-list::before { content: ''; position: absolute; top: 3rpx; left: 4rpx; right: 4rpx; height: 2rpx; background: #6B7280; box-shadow: 0 6rpx 0 #6B7280, 0 12rpx 0 #6B7280; }
.ico-calendar { width: 26rpx; height: 24rpx; border: 3rpx solid #4A6FA5; border-radius: 4rpx; position: relative; }
.ico-calendar::before { content: ''; position: absolute; top: -5rpx; left: 4rpx; width: 3rpx; height: 8rpx; background: #4A6FA5; box-shadow: 11rpx 0 0 #4A6FA5; }
.ico-calendar::after { content: ''; position: absolute; top: 7rpx; left: 4rpx; right: 4rpx; height: 2rpx; background: #4A6FA5; }
.ico-book { width: 24rpx; height: 22rpx; border: 3rpx solid #B8860B; border-radius: 0 4rpx 4rpx 0; position: relative; }
.ico-book::before { content: ''; position: absolute; left: -3rpx; top: 0; bottom: 0; width: 3rpx; background: #B8860B; }
.ico-book::after { content: ''; position: absolute; top: 4rpx; left: 4rpx; right: 3rpx; height: 2rpx; background: #B8860B; box-shadow: 0 5rpx 0 #B8860B; }
.ico-inbox { width: 36rpx; height: 28rpx; border: 3rpx solid #9CA3AF; border-radius: 4rpx; position: relative; }
.ico-inbox::before { content: ''; position: absolute; top: -7rpx; left: 3rpx; right: 3rpx; height: 7rpx; border: 3rpx solid #9CA3AF; border-bottom: none; border-radius: 4rpx 4rpx 0 0; }

/* ===== 列表 ===== */
.section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.section-title { font-size: 28rpx; font-weight: 700; color: #1A1D1F; letter-spacing: 0.5rpx; }
.section-link { font-size: 22rpx; color: #6B7280; font-weight: 500; }

.feed-item {
    display: flex; align-items: center;
    padding: 20rpx 0;
    border-bottom: 1rpx solid rgba(0,0,0,0.04);
}
.feed-item.last { border-bottom: none; padding-bottom: 4rpx; }

.feed-dot {
    width: 12rpx; height: 12rpx; border-radius: 50%;
    margin-right: 18rpx; flex-shrink: 0;
}
.dw { background: #F59E0B; box-shadow: 0 0 0 4rpx rgba(245,158,11,0.12); }
.di { background: #3B82F6; box-shadow: 0 0 0 4rpx rgba(59,130,246,0.12); }
.do { background: #10B981; box-shadow: 0 0 0 4rpx rgba(16,185,129,0.12); }

.feed-body { flex: 1; min-width: 0; }
.feed-title { font-size: 26rpx; font-weight: 600; color: #1A1D1F; display: block; margin-bottom: 2rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.feed-desc { font-size: 20rpx; color: #9CA3AF; display: block; }

.feed-tag {
    font-size: 18rpx; padding: 4rpx 12rpx; border-radius: 6rpx;
    font-weight: 600; flex-shrink: 0; margin-left: 12rpx;
}
.tw { background: #FEF3C7; color: #B45309; }
.ti { background: #DBEAFE; color: #1D4ED8; }
.to { background: #D1FAE5; color: #047857; }

/* ===== 空状态 ===== */
.empty-area { display: flex; flex-direction: column; align-items: center; padding: 48rpx 0; }
.empty-shell {
    width: 96rpx; height: 96rpx; border-radius: 50%;
    background: rgba(0,0,0,0.025); border: 1rpx solid rgba(0,0,0,0.04);
    padding: 8rpx; margin-bottom: 20rpx;
}
.empty-core {
    width: 100%; height: 100%; border-radius: 50%;
    background: #F8F9FA; display: flex; align-items: center; justify-content: center;
}
.empty-main { font-size: 26rpx; color: #6B7280; font-weight: 500; margin-bottom: 6rpx; }
.empty-sub { font-size: 20rpx; color: #9CA3AF; }
</style>
