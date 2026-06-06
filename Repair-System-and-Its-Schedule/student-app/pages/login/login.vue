<template>
    <view class="page">
        <view class="login-container">
            <view class="login-header">
                <view class="logo-circle">
                    <view class="logo-shield">
                        <view class="shield-inner"></view>
                    </view>
                </view>
                <text class="login-title">多媒体报修系统</text>
                <text class="login-subtitle">重庆移通学院綦江校区</text>
            </view>

            <view class="login-form">
                <view class="form-group">
                    <text class="form-label">学号</text>
                    <input class="form-input" v-model="studentId" placeholder="请输入学号"
                           @confirm="focusPassword" />
                </view>
                <view class="form-group">
                    <text class="form-label">密码</text>
                    <view class="input-wrap">
                        <input class="form-input" v-model="password" placeholder="请输入密码"
                               :password="!showPassword" ref="passwordInput" />
                        <text class="toggle-text" @click="showPassword = !showPassword">
                            {{ showPassword ? '隐藏' : '显示' }}
                        </text>
                    </view>
                </view>

                <button class="login-btn" @click="login" :disabled="loading">
                    {{ loading ? '登录中...' : '登 录' }}
                </button>
            </view>

            <text class="footer-text">设备报修 · 课表查询 · 空教室</text>
        </view>
    </view>
</template>

<script>
import config from '../../config/index.js'
const API_BASE = config.API_BASE

export default {
    data() {
        return { studentId: '', password: '', showPassword: false, loading: false }
    },
    methods: {
        focusPassword() { this.$refs.passwordInput.focus() },
        async login() {
            if (!this.studentId.trim()) { uni.showToast({ title: '请输入学号', icon: 'none' }); return }
            if (!this.password) { uni.showToast({ title: '请输入密码', icon: 'none' }); return }
            this.loading = true
            try {
                const res = await this.apiPost('/api/student/login', {
                    student_id: this.studentId.trim(), password: this.password,
                })
                if (res && res.status === 'ok') {
                    uni.setStorageSync('student_token', res.data.token)
                    uni.setStorageSync('student_id', res.data.student_id)
                    uni.setStorageSync('student_name', res.data.name)
                    uni.showToast({ title: '登录成功', icon: 'success' })
                    setTimeout(() => uni.reLaunch({ url: '/pages/index/index' }), 500)
                } else {
                    uni.showToast({ title: (res && res.message) || '学号或密码错误', icon: 'none' })
                }
            } catch (e) { uni.showToast({ title: '网络错误', icon: 'none' }) }
            finally { this.loading = false }
        },
        apiPost(url, data) {
            return new Promise((resolve, reject) => {
                uni.request({
                    url: API_BASE + url, method: 'POST', data,
                    header: { 'Content-Type': 'application/json' },
                    success: (res) => resolve(res.statusCode === 200 ? res.data : null),
                    fail: reject
                })
            })
        }
    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: #F5F6F8;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-container { width: 90%; max-width: 640rpx; }

.login-header { text-align: center; margin-bottom: 72rpx; }

.logo-circle {
    width: 120rpx; height: 120rpx; border-radius: 50%;
    background: #E8F2E9;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 28rpx;
}
.logo-shield {
    width: 44rpx; height: 50rpx;
    border: 4rpx solid #3D5A3E;
    border-radius: 6rpx 6rpx 22rpx 22rpx;
    position: relative;
}
.shield-inner {
    position: absolute; bottom: 8rpx; left: 50%; transform: translateX(-50%);
    width: 14rpx; height: 14rpx;
    border: 3rpx solid #3D5A3E;
    border-radius: 50%;
}

.login-title {
    font-size: 40rpx; font-weight: 700; color: #1A1D1F;
    display: block; margin-bottom: 10rpx; letter-spacing: 1rpx;
}
.login-subtitle { font-size: 24rpx; color: #9CA3AF; display: block; }

.login-form {
    background: #fff; border-radius: 28rpx;
    padding: 40rpx 36rpx;
    box-shadow: 0 1rpx 3rpx rgba(0,0,0,0.04), 0 12rpx 40rpx rgba(0,0,0,0.04);
}
.form-group { margin-bottom: 28rpx; }
.form-label { font-size: 24rpx; color: #6B7280; font-weight: 600; margin-bottom: 12rpx; display: block; letter-spacing: 0.5rpx; }
.input-wrap { position: relative; }
.form-input {
    width: 100%; height: 92rpx; padding: 0 28rpx;
    border: 2rpx solid #E5E7EB; border-radius: 16rpx;
    font-size: 28rpx; color: #1A1D1F; background: #FAFBFC;
    box-sizing: border-box;
}
.form-input:focus { border-color: #3D5A3E; background: #fff; }
.toggle-text {
    position: absolute; right: 24rpx; top: 50%; transform: translateY(-50%);
    font-size: 24rpx; color: #3D5A3E; font-weight: 500;
}

.login-btn {
    width: 100%; height: 96rpx;
    background: #3D5A3E; color: white;
    font-size: 30rpx; font-weight: 600;
    border: none; border-radius: 16rpx;
    margin-top: 12rpx; letter-spacing: 4rpx;
}
.login-btn:active { background: #2D4A2E; }
.login-btn:disabled { opacity: 0.5; }

.footer-text {
    display: block; text-align: center; margin-top: 48rpx;
    font-size: 22rpx; color: #9CA3AF; letter-spacing: 1rpx;
}
</style>
