<template>
    <view class="page">
        <view class="container">
            <!-- 统计 -->
            <view class="stats-bar">
                <text class="stats-text">共发布 {{ total }} 条防坑指南</text>
            </view>

            <!-- 列表 -->
            <view class="guide-card" v-for="item in records" :key="item.id">
                <view class="card-header">
                    <view class="post-time">{{ formatTime(item.created_at) }}</view>
                    <view class="card-actions-btn">
                        <text class="edit-btn" @click="goEdit(item)">编辑</text>
                        <text class="delete-btn" @click="confirmDelete(item.id)">删除</text>
                    </view>
                </view>
                <view class="card-content" @click="goDetail(item.id)">
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
                <view class="card-stats" @click="goDetail(item.id)">
                    <text>👍 {{ item.like_count || 0 }}</text>
                    <text>💬 {{ item.comment_count || 0 }}</text>
                    <text>⭐ {{ item.favorite_count || 0 }}</text>
                </view>
            </view>

            <view class="empty" v-if="!loading && records.length === 0">
                <text class="empty-icon">📝</text>
                <text class="empty-text">还没有发布过防坑指南</text>
            </view>

            <view class="loading" v-if="loading"><text>加载中...</text></view>

            <view class="load-more" v-if="records.length > 0">
                <view v-if="loadingMore" class="loading"><text>加载中...</text></view>
                <view v-else-if="hasMore" @click="loadMore" class="load-more-btn"><text>加载更多</text></view>
                <view v-else class="no-more"><text>没有更多了</text></view>
            </view>
        </view>
    </view>
</template>

<script>
import { getImageUrl as resolveImageUrl } from '../../config/index.js'
import { getMyGuidePosts, deleteGuide } from '../../api/index.js'

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
                const res = await getMyGuidePosts({ page: 1, page_size: 20 })
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
                const res = await getMyGuidePosts({ page: this.currentPage, page_size: 20 })
                if (res && res.status === 'ok') {
                    this.records = [...this.records, ...(res.records || [])]
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (e) { this.currentPage-- }
            finally { this.loadingMore = false }
        },
        confirmDelete(id) {
            uni.showModal({
                title: '确认删除', content: '确定删除这条防坑指南吗？',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            const resp = await deleteGuide(id)
                            if (resp && resp.status === 'ok') {
                                uni.showToast({ title: '删除成功', icon: 'success' })
                                this.loadRecords()
                            }
                        } catch (e) { uni.showToast({ title: '删除失败', icon: 'none' }) }
                    }
                }
            })
        },
        goDetail(id) { uni.navigateTo({ url: `/pages/guide/detail?id=${id}` }) },
        goEdit(item) { uni.navigateTo({ url: `/pages/guide/publish?edit=${item.id}` }) },
        getImageUrl(img) { return resolveImageUrl(img) },
        formatTime(t) { if (!t) return ''; const p = t.split(' '); if (p.length >= 2) return p[0].substring(5) + ' ' + p[1].substring(0,5); return t },
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #F5F7FA; }
.container { padding: 24rpx; }
.stats-bar { padding: 16rpx 0; }
.stats-text { font-size: 26rpx; color: #999; }
.guide-card { background: white; border-radius: 16rpx; padding: 28rpx; margin-bottom: 20rpx; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.post-time { font-size: 24rpx; color: #999; }
.card-actions-btn { display: flex; gap: 16rpx; }
.edit-btn { font-size: 24rpx; color: #4F7CFF; padding: 4rpx 16rpx; border: 1rpx solid #4F7CFF; border-radius: 6rpx; }
.delete-btn { font-size: 24rpx; color: #ff4d4f; padding: 4rpx 16rpx; border: 1rpx solid #ff4d4f; border-radius: 6rpx; }
.card-content { margin-bottom: 12rpx; }
.content-text { font-size: 28rpx; color: #333; line-height: 1.5; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 4; overflow: hidden; }
.card-images { display: flex; gap: 8rpx; margin-bottom: 12rpx; }
.grid-image { width: 160rpx; height: 160rpx; border-radius: 8rpx; background: #f0f0f0; }
.card-tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-bottom: 12rpx; }
.device-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; background: #EEF2FF; color: #4F7CFF; }
.location-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; background: #F0F9FF; color: #1890ff; }
.card-stats { display: flex; gap: 32rpx; font-size: 24rpx; color: #999; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; }
.empty-icon { font-size: 80rpx; margin-bottom: 24rpx; }
.empty-text { font-size: 28rpx; color: #999; }
.loading { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: #999; }
.load-more { padding: 20rpx 0; text-align: center; }
.load-more-btn { padding: 20rpx; font-size: 28rpx; color: #4F7CFF; }
.no-more { padding: 20rpx; font-size: 26rpx; color: #999; }
</style>
