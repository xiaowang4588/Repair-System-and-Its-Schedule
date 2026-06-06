<template>
    <view class="page">
        <!-- 用户头部 -->
        <view class="profile-header">
            <view class="profile-avatar">
                <text class="avatar-letter">{{ studentInfo.name ? studentInfo.name[0] : '?' }}</text>
            </view>
            <text class="profile-name">{{ studentInfo.name || '加载中...' }}</text>
            <text class="profile-id">学号 {{ studentInfo.student_id || '--' }}</text>
        </view>

        <!-- 统计卡片 -->
        <view class="stats-card">
            <view class="stat-block">
                <text class="stat-value accent">{{ teamTotal }}</text>
                <text class="stat-label">总报修量</text>
            </view>
            <view class="stat-sep"></view>
            <view class="stat-block" @click="goToRepairList">
                <text class="stat-value">{{ stats.total }}</text>
                <text class="stat-label">我的报修</text>
            </view>
            <view class="stat-sep"></view>
            <view class="stat-block" @click="goToRepairList">
                <text class="stat-value warn">{{ stats.pending }}</text>
                <text class="stat-label">待处理</text>
            </view>
        </view>

        <!-- 防坑指南 -->
        <view class="menu-card">
            <view class="menu-row" @click="navigateTo('/pages/guide/my-posts')">
                <view class="mi mi-green">&#x1f4dd;</view>
                <text class="ml">我的发布</text>
                <text class="mb">{{ guideStats.postCount }}</text>
                <text class="ma">&#x203a;</text>
            </view>
            <view class="menu-row" @click="navigateTo('/pages/guide/my-favorites')">
                <view class="mi mi-amber">&#x2b50;</view>
                <text class="ml">我的收藏</text>
                <text class="mb">{{ guideStats.favoriteCount }}</text>
                <text class="ma">&#x203a;</text>
            </view>
        </view>

        <!-- 修改密码 -->
        <view class="menu-card">
            <view class="menu-row" @click="showPwdForm = !showPwdForm">
                <view class="mi mi-blue">&#x1f512;</view>
                <text class="ml">修改密码</text>
                <text class="ma">&#x203a;</text>
            </view>
        </view>

        <view class="pwd-card" v-if="showPwdForm">
            <view class="fg">
                <text class="fl">当前密码</text>
                <input class="fi" v-model="pwdForm.old_password" placeholder="请输入当前密码" password />
            </view>
            <view class="fg">
                <text class="fl">新密码</text>
                <input class="fi" v-model="pwdForm.new_password" placeholder="请输入新密码" password />
            </view>
            <view class="fg">
                <text class="fl">确认密码</text>
                <input class="fi" v-model="pwdForm.confirm_password" placeholder="请再次输入新密码" password />
            </view>
            <button class="btn-confirm" @click="changePassword">确认修改</button>
        </view>

        <!-- 关于 -->
        <view class="menu-card">
            <view class="menu-row">
                <view class="mi mi-gray">&#x2139;</view>
                <text class="ml">多媒体设备报修管理系统 v1.0</text>
            </view>
        </view>

        <!-- 退出 -->
        <view class="logout-wrap">
            <button class="btn-logout" @click="logout">退出登录</button>
        </view>
    </view>
</template>

<script>
import { request, post, getGuideStats } from '../../api/index.js'

