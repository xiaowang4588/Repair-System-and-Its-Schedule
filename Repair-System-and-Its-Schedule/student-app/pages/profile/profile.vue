<template>
    <view class="page">
        <!-- 用户信息卡片 -->
        <view class="user-card">
            <view class="avatar">{{ studentInfo.name ? studentInfo.name[0] : '?' }}</view>
            <view class="user-text">
                <view class="user-name">{{ studentInfo.name || '加载中...' }}</view>
                <view class="user-id">学号：{{ studentInfo.student_id || '--' }}</view>
            </view>
        </view>

        <!-- 报修统计 -->
        <view class="card stats-card">
            <view class="card-title">报修统计</view>
            <view class="stats-row">
                <view class="stat-item">
                    <text class="stat-num total">{{ teamTotal }}</text>
                    <text class="stat-label">总报修量</text>
                </view>
                <view class="stat-divider"></view>
                <view class="stat-item" @click="goToRepairList('my')">
                    <text class="stat-num">{{ stats.total }}</text>
                    <text class="stat-label">我的报修</text>
                </view>
                <view class="stat-divider"></view>
                <view class="stat-item" @click="goToRepairList('my')">
                    <text class="stat-num pending">{{ stats.pending }}</text>
                    <text class="stat-label">我的待处理</text>
                </view>
            </view>
        </view>

        <!-- 防坑指南 -->
        <view class="card">
            <view class="card-title">防坑指南</view>
            <view class="menu-item" @click="navigateTo('/pages/guide/my-posts')">
                <text class="menu-icon">📝</text>
                <text class="menu-text">我的发布</text>
                <text class="menu-count">{{ guideStats.postCount }}</text>
                <text class="menu-arrow">＞</text>
            </view>
            <view class="menu-item" @click="navigateTo('/pages/guide/my-favorites')">
                <text class="menu-icon">⭐</text>
                <text class="menu-text">我的收藏</text>
                <text class="menu-count">{{ guideStats.favoriteCount }}</text>
                <text class="menu-arrow">＞</text>
            </view>
        </view>

        <!-- 修改密码 -->
        <view class="card">
            <view class="card-title">修改密码</view>
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
            <button class="btn-change-pwd" @click="changePassword">确认修改</button>
        </view>

        <!-- 关于系统 -->
        <view class="card">
            <view class="card-title">关于系统</view>
            <view class="about-row">
                <text class="about-label">系统名称</text>
                <text class="about-value">多媒体设备报修管理系统</text>
            </view>
            <view class="about-row">
                <text class="about-label">所属单位</text>
                <text class="about-value">重庆移通学院綦江校区</text>
            </view>
            <view class="about-row">
                <text class="about-label">版本</text>
                <text class="about-value">v1.0.0</text>
            </view>
        </view>

        <!-- 退出登录 -->
        <button class="btn-logout" @click="logout">退出登录</button>
    </view>
</template>

<script>
import config from '../../config/index.js'
import { request, post, getGuideStats } from '../../api/index.js'
const API_BASE = config.API_BASE

export default {
    data() {
        return {
            studentInfo: {},
            teamTotal: 0,
            stats: { total: 0, pending: 0 },
            guideStats: { postCount: 0, favoriteCount: 0 },
            pwdForm: {
                old_password: '',
                new_password: '',
                confirm_password: ''
            }
        }
    },
    onLoad() {
        // 检查登录状态
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        this.loadStudentInfo()
        this.loadGuideStats()
    },
    onShow() {
        // 每次显示页面刷新数据
        const token = uni.getStorageSync('student_token')
        if (token) {
            this.loadStudentInfo()
            this.loadGuideStats()
        }
    },
    methods: {
        // 获取学生信息和报修统计
        async loadStudentInfo() {
            const studentId = uni.getStorageSync('student_id') || ''

            // 获取个人统计（从token获取身份，无需传student_id）
            try {
                const res = await request('/api/student/info')
                if (res && res.status === 'ok' && res.data) {
                    this.studentInfo = res.data
                    if (res.data.stats) {
                        this.stats = res.data.stats
                    }
                }
            } catch (e) {
                console.warn('获取学生信息失败:', e)
            }

            // 获取团队总报修量（公开接口，不需要认证）
            try {
                const statsRes = await request('/api/repair/stats')
                if (statsRes && statsRes.status === 'ok' && statsRes.data) {
                    this.teamTotal = statsRes.data.total_count || 0
                }
            } catch (e) {
                console.warn('获取报修统计失败:', e)
            }
        },

        // 跳转到报修记录
        goToRepairList(type) {
            uni.navigateTo({ url: '/pages/repair/list' })
        },

        // 加载防坑指南统计（失败不影响主流程）
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
                // 静默失败，不提示，不影响页面正常使用
                console.warn('获取防坑指南统计失败（可忽略）:', e)
            }
        },

        // 普通页跳转
        navigateTo(url) {
            uni.navigateTo({ url })
        },

        // 修改密码
        async changePassword() {
            if (!this.pwdForm.old_password) {
                uni.showToast({ title: '请输入当前密码', icon: 'none' })
                return
            }
            if (!this.pwdForm.new_password) {
                uni.showToast({ title: '请输入新密码', icon: 'none' })
                return
            }
            if (this.pwdForm.new_password.length < 6) {
                uni.showToast({ title: '新密码至少6位', icon: 'none' })
                return
            }
            if (this.pwdForm.new_password !== this.pwdForm.confirm_password) {
                uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
                return
            }

            uni.showLoading({ title: '提交中...' })
            try {
                const studentId = uni.getStorageSync('student_id') || ''
                const res = await post('/api/student/change-password', {
                    student_id: studentId,
                    old_password: this.pwdForm.old_password,
                    new_password: this.pwdForm.new_password
                })
                if (res && res.status === 'ok') {
                    uni.showToast({ title: '密码修改成功', icon: 'success' })
                    this.pwdForm = { old_password: '', new_password: '', confirm_password: '' }
                } else {
                    uni.showToast({ title: res ? res.message || '修改失败' : '修改失败', icon: 'none' })
                }
            } catch (e) {
                console.error('修改密码失败:', e)
                uni.showToast({ title: '修改失败', icon: 'none' })
            } finally {
                uni.hideLoading()
            }
        },

        // 退出登录
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
        },

    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: #F5F7FA;
    padding: 24rpx;
    padding-bottom: 120rpx;
}

