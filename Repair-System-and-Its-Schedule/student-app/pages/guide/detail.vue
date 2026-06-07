<template>
    <view class="page">
        <view class="container" v-if="post">
            <!-- 动态内容 -->
            <view class="guide-card">
                <view class="card-header">
                    <view class="avatar">{{ post.student_name ? post.student_name[0] : '?' }}</view>
                    <view class="user-info">
                        <text class="user-name">{{ post.student_name }}</text>
                        <text class="post-time">{{ formatTime(post.created_at) }}</text>
                    </view>
                </view>

                <view class="card-content">
                    <text class="content-text">{{ post.content }}</text>
                </view>

                <!-- 图片 -->
                <view class="card-images" v-if="post.images && post.images.length > 0">
                    <view v-for="(img, idx) in post.images" :key="idx"
                          class="grid-image-wrap" :class="'grid-' + Math.min(post.images.length, 3)"
                          @click="previewImage(post.images, idx)">
                        <image :src="getImageUrl(img)" mode="aspectFill"
                               class="grid-image" @error="onImageError($event, img)" />
                    </view>
                </view>

                <!-- 视频 -->
                <view class="card-video" v-if="post.video_url">
                    <video :src="getImageUrl(post.video_url)" class="video-player"
                           controls :show-fullscreen-btn="true"
                           @error="onVideoError" />
                    <text class="video-duration" v-if="post.video_duration">
                        时长 {{ formatDuration(post.video_duration) }}
                    </text>
                </view>

                <!-- 标签 -->
                <view class="card-tags">
                    <view class="device-tag" v-for="tag in post.device_tags" :key="tag">
                        #{{ tag }}
                    </view>
                    <view class="location-tag" v-if="post.location_tag">
                        #{{ post.location_tag }}
                    </view>
                </view>

                <!-- 互动栏 -->
                <view class="card-actions">
                    <view class="action-item" :class="{ liked: post.is_liked }"
                          @click="toggleLike">
                        <text>{{ post.is_liked ? '❤️' : '👍' }}</text>
                        <text class="action-count">{{ post.like_count || '' }}</text>
                    </view>
                    <view class="action-item">
                        <text>💬</text>
                        <text class="action-count">{{ post.comment_count || '' }}</text>
                    </view>
                    <view class="action-item" :class="{ favorited: post.is_favorited }"
                          @click="toggleFavorite">
                        <text>{{ post.is_favorited ? '⭐' : '☆' }}</text>
                        <text class="action-count">{{ post.favorite_count || '' }}</text>
                    </view>
                </view>
            </view>

            <!-- 评论区 -->
            <view class="comment-section">
                <view class="section-title">评论 ({{ post.comment_count || 0 }})</view>

                <!-- 评论区域加载中 -->
                <view v-if="loadingComments" class="loading-comments">
                    <view class="cmt-spinner"></view>
                    <text>加载评论中...</text>
                </view>
                <view v-else-if="comments.length === 0" class="empty-comment">
                    <text>暂无评论，快来抢沙发吧～</text>
                </view>

                <view class="comment-item" v-for="c in comments" :key="c.id">
                    <view class="comment-header">
                        <view class="comment-avatar">{{ c.student_name ? c.student_name[0] : '?' }}</view>
                        <view class="comment-info">
                            <text class="comment-name">{{ c.student_name }}</text>
                            <text class="comment-time">{{ formatTime(c.created_at) }}</text>
                        </view>
                        <text class="comment-delete" v-if="isMyComment(c)"
                              @click="deleteComment(c.id)">删除</text>
                    </view>
                    <view class="comment-body">
                        <text v-if="c.reply_to_name" class="reply-to">回复 {{ c.reply_to_name }}：</text>
                        <text>{{ c.content }}</text>
                    </view>
                    <view class="comment-reply-btn" @click="startReply(c)">回复</view>
                </view>

                <!-- 加载更多评论 -->
                <view class="load-more" v-if="comments.length > 0">
                    <view v-if="loadingMoreComments" class="loading"><text>加载中...</text></view>
                    <view v-else-if="hasMoreComments" @click="loadMoreComments" class="load-more-btn">
                        <text>加载更多评论</text>
                    </view>
                    <view v-else class="no-more"><text>没有更多评论了</text></view>
                </view>
            </view>
        </view>

        <!-- 加载中 -->
        <view class="loading" v-if="loading"><text>加载中...</text></view>

        <!-- 底部评论输入栏 -->
        <view class="comment-input-bar">
            <view class="reply-hint" v-if="replyTo">
                <text>回复 {{ replyTo.student_name }}：</text>
                <text class="reply-cancel" @click="cancelReply">✕</text>
            </view>
            <view class="input-row">
                <input class="comment-input" v-model="commentContent"
                       :placeholder="replyTo ? '回复 ' + replyTo.student_name + '...' : '说点什么...'"
                       :confirm-type="'send'" @confirm="submitComment" />
                <view class="send-btn" :class="{ active: commentContent.trim() }"
                     @click="submitComment">发送</view>
            </view>
        </view>
    </view>
