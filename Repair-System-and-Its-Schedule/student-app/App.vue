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
/* ========================================
   Soft Structuralism Design System v2.0
   全局设计令牌 & 基础样式
   ======================================== */

/* ---- CSS 变量（设计令牌）---- */
page {
    /* 主色系 — 柔和蓝紫 */
    --color-primary: #6C5CE7;
    --color-primary-light: #A29BFE;
    --color-primary-dark: #5A4BD1;
    --color-primary-bg: #F0EEFF;
    --color-primary-gradient: linear-gradient(135deg, #6C5CE7 0%, #8B7CF6 50%, #A29BFE 100%);

    /* 强调色 */
    --color-accent: #4F7CFF;
    --color-accent-light: #DBE4FF;
    --color-accent-gradient: linear-gradient(135deg, #4F7CFF 0%, #6C9CFF 100%);

    /* 功能色 */
    --color-success: #10B981;
    --color-success-bg: #ECFDF5;
    --color-success-light: #D1FAE5;
    --color-warning: #F59E0B;
    --color-warning-bg: #FFFBEB;
    --color-warning-light: #FEF3C7;
    --color-danger: #EF4444;
    --color-danger-bg: #FEF2F2;
    --color-danger-light: #FEE2E2;
    --color-info: #3B82F6;
    --color-info-bg: #EFF6FF;
    --color-info-light: #DBEAFE;

    /* 中性色 */
    --color-bg: #F2F3F7;
    --color-bg-secondary: #F8F9FC;
    --color-surface: #FFFFFF;
    --color-border: #E8EAF0;
    --color-border-light: #F1F3F8;
    --color-divider: #F0F1F5;

    /* 文字色 */
    --color-text: #1E293B;
    --color-text-secondary: #64748B;
    --color-text-tertiary: #94A3B8;
    --color-text-placeholder: #CBD5E1;
    --color-text-inverse: #FFFFFF;

    /* 阴影系统 — 多层柔和阴影 */
    --shadow-xs: 0 1rpx 3rpx rgba(0, 0, 0, 0.04);
    --shadow-sm: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 8rpx 32rpx rgba(0, 0, 0, 0.08);
    --shadow-xl: 0 16rpx 48rpx rgba(0, 0, 0, 0.10);
    --shadow-glow: 0 0 24rpx rgba(108, 92, 231, 0.15);

    /* 圆角系统 */
    --radius-xs: 8rpx;
    --radius-sm: 12rpx;
    --radius-md: 16rpx;
    --radius-lg: 20rpx;
    --radius-xl: 24rpx;
    --radius-2xl: 32rpx;
    --radius-full: 9999rpx;

    /* 间距系统 */
    --space-xs: 8rpx;
    --space-sm: 12rpx;
    --space-md: 16rpx;
    --space-lg: 24rpx;
    --space-xl: 32rpx;
    --space-2xl: 48rpx;

    /* 字体 */
    --font-xs: 22rpx;
    --font-sm: 24rpx;
    --font-md: 28rpx;
    --font-lg: 32rpx;
    --font-xl: 36rpx;
    --font-2xl: 44rpx;
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;

    /* 动效 */
    --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 0.35s cubic-bezier(0.4, 0, 0.2, 1);

    /* 应用到 page */
    background-color: var(--color-bg);
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", "Microsoft YaHei", sans-serif;
    font-size: var(--font-md);
    color: var(--color-text);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ---- 全局动画 ---- */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20rpx); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.92); }
    to   { opacity: 1; transform: scale(1); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.5; }
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(30rpx); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes softBounce {
    0%   { transform: scale(1); }
    30%  { transform: scale(0.96); }
    60%  { transform: scale(1.02); }
    100% { transform: scale(1); }
}

/* ---- 通用工具类 ---- */
.container {
    padding: var(--space-lg);
}

/* 卡片系统 — 三层阴影 + 毛玻璃微质感 */
.card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: var(--space-xl);
    margin-bottom: var(--space-lg);
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
    transition: box-shadow var(--transition-normal), transform var(--transition-normal);
}
.card:active {
    box-shadow: var(--shadow-xs);
    transform: scale(0.985);
}
.card-elevated {
    box-shadow: var(--shadow-md);
    border: 1rpx solid transparent;
}
.card-glow {
    box-shadow: var(--shadow-glow);
    border: 1rpx solid rgba(108, 92, 231, 0.08);
}

.card-title {
    font-size: var(--font-lg);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
    margin-bottom: var(--space-lg);
    padding-bottom: var(--space-md);
    border-bottom: 1rpx solid var(--color-divider);
    display: flex;
    align-items: center;
    gap: 8rpx;
}
.card-title-icon {
    font-size: 36rpx;
}

