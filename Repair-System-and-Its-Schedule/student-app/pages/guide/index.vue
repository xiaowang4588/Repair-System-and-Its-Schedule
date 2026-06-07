<template>
    <view class="page">
        <!-- 搜索栏 -->
        <view class="search-bar">
            <view class="search-input-wrap">
                <text class="search-icon">🔍</text>
                <input class="search-input" v-model="keyword"
                       placeholder="搜索设备、故障、人员..." confirm-type="search"
                       @confirm="doSearch" />
                <text v-if="keyword" class="search-clear" @click="clearSearch">✕</text>
            </view>
            <text v-if="isSearching" class="search-cancel" @click="cancelSearch">取消</text>
        </view>

        <!-- 标签筛选 -->
        <scroll-view scroll-x class="tag-scroll" v-if="!isSearching">
            <view class="tag-list">
                <view class="tag-item" :class="{ active: activeDeviceTag === '' }"
                      @click="filterByDeviceTag('')">全部</view>
                <view class="tag-item" :class="{ active: activeDeviceTag === t.name }"
                      v-for="t in deviceTags" :key="t.name"
                      @click="filterByDeviceTag(t.name)">
                    #{{ t.name }}
                    <text class="tag-count">{{ t.count }}</text>
                </view>
            </view>
        </scroll-view>

        <!-- 搜索结果提示 -->
        <view v-if="isSearching" class="search-tip">
            <text>搜索"{{ searchKeyword }}"的结果（{{ total }}条）</text>
        </view>

        <!-- 动态列表 -->
        <view class="feed-list">
            <view class="guide-card" v-for="item in records" :key="item.id"
                  @click="goDetail(item.id)">
                <!-- 用户信息 -->
                <view class="card-header">
                    <view class="avatar">{{ item.student_name ? item.student_name[0] : '?' }}</view>
                    <view class="user-info">
                        <text class="user-name">{{ item.student_name }}</text>
                        <text class="post-time">{{ formatTime(item.created_at) }}</text>
                    </view>
                </view>

                <!-- 文字内容 -->
                <view class="card-content">
                    <text class="content-text">{{ item.content }}</text>
                </view>

                <!-- 图片 -->
                <view class="card-images" v-if="item.images && item.images.length > 0">
                    <view v-for="(img, idx) in item.images" :key="idx"
                          class="grid-image-wrap" :class="'grid-' + Math.min(item.images.length, 3)"
                          @click.stop="previewImage(item.images, idx)">
                        <image :src="getImageUrl(img)" mode="aspectFill"
                               class="grid-image" @error="onImageError" />
                    </view>
                </view>

                <!-- 视频 -->
                <view class="card-video" v-if="item.video_url" @click.stop="playVideo(item.video_url)">
                    <view class="video-cover">
                        <text class="video-play-icon">▶</text>
                        <text class="video-duration" v-if="item.video_duration">
                            {{ formatDuration(item.video_duration) }}
                        </text>
                    </view>
                </view>

                <!-- 标签 -->
                <view class="card-tags">
                    <view class="device-tag" v-for="tag in item.device_tags" :key="tag"
                          @click.stop="filterByDeviceTag(tag)">
                        #{{ tag }}
                    </view>
                    <view class="location-tag" v-if="item.location_tag"
                          @click.stop="filterByLocationTag(item.location_tag)">
                        #{{ item.location_tag }}
                    </view>
                </view>

                <!-- 互动栏 -->
                <view class="card-actions">
                    <view class="action-item" :class="{ liked: item.is_liked }"
                          @click.stop="toggleLike(item)">
                        <text>{{ item.is_liked ? '❤️' : '👍' }}</text>
                        <text class="action-count">{{ item.like_count || '' }}</text>
                    </view>
                    <view class="action-item" @click.stop="goDetail(item.id)">
                        <text>💬</text>
                        <text class="action-count">{{ item.comment_count || '' }}</text>
                    </view>
                    <view class="action-item" :class="{ favorited: item.is_favorited }"
                          @click.stop="toggleFavorite(item)">
                        <text>{{ item.is_favorited ? '⭐' : '☆' }}</text>
                        <text class="action-count">{{ item.favorite_count || '' }}</text>
                    </view>
                </view>
            </view>
        </view>

        <!-- 空状态 -->
        <view class="empty" v-if="!loading && records.length === 0">
            <text class="empty-icon">📚</text>
            <text class="empty-text">{{ isSearching ? '没有找到相关内容' : '还没有防坑指南，快来发布第一条吧！' }}</text>
        </view>

        <!-- 加载中 -->
        <view class="loading-area" v-if="loading">
            <view class="spinner-ring"></view>
            <text>加载中...</text>
        </view>

        <!-- 加载更多 -->
        <view class="load-more" v-if="records.length > 0">
            <view v-if="loadingMore" class="loading-more-spin"><view class="mini-spinner"></view><text>加载中...</text></view>
            <view v-else-if="hasMore" @click="loadMore" class="load-more-btn"><text>点击加载更多</text></view>
            <view v-else class="no-more"><text>没有更多了</text></view>
        </view>

        <!-- 发布按钮 -->
        <view class="fab-btn" @click="goPublish">
            <text class="fab-icon">✏️</text>
        </view>
    </view>
