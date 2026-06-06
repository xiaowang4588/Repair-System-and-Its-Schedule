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
                <text class="stat-value">{{ teamTotal }}</text>
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
                <view class="mi mi-green"><view class="mi-icon icon-doc"></view></view>
                <text class="ml">我的发布</text>
                <text class="mb">{{ guideStats.postCount }}</text>
                <view class="ma-arrow"></view>
            </view>
            <view class="menu-row" @click="navigateTo('/pages/guide/my-favorites')">
                <view class="mi mi-amber"><view class="mi-icon icon-star"></view></view>
                <text class="ml">我的收藏</text>
                <text class="mb">{{ guideStats.favoriteCount }}</text>
                <view class="ma-arrow"></view>
            </view>
        </view>

        <!-- 修改密码 -->
        <view class="menu-card">
            <view class="menu-row" @click="showPwdForm = !showPwdForm">
                <view class="mi mi-slate"><view class="mi-icon icon-lock"></view></view>
                <text class="ml">修改密码</text>
                <view class="ma-arrow"></view>
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
                <view class="mi mi-gray"><view class="mi-icon icon-info"></view></view>
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
.page { min-height: 100vh; background: #F5F6F8; }

/* 头部 */
.profile-header {
    background: #3D5A3E;
    padding: 56rpx 32rpx 84rpx;
    display: flex; flex-direction: column; align-items: center;
    border-radius: 0 0 44rpx 44rpx;
    position: relative; overflow: hidden;
}
.profile-header::after {
    content: ''; position: absolute; bottom: -80rpx; left: -40rpx;
    width: 300rpx; height: 300rpx; border-radius: 50%;
    background: rgba(255,255,255,0.04);
}
.profile-avatar {
    width: 108rpx; height: 108rpx; border-radius: 50%;
    background: rgba(255,255,255,0.15);
    border: 2rpx solid rgba(255,255,255,0.2);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 18rpx; position: relative; z-index: 1;
}
.avatar-letter { font-size: 44rpx; font-weight: 700; color: rgba(255,255,255,0.9); }
.profile-name { font-size: 34rpx; font-weight: 700; color: #fff; margin-bottom: 6rpx; position: relative; z-index: 1; }
.profile-id { font-size: 24rpx; color: rgba(255,255,255,0.6); position: relative; z-index: 1; }

/* 统计 */
.stats-card {
    display: flex; align-items: center;
    background: #fff; border-radius: 24rpx;
    padding: 28rpx 16rpx;
    margin: -40rpx 24rpx 20rpx; position: relative;
    box-shadow: 0 1rpx 3rpx rgba(0,0,0,0.04), 0 8rpx 24rpx rgba(0,0,0,0.04);
}
.stat-block { flex: 1; display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 40rpx; font-weight: 700; color: #1A1D1F; margin-bottom: 4rpx; }
.stat-value.warn { color: #D97706; }
.stat-label { font-size: 22rpx; color: #9CA3AF; }
.stat-sep { width: 1rpx; height: 52rpx; background: #F3F4F6; }

/* 菜单 */
.menu-card {
    background: #fff; border-radius: 24rpx;
    margin: 0 24rpx 16rpx; overflow: hidden;
    box-shadow: 0 1rpx 3rpx rgba(0,0,0,0.03);
}
.menu-row {
    display: flex; align-items: center;
    padding: 26rpx 28rpx;
    border-bottom: 1rpx solid #F3F4F6;
}
.menu-row:last-child { border-bottom: none; }
.menu-row:active { background: #FAFBFC; }

.mi {
    width: 56rpx; height: 56rpx; border-radius: 16rpx;
    display: flex; align-items: center; justify-content: center;
    margin-right: 20rpx;
}
.mi-green { background: #E8F2E9; }
.mi-amber { background: #FFF3E0; }
.mi-slate { background: #EEEFF2; }
.mi-gray { background: #F3F4F6; }

.mi-icon { width: 24rpx; height: 24rpx; position: relative; }

/* 小图标 */
.icon-doc { border: 3rpx solid #3D5A3E; border-radius: 3rpx; }
.icon-doc::after { content: ''; position: absolute; top: 4rpx; left: 3rpx; right: 3rpx; height: 2rpx; background: #3D5A3E; box-shadow: 0 6rpx 0 #3D5A3E; }
.icon-star { width: 22rpx; height: 22rpx; background: #B8860B; clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%); }
.icon-lock { border: 3rpx solid #6B7280; border-radius: 4rpx; width: 20rpx; height: 18rpx; }
.icon-lock::before { content: ''; position: absolute; top: -10rpx; left: 2rpx; width: 14rpx; height: 10rpx; border: 3rpx solid #6B7280; border-bottom: none; border-radius: 8rpx 8rpx 0 0; }
.icon-info { width: 22rpx; height: 22rpx; border: 3rpx solid #9CA3AF; border-radius: 50%; }
.icon-info::after { content: ''; position: absolute; top: 4rpx; left: 50%; transform: translateX(-50%); width: 3rpx; height: 8rpx; background: #9CA3AF; border-radius: 2rpx; }

.ml { flex: 1; font-size: 28rpx; color: #1A1D1F; font-weight: 500; }
.mb { font-size: 24rpx; color: #9CA3AF; margin-right: 12rpx; }
.ma-arrow { width: 12rpx; height: 12rpx; border-top: 2rpx solid #D1D5DB; border-right: 2rpx solid #D1D5DB; transform: rotate(45deg); }

/* 密码 */
.pwd-card {
    background: #fff; border-radius: 24rpx;
    padding: 28rpx; margin: 0 24rpx 16rpx;
    box-shadow: 0 1rpx 3rpx rgba(0,0,0,0.03);
}
.fg { margin-bottom: 20rpx; }
.fl { font-size: 24rpx; color: #6B7280; margin-bottom: 8rpx; display: block; font-weight: 500; }
.fi {
    width: 100%; height: 84rpx; padding: 0 24rpx;
    border: 2rpx solid #E5E7EB; border-radius: 14rpx;
    font-size: 28rpx; color: #1A1D1F; background: #FAFBFC; box-sizing: border-box;
}
.fi:focus { border-color: #3D5A3E; background: #fff; }
.btn-confirm {
    width: 100%; height: 88rpx; line-height: 88rpx;
    background: #3D5A3E; color: white; border: none;
    border-radius: 14rpx; font-size: 28rpx; font-weight: 600; margin-top: 8rpx;
}

/* 退出 */
.logout-wrap { padding: 24rpx; }
.btn-logout {
    width: 100%; height: 88rpx; line-height: 88rpx;
    background: #fff; color: #DC2626;
    border: 2rpx solid #FEE2E2; border-radius: 16rpx;
    font-size: 28rpx; font-weight: 600;
}
.btn-logout:active { background: #FEF2F2; }
</style>