export default {
    data() {
        return {
            studentInfo: {}, teamTotal: 0,
            stats: { total: 0, pending: 0 },
            guideStats: { postCount: 0, favoriteCount: 0 },
            showPwdForm: false,
            pwdForm: { old_password: '', new_password: '', confirm_password: '' }
        }
    },
    onLoad() {
        if (!uni.getStorageSync('student_token')) { uni.reLaunch({ url: '/pages/login/login' }); return }
        this.loadStudentInfo(); this.loadGuideStats()
    },
    onShow() {
        if (uni.getStorageSync('student_token')) { this.loadStudentInfo(); this.loadGuideStats() }
    },
    methods: {
        async loadStudentInfo() {
            try {
                const res = await request('/api/student/info')
                if (res?.status === 'ok' && res.data) {
                    this.studentInfo = res.data
                    if (res.data.stats) this.stats = res.data.stats
                }
                const sr = await request('/api/repair/stats')
                if (sr?.status === 'ok' && sr.data) this.teamTotal = sr.data.total_count || 0
            } catch (e) { console.warn(e) }
        },
        async loadGuideStats() {
            try {
                const res = await getGuideStats()
                if (res?.status === 'ok' && res.data) {
                    this.guideStats = { postCount: res.data.post_count || 0, favoriteCount: res.data.favorite_count || 0 }
                }
            } catch (e) { console.warn(e) }
        },
        goToRepairList() { uni.navigateTo({ url: '/pages/repair/list' }) },
        navigateTo(url) { uni.navigateTo({ url }) },
        async changePassword() {
            if (!this.pwdForm.old_password) { uni.showToast({ title: '请输入当前密码', icon: 'none' }); return }
            if (!this.pwdForm.new_password) { uni.showToast({ title: '请输入新密码', icon: 'none' }); return }
            if (this.pwdForm.new_password.length < 6) { uni.showToast({ title: '新密码至少6位', icon: 'none' }); return }
            if (this.pwdForm.new_password !== this.pwdForm.confirm_password) { uni.showToast({ title: '两次密码不一致', icon: 'none' }); return }
            uni.showLoading({ title: '提交中...' })
            try {
                const res = await post('/api/student/change-password', {
                    student_id: uni.getStorageSync('student_id') || '',
                    old_password: this.pwdForm.old_password,
                    new_password: this.pwdForm.new_password
                })
                if (res?.status === 'ok') {
                    uni.showToast({ title: '修改成功', icon: 'success' })
                    this.pwdForm = { old_password: '', new_password: '', confirm_password: '' }
                    this.showPwdForm = false
                } else { uni.showToast({ title: res?.message || '修改失败', icon: 'none' }) }
            } catch (e) { uni.showToast({ title: '修改失败', icon: 'none' }) }
            finally { uni.hideLoading() }
        },
        logout() {
            uni.showModal({
                title: '提示', content: '确定退出登录？',
                success: (r) => {
                    if (r.confirm) {
                        uni.removeStorageSync('student_token')
                        uni.removeStorageSync('student_id')
                        uni.removeStorageSync('student_name')
                        uni.reLaunch({ url: '/pages/login/login' })
                    }
                }
            })
        }
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #F7FAF8; }

/* 头部 */
.profile-header {
    background: #5BBF8A;
    padding: 56rpx 32rpx 80rpx;
    display: flex; flex-direction: column; align-items: center;
    border-radius: 0 0 36rpx 36rpx;
}
.profile-avatar {
    width: 112rpx; height: 112rpx; border-radius: 50%;
    background: rgba(255,255,255,0.25);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 18rpx;
}
.avatar-letter { font-size: 46rpx; font-weight: 700; color: white; }
.profile-name { font-size: 34rpx; font-weight: 700; color: white; margin-bottom: 6rpx; }
.profile-id { font-size: 24rpx; color: rgba(255,255,255,0.7); }

/* 统计 */
.stats-card {
    display: flex; align-items: center;
    background: white; border-radius: 20rpx;
    padding: 28rpx 16rpx;
    margin: -36rpx 24rpx 20rpx; position: relative;
    box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}
.stat-block { flex: 1; display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 42rpx; font-weight: 700; color: #2D3436; margin-bottom: 4rpx; }
.stat-value.accent { color: #5BBF8A; }
.stat-value.warn { color: #E17055; }
.stat-label { font-size: 22rpx; color: #A0A8AB; }
.stat-sep { width: 1rpx; height: 56rpx; background: #E8ECEF; }

/* 菜单 */
.menu-card {
    background: white; border-radius: 20rpx;
    margin: 0 24rpx 16rpx; overflow: hidden;
    box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.02);
}
.menu-row {
    display: flex; align-items: center;
    padding: 26rpx 28rpx;
    border-bottom: 1rpx solid #F1F5F1;
}
.menu-row:last-child { border-bottom: none; }
.menu-row:active { background: #F7FAF8; }

.mi {
    width: 60rpx; height: 60rpx; border-radius: 14rpx;
    display: flex; align-items: center; justify-content: center;
    margin-right: 18rpx; font-size: 26rpx;
}
.mi-green { background: #E8F5EE; }
.mi-amber { background: #FFF8E1; }
.mi-blue { background: #E3F2FD; }
.mi-gray { background: #F1F5F9; }

.ml { flex: 1; font-size: 28rpx; color: #2D3436; font-weight: 500; }
.mb { font-size: 24rpx; color: #A0A8AB; margin-right: 10rpx; }
.ma { font-size: 36rpx; color: #DFE6E9; font-weight: 300; }

/* 密码 */
.pwd-card {
    background: white; border-radius: 20rpx;
    padding: 28rpx; margin: 0 24rpx 16rpx;
    box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.02);
}
.fg { margin-bottom: 20rpx; }
.fl { font-size: 24rpx; color: #636E72; margin-bottom: 8rpx; display: block; font-weight: 500; }
.fi {
    width: 100%; height: 80rpx; padding: 0 24rpx;
    border: 2rpx solid #E8ECEF; border-radius: 12rpx;
    font-size: 28rpx; color: #2D3436; background: #FAFCFB; box-sizing: border-box;
}
.fi:focus { border-color: #5BBF8A; background: white; }

.btn-confirm {
    width: 100%; height: 84rpx; line-height: 84rpx;
    background: #5BBF8A; color: white; border: none;
    border-radius: 12rpx; font-size: 28rpx; font-weight: 600; margin-top: 8rpx;
}

/* 退出 */
.logout-wrap { padding: 24rpx; }
.btn-logout {
    width: 100%; height: 88rpx; line-height: 88rpx;
    background: white; color: #E17055;
    border: 2rpx solid #FFEAA7; border-radius: 16rpx;
    font-size: 28rpx; font-weight: 600;
}
.btn-logout:active { background: #FFF3E0; }
</style>