</template>

<script>
import { getImageUrl as resolveImageUrl } from '../../config/index.js'
import { getGuideDetail, toggleGuideLike, toggleGuideFavorite,
         getGuideComments, createGuideComment, deleteGuideComment } from '../../api/index.js'

export default {
    data() {
        return {
            postId: 0,
            post: null,
            comments: [],
            loading: false,
            loadingComments: false,
            loadingMoreComments: false,
            commentPage: 1,
            hasMoreComments: true,
            commentContent: '',
            replyTo: null,
            currentStudentId: '',
        }
    },
    onLoad(options) {
        this.postId = parseInt(options.id)
        this.currentStudentId = uni.getStorageSync('student_id') || ''
        this.loadDetail()
        this.loadComments()
    },
    methods: {
        // 加载动态详情
        async loadDetail() {
            this.loading = true
            try {
                const res = await getGuideDetail(this.postId)
                if (res && res.status === 'ok') {
                    this.post = res.data
                }
            } catch (e) {
                console.error('加载详情失败:', e)
            } finally {
                this.loading = false
            }
        },

        // 加载评论
        async loadComments() {
            this.loadingComments = true
            this.commentPage = 1
            try {
                const res = await getGuideComments({ post_id: this.postId, page: 1, page_size: 50 })
                if (res && res.status === 'ok') {
                    this.comments = res.records || []
                    this.hasMoreComments = this.commentPage < (res.total_pages || 1)
                }
            } catch (e) {
                console.error('加载评论失败:', e)
            } finally {
                this.loadingComments = false
            }
        },

        // 加载更多评论
        async loadMoreComments() {
            if (this.loadingMoreComments || !this.hasMoreComments) return
            this.loadingMoreComments = true
            this.commentPage++
            try {
                const res = await getGuideComments({
                    post_id: this.postId,
                    page: this.commentPage,
                    page_size: 50
                })
                if (res && res.status === 'ok') {
                    this.comments = [...this.comments, ...(res.records || [])]
                    this.hasMoreComments = this.commentPage < (res.total_pages || 1)
                }
            } catch (e) {
                this.commentPage--
            } finally {
                this.loadingMoreComments = false
            }
        },

        // 点赞
        async toggleLike() {
            try {
                const res = await toggleGuideLike(this.postId)
                if (res && res.status === 'ok') {
                    this.post.is_liked = res.data.is_liked
                    this.post.like_count = res.data.like_count
                }
            } catch (e) {}
        },

        // 收藏
        async toggleFavorite() {
            try {
                const res = await toggleGuideFavorite(this.postId)
                if (res && res.status === 'ok') {
                    this.post.is_favorited = res.data.is_favorited
                    this.post.favorite_count = res.data.favorite_count
                }
            } catch (e) {}
        },

        // 开始回复
        startReply(comment) {
            this.replyTo = comment
        },

        // 取消回复
        cancelReply() {
            this.replyTo = null
        },

        // 发表评论
        async submitComment() {
            const content = this.commentContent.trim()
            if (!content) {
                uni.showToast({ title: '请输入评论内容', icon: 'none' })
                return
            }
            if (content.length > 200) {
                uni.showToast({ title: '评论最多200字', icon: 'none' })
                return
            }

            try {
                const data = {
                    post_id: this.postId,
                    content: content,
                }
                if (this.replyTo) {
                    data.reply_to_id = this.replyTo.id
                }

                const res = await createGuideComment(data)
                if (res && res.status === 'ok') {
                    this.commentContent = ''
                    this.replyTo = null
                    // 刷新评论和评论数
                    this.loadComments()
                    if (this.post) {
                        this.post.comment_count = (this.post.comment_count || 0) + 1
                    }
                    uni.showToast({ title: '评论成功', icon: 'success' })
                } else {
                    uni.showToast({ title: res?.message || '评论失败', icon: 'none' })
                }
            } catch (e) {
                uni.showToast({ title: '评论失败', icon: 'none' })
            }
        },

        // 删除评论
        deleteComment(id) {
            uni.showModal({
                title: '确认删除',
                content: '确定删除这条评论吗？',
                success: async (res) => {
                    if (res.confirm) {
                        try {
                            const resp = await deleteGuideComment(id)
                            if (resp && resp.status === 'ok') {
                                uni.showToast({ title: '删除成功', icon: 'success' })
                                this.loadComments()
                                if (this.post) {
                                    this.post.comment_count = Math.max(0, (this.post.comment_count || 0) - 1)
                                }
                            }
                        } catch (e) {
                            uni.showToast({ title: '删除失败', icon: 'none' })
                        }
                    }
                }
            })
        },

        // 判断是否是自己的评论
        isMyComment(c) {
            return c.student_id === this.currentStudentId
        },

        // 图片预览
        previewImage(images, index) {
            const urls = images.map(img => this.getImageUrl(img))
            uni.previewImage({ urls, current: urls[index] })
        },

        getImageUrl(img) { return resolveImageUrl(img) },

        onImageError(e, img) {
            console.error('图片加载失败:', this.getImageUrl(img), e)
        },

        onVideoError(e) {
            console.error('视频加载失败:', e)
            uni.showToast({ title: '视频加载失败', icon: 'none' })
        },

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
    padding-bottom: 140rpx;
}

.container {
    padding: 24rpx;
}

/* ---- 动态卡片 ---- */
.guide-card {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 28rpx;
    margin-bottom: 20rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
}

.card-header {
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;
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

.user-info { flex: 1; }
.user-name { font-size: 30rpx; font-weight: 600; color: var(--color-text); display: block; }
.post-time { font-size: 22rpx; color: var(--color-text-tertiary); display: block; margin-top: 4rpx; }

.card-content { margin-bottom: 16rpx; }
.content-text { font-size: 30rpx; color: var(--color-text); line-height: 1.75; }

.card-images { display: flex; flex-wrap: wrap; gap: 8rpx; margin-bottom: 16rpx; }
.grid-image-wrap { border-radius: 10rpx; overflow: hidden; background: var(--color-bg); }
.grid-image { width: 100%; height: 100%; }
.grid-1 { width: 580rpx; height: 400rpx; }
.grid-2 { width: 285rpx; height: 214rpx; }
.grid-3 { width: 186rpx; height: 186rpx; }

.card-video { margin-bottom: 16rpx; }
.video-player { width: 100%; height: 400rpx; border-radius: 12rpx; }
.video-duration { font-size: 22rpx; color: var(--color-text-tertiary); margin-top: 8rpx; display: block; }

.card-tags { display: flex; flex-wrap: wrap; gap: 10rpx; margin-bottom: 16rpx; }
.device-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; background: var(--color-primary-bg); color: var(--color-primary); font-weight: 500; }
.location-tag { padding: 4rpx 16rpx; border-radius: 8rpx; font-size: 22rpx; background: var(--color-info-bg); color: var(--color-info); font-weight: 500; }

.card-actions { display: flex; border-top: 1rpx solid var(--color-divider); padding-top: 16rpx; }
.action-item { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6rpx; font-size: 28rpx; color: var(--color-text-tertiary); padding: 10rpx 0; border-radius: var(--radius-sm); transition: all var(--transition-fast); }
.action-item:active { background: var(--color-bg-secondary); }
.action-item.liked { color: #EF4444; }
.action-item.favorited { color: #F59E0B; }
.action-count { font-size: 26rpx; }

/* ---- 评论区 ---- */
.comment-section {
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    padding: 28rpx;
    box-shadow: var(--shadow-sm);
    border: 1rpx solid var(--color-border-light);
}

.section-title {
    font-size: 30rpx;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 20rpx;
    padding-bottom: 16rpx;
    border-bottom: 1rpx solid var(--color-divider);
}

/* 评论加载 */
.loading-comments {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40rpx 0;
    gap: 12rpx;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}
.cmt-spinner {
    width: 40rpx;
    height: 40rpx;
    border: 3rpx solid var(--color-border);
    border-top: 3rpx solid var(--color-primary);
    border-radius: 50%;
    animation: cmt-spin 0.7s linear infinite;
}
@keyframes cmt-spin { to { transform: rotate(360deg); } }

.empty-comment {
    text-align: center;
    padding: 40rpx 0;
    font-size: 26rpx;
    color: var(--color-text-tertiary);
}

.comment-item {
    padding: 20rpx 0;
    border-bottom: 1rpx solid var(--color-divider);
    transition: background var(--transition-fast);
}
.comment-item:last-child { border-bottom: none; }

.comment-header {
    display: flex;
    align-items: center;
    margin-bottom: 12rpx;
}

.comment-avatar {
    width: 56rpx;
    height: 56rpx;
    border-radius: 50%;
    background: var(--color-primary-bg);
    color: var(--color-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24rpx;
    font-weight: 600;
    margin-right: 16rpx;
    flex-shrink: 0;
}

.comment-info { flex: 1; }
.comment-name { font-size: 26rpx; font-weight: 600; color: var(--color-text); display: block; }
.comment-time { font-size: 20rpx; color: var(--color-text-tertiary); display: block; margin-top: 2rpx; }

.comment-delete {
    font-size: 24rpx;
    color: var(--color-danger);
    padding: 8rpx;
    font-weight: 500;
}

.comment-body {
    font-size: 28rpx;
    color: var(--color-text);
    line-height: 1.55;
    padding-left: 72rpx;
}

.reply-to { color: var(--color-primary); font-weight: 500; }

.comment-reply-btn {
    font-size: 24rpx;
    color: var(--color-text-tertiary);
    padding-left: 72rpx;
    margin-top: 8rpx;
    font-weight: 500;
}

.load-more { padding: 20rpx 0; text-align: center; }
.load-more-btn { padding: 20rpx; font-size: 28rpx; color: var(--color-primary); font-weight: 500; }
.no-more { padding: 20rpx; font-size: 26rpx; color: var(--color-text-tertiary); }
.loading { text-align: center; padding: 40rpx 0; font-size: 26rpx; color: var(--color-text-tertiary); }

/* ---- 底部评论输入栏 ---- */
.comment-input-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--color-surface);
    border-top: 1rpx solid var(--color-border-light);
    padding: 16rpx 24rpx;
    padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
    z-index: 100;
    box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.reply-hint {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 24rpx;
    color: var(--color-primary);
    margin-bottom: 12rpx;
    background: var(--color-primary-bg);
    padding: 8rpx 16rpx;
    border-radius: var(--radius-xs);
}

.reply-cancel {
    font-size: 28rpx;
    color: var(--color-text-tertiary);
    padding: 8rpx;
}

.input-row {
    display: flex;
    align-items: center;
    gap: 16rpx;
}

.comment-input {
    flex: 1;
    height: 72rpx;
    background: var(--color-bg);
    border-radius: 36rpx;
    padding: 0 28rpx;
    font-size: 28rpx;
    border: 2rpx solid transparent;
    transition: all var(--transition-fast);
}
.comment-input:focus {
    border-color: var(--color-primary-light);
    background: var(--color-surface);
}

.send-btn {
    width: 120rpx;
    height: 72rpx;
    line-height: 72rpx;
    text-align: center;
    background: var(--color-border);
    color: white;
    border-radius: 36rpx;
    font-size: 28rpx;
    font-weight: 600;
    transition: all var(--transition-fast);
}
.send-btn.active {
    background: var(--color-primary-gradient);
    box-shadow: 0 4rpx 16rpx rgba(108, 92, 231, 0.3);
}
</style>