/* 按钮系统 */
.btn-primary {
    background: var(--color-primary-gradient);
    color: var(--color-text-inverse);
    border: none;
    border-radius: var(--radius-md);
    height: 88rpx;
    line-height: 88rpx;
    font-size: 30rpx;
    font-weight: var(--font-weight-semibold);
    letter-spacing: 2rpx;
    box-shadow: 0 6rpx 20rpx rgba(108, 92, 231, 0.3);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}
.btn-primary::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%);
    opacity: 0;
    transition: opacity var(--transition-fast);
}
.btn-primary:active {
    transform: translateY(2rpx) scale(0.98);
    box-shadow: 0 3rpx 12rpx rgba(108, 92, 231, 0.2);
}
.btn-primary:active::after {
    opacity: 1;
}

.btn-outline {
    background: var(--color-surface);
    color: var(--color-primary);
    border: 2rpx solid var(--color-primary-light);
    border-radius: var(--radius-md);
    height: 88rpx;
    line-height: 88rpx;
    font-size: 30rpx;
    font-weight: var(--font-weight-medium);
    transition: all var(--transition-fast);
}
.btn-outline:active {
    background: var(--color-primary-bg);
    border-color: var(--color-primary);
}

/* 表单系统 */
.form-group {
    margin-bottom: var(--space-lg);
}
.form-label {
    font-size: var(--font-sm);
    color: var(--color-text-secondary);
    margin-bottom: var(--space-sm);
    font-weight: var(--font-weight-medium);
    display: block;
}
.form-input {
    width: 100%;
    height: 88rpx;
    padding: 0 var(--space-lg);
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: var(--font-md);
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
.form-input::placeholder {
    color: var(--color-text-placeholder);
}

.form-select {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 88rpx;
    padding: 0 var(--space-lg);
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: var(--font-md);
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
}

.form-textarea {
    width: 100%;
    min-height: 160rpx;
    padding: var(--space-md) var(--space-lg);
    border: 2rpx solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: var(--font-md);
    color: var(--color-text);
    background: var(--color-bg-secondary);
    box-sizing: border-box;
    transition: all var(--transition-fast);
    line-height: 1.6;
}
.form-textarea:focus {
    border-color: var(--color-primary);
    background: var(--color-surface);
    box-shadow: 0 0 0 4rpx rgba(108, 92, 231, 0.08);
}

/* 标签系统 */
.tag {
    display: inline-flex;
    align-items: center;
    padding: 4rpx 14rpx;
    border-radius: var(--radius-xs);
    font-size: var(--font-xs);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.5rpx;
}
.tag-success {
    background: var(--color-success-bg);
    color: var(--color-success);
}
.tag-info {
    background: var(--color-info-bg);
    color: var(--color-info);
}
.tag-warning {
    background: var(--color-warning-bg);
    color: var(--color-warning);
}
.tag-danger {
    background: var(--color-danger-bg);
    color: var(--color-danger);
}

/* 状态指示点 */
.status-dot {
    display: inline-block;
    width: 12rpx;
    height: 12rpx;
    border-radius: 50%;
    margin-right: 8rpx;
}
.status-dot-pending   { background: var(--color-warning); box-shadow: 0 0 8rpx rgba(245, 158, 11, 0.4); }
.status-dot-processing { background: var(--color-info);    box-shadow: 0 0 8rpx rgba(59, 130, 246, 0.4); }
.status-dot-resolved   { background: var(--color-success); box-shadow: 0 0 8rpx rgba(16, 185, 129, 0.4); }

/* 加载态 */
.loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80rpx var(--space-xl);
    color: var(--color-text-tertiary);
    font-size: var(--font-md);
    gap: var(--space-md);
}

/* 加载旋转器 */
.spinner {
    width: 44rpx;
    height: 44rpx;
    border: 3rpx solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

/* 骨架屏 */
.skeleton {
    background: linear-gradient(90deg, var(--color-border-light) 25%, var(--color-bg) 50%, var(--color-border-light) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: var(--radius-xs);
}

/* 空状态 */
.empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100rpx var(--space-2xl);
    color: var(--color-text-tertiary);
}
.empty-icon {
    font-size: 100rpx;
    margin-bottom: var(--space-lg);
    opacity: 0.6;
}
.empty-text {
    font-size: var(--font-md);
    text-align: center;
    line-height: 1.6;
}

/* 分隔线 */
.divider {
    height: 1rpx;
    background: var(--color-divider);
    margin: var(--space-md) 0;
}

/* 淡入动画工具类 */
.anim-fade-in {
    animation: fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1) both;
}
.anim-stagger-1 { animation-delay: 0.05s; }
.anim-stagger-2 { animation-delay: 0.10s; }
.anim-stagger-3 { animation-delay: 0.15s; }
.anim-stagger-4 { animation-delay: 0.20s; }
.anim-stagger-5 { animation-delay: 0.25s; }
</style>
