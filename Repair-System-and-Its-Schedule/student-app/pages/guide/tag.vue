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

        <view class="loading" v-if="loading"><text>加载中...</text></view>

        <view class="load-more" v-if="records.length > 0">
            <view v-if="loadingMore" class="loading"><text>加载中...</text></view>
            <view v-else-if="hasMore" @click="loadMore" class="load-more-btn"><text>加载更多</text></view>
            <view v-else class="no-more"><text>没有更多了</text></view>
        </view>
    </view>
</template>

<script>
import config from '../../config/index.js'
import { getGuideList } from '../../api/index.js'
const API_BASE = config.API_BASE

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
        getImageUrl(img) { if (!img) return ''; if (img.startsWith('http')) return img; return API_BASE + img },
        formatTime(t) { if (!t) return ''; const p = t.split(' '); if (p.length >= 2) return p[0].substring(5) + ' ' + p[1].substring(0,5); return t },
    }
}
</script>

<style scoped>
.page { min-height: 100vh; background: #F5F7FA; }
.tag-header { background: #4F7CFF; padding: 32rpx 24rpx; }
.tag-name { font-size: 40rpx; font-weight: 700; color: white; display: block; }
.tag-total { font-size: 24rpx; color: rgba(255,255,255,0.8); display: block; margin-top: 8rpx; }
.feed-list { padding: 16rpx 24rpx; }
.guide-card { background: white; border-radius: 16rpx; padding: 28rpx; margin-bottom: 20rpx; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06); }
.guide-card:active { background: #fafbff; }
.card-header { display: flex; align-items: center; margin-bottom: 16rpx; }
.avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: #4F7CFF; color: white; display: flex; align-items: center; justify-content: center; font-size: 28rpx; font-weight: 600; margin-right: 16rpx; flex-shrink: 0; }
.user-info { flex: 1; }
.user-name { font-size: 28rpx; font-weight: 600; color: #333; display: block; }
.post-time { font-size: 20rpx; color: #999; display: block; }
.card-content { margin-bottom: 12rpx; }
.content-text { font-size: 28rpx; color: #333; line-height: 1.5; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; }
.card-images { display: flex; gap: 8rpx; margin-bottom: 12rpx; }
.grid-image { width: 180rpx; height: 180rpx; border-radius: 8rpx; background: #f0f0f0; }
.card-tags { display: flex; flex-wrap: wrap; gap: 12rpx; margin-bottom: 12rpx; }
.device-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; background: #EEF2FF; color: #4F7CFF; }
.location-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; background: #F0F9FF; color: #1890ff; }
.card-actions { display: flex; border-top: 1rpx solid #f5f5f5; padding-top: 12rpx; }
.action-item { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8rpx; font-size: 24rpx; color: #999; }
.action-count { font-size: 22rpx; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; }
.empty-icon { font-size: 80rpx; margin-bottom: 24rpx; }
.empty-text { font-size: 28rpx; color: #999; }
.loading { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: #999; }
.load-more { padding: 20rpx 0; text-align: center; }
.load-more-btn { padding: 20rpx; font-size: 28rpx; color: #4F7CFF; }
.no-more { padding: 20rpx; font-size: 26rpx; color: #999; }
</style>