</template>

<script>
import { getImageUrl as resolveImageUrl } from '../../config/index.js'
import { getGuideList, searchGuide, getGuideTags, toggleGuideLike, toggleGuideFavorite } from '../../api/index.js'

export default {
    data() {
        return {
            records: [],
            deviceTags: [],
            activeDeviceTag: '',
            activeLocationTag: '',
            keyword: '',
            searchKeyword: '',
            isSearching: false,
            loading: false,
            loadingMore: false,
            currentPage: 1,
            totalPages: 1,
            hasMore: true,
            total: 0,
        }
    },
    onLoad() {
        this.loadTags()
        this.loadRecords()
    },
    onShow() {
        // 从发布页返回时刷新
        if (this._needRefresh) {
            this._needRefresh = false
            this.refreshList()
        }
    },
    methods: {
        // 加载标签
        async loadTags() {
            try {
                const res = await getGuideTags()
                if (res && res.status === 'ok') {
                    this.deviceTags = res.data.device_tags || []
                }
            } catch (e) {
                console.error('加载标签失败:', e)
            }
        },

        // 加载动态列表
        async loadRecords() {
            this.loading = true
            this.currentPage = 1
            const params = { page: 1, page_size: 20 }
            if (this.activeDeviceTag) params.device_tag = this.activeDeviceTag
            if (this.activeLocationTag) params.location_tag = this.activeLocationTag

            try {
                const res = await getGuideList(params)
                if (res && res.status === 'ok') {
                    this.records = res.records || []
                    this.totalPages = res.total_pages || 1
                    this.total = res.total || 0
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (e) {
                console.error('加载动态失败:', e)
            } finally {
                this.loading = false
            }
        },

        // 加载更多
        async loadMore() {
            if (this.loadingMore || !this.hasMore) return
            this.loadingMore = true
            this.currentPage++

            const params = { page: this.currentPage, page_size: 20 }
            if (this.activeDeviceTag) params.device_tag = this.activeDeviceTag
            if (this.activeLocationTag) params.location_tag = this.activeLocationTag

            try {
                const fn = this.isSearching ? searchGuide : getGuideList
                if (this.isSearching) params.keyword = this.searchKeyword
                const res = await fn(params)
                if (res && res.status === 'ok') {
                    this.records = [...this.records, ...(res.records || [])]
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (e) {
                this.currentPage--
            } finally {
                this.loadingMore = false
            }
        },

        // 刷新列表
        refreshList() {
            this.records = []
            this.hasMore = true
            this.loadRecords()
            this.loadTags()
        },

        // 按设备标签筛选
        filterByDeviceTag(tag) {
            if (this.activeDeviceTag === tag) return
            this.activeDeviceTag = tag
            this.isSearching = false
            this.keyword = ''
            this.refreshList()
        },

        // 按地点标签筛选
        filterByLocationTag(tag) {
            this.activeLocationTag = tag
            this.isSearching = false
            this.keyword = ''
            this.refreshList()
        },

        // 搜索
        async doSearch() {
            const kw = this.keyword.trim()
            if (!kw) return
            this.isSearching = true
            this.searchKeyword = kw
            this.loading = true
            this.currentPage = 1

            try {
                const res = await searchGuide({ keyword: kw, page: 1, page_size: 20 })
                if (res && res.status === 'ok') {
                    this.records = res.records || []
                    this.total = res.total || 0
                    this.totalPages = res.total_pages || 1
                    this.hasMore = this.currentPage < this.totalPages
                }
            } catch (e) {
                console.error('搜索失败:', e)
            } finally {
                this.loading = false
            }
        },

        // 清除搜索
        clearSearch() {
            this.keyword = ''
            if (this.isSearching) {
                this.cancelSearch()
            }
        },

        // 取消搜索
        cancelSearch() {
            this.isSearching = false
            this.searchKeyword = ''
            this.keyword = ''
            this.refreshList()
        },

        // 点赞
        async toggleLike(item) {
            try {
                const res = await toggleGuideLike(item.id)
                if (res && res.status === 'ok') {
                    item.is_liked = res.data.is_liked
                    item.like_count = res.data.like_count
                }
            } catch (e) {
                console.error('点赞失败:', e)
            }
        },

        // 收藏
        async toggleFavorite(item) {
            try {
                const res = await toggleGuideFavorite(item.id)
                if (res && res.status === 'ok') {
                    item.is_favorited = res.data.is_favorited
                    item.favorite_count = res.data.favorite_count
                }
            } catch (e) {
                console.error('收藏失败:', e)
            }
        },

        // 跳转详情
        goDetail(id) {
            uni.navigateTo({ url: `/pages/guide/detail?id=${id}` })
        },

        // 跳转发布
        goPublish() {
            this._needRefresh = true
            uni.navigateTo({ url: '/pages/guide/publish' })
        },

        // 图片预览
        previewImage(images, index) {
            const urls = images.map(img => this.getImageUrl(img))
            uni.previewImage({ urls, current: urls[index] })
        },

        onImageError(e) {
            console.error('图片加载失败:', e)
        },

        // 播放视频
        playVideo(url) {
            uni.navigateTo({ url: `/pages/guide/detail?id=${this.records.find(r => r.video_url === url)?.id || ''}` })
        },

        // 获取图片完整URL（委托给共享工具函数）
        getImageUrl(img) { return resolveImageUrl(img) },

        // 格式化时间
        formatTime(t) {
            if (!t) return ''
            const parts = t.split(' ')
            if (parts.length >= 2) {
                const md = parts[0].substring(5)
                const hm = parts[1].substring(0, 5)
                return `${md} ${hm}`
            }
            return t
        },

        // 格式化视频时长
        formatDuration(seconds) {
            if (!seconds) return ''
            const m = Math.floor(seconds / 60)
            const s = seconds % 60
            return `${m}:${s.toString().padStart(2, '0')}`
        },
    }
}
</script>

<style scoped>
.page {
    min-height: 100vh;
    background: var(--color-bg);
    padding-bottom: 120rpx;
}

/* ---- 搜索栏 ---- */
.search-bar {
    display: flex;
    align-items: center;
    padding: 16rpx 24rpx;
    background: var(--color-surface);
    position: sticky;
    top: 0;
    z-index: 10;
    border-bottom: 1rpx solid var(--color-border-light);
}

.search-input-wrap {
    flex: 1;
    display: flex;
    align-items: center;
    background: var(--color-bg);
    border-radius: 36rpx;
    padding: 0 24rpx;
    height: 72rpx;
    border: 2rpx solid transparent;
    transition: all var(--transition-fast);
}
.search-input-wrap:focus-within {
    border-color: var(--color-primary-light);
    background: var(--color-surface);
    box-shadow: 0 0 0 4rpx rgba(108, 92, 231, 0.06);
}

.search-icon {
    font-size: 28rpx;
    margin-right: 12rpx;
    opacity: 0.5;
}

.search-input {
    flex: 1;
    font-size: 28rpx;
    color: var(--color-text);
}

.search-clear {
    font-size: 28rpx;
    color: var(--color-text-tertiary);
    padding: 8rpx;
}

.search-cancel {
    font-size: 28rpx;
    color: var(--color-primary);
    margin-left: 16rpx;
    white-space: nowrap;
    font-weight: 500;
}

.search-tip {
    padding: 16rpx 24rpx;
    font-size: 24rpx;
    color: var(--color-text-tertiary);
    background: var(--color-surface);
    border-bottom: 1rpx solid var(--color-divider);
}

/* ---- 标签滚动 ---- */
.tag-scroll {
    background: var(--color-surface);
    white-space: nowrap;
    border-bottom: 1rpx solid var(--color-divider);
}

.tag-list {
    display: inline-flex;
    padding: 16rpx 24rpx;
    gap: 12rpx;
}

.tag-item {
    display: inline-flex;
    align-items: center;
    padding: 8rpx 22rpx;
    border-radius: 28rpx;
    font-size: 24rpx;
    color: var(--color-text-secondary);
    background: var(--color-bg);
    white-space: nowrap;
    font-weight: 500;
    transition: all var(--transition-fast);
}
.tag-item.active {
    background: var(--color-primary-gradient);
    color: white;
    box-shadow: 0 4rpx 12rpx rgba(108, 92, 231, 0.25);
}

.tag-count {
    font-size: 20rpx;
    margin-left: 6rpx;
    opacity: 0.75;
}

/* ---- 动态卡片 ---- */
.feed-list {
    padding: 16rpx 24rpx;
}

.guide-card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 28rpx;
    margin-bottom: 20rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
    transition: all var(--transition-fast);
    animation: fadeInUp 0.35s ease both;
}
.guide-card:active {
    transform: scale(0.985);
    box-shadow: var(--shadow-xs);
}

.card-header {
    display: flex;
    align-items: center;
    margin-bottom: 18rpx;
}

.avatar {
    width: 72rpx;
    height: 72rpx;
    border-radius: 50%;
    background: var(--color-primary-gradient);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32rpx;
    font-weight: 600;
    margin-right: 18rpx;
    flex-shrink: 0;
    box-shadow: 0 4rpx 12rpx rgba(108, 92, 231, 0.2);
}

.user-info {
    flex: 1;
}

.user-name {
    font-size: 30rpx;
    font-weight: 600;
    color: var(--color-text);
    display: block;
}

.post-time {
    font-size: 22rpx;
    color: var(--color-text-tertiary);
    display: block;
    margin-top: 4rpx;
}

.card-content {
    margin-bottom: 16rpx;
}

.content-text {
    font-size: 28rpx;
    color: var(--color-text);
    line-height: 1.7;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 6;
    overflow: hidden;
}

/* ---- 图片网格 ---- */
.card-images {
    display: flex;
    flex-wrap: wrap;
    gap: 8rpx;
    margin-bottom: 16rpx;
}

.grid-image-wrap {
    border-radius: 10rpx;
    overflow: hidden;
    background: var(--color-bg);
}

.grid-image {
    width: 100%;
    height: 100%;
}

.grid-1 { width: 400rpx; height: 300rpx; }
.grid-2 { width: 320rpx; height: 240rpx; }
.grid-3 { width: 210rpx; height: 210rpx; }

/* ---- 视频封面 ---- */
.card-video {
    margin-bottom: 16rpx;
}

.video-cover {
    width: 400rpx;
    height: 240rpx;
    background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
    border-radius: 12rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.video-play-icon {
    font-size: 56rpx;
    color: white;
    opacity: 0.9;
}

.video-duration {
    position: absolute;
    bottom: 12rpx;
    right: 12rpx;
    background: rgba(0,0,0,0.55);
    backdrop-filter: blur(8rpx);
    color: white;
    font-size: 22rpx;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;
}

/* ---- 标签 ---- */
.card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 10rpx;
    margin-bottom: 16rpx;
}

.device-tag {
    display: inline-block;
    padding: 4rpx 16rpx;
    border-radius: 8rpx;
    font-size: 22rpx;
    background: var(--color-primary-bg);
    color: var(--color-primary);
    font-weight: 500;
}

.location-tag {
    display: inline-block;
    padding: 4rpx 16rpx;
    border-radius: 8rpx;
    font-size: 22rpx;
    background: var(--color-info-bg);
    color: var(--color-info);
    font-weight: 500;
}

/* ---- 互动栏 ---- */
.card-actions {
    display: flex;
    border-top: 1rpx solid var(--color-divider);
    padding-top: 16rpx;
}

.action-item {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
    padding: 8rpx 0;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
}
.action-item:active {
    background: var(--color-bg-secondary);
}

.action-item.liked {
    color: #EF4444;
}
.action-item.favorited {
    color: #F59E0B;
}

.action-count {
    font-size: 24rpx;
}

/* ---- 空状态 ---- */
.empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 120rpx 0;
}
.empty-icon {
    font-size: 80rpx;
    margin-bottom: 24rpx;
    opacity: 0.5;
}
.empty-text {
    font-size: 28rpx;
    color: var(--color-text-tertiary);
    text-align: center;
    padding: 0 60rpx;
}

/* ---- 加载 ---- */
.loading-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60rpx 0;
    gap: 12rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}
.spinner-ring {
    width: 44rpx;
    height: 44rpx;
    border: 3rpx solid var(--color-border);
    border-top: 3rpx solid var(--color-primary);
    border-radius: 50%;
    animation: feed-spin 0.7s linear infinite;
}
@keyframes feed-spin { to { transform: rotate(360deg); } }

.loading-more-spin {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8rpx;
    padding: 20rpx 0;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}
.mini-spinner {
    width: 28rpx;
    height: 28rpx;
    border: 2rpx solid var(--color-border);
    border-top: 2rpx solid var(--color-primary);
    border-radius: 50%;
    animation: feed-spin 0.7s linear infinite;
}
.loading {
    text-align: center;
    padding: 40rpx 0;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}

.load-more { padding: 20rpx 0; text-align: center; }
.load-more-btn {
    padding: 20rpx;
    font-size: 28rpx;
    color: var(--color-primary);
    font-weight: 500;
}
.no-more {
    padding: 20rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}

/* ---- 悬浮发布按钮 ---- */
.fab-btn {
    position: fixed;
    right: 40rpx;
    bottom: 140rpx;
    width: 104rpx;
    height: 104rpx;
    border-radius: 50%;
    background: var(--color-primary-gradient);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8rpx 28rpx rgba(108, 92, 231, 0.4);
    z-index: 100;
    transition: all var(--transition-fast);
}
.fab-btn:active {
    transform: scale(0.9);
    box-shadow: 0 4rpx 16rpx rgba(108, 92, 231, 0.25);
}

.fab-icon {
    font-size: 44rpx;
}
</style>
