<template>
    <view class="page">
        <view class="login-container">
            <view class="login-header">
                <text class="login-icon">🔐</text>
                <text class="login-title">学生登录</text>
                <text class="login-subtitle">重庆移通学院綦江校区多媒体设备报修管理平台</text>
            </view>

            <view class="login-form">
                <view class="form-group">
                    <text class="form-label">学号</text>
                    <input class="form-input" v-model="studentId" placeholder="请输入学号"
                           @confirm="focusPassword" />
                </view>
                <view class="form-group">
                    <text class="form-label">密码</text>
                    <input class="form-input" v-model="password" placeholder="请输入密码"
                           :password="!showPassword" ref="passwordInput" />
                    <view class="password-toggle" @click="showPassword = !showPassword">
                        <text class="toggle-text">{{ showPassword ? '隐藏' : '显示' }}</text>
                    </view>
                </view>

                <button class="login-btn" @click="login" :disabled="loading">
                    {{ loading ? '登录中...' : '登录' }}
                </button>
            </view>
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
        // 检查是否已登录
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
                    // 保存登录信息
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
    background: #F5F7FA;
    display: flex;
    align-items: center;
    justify-content: center;
}

.login-container {
    width: 90%;
    max-width: 600rpx;
}

.login-header {
    text-align: center;
    margin-bottom: 48rpx;
}

.login-title {
    font-size: 44rpx;
    font-weight: 700;
    color: #1F2937;
    display: block;
    margin-bottom: 12rpx;
}

.login-subtitle {
    font-size: 24rpx;
    color: #9CA3AF;
    display: block;
}

.login-form {
    background: white;
    border-radius: 20rpx;
    padding: 40rpx 32rpx;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

.form-group {
    margin-bottom: 28rpx;
    position: relative;
}

.form-label {
    font-size: 26rpx;
    color: #1F2937;
    font-weight: 500;
    margin-bottom: 10rpx;
    display: block;
}

.form-input {
    width: 100%;
    height: 84rpx;
    padding: 0 24rpx;
    border: 2rpx solid #E5E7EB;
    border-radius: 12rpx;
    font-size: 28rpx;
    background: #F9FAFB;
    box-sizing: border-box;
    transition: border-color 0.2s;
}

.form-input:focus {
    border-color: #4F7CFF;
    background: white;
}

.password-toggle {
    position: absolute;
    right: 24rpx;
    top: 52rpx;
}

.toggle-text {
    font-size: 22rpx;
    color: #4F7CFF;
}

.login-btn {
    width: 100%;
    height: 84rpx;
    background: #4F7CFF;
    color: white;
    font-size: 30rpx;
    font-weight: 600;
    border: none;
    border-radius: 12rpx;
    margin-top: 12rpx;
    transition: all 0.15s;
}

.login-btn:active {
    transform: scale(0.98);
    background: #3D66E0;
}

.login-btn:disabled {
    opacity: 0.5;
}

.login-hint {
    text-align: center;
    margin-top: 20rpx;
}

.hint-text {
    font-size: 22rpx;
    color: #9CA3AF;
}
</style>
