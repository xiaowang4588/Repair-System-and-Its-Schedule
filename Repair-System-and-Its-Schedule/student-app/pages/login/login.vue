<template>
    <view class="page">
        <view class="login-container">
            <view class="login-header">
                <view class="logo-circle">
                    <text class="logo-icon">&#x1f6e1;</text>
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
        return {
            studentId: '',
            password: '',
            showPassword: false,
            loading: false,
        }
    },
    onLoad() {
        const token = uni.getStorageSync('student_token')
        if (token) this.redirectToMain()
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
                    setTimeout(() => this.redirectToMain(), 500)
                } else {
                    uni.showToast({ title: (res && res.message) || '学号或密码错误', icon: 'none' })
                }
            } catch (e) { uni.showToast({ title: '网络错误', icon: 'none' }) }
            finally { this.loading = false }
        },
        redirectToMain() { uni.reLaunch({ url: '/pages/index/index' }) },
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
    background: #F7FAF8;
    display: flex;
    align-items: center;
    justify-content: center;
}

.login-container {
    width: 90%;
    max-width: 640rpx;
}

.login-header {
    text-align: center;
    margin-bottom: 64rpx;
}

.logo-circle {
    width: 128rpx;
    height: 128rpx;
    border-radius: 50%;
    background: #E8F5EE;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 28rpx;
}

.logo-icon { font-size: 56rpx; }

.login-title {
    font-size: 42rpx;
    font-weight: 700;
    color: #2D3436;
    display: block;
    margin-bottom: 10rpx;
}

.login-subtitle {
    font-size: 24rpx;
    color: #A0A8AB;
    display: block;
}

.login-form {
    background: white;
    border-radius: 24rpx;
    padding: 40rpx 36rpx;
    box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.04);
}

.form-group { margin-bottom: 28rpx; }

.form-label {
    font-size: 26rpx;
    color: #636E72;
    font-weight: 600;
    margin-bottom: 12rpx;
    display: block;
}

.input-wrap { position: relative; }

.form-input {
    width: 100%;
    height: 88rpx;
    padding: 0 28rpx;
    border: 2rpx solid #E8ECEF;
    border-radius: 14rpx;
    font-size: 28rpx;
    color: #2D3436;
    background: #FAFCFB;
    box-sizing: border-box;
}

.form-input:focus {
    border-color: #5BBF8A;
    background: white;
}

.toggle-text {
    position: absolute;
    right: 24rpx;
    top: 50%;
    transform: translateY(-50%);
    font-size: 24rpx;
    color: #5BBF8A;
    font-weight: 500;
}

.login-btn {
    width: 100%;
    height: 92rpx;
    background: #5BBF8A;
    color: white;
    font-size: 30rpx;
    font-weight: 600;
    border: none;
    border-radius: 14rpx;
    margin-top: 12rpx;
    letter-spacing: 4rpx;
}

.login-btn:active {
    background: #4AAE79;
}

.login-btn:disabled { opacity: 0.5; }

.footer-text {
    display: block;
    text-align: center;
    margin-top: 40rpx;
    font-size: 22rpx;
    color: #B2BEC3;
    letter-spacing: 2rpx;
}
</style>