/* 用户信息卡片 */
.user-card {
    display: flex;
    align-items: center;
    background: #4F7CFF;
    border-radius: 16rpx;
    padding: 40rpx 32rpx;
    margin-bottom: 24rpx;
    box-shadow: 0 4rpx 16rpx rgba(102, 126, 234, 0.3);
}

.avatar {
    width: 96rpx;
    height: 96rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.25);
    color: #fff;
    font-size: 40rpx;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 28rpx;
    flex-shrink: 0;
}

.user-text {
    flex: 1;
}

.user-name {
    font-size: 36rpx;
    font-weight: 700;
    color: #fff;
    margin-bottom: 8rpx;
}

.user-id {
    font-size: 26rpx;
    color: rgba(255, 255, 255, 0.8);
}

/* 通用卡片 */
.card {
    background: white;
    border-radius: 16rpx;
    padding: 32rpx;
    margin-bottom: 24rpx;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.card-title {
    font-size: 32rpx;
    font-weight: 600;
    color: #333;
    margin-bottom: 24rpx;
    padding-bottom: 16rpx;
    border-bottom: 1rpx solid #f0f0f0;
}

/* 统计 */
.stats-row {
    display: flex;
    align-items: center;
}

.stat-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.stat-num {
    font-size: 44rpx;
    font-weight: 700;
    color: #333;
    margin-bottom: 8rpx;
}

.stat-num.pending {
    color: #ff9500;
}

.stat-num.total {
    color: #4F7CFF;
}

.stat-label {
    font-size: 24rpx;
    color: #999;
}

.stat-divider {
    width: 1rpx;
    height: 60rpx;
    background: #eee;
}

/* 表单 */
.form-group {
    margin-bottom: 24rpx;
}

.form-label {
    font-size: 28rpx;
    color: #555;
    margin-bottom: 12rpx;
    display: block;
}

.form-input {
    width: 100%;
    height: 88rpx;
    padding: 0 24rpx;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    background: #fafafa;
    box-sizing: border-box;
}

.form-input:focus {
    border-color: #4F7CFF;
    background: white;
}

.btn-change-pwd {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    background: #4F7CFF;
    color: white;
    border: none;
    border-radius: 12rpx;
    font-size: 30rpx;
    font-weight: 500;
    margin-top: 8rpx;
}

.btn-change-pwd:active {
    opacity: 0.8;
}

/* 关于系统 */
.about-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16rpx 0;
    border-bottom: 1rpx solid #f5f5f5;
}

.about-row:last-child {
    border-bottom: none;
}

.about-label {
    font-size: 28rpx;
    color: #999;
}

.about-value {
    font-size: 28rpx;
    color: #333;
}

/* 菜单项 */
.menu-item {
    display: flex;
    align-items: center;
    padding: 20rpx 0;
    border-bottom: 1rpx solid #f5f5f5;
}

.menu-item:last-child { border-bottom: none; }
.menu-icon { font-size: 36rpx; margin-right: 16rpx; }
.menu-text { flex: 1; font-size: 28rpx; color: #333; }
.menu-count { font-size: 26rpx; color: #999; margin-right: 12rpx; }
.menu-arrow { font-size: 24rpx; color: #ccc; }

/* 退出登录 */
.btn-logout {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    background: white;
    color: #ff4d4f;
    border: 1rpx solid #ff4d4f;
    border-radius: 12rpx;
    font-size: 30rpx;
    font-weight: 500;
    margin-top: 16rpx;
}

.btn-logout:active {
    background: #fff1f0;
}
</style>
