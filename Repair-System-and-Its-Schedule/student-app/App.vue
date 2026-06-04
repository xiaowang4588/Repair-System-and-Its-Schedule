<script>
export default {
    onLaunch() {
        console.log('App Launch')
    },
    onShow() {
        console.log('App Show')
    },
    onHide() {
        console.log('App Hide')
    }
}
</script>

<style>
/* 全局样式 */
page {
    background-color: #f0f2f5;
    font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 28rpx;
    color: #333;
}

/* 通用工具类 */
.container {
    padding: 24rpx;
}

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

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12rpx;
    height: 88rpx;
    line-height: 88rpx;
    font-size: 30rpx;
    font-weight: 500;
}

.btn-primary:active {
    opacity: 0.9;
}

.form-group {
    margin-bottom: 24rpx;
}

.form-label {
    font-size: 28rpx;
    color: #555;
    margin-bottom: 12rpx;
}

.form-input {
    width: 100%;
    height: 88rpx;
    padding: 0 24rpx;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    background: #fafafa;
}

.form-input:focus {
    border-color: #667eea;
    background: white;
}

.form-select {
    width: 100%;
    height: 88rpx;
    padding: 0 24rpx;
    border: 1rpx solid #d9d9d9;
    border-radius: 12rpx;
    font-size: 28rpx;
    background: #fafafa;
}

.tag {
    display: inline-block;
    padding: 4rpx 16rpx;
    border-radius: 8rpx;
    font-size: 24rpx;
}

.tag-success {
    background: #f6ffed;
    border: 1rpx solid #b7eb8f;
    color: #389e0d;
}

.tag-info {
    background: #e6f7ff;
    border: 1rpx solid #91d5ff;
    color: #1890ff;
}

/* 加载状态 */
.loading {
    text-align: center;
    padding: 60rpx;
    color: #999;
    font-size: 28rpx;
}

/* 空状态 */
.empty {
    text-align: center;
    padding: 80rpx 40rpx;
    color: #999;
}

.empty-icon {
    font-size: 96rpx;
    margin-bottom: 24rpx;
}

.empty-text {
    font-size: 28rpx;
}
</style>
