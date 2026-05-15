<template>
  <view class="container">
    
    <view class="header">
          <view class="title-bar">
            <text class="title">今日听写</text>
            <view class="account-info" v-if="isLoggedIn">
              <text class="progress-text">学习者: <text class="highlight">{{ currentChildId }}</text></text>
              <text class="switch-btn" @click="handleLogout">[切换]</text>
            </view>
          </view>
          <view class="progress-track" v-if="isLoggedIn">
            <view class="progress-fill" :style="{ width: dailyProgressPercent + '%' }"></view>
          </view>
          <view class="progress-text-bottom" v-if="isLoggedIn">
            <text class="daily-text">今日任务: <text class="daily-num">{{ dailyCount }}</text> / {{ dailyLimit }}</text>
            <text class="total-text">已彻底掌握: {{ learnedCount }} / {{ totalCount }}</text>
          </view>
	</view>

    <view v-if="!isLoggedIn" class="main-card unlogin-card">
      <text class="unlogin-icon">👋</text>
      <text class="unlogin-title">欢迎来到听写闯关</text>
      <text class="unlogin-desc">请先验证身份，开启今天的学习之旅吧！</text>
      <button class="btn-login-big" @click="showLoginDialog = true">输入专属 ID 登录</button>
    </view>

    <scroll-view 
          v-else 
          class="main-card" 
          scroll-y="true" 
          refresher-enabled="true" 
          :refresher-triggered="isRefreshing"
          @refresherrefresh="onRefresh"
        >
          <view class="card-inner">
            
            <view v-if="isFinished" class="finished-state">
              <text class="congrats">🎉 太棒了！</text>
              <text class="sub-text">当前年级的汉字已全部掌握！</text>
              <button class="btn-refresh" @click="fetchNextWord">再次复习</button>
            </view>
    
            <view v-else-if="currentWord" class="word-state">
              <view v-if="!showResult" class="dictating-box warm-card" hover-class="card-hover" @click="playAudio">
                <view class="pulse-ring"><text class="dictating-icon">🎧</text></view>
                <text class="dictating-text">点击播放语音</text>
                <text class="play-tip">当前拼音: {{ currentWord.pinyin }}</text>
                <!-- 找到这一段并替换 -->
                <view class="cheat-box" @click.stop="showCheat = !showCheat">
                  <text v-if="showCheat" class="cheat-char">{{ currentWord.character }}</text>
                  <text v-else class="cheat-tip">家长点击此处偷瞄答案</text>
                </view>
              </view>
    
              <view v-else class="result-box">
                <text class="result-char">{{ currentWord.character }}</text>
                <text class="result-hint">“ {{ currentWord.tts_hint }} ”</text>
                <view class="common-words-card">
                  <text class="words-title">📚 拓展词组：</text>
                  <view class="words-tags">
                    <text class="word-tag" v-for="(word, index) in currentWord.common_words.split(',')" :key="index">{{ word }}</text>
                  </view>
                </view>
              </view>
            </view>
    
            <view v-else class="loading-state">
              <text>努力抽取中...</text>
            </view>
    
          </view>
        </scroll-view>

    <view class="action-area" v-if="isLoggedIn && currentWord && !isFinished">
      <block v-if="!showResult">
        <button class="btn btn-wrong" @click="handleJudge(false)">没写出 ❌</button>
        <button class="btn btn-correct" @click="handleJudge(true)">写对了 ✅</button>
      </block>
      <block v-else>
        <button class="btn btn-next" @click="goToNext">继续下一个 ➔</button>
      </block>
    </view>

    <view class="dialog-overlay" v-if="showLoginDialog">
      <view class="dialog-card">
        <text class="dialog-title">账号登录</text>
        <text class="dialog-desc">家里有多个宝贝？输入不同的 ID 即可隔离进度。</text>
        <input 
          class="dialog-input" 
          v-model="tempInputId" 
          placeholder="请输入孩子ID" 
          focus
        />
        <view class="dialog-actions">
          <button class="dialog-btn cancel" @click="showLoginDialog = false">取消</button>
          <button class="dialog-btn confirm" @click="confirmLogin">开始学习</button>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad,onShow, onUnload } from '@dcloudio/uni-app' // 确保导入了 onShow

