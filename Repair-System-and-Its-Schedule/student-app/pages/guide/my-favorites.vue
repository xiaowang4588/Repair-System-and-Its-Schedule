<template>
    <view class="page">
        <view class="container">
            <view class="stats-bar">
                <text class="stats-text">共收藏 {{ total }} 条防坑指南</text>
            </view>

            <view class="guide-card" v-for="item in records" :key="item.id"
                  @click="goDetail(item.id)">
                <view class="card-header">
                    <view class="avatar">{{ item.student_name ? item.student_name[0] : '?' }}</view>
                    <view class="user-info">
                        <text class="user-name">{{ item.student_name }}</text>
                        <text class="post-time">{{ formatTime(item.created_at) }}</text>
                    </view>
                    <text class="unfav-btn" @click.stop="unfavorite(item)">取消收藏</text>
                </view>
                <view class="card-content">
                    <text class="content-text">{{ item.content }}</text>
                </view>
                <view class="card-tags">
                    <view class="device-tag" v-for="tag in item.device_tags" :key="tag">#{{ tag }}</view>
                    <view class="location-tag" v-if="item.location_tag">#{{ item.location_tag }}</view>
                </view>
            </view>

            <view class="empty" v-if="!loading && records.length === 0">
                <text class="empty-icon">⭐</text>
                <text class="empty-text">还没有收藏任何防坑指南</text>
            </view>

            <view class="loading-area" v-if="loading">
                <view class="spinner-ring"></view>
                <text>加载中...</text>
            </view>

            <view class="load-more" v-if="records.length > 0">
                <view v-if="loadingMore" class="loading-spin"><view class="mini-spinner"></view><text>加载中...</text></view>
                <view v-else-if="hasMore" @click="loadMore" class="load-more-btn"><text>加载更多</text></view>
                <view v-else class="no-more"><text>没有更多了</text></view>
            </view>
        </view>
    </view>
</template>

<script>
import { getMyGuideFavorites, toggleGuideFavorite } from '../../api/index.js'

export default {
    data() {
        return {
            records: [],
            loading: false,
            loadingMore: false,
            currentPage: 1,
            totalPages: 1,
            hasMore: true,
            total: 0,
        }
    },
    onLoad() { this.loadRecords() },
    onShow() { this.loadRecords() },
    methods: {
        async loadRecords() {
            this.loading = true
            this.currentPage = 1
            try {
                const res = await getMyGuideFavorites({ page: 1, page_size: 20 })
                if (res && res.status === 'ok') {
                    this.records = res.records || []
                    this.total = res.total || 0
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (e) { console.error(e) }
            finally { this.loading = false }
        },
        async loadMore() {
            if (this.loadingMore || !this.hasMore) return
            this.loadingMore = true
            this.currentPage++
            try {
                const res = await getMyGuideFavorites({ page: this.currentPage, page_size: 20 })
                if (res && res.status === 'ok') {
                    this.records = [...this.records, ...(res.records || [])]
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (e) { this.currentPage-- }
            finally { this.loadingMore = false }
        },
        async unfavorite(item) {
            try {
                const res = await toggleGuideFavorite(item.id)
                if (res && res.status === 'ok') {
                    uni.showToast({ title: '已取消收藏', icon: 'success' })
                    this.records = this.records.filter(r => r.id !== item.id)
                    this.total = Math.max(0, this.total - 1)
                }
            } catch (e) { uni.showToast({ title: '操作失败', icon: 'none' }) }
        },
        goDetail(id) { uni.navigateTo({ url: `/pages/guide/detail?id=${id}` }) },
        formatTime(t) { if (!t) return ''; const p = t.split(' '); if (p.length >= 2) return p[0].substring(5) + ' ' + p[1].substring(0,5); return t },
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg); }
.container { padding: 24rpx; }
.stats-bar { padding: 16rpx 0; }
.stats-text { font-size: 26rpx; color: var(--color-text-tertiary); }
.guide-card {
    background: var(--color-surface); border-radius: var(--radius-lg); padding: 28rpx;
    margin-bottom: 16rpx; box-shadow: var(--shadow-sm); border: 1rpx solid var(--color-border-light);
    transition: all var(--transition-fast);
}
.guide-card:active { transform: scale(0.985); box-shadow: var(--shadow-xs); }
.card-header { display: flex; align-items: center; margin-bottom: 16rpx; }
.avatar {
    width: 64rpx; height: 64rpx; border-radius: 50%;
    background: var(--color-primary-gradient); color: white;
    display: flex; align-items: center; justify-content: center;
    font-size: 28rpx; font-weight: 600; margin-right: 16rpx; flex-shrink: 0;
    box-shadow: 0 3rpx 10rpx rgba(108, 92, 231, 0.2);
}
.user-info { flex: 1; }
.user-name { font-size: 28rpx; font-weight: 600; color: var(--color-text); display: block; }
.post-time { font-size: 20rpx; color: var(--color-text-tertiary); display: block; }
.unfav-btn { font-size: 24rpx; color: var(--color-warning); padding: 6rpx 18rpx; border: 1rpx solid var(--color-warning-light); border-radius: var(--radius-xs); white-space: nowrap; font-weight: 500; }
.card-content { margin-bottom: 12rpx; }
.content-text { font-size: 28rpx; color: var(--color-text); line-height: 1.55; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; }
.card-tags { display: flex; flex-wrap: wrap; gap: 10rpx; }
.device-tag { padding: 4rpx 14rpx; border-radius: 6rpx; font-size: 22rpx; background: var(--color-primary-bg); color: var(--color-primary); font-weight: 500; }
.location-tag { padding: 4rpx 14rpx; border-radius: 6rpx; font-size: 22rpx; background: var(--color-info-bg); color: var(--color-info); font-weight: 500; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; }
.empty-icon { font-size: 80rpx; margin-bottom: 24rpx; opacity: 0.5; }
.empty-text { font-size: 28rpx; color: var(--color-text-tertiary); }
.loading-area { display: flex; flex-direction: column; align-items: center; padding: 60rpx 0; gap: 12rpx; font-size: 26rpx; color: var(--color-text-tertiary); }
.spinner-ring { width: 44rpx; height: 44rpx; border: 3rpx solid var(--color-border); border-top: 3rpx solid var(--color-primary); border-radius: 50%; animation: fav-spin 0.7s linear infinite; }
@keyframes fav-spin { to { transform: rotate(360deg); } }
.loading-spin { display: flex; align-items: center; justify-content: center; gap: 8rpx; padding: 20rpx 0; font-size: 26rpx; color: var(--color-text-tertiary); }
.mini-spinner { width: 28rpx; height: 28rpx; border: 2rpx solid var(--color-border); border-top: 2rpx solid var(--color-primary); border-radius: 50%; animation: fav-spin 0.7s linear infinite; }
.loading { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: var(--color-text-tertiary); }
.load-more { padding: 20rpx 0; text-align: center; }
.load-more-btn { padding: 20rpx; font-size: 28rpx; color: var(--color-primary); font-weight: 500; }
.no-more { padding: 20rpx; font-size: 26rpx; color: var(--color-text-tertiary); }
</style>
