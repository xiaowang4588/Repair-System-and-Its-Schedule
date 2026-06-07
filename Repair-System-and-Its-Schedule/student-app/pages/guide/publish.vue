<template>
    <view class="page">
        <view class="container">
            <!-- 标签提示 -->
            <view class="card hint-card">
                <text class="hint-title">💡 在正文中用 #标签 来分类，例如：#投影仪 #行者楼</text>
            </view>

            <!-- 文字输入 -->
            <view class="card content-card">
                <textarea class="content-input" v-model="form.content"
                          placeholder="分享你的维修经验和避坑心得..."
                          :show-confirm-bar="false"
                          @input="onContentInput" />

                <!-- 已识别的标签预览 -->
                <view class="parsed-tags" v-if="parsedDeviceTags.length > 0 || parsedLocationTag">
                    <text class="parsed-label">已识别：</text>
                    <view class="parsed-tag device" v-for="t in parsedDeviceTags" :key="'d'+t">#{{ t }}</view>
                    <view class="parsed-tag location" v-if="parsedLocationTag">#{{ parsedLocationTag }}</view>
                </view>
            </view>

            <!-- 图片上传 -->
            <view class="card">
                <view class="media-title">📷 图片</view>
                <view class="image-list">
                    <view class="image-item" v-for="(img, index) in form.images" :key="index">
                        <image :src="getImageUrl(img)" mode="aspectFill" class="preview-image" />
                        <view class="image-delete" @click="deleteImage(index)">×</view>
                    </view>
                    <view class="image-add" @click="chooseImage" v-if="form.images.length < 9">
                        <text class="add-icon">📷</text>
                        <text class="add-text">{{ form.images.length }}/9</text>
                    </view>
                </view>
            </view>

            <!-- 视频上传 -->
            <view class="card">
                <view class="media-title">🎬 视频</view>
                <view v-if="!form.video_url" class="video-add" @click="chooseVideo">
                    <text class="video-add-icon">🎬</text>
                    <text class="video-add-text">选择视频（≤60秒）</text>
                </view>
                <view v-else class="video-selected">
                    <view class="video-info">
                        <text class="video-name">已选择视频</text>
                        <text class="video-dur" v-if="form.video_duration">
                            {{ formatDuration(form.video_duration) }}
                        </text>
                    </view>
                    <text class="video-remove" @click="removeVideo">✕</text>
                </view>
            </view>

            <!-- 发布按钮 -->
            <button class="btn-publish" :disabled="publishing" @click="submitPost">
                {{ publishing ? '发布中...' : '✨ 发布' }}
            </button>
        </view>
    </view>
</template>

<script>
import config, { getImageUrl as resolveImageUrl } from '../../config/index.js'
import { createGuide, uploadGuideVideo, getGuideAvailableTags } from '../../api/index.js'