import { getNextWordApi, submitReviewApi, HOST } from '@/utils/api.js'
const currentGradeInPage = ref(0) // ⭐️ 记录当前页面加载数据时用的年级
const currentWord = ref(null)
const isFinished = ref(false)
const showCheat = ref(false)
const showResult = ref(false) 
const isRefreshing = ref(false)
// ⭐️ 新增：进度数据
const learnedCount = ref(0)
const totalCount = ref(100) // 后期由后端返回真实总数
// ⭐️ 新增：今日进度与额度上限
const dailyCount = ref(0)
const dailyLimit = ref(50) // 与后端 DAILY_LIMIT 保持一致

// ⭐️ 进度条改为计算今日的百分比
const dailyProgressPercent = computed(() => {
  if (dailyLimit.value === 0) return 0
  return Math.min(100, Math.round((dailyCount.value / dailyLimit.value) * 100))
})
// ⭐️ 新增：多账号登录状态
const isLoggedIn = ref(false)
const currentChildId = ref('')
const showLoginDialog = ref(false)
const tempInputId = ref('admin') // 弹窗里默认输入 admin

const progressPercent = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.min(100, Math.round((learnedCount.value / totalCount.value) * 100))
})

const audioCtx = uni.createInnerAudioContext()

const onRefresh = async () => {
  if (!isLoggedIn.value) return
  
  // 1. 开启顶部的 loading 菊花图
  isRefreshing.value = true 
  
  // 2. 重新抽词 (会自动带上最新的年级设置)
  await fetchNextWord()
  
  // 3. 停顿极短的时间后，收回下拉动画 (让体验更丝滑)
  setTimeout(() => {
    isRefreshing.value = false 
    uni.showToast({ title: '已刷新', icon: 'none', duration: 1000 })
  }, 300)
}



const checkLoginStatus = () => {
  const savedId = uni.getStorageSync('child_id')
  const savedGrade = uni.getStorageSync('user_max_grade') || 6 // 获取最新的年级设置

  if (savedId) {
    currentChildId.value = savedId
    isLoggedIn.value = true
    
    // ⭐️ 核心修复：如果当前年级设置和页面记录的不一致，或者屏幕没字，就重新抓取
    if (currentGradeInPage.value !== savedGrade || (!currentWord.value && !isFinished.value)) {
      currentGradeInPage.value = savedGrade // 更新页面年级记录
      fetchNextWord() 
    }
  } else {
    isLoggedIn.value = false
    currentWord.value = null
    currentGradeInPage.value = 0
  }
}


// 2. 确认登录
const confirmLogin = () => {
  const id = tempInputId.value.trim()
  if (!id) {
    uni.showToast({ title: 'ID 不能为空', icon: 'none' })
    return
  }
  // 保存到本地
  uni.setStorageSync('child_id', id)
  currentChildId.value = id
  isLoggedIn.value = true
  showLoginDialog.value = false
  
  // 登录成功，立刻抽词
  fetchNextWord()
}

// 3. 切换账号 (退出登录)
const handleLogout = () => {
  uni.showModal({
    title: '切换账号',
    content: '确定要退出当前账号吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('child_id')
        isLoggedIn.value = false
        currentWord.value = null // 清空屏幕上的字
      }
    }
  })
}

// 1. 获取下一个字
const fetchNextWord = async () => {
  if (!isLoggedIn.value) return 

  isFinished.value = false
  currentWord.value = null
  showResult.value = false
  showCheat.value = false
  
  try {
    const userMaxGrade = uni.getStorageSync('user_max_grade') || 6
	currentGradeInPage.value = userMaxGrade
    const data = await getNextWordApi(userMaxGrade)
    
    // ⭐️ 统一抽取赋值逻辑
    if (data.learned_count !== undefined) learnedCount.value = data.learned_count
    if (data.total_count !== undefined) totalCount.value = data.total_count
    if (data.daily_count !== undefined) dailyCount.value = data.daily_count

    if (data.status === 'success') {
      currentWord.value = data.word
      playAudio()
    } else if (data.status === 'finished') {
      isFinished.value = true
    }
  } catch (error) {
    console.error("获取生字失败", error)
    if (!uni.getStorageSync('child_id')) {
      isLoggedIn.value = false
    }
  }
}

// 2. 播放语音
const playAudio = () => {
  if (currentWord.value) {
    // ⭐️ 完美拼接：使用全局配置的 HOST
    audioCtx.src = `${HOST}/static/audio/${currentWord.value.character}.mp3`
    audioCtx.seek(0)
    audioCtx.play()
  }
}

