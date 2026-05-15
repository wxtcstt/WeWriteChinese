// ⭐️ 提取最根部的服务器地址，统一暴露出去
export const HOST = 'http://127.0.0.1:9000' 

// 接口的 Base URL 拼接上版本号
const API_BASE_URL = `${HOST}/api/v1`

/**
 * 核心请求封装
 */
const request = (url, method, data = {}) => {
  return new Promise((resolve, reject) => {
    // ⭐️ 核心：每次请求前，去本地缓存拿一下孩子 ID
    const childId = uni.getStorageSync('child_id') || ''

    uni.request({
      url: API_BASE_URL + url,
      method: method,
      data: data,
      header: {
        'X-User-Id': childId // ⭐️ 塞入 HTTP 请求头，发给后端
      },
      success: (res) => {
        // 拦截一下 401 未授权
        if (res.statusCode === 401) {
          uni.showToast({ title: '登录已过期，请重新输入 ID', icon: 'none' })
          uni.removeStorageSync('child_id') // 清除失效的 ID
          reject('Unauthorized')
          return
        }
        resolve(res.data)
      },
      fail: (err) => {
        uni.showToast({ title: '网络请求失败，请检查后端', icon: 'none' })
        reject(err)
      }
    })
  })
}

// --- 导出具体的业务接口 ---
export const getNextWordApi = (maxGrade) => {
  return request(`/review/next_word?max_grade=${maxGrade}`, 'GET')
}

export const submitReviewApi = (wordId, isCorrect) => {
  return request('/review/submit', 'POST', {
    word_id: wordId,
    is_correct: isCorrect
  })
}



// ⭐️ 加上 search 参数
export const getWords = async (skip = 0, limit = 100, search = '') => {
  let url = `${API_BASE_URL}/words/?skip=${skip}&limit=${limit}`;
  if (search) {
    url += `&search=${encodeURIComponent(search)}`;
  }
  const res = await uni.request({
    url: url,
    method: 'GET'
  });
  return res.data;
};

// ⭐️ 确保接收完整的 wordData 字典
export const addWord = async (wordData) => {
  const res = await uni.request({
    url: `${API_BASE_URL}/words/`,
    method: 'POST',
    data: wordData
  });
  if(res.statusCode !== 200) throw new Error(res.data.detail || '添加失败');
  return res.data;
};

export const deleteWord = async (wordId) => {
  const res = await uni.request({
    url: `${API_BASE_URL}/words/${wordId}`,
    method: 'DELETE'
  });
  if(res.statusCode !== 200) throw new Error(res.data.detail || '删除失败');
  return res.data;
};

// ⭐️ 新增修改生字 API
export const updateWord = async (wordId, wordData) => {
  const res = await uni.request({
    url: `${API_BASE_URL}/words/${wordId}`,
    method: 'PUT',
    data: wordData
  });
  if(res.statusCode !== 200) throw new Error(res.data.detail || '更新失败');
  return res.data;
};