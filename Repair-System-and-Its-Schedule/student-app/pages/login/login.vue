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
import config, { initConfig } from '../../config/index.js'

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
        // 不自动跳转。旧 token 可能因服务器重启失效，
        // 自动跳转会导致：进首页 → 401 → 踢回登录 → 死循环
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
        async apiPost(url, data) {
            await initConfig()
            return new Promise((resolve, reject) => {
                uni.request({
                    url: config.API_BASE + url,
                    method: 'POST',
                    data: data,
                    header: { 'Content-Type': 'application/json' },
                    success: (res) => {
                        if (res.statusCode === 200) {
                            resolve(res.data)
                        } else {
                            console.error('[API Error]', res.statusCode, res.data)
                            resolve(res.data || { status: 'error', message: `服务器错误(${res.statusCode})` })
                        }
                    },
                    fail: (err) => {
                        console.error('[API Fail]', err)
                        reject(err)
                    }
                })
            })
        }
    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: var(--color-bg);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

/* ---- 装饰背景 ---- */
.login-bg {
    position: absolute;
    top: -160rpx;
    left: -80rpx;
    width: 600rpx;
    height: 600rpx;
    border-radius: 50%;
    background: var(--color-primary-gradient);
    opacity: 0.08;
    animation: float-bg 8s ease-in-out infinite;
}
@keyframes float-bg {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50%      { transform: translate(30rpx, -20rpx) scale(1.05); }
}

/* 第二个装饰圆 */
.login-bg::after {
    content: '';
    position: absolute;
    bottom: -100rpx;
    right: -60rpx;
    width: 300rpx;
    height: 300rpx;
    border-radius: 50%;
    background: var(--color-primary-gradient);
    opacity: 0.06;
}

.login-container {
    width: 88%;
    max-width: 640rpx;
    position: relative;
    z-index: 1;
}

/* ---- Logo区域 ---- */
.login-header {
    text-align: center;
    margin-bottom: 56rpx;
    animation: fadeInUp 0.5s ease both;
}

.logo-circle {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: var(--color-primary-gradient);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24rpx;
    box-shadow: 0 12rpx 40rpx rgba(108, 92, 231, 0.3);
}

.logo-icon {
    font-size: 52rpx;
}

.login-title {
    font-size: 44rpx;
    font-weight: 700;
    color: var(--color-text);
    display: block;
    margin-bottom: 10rpx;
    letter-spacing: 2rpx;
}

.login-subtitle {
    font-size: 24rpx;
    color: var(--color-text-tertiary);
    display: block;
    font-weight: 500;
}

/* ---- 登录表单 ---- */
.login-form {
    background: var(--color-surface);
    border-radius: var(--radius-xl);
    padding: 40rpx 36rpx;
    box-shadow: var(--shadow-lg);
    border: 1rpx solid var(--color-border-light);
    animation: fadeInUp 0.5s ease 0.1s both;
}

.form-group {
    margin-bottom: 32rpx;
}

.form-label {
    font-size: 26rpx;
    color: var(--color-text-secondary);
    font-weight: 600;
    margin-bottom: 12rpx;
    display: block;
}

.input-wrap {
    position: relative;
}

.form-input {
    width: 100%;
    height: 96rpx;
    padding: 0 28rpx;
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 30rpx;
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-normal);
}
.form-input:focus {
    border-color: var(--color-primary);
    background: var(--color-surface);
    box-shadow: 0 0 0 6rpx rgba(108, 92, 231, 0.07);
}

.password-toggle {
    position: absolute;
    right: 24rpx;
    top: 50%;
    transform: translateY(-50%);
}

.toggle-text {
    font-size: 24rpx;
    color: var(--color-primary);
    font-weight: 500;
}

/* ---- 登录按钮 ---- */
.login-btn {
    width: 100%;
    height: 100rpx;
    background: var(--color-primary-gradient);
    color: white;
    font-size: 34rpx;
    font-weight: 600;
    border: none;
    border-radius: var(--radius-md);
    margin-top: 20rpx;
    letter-spacing: 6rpx;
    box-shadow: 0 8rpx 28rpx rgba(108, 92, 231, 0.35);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}
.login-btn::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.12) 50%, transparent 100%);
    opacity: 0;
    transition: opacity var(--transition-fast);
}
.login-btn:active {
    transform: translateY(2rpx) scale(0.98);
    box-shadow: 0 4rpx 16rpx rgba(108, 92, 231, 0.2);
}
.login-btn:active::after {
    opacity: 1;
}
.login-btn:disabled {
    opacity: 0.6;
}

.footer-text {
    display: block;
    text-align: center;
    margin-top: 40rpx;
    font-size: 22rpx;
    color: var(--color-text-tertiary);
    letter-spacing: 2rpx;
    animation: fadeInUp 0.5s ease 0.2s both;
}
</style>