// 3. 妈妈判卷
// 3. 妈妈判卷
const handleJudge = async (isCorrect) => {
  try {
    // 1. 发给后端更新核心权重 (带上 user_id)
    await submitReviewApi(currentWord.value.id, isCorrect)
    
    // 2. ⭐️ 记录到本地缓存，供“我的”页面画图使用
    saveStatsToLocal(isCorrect)

    showResult.value = true
  } catch (error) {
    console.error("提交结果失败", error)
  }
}

// ⭐️ 核心防脱发逻辑：本地轻量级统计
const saveStatsToLocal = (isCorrect) => {
  // 获取今天的日期字符串，例如 "2023-10-27"
  const today = new Date().toISOString().split('T')[0] 
  
  // 从本地缓存拿历史数据，没有的话就是一个空对象
  let stats = uni.getStorageSync('study_stats') || {}
  
  // 如果今天还没听写过，初始化一下
  if (!stats[today]) {
    stats[today] = { correct: 0, wrong: 0 }
  }
  
  // 累加
  if (isCorrect) {
    stats[today].correct++
  } else {
    stats[today].wrong++
  }
  
  // 塞回本地缓存
  uni.setStorageSync('study_stats', stats)
}

// 4. 进入下一个字
const goToNext = () => {
  fetchNextWord()
}

// onLoad(() => { checkLoginStatus() })
onShow(() => { 
  checkLoginStatus() 
})
onUnload(() => { audioCtx.destroy() })
</script>

