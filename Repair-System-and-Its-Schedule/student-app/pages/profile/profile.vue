<template>
    <view class="page">
        <!-- 用户头部 -->
        <view class="header">
            <view class="header-content">
                <view class="avatar-outer">
                    <view class="avatar-inner">
                        <text class="avatar-char">{{ studentInfo.name ? studentInfo.name[0] : '?' }}</text>
                    </view>
                </view>
                <text class="user-name">{{ studentInfo.name || '加载中...' }}</text>
                <text class="user-id">学号 {{ studentInfo.student_id || '--' }}</text>
            </view>
        </view>

        <!-- 统计 - 双层嵌套 -->
        <view class="card-outer stats-outer">
            <view class="card-inner stats-inner">
                <view class="stat-block" @click="goToRepairList">
                    <text class="stat-num">{{ teamTotal }}</text>
                    <text class="stat-lbl">总报修量</text>
                </view>
                <view class="stat-sep"></view>
                <view class="stat-block" @click="goToRepairList">
                    <text class="stat-num">{{ stats.total }}</text>
                    <text class="stat-lbl">我的报修</text>
                </view>
                <view class="stat-sep"></view>
                <view class="stat-block" @click="goToRepairList">
                    <text class="stat-num warn">{{ stats.pending }}</text>
                    <text class="stat-lbl">待处理</text>
                </view>
            </view>
        </view>

        <!-- 防坑指南菜单 -->
        <view class="card-outer">
            <view class="card-inner menu-card">
                <view class="menu-row" @click="navigateTo('/pages/guide/my-posts')">
                    <view class="menu-shell mi-green"><view class="menu-core"><view class="ico-doc"></view></view></view>
                    <text class="menu-label">我的发布</text>
                    <text class="menu-count">{{ guideStats.postCount }}</text>
                    <view class="menu-arrow"></view>
                </view>
                <view class="menu-row" @click="navigateTo('/pages/guide/my-favorites')">
                    <view class="menu-shell mi-warm"><view class="menu-core"><view class="ico-star"></view></view></view>
                    <text class="menu-label">我的收藏</text>
                    <text class="menu-count">{{ guideStats.favoriteCount }}</text>
                    <view class="menu-arrow"></view>
                </view>
            </view>
        </view>

        <!-- 修改密码 -->
        <view class="card-outer">
            <view class="card-inner menu-card">
                <view class="menu-row" @click="showPwdForm = !showPwdForm">
                    <view class="menu-shell mi-slate"><view class="menu-core"><view class="ico-lock"></view></view></view>
                    <text class="menu-label">修改密码</text>
                    <view class="menu-arrow"></view>
                </view>
            </view>
        </view>

        <!-- 密码表单 - 双层嵌套 -->
        <view class="card-outer" v-if="showPwdForm">
            <view class="card-inner">
                <view class="pwd-group">
                    <text class="pwd-label">当前密码</text>
                    <view class="pwd-shell"><input class="pwd-input" v-model="pwdForm.old_password" placeholder="请输入" password /></view>
                </view>
                <view class="pwd-group">
                    <text class="pwd-label">新密码</text>
                    <view class="pwd-shell"><input class="pwd-input" v-model="pwdForm.new_password" placeholder="请输入" password /></view>
                </view>
                <view class="pwd-group">
                    <text class="pwd-label">确认密码</text>
                    <view class="pwd-shell"><input class="pwd-input" v-model="pwdForm.confirm_password" placeholder="请再次输入" password /></view>
                </view>
                <view class="btn-outer" @click="changePassword">
                    <view class="btn-inner"><text class="btn-text">确认修改</text></view>
                </view>
            </view>
        </view>

        <!-- 关于 -->
        <view class="card-outer">
            <view class="card-inner menu-card">
                <view class="menu-row">
                    <view class="menu-shell mi-gray"><view class="menu-core"><view class="ico-info"></view></view></view>
                    <text class="menu-label">多媒体设备报修管理系统 v1.0</text>
                </view>
            </view>
        </view>

        <!-- 退出 -->
        <view class="logout-area">
            <view class="logout-outer" @click="logout">
                <view class="logout-inner"><text class="logout-text">退出登录</text></view>
            </view>
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
        this.loadAll()
    },
    onShow() {
        if (uni.getStorageSync('student_token')) this.loadAll()
    },
    methods: {
        async loadAll() {
            try {
                const r1 = await request('/api/student/info')
                if (r1?.status === 'ok' && r1.data) { this.studentInfo = r1.data; if (r1.data.stats) this.stats = r1.data.stats }
                const r2 = await request('/api/repair/stats')
                if (r2?.status === 'ok' && r2.data) this.teamTotal = r2.data.total_count || 0
            } catch (e) { console.warn(e) }
            try {
                const r3 = await getGuideStats()
                if (r3?.status === 'ok' && r3.data) this.guideStats = { postCount: r3.data.post_count || 0, favoriteCount: r3.data.favorite_count || 0 }
            } catch (e) { console.warn(e) }
        },
        goToRepairList() { uni.navigateTo({ url: '/pages/repair/list' }) },
        navigateTo(u) { uni.navigateTo({ url: u }) },
        async changePassword() {
            if (!this.pwdForm.old_password) { uni.showToast({ title: '请输入当前密码', icon: 'none' }); return }
            if (!this.pwdForm.new_password) { uni.showToast({ title: '请输入新密码', icon: 'none' }); return }
            if (this.pwdForm.new_password.length < 6) { uni.showToast({ title: '新密码至少6位', icon: 'none' }); return }
            if (this.pwdForm.new_password !== this.pwdForm.confirm_password) { uni.showToast({ title: '两次密码不一致', icon: 'none' }); return }
            uni.showLoading({ title: '提交中...' })
            try {
                const r = await post('/api/student/change-password', { student_id: uni.getStorageSync('student_id') || '', old_password: this.pwdForm.old_password, new_password: this.pwdForm.new_password })
                if (r?.status === 'ok') { uni.showToast({ title: '修改成功', icon: 'success' }); this.pwdForm = { old_password: '', new_password: '', confirm_password: '' }; this.showPwdForm = false }
                else uni.showToast({ title: r?.message || '修改失败', icon: 'none' })
            } catch (e) { uni.showToast({ title: '修改失败', icon: 'none' }) }
            finally { uni.hideLoading() }
        },
        logout() {
            uni.showModal({ title: '提示', content: '确定退出登录？', success: r => {
                if (r.confirm) { uni.removeStorageSync('student_token'); uni.removeStorageSync('student_id'); uni.removeStorageSync('student_name'); uni.reLaunch({ url: '/pages/login/login' }) }
            }})
        }
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #F2F3F5; }

/* 头部 */
.header {
    background: #1A1D1F;
    padding: 60rpx 32rpx 88rpx;
    border-radius: 0 0 48rpx 48rpx;
    position: relative; overflow: hidden;
}
.header::before { content: ''; position: absolute; bottom: -100rpx; left: -60rpx; width: 320rpx; height: 320rpx; border-radius: 50%; background: rgba(255,255,255,0.03); }
.header-content { display: flex; flex-direction: column; align-items: center; position: relative; z-index: 1; }
.avatar-outer { width: 112rpx; height: 112rpx; border-radius: 50%; background: rgba(255,255,255,0.08); border: 1rpx solid rgba(255,255,255,0.1); padding: 6rpx; margin-bottom: 18rpx; }
.avatar-inner { width: 100%; height: 100%; border-radius: 50%; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; }
.avatar-char { font-size: 42rpx; font-weight: 700; color: rgba(255,255,255,0.85); }
.user-name { font-size: 34rpx; font-weight: 700; color: #fff; margin-bottom: 6rpx; }
.user-id { font-size: 22rpx; color: rgba(255,255,255,0.45); }

/* 双层嵌套卡片 */
.card-outer {
    background: rgba(0,0,0,0.025);
    border: 1rpx solid rgba(0,0,0,0.04);
    border-radius: 28rpx;
    padding: 8rpx;
    margin: 0 20rpx 16rpx;
}
.card-inner {
    background: #fff;
    border-radius: 22rpx;
    padding: 24rpx;
    box-shadow: inset 0 1rpx 1rpx rgba(255,255,255,0.8), 0 2rpx 12rpx rgba(0,0,0,0.03);
}
.stats-outer { margin-top: -44rpx; }

/* 统计 */
.stats-inner { display: flex; align-items: center; padding: 20rpx 12rpx; }
.stat-block { flex: 1; display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 38rpx; font-weight: 800; color: #1A1D1F; margin-bottom: 2rpx; }
.stat-num.warn { color: #D97706; }
.stat-lbl { font-size: 20rpx; color: #9CA3AF; }
.stat-sep { width: 1rpx; height: 48rpx; background: rgba(0,0,0,0.06); }

/* 菜单 */
.menu-card { padding: 4rpx 0; }
.menu-row {
    display: flex; align-items: center;
    padding: 22rpx 24rpx;
    border-bottom: 1rpx solid rgba(0,0,0,0.04);
}
.menu-row:last-child { border-bottom: none; }
.menu-row:active { background: #FAFBFC; }

.menu-shell {
    width: 52rpx; height: 52rpx; border-radius: 16rpx;
    background: rgba(0,0,0,0.025); border: 1rpx solid rgba(0,0,0,0.04);
    padding: 5rpx; margin-right: 18rpx;
}
.menu-core {
    width: 100%; height: 100%; border-radius: 12rpx;
    display: flex; align-items: center; justify-content: center;
}
.mi-green .menu-core { background: #EDF5EE; }
.mi-warm .menu-core { background: #FFF5EB; }
.mi-slate .menu-core { background: #EEEFF1; }
.mi-gray .menu-core { background: #F3F4F6; }

.menu-label { flex: 1; font-size: 26rpx; color: #1A1D1F; font-weight: 500; }
.menu-count { font-size: 22rpx; color: #9CA3AF; margin-right: 12rpx; }
.menu-arrow { width: 10rpx; height: 10rpx; border-top: 2rpx solid #D1D5DB; border-right: 2rpx solid #D1D5DB; transform: rotate(45deg); }

/* 小图标 */
.ico-doc { width: 20rpx; height: 20rpx; border: 2rpx solid #3D5A3E; border-radius: 3rpx; position: relative; }
.ico-doc::after { content: ''; position: absolute; top: 3rpx; left: 3rpx; right: 3rpx; height: 2rpx; background: #3D5A3E; box-shadow: 0 5rpx 0 #3D5A3E; }
.ico-star { width: 20rpx; height: 20rpx; background: #B8860B; clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%); }
.ico-lock { width: 18rpx; height: 16rpx; border: 2rpx solid #6B7280; border-radius: 3rpx; position: relative; }
.ico-lock::before { content: ''; position: absolute; top: -8rpx; left: 2rpx; width: 12rpx; height: 8rpx; border: 2rpx solid #6B7280; border-bottom: none; border-radius: 6rpx 6rpx 0 0; }
.ico-info { width: 20rpx; height: 20rpx; border: 2rpx solid #9CA3AF; border-radius: 50%; position: relative; }
.ico-info::after { content: ''; position: absolute; top: 3rpx; left: 50%; transform: translateX(-50%); width: 2rpx; height: 7rpx; background: #9CA3AF; border-radius: 2rpx; }

/* 密码 */
.pwd-group { margin-bottom: 20rpx; }
.pwd-label { font-size: 22rpx; color: #6B7280; margin-bottom: 8rpx; display: block; font-weight: 500; }
.pwd-shell { background: #F8F9FA; border: 1rpx solid rgba(0,0,0,0.06); border-radius: 14rpx; }
.pwd-input { width: 100%; height: 80rpx; padding: 0 20rpx; font-size: 26rpx; color: #1A1D1F; background: transparent; border: none; }

.btn-outer { background: rgba(0,0,0,0.04); border: 1rpx solid rgba(0,0,0,0.06); border-radius: 18rpx; padding: 6rpx; margin-top: 12rpx; }
.btn-inner { background: #1A1D1F; border-radius: 14rpx; height: 80rpx; display: flex; align-items: center; justify-content: center; }
.btn-inner:active { background: #2D2F31; }
.btn-text { color: #fff; font-size: 26rpx; font-weight: 600; letter-spacing: 2rpx; }

/* 退出 */
.logout-area { padding: 12rpx 20rpx 40rpx; }
.logout-outer { background: rgba(220,38,38,0.04); border: 1rpx solid rgba(220,38,38,0.1); border-radius: 20rpx; padding: 6rpx; }
.logout-inner { background: #fff; border-radius: 16rpx; height: 84rpx; display: flex; align-items: center; justify-content: center; }
.logout-inner:active { background: #FEF2F2; }
.logout-text { color: #DC2626; font-size: 26rpx; font-weight: 600; }
</style>
