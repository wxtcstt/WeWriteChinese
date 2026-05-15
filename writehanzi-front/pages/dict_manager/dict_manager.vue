<template>
  <view class="container">
    <!-- 顶部导航 -->
    <view class="custom-header">
      <view class="back-btn" @click="goBack">
        <text class="back-arrow">{{ '<' }}</text>
        <text class="back-text">返回</text>
      </view>
      <text class="page-title">字库管理</text>
      <view class="header-placeholder"></view>
    </view>

    <!-- 1. 表单卡片 (根据状态变化标题) -->
    <view class="card">
      <view class="card-title">{{ editingId ? '✏️ 编辑汉字' : '📝 录入新汉字' }}</view>
      <view class="form-grid">
        <view class="form-item">
          <text class="label">汉字*</text>
          <input class="input" v-model="newWord.character" placeholder="如: 专" maxlength="1" />
        </view>
        <view class="form-item">
          <text class="label">拼音*</text>
          <input class="input" v-model="newWord.pinyin" placeholder="如: zhuān" />
        </view>
        <view class="form-item">
          <text class="label">年级</text>
          <input class="input" type="number" v-model="newWord.grade" placeholder="1-6" />
        </view>
        <view class="form-item">
          <text class="label">单元</text>
          <input class="input" type="number" v-model="newWord.unit" placeholder="选填" />
        </view>
      </view>
      
      <view class="form-item form-item-full">
        <text class="label">语音提示词 (选填)</text>
        <input class="input" v-model="newWord.tts_hint" placeholder="如: 专心的专" />
      </view>
      <view class="form-item form-item-full">
        <text class="label">常用词组 (选填，用逗号分隔)</text>
        <input class="input" v-model="newWord.common_words" placeholder="如: 专心,专家" />
      </view>
      <view class="form-item form-item-full">
        <text class="label">图片路径 (选填，高级用法)</text>
        <input class="input" v-model="newWord.image_path" placeholder="/static/images/words/专.png" />
      </view>

      <!-- ⭐️ 操作按钮区 -->
      <view class="form-actions">
        <button class="btn-submit" @click="handleSubmit" :disabled="!newWord.character || !newWord.pinyin">
          {{ editingId ? '确认修改' : '确认录入' }}
        </button>
        <button class="btn-cancel" v-if="editingId" @click="cancelEdit">取消编辑</button>
      </view>
    </view>

    <!-- 2. 搜索与列表卡片 -->
    <view class="card list-card">
      <view class="search-box">
        <text class="search-icon">🔍</text>
        <input 
          class="search-input" 
          v-model="searchQuery" 
          placeholder="输入汉字搜索..." 
          @confirm="onSearch"
          confirm-type="search"
        />
        <button class="btn-search" @click="onSearch">搜索</button>
      </view>

      <scroll-view scroll-y class="word-list" @scrolltolower="loadMoreWords">
        <view v-if="wordList.length === 0" class="empty-state">暂无数据</view>
        <view class="word-item" v-for="word in wordList" :key="word.id">
          <view class="word-info">
            <text class="w-char">{{ word.character }}</text>
            <view class="w-details">
              <text class="w-py">{{ word.pinyin }}</text>
              <text class="w-gr">{{ word.grade }}年级</text>
              <text class="w-hint" v-if="word.tts_hint">{{ word.tts_hint }}</text>
            </view>
          </view>
          <!-- ⭐️ 新增操作栏 -->
          <view class="word-actions">
            <button class="btn-edit" @click="handleEditClick(word)">编辑</button>
            <button class="btn-delete" @click="handleDeleteWord(word)">删除</button>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'

import { getWords, addWord, deleteWord, updateWord } from '@/utils/api.js'

const goBack = () => {
  uni.switchTab({
    url: '/pages/user/user'
  })
}

// 表单与状态
const getEmptyWord = () => ({ character: '', pinyin: '', grade: 1, unit: 1, tts_hint: '', common_words: '', image_path: '' })
const newWord = ref(getEmptyWord())
const editingId = ref(null) // ⭐️ 核心：记录当前正在编辑的词 ID，为空则代表新增

// 列表与搜索状态
const wordList = ref([])
const searchQuery = ref('')
let currentSkip = 0
const LIMIT = 50

onMounted(() => {
  fetchWords()
})

const onSearch = () => {
  wordList.value = []
  currentSkip = 0
  fetchWords()
}

