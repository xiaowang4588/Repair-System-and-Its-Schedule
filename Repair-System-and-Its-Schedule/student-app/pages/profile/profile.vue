<template>
    <view class="page">
        <!-- 顶部用户卡片 -->
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
                <text class="stat-value blue">{{ teamTotal }}</text>
                <text class="stat-label">总报修量</text>
            </view>
            <view class="stat-sep"></view>
            <view class="stat-block" @click="goToRepairList">
                <text class="stat-value">{{ stats.total }}</text>
                <text class="stat-label">我的报修</text>
            </view>
            <view class="stat-sep"></view>
            <view class="stat-block" @click="goToRepairList">
                <text class="stat-value orange">{{ stats.pending }}</text>
                <text class="stat-label">待处理</text>
            </view>
        </view>

        <!-- 防坑指南 -->
        <view class="menu-card">
            <view class="menu-row" @click="navigateTo('/pages/guide/my-posts')">
                <view class="menu-icon-wrap bg-purple">
                    <text class="menu-icon-text">&#x1f4dd;</text>
                </view>
                <text class="menu-label">我的发布</text>
                <text class="menu-badge">{{ guideStats.postCount }}</text>
                <text class="menu-arrow">&#x203a;</text>
            </view>
            <view class="menu-row" @click="navigateTo('/pages/guide/my-favorites')">
                <view class="menu-icon-wrap bg-amber">
                    <text class="menu-icon-text">&#x2b50;</text>
                </view>
                <text class="menu-label">我的收藏</text>
                <text class="menu-badge">{{ guideStats.favoriteCount }}</text>
                <text class="menu-arrow">&#x203a;</text>
            </view>
        </view>

        <!-- 修改密码 -->
        <view class="menu-card">
            <view class="menu-row" @click="showPwdForm = !showPwdForm">
                <view class="menu-icon-wrap bg-blue">
                    <text class="menu-icon-text">&#x1f512;</text>
                </view>
                <text class="menu-label">修改密码</text>
                <text class="menu-arrow">&#x203a;</text>
            </view>
        </view>

        <!-- 密码表单（展开） -->
        <view class="pwd-card" v-if="showPwdForm">
            <view class="form-group">
                <text class="form-label">当前密码</text>
                <input class="form-input" v-model="pwdForm.old_password" placeholder="请输入当前密码" password />
            </view>
            <view class="form-group">
                <text class="form-label">新密码</text>
                <input class="form-input" v-model="pwdForm.new_password" placeholder="请输入新密码" password />
            </view>
            <view class="form-group">
                <text class="form-label">确认密码</text>
                <input class="form-input" v-model="pwdForm.confirm_password" placeholder="请再次输入新密码" password />
            </view>
            <button class="btn-confirm" @click="changePassword">确认修改</button>
        </view>

        <!-- 关于 -->
        <view class="menu-card">
            <view class="menu-row">
                <view class="menu-icon-wrap bg-gray">
                    <text class="menu-icon-text">&#x2139;</text>
                </view>
                <text class="menu-label">多媒体设备报修管理系统 v1.0</text>
            </view>
        </view>

        <!-- 退出登录 -->
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
            studentInfo: {},
            teamTotal: 0,
            stats: { total: 0, pending: 0 },
            guideStats: { postCount: 0, favoriteCount: 0 },
            showPwdForm: false,
            pwdForm: {
                old_password: '',
                new_password: '',
                confirm_password: ''
            }
        }
    },
    onLoad() {
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        this.loadStudentInfo()
        this.loadGuideStats()
    },
    onShow() {
        const token = uni.getStorageSync('student_token')
        if (token) {
            this.loadStudentInfo()
            this.loadGuideStats()
        }
    },
    methods: {
        async loadStudentInfo() {
            try {
                const res = await request('/api/student/info')
                if (res && res.status === 'ok' && res.data) {
                    this.studentInfo = res.data
                    if (res.data.stats) this.stats = res.data.stats
                }
                const statsRes = await request('/api/repair/stats')
                if (statsRes && statsRes.status === 'ok' && statsRes.data) {
                    this.teamTotal = statsRes.data.total_count || 0
                }
            } catch (e) {
                console.warn('获取学生信息失败:', e)
            }
        },
        async loadGuideStats() {
            try {
                const res = await getGuideStats()
                if (res && res.status === 'ok' && res.data) {
                    this.guideStats = {
                        postCount: res.data.post_count || 0,
                        favoriteCount: res.data.favorite_count || 0,
                    }
                }
            } catch (e) {
                console.warn('获取防坑指南统计失败:', e)
            }
        },
        goToRepairList() {
            uni.navigateTo({ url: '/pages/repair/list' })
        },
        navigateTo(url) {
            uni.navigateTo({ url })
        },
        async changePassword() {
            if (!this.pwdForm.old_password) {
                uni.showToast({ title: '请输入当前密码', icon: 'none' }); return
            }
            if (!this.pwdForm.new_password) {
                uni.showToast({ title: '请输入新密码', icon: 'none' }); return
            }
            if (this.pwdForm.new_password.length < 6) {
                uni.showToast({ title: '新密码至少6位', icon: 'none' }); return
            }
            if (this.pwdForm.new_password !== this.pwdForm.confirm_password) {
                uni.showToast({ title: '两次输入的密码不一致', icon: 'none' }); return
            }
            uni.showLoading({ title: '提交中...' })
            try {
                const res = await post('/api/student/change-password', {
                    student_id: uni.getStorageSync('student_id') || '',
                    old_password: this.pwdForm.old_password,
                    new_password: this.pwdForm.new_password
                })
                if (res && res.status === 'ok') {
                    uni.showToast({ title: '密码修改成功', icon: 'success' })
                    this.pwdForm = { old_password: '', new_password: '', confirm_password: '' }
                    this.showPwdForm = false
                } else {
                    uni.showToast({ title: res ? res.message || '修改失败' : '修改失败', icon: 'none' })
                }
            } catch (e) {
                uni.showToast({ title: '修改失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
        },
        logout() {
            uni.showModal({
                title: '提示',
                content: '确定要退出登录吗？',
                success: (res) => {
                    if (res.confirm) {
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
.page {
    min-height: 100vh;
    background: #F0F4FF;
}

/* 用户头部 */
.profile-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 60rpx 32rpx 80rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    border-radius: 0 0 40rpx 40rpx;
}

.profile-avatar {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20rpx;
}

.avatar-letter {
    font-size: 48rpx;
    font-weight: 700;
    color: white;
}

.profile-name {
    font-size: 36rpx;
    font-weight: 700;
    color: white;
    margin-bottom: 8rpx;
}

.profile-id {
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.7);
}

/* 统计卡片 */
.stats-card {
    display: flex;
    align-items: center;
    background: white;
    border-radius: 20rpx;
    padding: 32rpx 16rpx;
    margin: -36rpx 24rpx 20rpx;
    position: relative;
    box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);
}

.stat-block {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.stat-value {
    font-size: 44rpx;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 6rpx;
}

.stat-value.blue { color: #667eea; }
.stat-value.orange { color: #F59E0B; }

.stat-label {
    font-size: 22rpx;
    color: #94A3B8;
}

.stat-sep {
    width: 1rpx;
    height: 60rpx;
    background: #E2E8F0;
}

/* 菜单卡片 */
.menu-card {
    background: white;
    border-radius: 20rpx;
    margin: 0 24rpx 16rpx;
    overflow: hidden;
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}

.menu-row {
    display: flex;
    align-items: center;
    padding: 28rpx 28rpx;
    border-bottom: 1rpx solid #F1F5F9;
}

.menu-row:last-child {
    border-bottom: none;
}

.menu-row:active {
    background: #F8FAFC;
}

.menu-icon-wrap {
    width: 64rpx;
    height: 64rpx;
    border-radius: 16rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20rpx;
}

.bg-purple { background: #F3E8FF; }
.bg-amber { background: #FEF3C7; }
.bg-blue { background: #DBEAFE; }
.bg-gray { background: #F1F5F9; }

.menu-icon-text { font-size: 28rpx; }

.menu-label {
    flex: 1;
    font-size: 28rpx;
    color: #1E293B;
    font-weight: 500;
}

.menu-badge {
    font-size: 24rpx;
    color: #94A3B8;
    margin-right: 12rpx;
}

.menu-arrow {
    font-size: 36rpx;
    color: #CBD5E1;
    font-weight: 300;
}

/* 密码表单 */
.pwd-card {
    background: white;
    border-radius: 20rpx;
    padding: 28rpx;
    margin: 0 24rpx 16rpx;
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.03);
}

.form-group {
    margin-bottom: 20rpx;
}

.form-label {
    font-size: 24rpx;
    color: #64748B;
    margin-bottom: 10rpx;
    display: block;
    font-weight: 500;
}

.form-input {
    width: 100%;
    height: 84rpx;
    padding: 0 24rpx;
    border: 2rpx solid #E2E8F0;
    border-radius: 14rpx;
    font-size: 28rpx;
    color: #1E293B;
    background: #F8FAFC;
    box-sizing: border-box;
}

.form-input:focus {
    border-color: #667eea;
    background: white;
}

.btn-confirm {
    width: 100%;
    height: 84rpx;
    line-height: 84rpx;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 14rpx;
    font-size: 28rpx;
    font-weight: 600;
    margin-top: 8rpx;
}

/* 退出 */
.logout-wrap {
    padding: 24rpx;
}

.btn-logout {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    background: white;
    color: #EF4444;
    border: 2rpx solid #FEE2E2;
    border-radius: 16rpx;
    font-size: 28rpx;
    font-weight: 600;
}

.btn-logout:active {
    background: #FEF2F2;
}
</style>