export default {
    data() {
        return {
            form: {
                content: '',
                images: [],
                video_url: '',
                video_duration: 0,
                device_tags: [],
                location_tag: '',
            },
            deviceTagOptions: [],
            locationTagOptions: [],
            publishing: false,
        }
    },
    computed: {
        parsedDeviceTags() {
            return this.form.device_tags
        },
        parsedLocationTag() {
            return this.form.location_tag
        },
    },
    onLoad() {
        this.loadAvailableTags()
    },
    methods: {
        // 从后端动态加载所有可用标签（与项目数据联动）
        async loadAvailableTags() {
            try {
                const res = await getGuideAvailableTags()
                if (res && res.status === 'ok' && res.data) {
                    this.deviceTagOptions = res.data.device_tags || []
                    this.locationTagOptions = res.data.location_tags || []
                }
            } catch (e) {
                console.error('加载标签失败:', e)
            }
        },

        // 内容变化时解析标签
        onContentInput() {
            this.parseTags()
        },

        // 从文字中解析 #标签
        parseTags() {
            const text = this.form.content
            const regex = /#([一-龥a-zA-Z0-9]+)/g
            const allTags = []
            let match
            while ((match = regex.exec(text)) !== null) {
                allTags.push(match[1])
            }

            // 用后端返回的动态列表来匹配
            const deviceTags = []
            let locationTag = ''
            for (const tag of allTags) {
                if (this.deviceTagOptions.includes(tag)) {
                    if (!deviceTags.includes(tag)) deviceTags.push(tag)
                } else if (this.locationTagOptions.includes(tag)) {
                    if (!locationTag) locationTag = tag
                }
            }

            this.form.device_tags = deviceTags
            this.form.location_tag = locationTag
        },

        // 选择图片
        chooseImage() {
            uni.chooseImage({
                count: 9 - this.form.images.length,
                sizeType: ['compressed'],
                sourceType: ['album', 'camera'],
                success: async (res) => {
                    for (const tempPath of res.tempFilePaths) {
                        try {
                            const fileInfo = await new Promise((resolve, reject) => {
                                uni.getFileInfo({ filePath: tempPath, success: resolve, fail: reject })
                            })
                            if (fileInfo.size > 10 * 1024 * 1024) {
                                uni.showToast({ title: '图片不能超过10MB', icon: 'none' })
                                continue
                            }
                            const uploadRes = await this.uploadImage(tempPath)
                            if (uploadRes && uploadRes.status === 'ok') {
                                this.form.images.push(uploadRes.data.url)
                            } else {
                                uni.showToast({ title: uploadRes?.message || '上传失败', icon: 'none' })
                            }
                        } catch (e) {
                            uni.showToast({ title: '图片上传失败', icon: 'none' })
                        }
                    }
                }
            })
        },

        // 上传图片
        uploadImage(filePath) {
            return new Promise((resolve, reject) => {
                uni.uploadFile({
                    url: config.API_BASE + '/api/repair/upload-image',
                    filePath: filePath,
                    name: 'file',
                    success: (res) => {
                        try { resolve(JSON.parse(res.data)) } catch (e) { reject(e) }
                    },
                    fail: reject
                })
            })
        },

        // 删除图片
        deleteImage(index) {
            this.form.images.splice(index, 1)
        },

        // 选择视频
        chooseVideo() {
            uni.chooseVideo({
                sourceType: ['album', 'camera'],
                maxDuration: 60,
                compressed: true,
                success: async (res) => {
                    const tempPath = res.tempFilePath
                    if (!tempPath) {
                        uni.showToast({ title: '获取视频文件失败', icon: 'none' })
                        return
                    }
                    const size = res.size || 0
                    if (size > 50 * 1024 * 1024) {
                        uni.showToast({ title: '视频不能超过50MB', icon: 'none' })
                        return
                    }
                    uni.showLoading({ title: '上传视频中...' })
                    try {
                        const uploadRes = await uploadGuideVideo(tempPath)
                        if (uploadRes && uploadRes.status === 'ok') {
                            this.form.video_url = uploadRes.data.url
                            this.form.video_duration = uploadRes.data.duration || 0
                            uni.showToast({ title: '上传成功', icon: 'success' })
                        } else {
                            uni.showToast({ title: uploadRes?.message || '上传失败', icon: 'none' })
                        }
                    } catch (e) {
                        console.error('视频上传异常:', e)
                        uni.showToast({ title: '视频上传失败，请重试', icon: 'none' })
                    } finally {
                        uni.hideLoading()
                    }
                },
                fail: (err) => {
                    console.error('选择视频失败:', err)
                }
            })
        },

        // 移除视频
        removeVideo() {
            this.form.video_url = ''
            this.form.video_duration = 0
        },

        // 发布
        async submitPost() {
            if (!this.form.content || !this.form.content.trim()) {
                uni.showToast({ title: '请输入内容', icon: 'none' })
                return
            }
            // 先解析一次标签
            this.parseTags()

            this.publishing = true
            try {
                const res = await createGuide(this.form)
                if (res && res.status === 'ok') {
                    uni.showToast({ title: '发布成功', icon: 'success' })
                    setTimeout(() => uni.navigateBack(), 1500)
                } else {
                    uni.showToast({ title: res?.message || '发布失败', icon: 'none' })
                }
            } catch (e) {
                uni.showToast({ title: '发布失败', icon: 'none' })
            } finally {
                this.publishing = false
            }
        },

        getImageUrl(img) { return resolveImageUrl(img) },

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
    background: #F5F7FA;
}

.container {
    padding: 24rpx;
    padding-bottom: 140rpx;
}

.card {
    background: white;
    border-radius: 16rpx;
    padding: 28rpx;
    margin-bottom: 20rpx;
    box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}

/* 文字输入 */
.content-card {
    min-height: 300rpx;
}

.content-input {
    width: 100%;
    height: 260rpx;
    font-size: 30rpx;
    color: #333;
    line-height: 1.6;
}

/* 标签提示卡片 */
.hint-card {
    padding: 20rpx 28rpx;
    background: #FFFBEB;
    border: 1rpx solid #FDE68A;
}

.hint-title {
    font-size: 24rpx;
    color: #92400E;
}

/* 已识别标签预览 */
.parsed-tags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10rpx;
    margin-top: 16rpx;
    padding-top: 16rpx;
    border-top: 1rpx solid #f0f0f0;
}

