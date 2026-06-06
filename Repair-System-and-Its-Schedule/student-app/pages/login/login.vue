<template>
    <view class="page">
        <view class="login-bg"></view>
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
                    <view class="input-wrap">
                        <input class="form-input" v-model="studentId" placeholder="请输入学号"
                               @confirm="focusPassword" />
                    </view>
                </view>
                <view class="form-group">
                    <text class="form-label">密码</text>
                    <view class="input-wrap">
                        <input class="form-input" v-model="password" placeholder="请输入密码"
                               :password="!showPassword" ref="passwordInput" />
                        <view class="password-toggle" @click="showPassword = !showPassword">
                            <text class="toggle-text">{{ showPassword ? '隐藏' : '显示' }}</text>
                        </view>
                    </view>
                </view>

                <button class="login-btn" @click="login" :disabled="loading">
                    {{ loading ? '登录中...' : '登 录' }}
                </button>
            </view>

            <text class="footer-text">设备报修 / 课表查询 / 空教室</text>
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
        if (token) {
            this.redirectToMain()
        }
    },
    methods: {
        focusPassword() {
            this.$refs.passwordInput.focus()
        },
        async login() {
            if (!this.studentId.trim()) {
                uni.showToast({ title: '请输入学号', icon: 'none' })
                return
            }
            if (!this.password) {
                uni.showToast({ title: '请输入密码', icon: 'none' })
                return
            }
            this.loading = true
            try {
                const res = await this.apiPost('/api/student/login', {
                    student_id: this.studentId.trim(),
                    password: this.password,
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
            } catch (e) {
                uni.showToast({ title: '网络错误', icon: 'none' })
            } finally {
                this.loading = false
            }
        },
        redirectToMain() {
            uni.reLaunch({ url: '/pages/index/index' })
        },
        apiPost(url, data) {
            return new Promise((resolve, reject) => {
                uni.request({
                    url: API_BASE + url,
                    method: 'POST',
                    data: data,
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
    background: #F0F4FF;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

.login-bg {
    position: absolute;
    top: -200rpx;
    left: -100rpx;
    width: 700rpx;
    height: 700rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    opacity: 0.15;
}

.login-container {
    width: 90%;
    max-width: 640rpx;
    position: relative;
    z-index: 1;
}

.login-header {
    text-align: center;
    margin-bottom: 60rpx;
}

.logo-circle {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24rpx;
    box-shadow: 0 8rpx 32rpx rgba(102, 126, 234, 0.35);
}

.logo-icon {
    font-size: 52rpx;
}

.login-title {
    font-size: 44rpx;
    font-weight: 700;
    color: #1E293B;
    display: block;
    margin-bottom: 12rpx;
    letter-spacing: 2rpx;
}

.login-subtitle {
    font-size: 24rpx;
    color: #94A3B8;
    display: block;
}

.login-form {
    background: white;
    border-radius: 24rpx;
    padding: 40rpx 36rpx;
    box-shadow: 0 8rpx 40rpx rgba(0, 0, 0, 0.06);
}

.form-group {
    margin-bottom: 32rpx;
}

.form-label {
    font-size: 26rpx;
    color: #475569;
    font-weight: 600;
    margin-bottom: 14rpx;
    display: block;
}

.input-wrap {
    position: relative;
}

.form-input {
    width: 100%;
    height: 92rpx;
    padding: 0 28rpx;
    border: 2rpx solid #E2E8F0;
    border-radius: 16rpx;
    font-size: 30rpx;
    color: #1E293B;
    background: #F8FAFC;
    box-sizing: border-box;
    transition: all 0.2s;
}

.form-input:focus {
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 4rpx rgba(102, 126, 234, 0.1);
}

.password-toggle {
    position: absolute;
    right: 24rpx;
    top: 50%;
    transform: translateY(-50%);
}

.toggle-text {
    font-size: 24rpx;
    color: #667eea;
    font-weight: 500;
}

.login-btn {
    width: 100%;
    height: 96rpx;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 32rpx;
    font-weight: 600;
    border: none;
    border-radius: 16rpx;
    margin-top: 16rpx;
    letter-spacing: 4rpx;
    box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.35);
}

.login-btn:active {
    transform: translateY(2rpx);
    box-shadow: 0 4rpx 12rpx rgba(102, 126, 234, 0.25);
}

.login-btn:disabled {
    opacity: 0.6;
}

.footer-text {
    display: block;
    text-align: center;
    margin-top: 40rpx;
    font-size: 22rpx;
    color: #94A3B8;
    letter-spacing: 2rpx;
}
</style>
