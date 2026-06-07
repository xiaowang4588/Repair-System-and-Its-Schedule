<template>
    <view class="page">
        <!-- 标签头部 -->
        <view class="tag-header">
            <text class="tag-name">#{{ tagName }}</text>
            <text class="tag-total">共 {{ total }} 条相关指南</text>
        </view>

        <!-- 动态列表 -->
        <view class="feed-list">
            <view class="guide-card" v-for="item in records" :key="item.id"
                  @click="goDetail(item.id)">
                <view class="card-header">
                    <view class="avatar">{{ item.student_name ? item.student_name[0] : '?' }}</view>
                    <view class="user-info">
                        <text class="user-name">{{ item.student_name }}</text>
                        <text class="post-time">{{ formatTime(item.created_at) }}</text>
                    </view>
                </view>
                <view class="card-content">
                    <text class="content-text">{{ item.content }}</text>
                </view>
                <view class="card-images" v-if="item.images && item.images.length > 0">
                    <image v-for="(img, idx) in item.images.slice(0,3)" :key="idx"
                           :src="getImageUrl(img)" mode="aspectFill" class="grid-image" />
                </view>
                <view class="card-tags">
                    <view class="device-tag" v-for="tag in item.device_tags" :key="tag">#{{ tag }}</view>
                    <view class="location-tag" v-if="item.location_tag">#{{ item.location_tag }}</view>
                </view>
                <view class="card-actions">
                    <view class="action-item"><text>👍</text><text class="action-count">{{ item.like_count || '' }}</text></view>
                    <view class="action-item"><text>💬</text><text class="action-count">{{ item.comment_count || '' }}</text></view>
                    <view class="action-item"><text>☆</text><text class="action-count">{{ item.favorite_count || '' }}</text></view>
                </view>
            </view>
        </view>

        <view class="empty" v-if="!loading && records.length === 0">
            <text class="empty-icon">📚</text>
            <text class="empty-text">暂无相关内容</text>
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
</template>

<script>
import { getImageUrl as resolveImageUrl } from '../../config/index.js'
import { getGuideList } from '../../api/index.js'

export default {
    data() {
        return {
            tagName: '',
            tagType: 'device',
            records: [],
            loading: false,
            loadingMore: false,
            currentPage: 1,
            totalPages: 1,
            hasMore: true,
            total: 0,
        }
    },
    onLoad(options) {
        this.tagName = decodeURIComponent(options.tag || '')
        this.tagType = options.type || 'device'
        this.loadRecords()
    },
    methods: {
        async loadRecords() {
            this.loading = true
            this.currentPage = 1
            const params = { page: 1, page_size: 20 }
            if (this.tagType === 'device') params.device_tag = this.tagName
            else params.location_tag = this.tagName

            try {
                const res = await getGuideList(params)
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
            const params = { page: this.currentPage, page_size: 20 }
            if (this.tagType === 'device') params.device_tag = this.tagName
            else params.location_tag = this.tagName
            try {
                const res = await getGuideList(params)
                if (res && res.status === 'ok') {
                    this.records = [...this.records, ...(res.records || [])]
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (e) { this.currentPage-- }
            finally { this.loadingMore = false }
        },
        goDetail(id) { uni.navigateTo({ url: `/pages/guide/detail?id=${id}` }) },
        getImageUrl(img) { return resolveImageUrl(img) },
        formatTime(t) { if (!t) return ''; const p = t.split(' '); if (p.length >= 2) return p[0].substring(5) + ' ' + p[1].substring(0,5); return t },
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: var(--color-bg); }
.tag-header {
    background: var(--color-primary-gradient); padding: 36rpx 28rpx 40rpx;
    border-radius: 0 0 32rpx 32rpx; position: relative; overflow: hidden;
}
.tag-header::after {
    content: ''; position: absolute; top: -40rpx; right: -30rpx;
    width: 160rpx; height: 160rpx; border-radius: 50%;
    background: rgba(255,255,255,0.06);
}
.tag-name { font-size: 40rpx; font-weight: 700; color: white; display: block; position: relative; z-index: 1; }
.tag-total { font-size: 24rpx; color: rgba(255,255,255,0.75); display: block; margin-top: 8rpx; position: relative; z-index: 1; }
.feed-list { padding: 16rpx 24rpx; }
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
.card-content { margin-bottom: 12rpx; }
.content-text { font-size: 28rpx; color: var(--color-text); line-height: 1.55; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; }
.card-images { display: flex; gap: 8rpx; margin-bottom: 12rpx; }
.grid-image { width: 180rpx; height: 180rpx; border-radius: 10rpx; background: var(--color-bg); }
.card-tags { display: flex; flex-wrap: wrap; gap: 10rpx; margin-bottom: 12rpx; }
.device-tag { padding: 4rpx 14rpx; border-radius: 6rpx; font-size: 22rpx; background: var(--color-primary-bg); color: var(--color-primary); font-weight: 500; }
.location-tag { padding: 4rpx 14rpx; border-radius: 6rpx; font-size: 22rpx; background: var(--color-info-bg); color: var(--color-info); font-weight: 500; }
.card-actions { display: flex; border-top: 1rpx solid var(--color-divider); padding-top: 12rpx; }
.action-item { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6rpx; font-size: 24rpx; color: var(--color-text-tertiary); }
.action-count { font-size: 22rpx; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; }
.empty-icon { font-size: 80rpx; margin-bottom: 24rpx; opacity: 0.5; }
.empty-text { font-size: 28rpx; color: var(--color-text-tertiary); }
.loading-area { display: flex; flex-direction: column; align-items: center; padding: 60rpx 0; gap: 12rpx; font-size: 26rpx; color: var(--color-text-tertiary); }
.spinner-ring { width: 44rpx; height: 44rpx; border: 3rpx solid var(--color-border); border-top: 3rpx solid var(--color-primary); border-radius: 50%; animation: tag-spin 0.7s linear infinite; }
@keyframes tag-spin { to { transform: rotate(360deg); } }
.loading-spin { display: flex; align-items: center; justify-content: center; gap: 8rpx; padding: 20rpx 0; font-size: 26rpx; color: var(--color-text-tertiary); }
.mini-spinner { width: 28rpx; height: 28rpx; border: 2rpx solid var(--color-border); border-top: 2rpx solid var(--color-primary); border-radius: 50%; animation: tag-spin 0.7s linear infinite; }
.loading { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: var(--color-text-tertiary); }
.load-more { padding: 20rpx 0; text-align: center; }
.load-more-btn { padding: 20rpx; font-size: 28rpx; color: var(--color-primary); font-weight: 500; }
.no-more { padding: 20rpx; font-size: 26rpx; color: var(--color-text-tertiary); }
</style>