<style scoped>
/* 核心布局保持不变 */
.container { height: 100%; box-sizing: border-box; overflow: hidden; background-color: #f5f7fa; display: flex; flex-direction: column; padding: 40rpx; }

/* 头部修改 */
.header { margin-bottom: 30rpx; margin-top: 10rpx; flex-shrink: 0; }
.title-bar { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 15rpx; }
.title { font-size: 44rpx; font-weight: bold; color: #333; }
.account-info { display: flex; align-items: center; }
.progress-text { font-size: 26rpx; color: #999; }
.highlight { color: #409eff; font-weight: bold; margin: 0 4rpx; }
.switch-btn { font-size: 24rpx; color: #409eff; margin-left: 10rpx; }
.progress-track { height: 12rpx; background-color: #e4e7ed; border-radius: 6rpx; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #66b1ff, #409eff); border-radius: 6rpx; transition: width 0.3s ease; }
.progress-text-bottom { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-top: 12rpx; 
}
.daily-text { font-size: 26rpx; color: #666; font-weight: bold; }
.daily-num { color: #409eff; font-size: 32rpx; margin: 0 4rpx; }
.total-text { font-size: 22rpx; color: #ccc; }
/* 未登录空状态卡片 */
.unlogin-card { 
  display: flex;         /* ⭐️ 核心修复：找回丢失的 flex 布局 */
  flex-direction: column; 
  align-items: center;   /* ⭐️ 确保子元素水平居中 */
  justify-content: center; 
  background: #fff; 
  text-align: center; 
  height: 100%;          /* 确保整体内容在白色卡片里垂直居中 */
}
.unlogin-icon { font-size: 120rpx; margin-bottom: 30rpx; display: block; }
.unlogin-title { font-size: 40rpx; font-weight: bold; color: #333; margin-bottom: 20rpx; display: block; /* 强制独占一行 */ }
.unlogin-desc { font-size: 28rpx; color: #999; margin-bottom: 60rpx; padding: 0 40rpx; display: block; /* 强制独占一行 */ line-height: 1.5; }
.btn-login-big { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 50rpx; width: 80%; height: 90rpx; line-height: 90rpx; font-size: 32rpx; font-weight: bold; box-shadow: 0 10rpx 20rpx rgba(118, 75, 162, 0.2); }
.main-card { 
  flex: 1; 
  background-color: #ffffff; 
  border-radius: 40rpx; 
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.04); 
  margin-bottom: 40rpx; 
  width: 100%; 
  box-sizing: border-box; 
  overflow: hidden; /* 这里改用 hidden，因为滚动交给了 scroll-view 自己 */
}

/* ⭐️ 新增的内层容器，接管排版任务 */
.card-inner {
  min-height: 100%; /* 确保内容少时也能撑满整个卡片高度 */
  display: flex; 
  flex-direction: column;
  justify-content: center; 
  align-items: center; 
  padding: 40rpx; 
  box-sizing: border-box;
}
.word-state { width: 100%; display: flex; flex-direction: column; align-items: center; }

/* ⭐️ 暖色系拟物播放卡片 */
.warm-card {
  background: linear-gradient(135deg, #fffcf5 0%, #fff2d9 100%); /* 淡淡的暖黄 */
  border: 2rpx solid #ffe6a8; /* 增加一点边界感 */
  border-radius: 30rpx;
  padding: 60rpx 40rpx;
  box-shadow: 0 16rpx 40rpx rgba(255, 165, 0, 0.1); /* 橙色软阴影 */
  transition: all 0.2s ease;
}
.card-hover { transform: scale(0.98); box-shadow: 0 8rpx 20rpx rgba(255, 165, 0, 0.05); } /* 按下时的动效 */

.dictating-box { display: flex; flex-direction: column; align-items: center; width: 100%; }
.dictating-icon { font-size: 100rpx; margin-bottom: 20rpx; text-shadow: 0 4rpx 10rpx rgba(255,165,0,0.2); }
.dictating-text { font-size: 40rpx; font-weight: bold; color: #d08c28; margin-bottom: 10rpx; }
.play-tip { font-size: 32rpx; color: #e6a23c; font-weight: bold; margin-bottom: 60rpx; }

/* 偷瞄功能 */
.cheat-box { height: 120rpx; display: flex; justify-content: center; align-items: center; }
.cheat-char { font-size: 80rpx; font-weight: bold; color: #f56c6c; text-shadow: 0 4rpx 10rpx rgba(245,108,108,0.2); }
.cheat-tip { font-size: 26rpx; color: #d08c28; opacity: 0.6; border-bottom: 1px dashed #d08c28; padding-bottom: 4rpx; }

/* 其他样式保持之前的... */
.result-box { display: flex; flex-direction: column; align-items: center; width: 100%; animation: fadeIn 0.4s ease; }
.result-char { font-size: 160rpx; font-weight: bold; color: #333; margin-bottom: 20rpx; line-height: 1; }
.result-hint { font-size: 40rpx; color: #666; margin-bottom: 50rpx; text-align: center; }
.common-words-card { background-color: #f8fbff; width: 100%; border-radius: 20rpx; padding: 30rpx; box-sizing: border-box; }
.words-title { font-size: 28rpx; color: #999; display: block; margin-bottom: 20rpx; }
.words-tags { display: flex; flex-wrap: wrap; gap: 20rpx; justify-content: center; }
.word-tag { background-color: #e1f0ff; color: #0277bd; padding: 10rpx 30rpx; border-radius: 30rpx; font-size: 32rpx; font-weight: bold; }
.action-area { display: flex; justify-content: space-between; padding-bottom: 20rpx; flex-shrink: 0;}
.btn { height: 110rpx; border-radius: 55rpx; font-size: 36rpx; font-weight: bold; display: flex; justify-content: center; align-items: center; color: white; border: none; box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.1); }
.btn-wrong { width: 45%; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #d81b60; }
.btn-correct { width: 45%; background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); color: #0277bd; }
.btn-next { width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); letter-spacing: 4rpx; }

/* ================= 登录弹窗样式 ================= */
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 999; animation: fadeIn 0.2s ease; }
.dialog-card { width: 80%; background-color: white; border-radius: 30rpx; padding: 50rpx 40rpx; display: flex; flex-direction: column; align-items: center; box-shadow: 0 20rpx 50rpx rgba(0,0,0,0.15); }
.dialog-title { font-size: 36rpx; font-weight: bold; color: #333; margin-bottom: 10rpx; }
.dialog-desc { font-size: 26rpx; color: #999; text-align: center; margin-bottom: 40rpx; }
.dialog-input { width: 100%; height: 90rpx; background-color: #f5f7fa; border-radius: 20rpx; padding: 0 30rpx; font-size: 32rpx; color: #333; margin-bottom: 50rpx; box-sizing: border-box; text-align: center; border: 2rpx solid transparent; transition: all 0.2s; }
.dialog-input:focus { border-color: #409eff; background-color: #e1f0ff; }
.dialog-actions { display: flex; justify-content: space-between; width: 100%; }
.dialog-btn { width: 45%; height: 80rpx; line-height: 80rpx; border-radius: 40rpx; font-size: 30rpx; font-weight: bold; }
.dialog-btn.cancel { background-color: #f5f7fa; color: #666; }
.dialog-btn.confirm { background-color: #409eff; color: white; box-shadow: 0 8rpx 20rpx rgba(64,158,255,0.3); }


@keyframes fadeIn { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
</style>