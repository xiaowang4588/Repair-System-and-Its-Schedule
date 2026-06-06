<template>
    <view class="page">
        <view class="container">
            <!-- Logo 区域 -->
            <view class="logo-area">
                <view class="logo-outer">
                    <view class="logo-inner">
                        <view class="shield">
                            <view class="shield-body"></view>
                            <view class="shield-check"></view>
                        </view>
                    </view>
                </view>
                <text class="app-name">报修系统</text>
                <text class="app-sub">重庆移通学院綦江校区</text>
            </view>

            <!-- 表单区域 - 双层嵌套卡片 -->
            <view class="form-outer">
                <view class="form-inner">
                    <view class="input-group">
                        <text class="input-label">学号</text>
                        <view class="input-shell">
                            <input class="input-field" v-model="studentId"
                                   placeholder="请输入学号" @confirm="focusPassword" />
                        </view>
                    </view>

                    <view class="input-group">
                        <text class="input-label">密码</text>
                        <view class="input-shell">
                            <input class="input-field" v-model="password"
                                   placeholder="请输入密码" :password="!showPassword"
                                   ref="passwordInput" />
                            <view class="eye-btn" @click="showPassword = !showPassword">
                                <view class="eye-icon" :class="{ closed: !showPassword }">
                                    <view class="eye-ball"></view>
                                </view>
                            </view>
                        </view>
                    </view>

                    <view class="btn-outer" @click="login">
                        <view class="btn-inner" :class="{ loading: loading }">
                            <text class="btn-text">{{ loading ? '验证中...' : '登 录' }}</text>
                        </view>
                    </view>
                </view>
            </view>

            <text class="footer-hint">设备报修 · 课表查询 · 空教室</text>
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
    background: #F2F3F5;
    display: flex;
    align-items: center;
    justify-content: center;
}
.container { width: 90%; max-width: 680rpx; }

/* Logo */
.logo-area { text-align: center; margin-bottom: 80rpx; }
.logo-outer {
    width: 128rpx; height: 128rpx; border-radius: 36rpx;
    background: rgba(0,0,0,0.03);
    border: 1rpx solid rgba(0,0,0,0.04);
    padding: 8rpx; display: inline-flex;
    margin-bottom: 32rpx;
}
.logo-inner {
    width: 100%; height: 100%; border-radius: 28rpx;
    background: #fff;
    box-shadow: inset 0 1rpx 1rpx rgba(255,255,255,0.8), 0 2rpx 8rpx rgba(0,0,0,0.04);
    display: flex; align-items: center; justify-content: center;
}
.shield { width: 44rpx; height: 52rpx; position: relative; }
.shield-body {
    width: 100%; height: 100%;
    border: 3rpx solid #1A1D1F;
    border-radius: 6rpx 6rpx 22rpx 22rpx;
}
.shield-check {
    position: absolute; bottom: 12rpx; left: 50%; transform: translateX(-50%);
    width: 16rpx; height: 10rpx;
    border-left: 3rpx solid #1A1D1F;
    border-bottom: 3rpx solid #1A1D1F;
    transform: translateX(-50%) rotate(-45deg);
}
.app-name { font-size: 44rpx; font-weight: 800; color: #1A1D1F; display: block; letter-spacing: 2rpx; }
.app-sub { font-size: 22rpx; color: #9CA3AF; display: block; margin-top: 10rpx; letter-spacing: 1rpx; }

/* 双层嵌套表单卡片 */
.form-outer {
    background: rgba(0,0,0,0.025);
    border: 1rpx solid rgba(0,0,0,0.04);
    border-radius: 32rpx;
    padding: 10rpx;
}
.form-inner {
    background: #fff;
    border-radius: 24rpx;
    padding: 40rpx 36rpx;
    box-shadow: inset 0 1rpx 1rpx rgba(255,255,255,0.8), 0 4rpx 16rpx rgba(0,0,0,0.03);
}

.input-group { margin-bottom: 32rpx; }
.input-label { font-size: 22rpx; color: #6B7280; font-weight: 600; margin-bottom: 12rpx; display: block; letter-spacing: 1rpx; text-transform: uppercase; }
.input-shell {
    background: #F8F9FA;
    border: 1rpx solid rgba(0,0,0,0.06);
    border-radius: 16rpx;
    display: flex; align-items: center;
    padding-right: 16rpx;
}
.input-field {
    flex: 1; height: 88rpx; padding: 0 24rpx;
    font-size: 28rpx; color: #1A1D1F;
    background: transparent; border: none;
}
.eye-btn { padding: 12rpx; }
.eye-icon {
    width: 36rpx; height: 24rpx;
    border: 2rpx solid #9CA3AF; border-radius: 12rpx;
    position: relative; display: flex; align-items: center; justify-content: center;
}
.eye-ball { width: 10rpx; height: 10rpx; border-radius: 50%; background: #9CA3AF; }
.eye-icon.closed { border-color: #D1D5DB; }
.eye-icon.closed .eye-ball { background: #D1D5DB; width: 2rpx; height: 2rpx; border-radius: 1rpx; }

/* 按钮 - 双层嵌套 */
.btn-outer {
    background: rgba(0,0,0,0.04);
    border: 1rpx solid rgba(0,0,0,0.06);
    border-radius: 20rpx;
    padding: 8rpx;
    margin-top: 12rpx;
}
.btn-inner {
    background: #1A1D1F;
    border-radius: 14rpx;
    height: 88rpx; display: flex; align-items: center; justify-content: center;
    box-shadow: inset 0 1rpx 1rpx rgba(255,255,255,0.05), 0 4rpx 12rpx rgba(0,0,0,0.15);
}
.btn-inner:active { background: #2D2F31; }
.btn-inner.loading { opacity: 0.6; }
.btn-text { color: #fff; font-size: 28rpx; font-weight: 600; letter-spacing: 4rpx; }

.footer-hint {
    display: block; text-align: center; margin-top: 48rpx;
    font-size: 20rpx; color: #B0B5BA; letter-spacing: 2rpx;
}
</style>