.parsed-label {
    font-size: 22rpx;
    color: #999;
}

.parsed-tag {
    display: inline-block;
    padding: 4rpx 14rpx;
    border-radius: 8rpx;
    font-size: 22rpx;
}

.parsed-tag.device {
    background: #EEF2FF;
    color: #4F7CFF;
    border: 1rpx solid #d4deff;
}

.parsed-tag.location {
    background: #F0F9FF;
    color: #1890ff;
    border: 1rpx solid #bae0ff;
}

/* 图片上传 */
.media-title {
    font-size: 26rpx;
    font-weight: 600;
    color: #333;
    margin-bottom: 16rpx;
}

.image-list {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
}

.image-item {
    position: relative;
    width: 160rpx;
    height: 160rpx;
}

.preview-image {
    width: 100%;
    height: 100%;
    border-radius: 8rpx;
}

.image-delete {
    position: absolute;
    top: -12rpx;
    right: -12rpx;
    width: 40rpx;
    height: 40rpx;
    background: #ff4d4f;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24rpx;
}

.image-add {
    width: 160rpx;
    height: 160rpx;
    border: 2rpx dashed #d9d9d9;
    border-radius: 8rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8rpx;
}

.image-add:active {
    border-color: #4F7CFF;
    background: #f8f9ff;
}

.add-icon { font-size: 40rpx; }
.add-text { font-size: 22rpx; color: #999; }

/* 视频上传 */
.video-add {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16rpx;
    height: 100rpx;
    border: 2rpx dashed #d9d9d9;
    border-radius: 12rpx;
}

.video-add:active {
    border-color: #4F7CFF;
    background: #f8f9ff;
}

.video-add-icon { font-size: 40rpx; }
.video-add-text { font-size: 26rpx; color: #666; }

.video-selected {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20rpx;
    background: #f8f9ff;
    border-radius: 12rpx;
    border: 1rpx solid #d4deff;
}

.video-info {
    display: flex;
    align-items: center;
    gap: 16rpx;
}

.video-name {
    font-size: 28rpx;
    color: #333;
}

.video-dur {
    font-size: 24rpx;
    color: #4F7CFF;
    background: #EEF2FF;
    padding: 4rpx 12rpx;
    border-radius: 6rpx;
}

.video-remove {
    font-size: 32rpx;
    color: #999;
    padding: 8rpx;
}

/* 发布按钮 */
.btn-publish {
    position: fixed;
    bottom: 24rpx;
    left: 24rpx;
    right: 24rpx;
    height: 88rpx;
    line-height: 88rpx;
    background: #4F7CFF;
    color: white;
    border: none;
    border-radius: 12rpx;
    font-size: 32rpx;
    font-weight: 500;
    z-index: 100;
}

.btn-publish:active { opacity: 0.8; }
.btn-publish[disabled] { opacity: 0.5; }
</style>
