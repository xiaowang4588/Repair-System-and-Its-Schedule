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
            <!-- 加载状态：骨架屏 -->
            <block v-if="loadingInfo">
                <view class="stat-block" v-for="i in 3" :key="'skeleton-'+i">
                    <view class="stat-skeleton-bar stat-skeleton-value"></view>
                    <view class="stat-skeleton-bar stat-skeleton-label"></view>
                </view>
            </block>

            <!-- 错误状态：可点击重试 -->
            <view v-else-if="infoError" class="stats-error" @click="loadStudentInfo">
                <text class="error-icon">&#x26A0;</text>
                <text class="error-text">加载失败</text>
                <text class="error-retry">点击重试</text>
            </view>

            <!-- 正常状态：使用view替代template避免uni-app渲染异常 -->
            <view v-else class="stats-content">
                <view class="stat-block" @click="goToRepairList('all', 'all')">
                    <text class="stat-value blue">{{ teamTotal }}</text>
                    <text class="stat-label">总报修量</text>
                </view>
                <view class="stat-sep"></view>
                <view class="stat-block" @click="goToRepairList('all', 'my')">
                    <text class="stat-value">{{ stats.total }}</text>
                    <text class="stat-label">我的报修</text>
                </view>
                <view class="stat-sep"></view>
                <view class="stat-block" @click="goToRepairList('未处理', 'my')">
                    <text class="stat-value orange">{{ stats.pending }}</text>
                    <text class="stat-label">待处理</text>
                </view>
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
            loadingInfo: true,
            infoError: false,
            loadingGuide: false,
            isFirstLoad: true,  // 标记是否为首次加载，防止onShow重复触发
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
        this.isFirstLoad = true
        this.loadStudentInfo()
        this.loadGuideStats()
    },
    onShow() {
        const token = uni.getStorageSync('student_token')
        if (!token) {
            uni.reLaunch({ url: '/pages/login/login' })
            return
        }
        // 首次加载由 onLoad 处理，onShow 仅在从其他页面返回时刷新
        // 增加双重判断：非首次加载 + 非加载中，才执行刷新
        if (!this.isFirstLoad && !this.loadingInfo) {
            this.loadStudentInfo()
            this.loadGuideStats()
        }
        // 首次加载完成后，将标记设为false
        if (this.isFirstLoad && !this.loadingInfo) {
            this.isFirstLoad = false
        }
    },
    methods: {
        async loadStudentInfo() {
            this.loadingInfo = true
            this.infoError = false
            try {
                // 两个接口互不依赖，并行请求
                const [infoRes, statsRes] = await Promise.all([
                    request('/api/student/info'),
                    request('/api/repair/stats')
                ])
                if (infoRes && infoRes.status === 'ok' && infoRes.data) {
                    this.studentInfo = infoRes.data
                    if (infoRes.data.stats) this.stats = infoRes.data.stats
                }
                if (statsRes && statsRes.status === 'ok' && statsRes.data) {
                    this.teamTotal = statsRes.data.total_count || 0
                }
            } catch (e) {
                console.warn('获取学生信息失败:', e)
                this.infoError = true
            } finally {
                this.loadingInfo = false
            }
        },
        async loadGuideStats() {
            this.loadingGuide = true
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
            } finally {
                this.loadingGuide = false
            }
        },
        goToRepairList(filter, listType) {
            uni.navigateTo({ url: `/pages/repair/list?filter=${filter}&listType=${listType}` })
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
    background: var(--color-bg);
    padding-bottom: 24rpx;
}

/* ---- 用户头部（装饰光斑 + 毛玻璃）---- */
.profile-header {
    background: var(--color-primary-gradient);
    padding: 64rpx 32rpx 88rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    border-radius: 0 0 44rpx 44rpx;
    position: relative;
    overflow: hidden;
}
.profile-header::before {
    content: '';
    position: absolute;
    top: -60rpx;
    right: -40rpx;
    width: 200rpx;
    height: 200rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.05);
}
.profile-header::after {
    content: '';
    position: absolute;
    bottom: -30rpx;
    left: 30%;
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.03);
}

.profile-avatar {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(10rpx);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20rpx;
    border: 3rpx solid rgba(255, 255, 255, 0.3);
    position: relative;
    z-index: 1;
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
    margin-bottom: 6rpx;
    position: relative;
    z-index: 1;
}

.profile-id {
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.65);
    position: relative;
    z-index: 1;
}

/* ---- 统计卡片（毛玻璃悬浮）---- */
.stats-card {
    display: flex;
    align-items: center;
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 32rpx 16rpx;
    margin: -40rpx 24rpx 20rpx;
    position: relative;
    box-shadow: var(--shadow-lg);
    border: 1rpx solid var(--color-border-light);
    animation: fadeInUp 0.4s ease 0.1s both;
}

/* 统计内容容器：确保flex布局正确 */
.stats-content {
    display: flex;
    align-items: center;
    width: 100%;
}