const fetchWords = async () => {
  try {
    const data = await getWords(currentSkip, LIMIT, searchQuery.value.trim())
    if (data && data.length > 0) {
      wordList.value = [...wordList.value, ...data]
      currentSkip += LIMIT
    }
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

const loadMoreWords = () => fetchWords()

// ⭐️ 点击列表中的“编辑”按钮
const handleEditClick = (word) => {
  editingId.value = word.id
  // 将原数据拷贝到表单中
  newWord.value = { ...word }
  // 贴心地滚回顶部，方便用户修改
  uni.pageScrollTo({ scrollTop: 0, duration: 300 })
}

// ⭐️ 取消编辑，重置为新增模式
const cancelEdit = () => {
  editingId.value = null
  newWord.value = getEmptyWord()
}

// ⭐️ 合并提交逻辑：根据 editingId 判断是更新还是新增
const handleSubmit = async () => {
  if (!newWord.value.character || !newWord.value.pinyin) return
  
  try {
    uni.showLoading({ title: '提交中...' })
    
    // 解析并清洗数字
    const payload = { ...newWord.value }
    payload.grade = parseInt(payload.grade) || 5
    payload.unit = parseInt(payload.unit) || 1

    if (editingId.value) {
      // ===== 更新模式 =====
      const updatedData = await updateWord(editingId.value, payload)
      uni.showToast({ title: '修改成功', icon: 'success' })
      // 直接在列表中替换对应的数据，不需要刷新整个列表
      const index = wordList.value.findIndex(w => w.id === editingId.value)
      if (index !== -1) wordList.value[index] = updatedData
    } else {
      // ===== 新增模式 =====
      const data = await addWord(payload)
      uni.showToast({ title: '录入成功', icon: 'success' })
      // 把新字塞到列表最前面
      wordList.value.unshift(data)
    }

    // 成功后自动重置状态
    cancelEdit()
    uni.hideLoading()

  } catch (error) {
    uni.hideLoading()
    uni.showToast({ title: error.message || '操作失败', icon: 'none' })
  }
}

const handleDeleteWord = (word) => {
  uni.showModal({
    title: '危险操作',
    content: `确定要从字库中永久删除【${word.character}】吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          uni.showLoading({ title: '删除中...' })
          await deleteWord(word.id)
          uni.hideLoading()
          uni.showToast({ title: '已删除' })
          wordList.value = wordList.value.filter(w => w.id !== word.id)
          
          // 如果用户正在编辑这个被删除的字，重置编辑状态
          if (editingId.value === word.id) cancelEdit()
          
        } catch (error) {
          uni.hideLoading()
          uni.showToast({ title: error.message || '删除失败', icon: 'none' })
        }
      }
    }
  })
}
</script>

<style scoped>
/* 大部分样式复用原来的，只修改/新增按钮布局 */
.container { min-height: 100vh; background-color: #f5f7fa; padding: 30rpx; box-sizing: border-box; display: flex; flex-direction: column;}
.custom-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30rpx; padding-top: 10rpx; }
.back-btn { display: flex; align-items: center; background-color: #fff; padding: 12rpx 24rpx 12rpx 16rpx; border-radius: 40rpx; box-shadow: 0 4rpx 15rpx rgba(0,0,0,0.03); }
.back-arrow { font-size: 32rpx; color: #333; font-weight: bold; margin-right: 8rpx; }
.back-text { font-size: 28rpx; color: #333; font-weight: bold; }
.page-title { font-size: 34rpx; font-weight: bold; color: #333; }
.header-placeholder { width: 120rpx; }

.card { background: #fff; border-radius: 30rpx; padding: 30rpx; margin-bottom: 30rpx; box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.03); }
.card-title { font-size: 32rpx; font-weight: bold; color: #333; margin-bottom: 30rpx; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20rpx; margin-bottom: 20rpx; }
.form-item { display: flex; flex-direction: column; }
.form-item-full { margin-bottom: 20rpx; }
.label { font-size: 24rpx; color: #666; margin-bottom: 8rpx; margin-left: 8rpx; }
.input { height: 80rpx; background: #f8f9fb; border-radius: 20rpx; padding: 0 24rpx; font-size: 28rpx; border: 2rpx solid transparent; transition: all 0.2s; }
.input:focus { background: #fff; border-color: #409eff; }

/* ⭐️ 表单按钮组 */
.form-actions { display: flex; gap: 20rpx; margin-top: 20rpx; }
.btn-submit { flex: 2; background: #409eff; color: #fff; height: 88rpx; line-height: 88rpx; border-radius: 44rpx; font-size: 32rpx; font-weight: bold; margin: 0; }
.btn-submit[disabled] { background: #a0cfff; }
.btn-cancel { flex: 1; background: #f5f7fa; color: #666; height: 88rpx; line-height: 88rpx; border-radius: 44rpx; font-size: 28rpx; font-weight: bold; margin: 0; }

.list-card { flex: 1; display: flex; flex-direction: column; overflow: hidden; padding-bottom: 0; margin-bottom: 0;}
.search-box { display: flex; align-items: center; background: #f8f9fb; border-radius: 40rpx; padding: 10rpx 10rpx 10rpx 30rpx; margin-bottom: 30rpx; }
.search-icon { font-size: 32rpx; color: #999; margin-right: 16rpx; }
.search-input { flex: 1; height: 60rpx; font-size: 28rpx; }
.btn-search { background: #333; color: #fff; height: 60rpx; line-height: 60rpx; border-radius: 30rpx; font-size: 26rpx; margin: 0; padding: 0 30rpx; }

.word-list { flex: 1; height: 0; }
.empty-state { text-align: center; padding: 100rpx 0; color: #999; font-size: 28rpx; }
.word-item { display: flex; justify-content: space-between; align-items: center; padding: 30rpx 0; border-bottom: 2rpx dashed #eee; }
.word-info { display: flex; align-items: center; }
.w-char { font-size: 48rpx; font-weight: bold; color: #333; margin-right: 20rpx; width: 60rpx; text-align: center;}
.w-details { display: flex; flex-direction: column; gap: 6rpx; }
.w-py { font-size: 28rpx; font-weight: bold; color: #409eff; }
.w-gr { font-size: 22rpx; color: #fff; background: #ff9800; padding: 2rpx 12rpx; border-radius: 10rpx; width: fit-content;}
.w-hint { font-size: 22rpx; color: #999; }

/* ⭐️ 列表卡片右侧的操作按钮区 */
.word-actions { display: flex; gap: 10rpx; flex-direction: column; align-items: flex-end;}
.btn-edit { background: #f0f7ff; color: #409eff; border-radius: 15rpx; font-size: 24rpx; margin: 0; padding: 0 20rpx; height: 50rpx; line-height: 50rpx; border: 2rpx solid transparent;}
.btn-edit:active { border-color: #409eff; }
.btn-delete { background: #fef0f0; color: #f56c6c; border-radius: 15rpx; font-size: 24rpx; margin: 0; padding: 0 20rpx; height: 50rpx; line-height: 50rpx; }
.btn-delete:active { opacity: 0.7; }
</style>