.stat-block {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: transform var(--transition-fast);
}
.stat-block:active {
    transform: scale(0.95);
}

/* 统计骨架屏 */
.stat-skeleton-bar {
    background: var(--color-border-light);
    border-radius: 6rpx;
    margin: 0 auto 8rpx auto;
    animation: pulse 1.5s ease-in-out infinite;
}
.stat-skeleton-value {
    width: 80rpx;
    height: 36rpx;
    margin-bottom: 8rpx;
}
.stat-skeleton-label {
    width: 100rpx;
    height: 16rpx;
}

.stat-value {
    font-size: 44rpx;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 4rpx;
    transition: color var(--transition-fast);
}
.stat-value.blue   { color: var(--color-primary); }
.stat-value.orange { color: var(--color-warning); }

.stat-label {
    font-size: 22rpx;
    color: var(--color-text-tertiary);
    font-weight: 500;
}

.stat-sep {
    width: 1rpx;
    height: 56rpx;
    background: var(--color-divider);
}

/* 统计卡片错误状态 */
.stats-error {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20rpx 0;
    transition: opacity var(--transition-fast);
}
.stats-error:active {
    opacity: 0.7;
}
.error-icon {
    font-size: 40rpx;
    margin-bottom: 4rpx;
}
.error-text {
    font-size: 22rpx;
    color: var(--color-text-tertiary);
}
.error-retry {
    font-size: 20rpx;
    color: var(--color-primary);
    margin-top: 6rpx;
    font-weight: 500;
}

/* ---- 菜单卡片 ---- */
.menu-card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    margin: 0 24rpx 16rpx;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
}

.menu-row {
    display: flex;
    align-items: center;
    padding: 28rpx 28rpx;
    border-bottom: 1rpx solid var(--color-divider);
    transition: background var(--transition-fast);
}
.menu-row:last-child {
    border-bottom: none;
}
.menu-row:active {
    background: var(--color-bg-secondary);
}

.menu-icon-wrap {
    width: 68rpx;
    height: 68rpx;
    border-radius: 18rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20rpx;
}

.bg-purple { background: linear-gradient(135deg, #F3E8FF, #EDE0FF); }
.bg-amber  { background: linear-gradient(135deg, #FEF9E7, #FEF3C7); }
.bg-blue   { background: linear-gradient(135deg, #EFF6FF, #DBEAFE); }
.bg-gray   { background: linear-gradient(135deg, #F8FAFC, #F1F5F9); }

.menu-icon-text { font-size: 30rpx; }

.menu-label {
    flex: 1;
    font-size: 28rpx;
    color: var(--color-text);
    font-weight: 500;
}

.menu-badge {
    font-size: 24rpx;
    color: var(--color-text-tertiary);
    margin-right: 12rpx;
    background: var(--color-bg-secondary);
    padding: 4rpx 14rpx;
    border-radius: var(--radius-full);
}

.menu-arrow {
    font-size: 32rpx;
    color: var(--color-text-placeholder);
    font-weight: 300;
}

/* ---- 密码表单 ---- */
.pwd-card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 28rpx;
    margin: 0 24rpx 16rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
    animation: fadeInUp 0.3s ease both;
}

.form-group {
    margin-bottom: 20rpx;
}

.form-label {
    font-size: 24rpx;
    color: var(--color-text-secondary);
    margin-bottom: 10rpx;
    display: block;
    font-weight: 500;
}

.form-input {
    width: 100%;
    height: 84rpx;
    padding: 0 24rpx;
    border: 2rpx solid var(--color-border);
    border-radius: 14rpx;
    font-size: 28rpx;
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
}
.form-input:focus {
    border-color: var(--color-primary);
    background: var(--color-surface);
    box-shadow: 0 0 0 4rpx rgba(108, 92, 231, 0.08);
}

.btn-confirm {
    width: 100%;
    height: 84rpx;
    line-height: 84rpx;
    background: var(--color-primary-gradient);
    color: white;
    border: none;
    border-radius: 14rpx;
    font-size: 28rpx;
    font-weight: 600;
    margin-top: 8rpx;
    box-shadow: 0 4rpx 16rpx rgba(108, 92, 231, 0.25);
    transition: all var(--transition-fast);
}
.btn-confirm:active {
    transform: translateY(2rpx);
    box-shadow: 0 2rpx 8rpx rgba(108, 92, 231, 0.15);
}

/* ---- 退出 ---- */
.logout-wrap {
    padding: 24rpx;
}

.btn-logout {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    background: var(--color-surface);
    color: var(--color-danger);
    border: 2rpx solid var(--color-danger-light);
    border-radius: var(--radius-md);
    font-size: 28rpx;
    font-weight: 600;
    transition: all var(--transition-fast);
}
.btn-logout:active {
    background: var(--color-danger-bg);
    transform: scale(0.98);
}
</style>
