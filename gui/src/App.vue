<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 用户登录状态
const isLoggedIn = ref(false)
const userInfo = ref(null)
const isCheckingLogin = ref(true)
const isLoginFailed = ref(false)
const loginErrorMessage = ref('')
const loadingText = ref('正在连接本地程序接口...')

// 锁定标识，防止 checkLogin 并发触发
let isCheckLoginRunning = false

// 检查登录状态
const checkLogin = async () => {
  // 如果当前已经有一个验证流程在跑，则直接跳过
  if (isCheckLoginRunning) {
    console.log('[DEBUG] checkLogin 已在运行，跳过并发调用')
    return
  }
  
  isCheckLoginRunning = true
  console.log('[DEBUG] 进入 checkLogin')
  isCheckingLogin.value = true
  isLoginFailed.value = false
  loadingText.value = '正在验证登录状态...'
  
  try {
    // 1. 验证 pywebview API 是否就绪
    if (!window.pywebview || !window.pywebview.api) {
      console.error('[DEBUG] pywebview.api 未定义')
      isLoginFailed.value = true
      loginErrorMessage.value = '本地程序接口未就绪，请尝试刷新页面'
      return
    }

    // 首先检查 URL 中的授权码参数，但不立即处理
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const isBackPath = window.location.pathname.includes('/back') || 
    window.location.pathname.includes('/back.html') || 
    urlParams.has('code')
    console.log('[DEBUG] isBackPath:', isBackPath)
    
    // 其次：检查数据库中是否有存储的 Token
    const tokenResult = await window.pywebview.api.get_casdoor_token()
    console.log('[DEBUG] 从 URL 获取到的 code:', code)
    if (tokenResult.success && tokenResult.token) {
      console.log('[DEBUG] 发现数据库 Token，验证其有效性')
      loadingText.value = '正在验证本地会话...'
      try {
        const result = await window.pywebview.api.verify_casdoor_token(tokenResult.token)
        if (result.success) {
          console.log('[DEBUG] 数据库 Token 验证成功')
          isLoggedIn.value = true
          userInfo.value = result.user
          isCheckingLogin.value = false
          
          // 重要：清理 URL 参数，避免下次打开软件时重复处理
          if (code) {
            window.history.replaceState({}, document.title, '/')
          }
          
          return
        } else {
          console.warn('[DEBUG] 数据库 Token 验证失效:', result.message)
          await window.pywebview.api.delete_casdoor_token()
        }
      } catch (error) {
        console.error('[DEBUG] verify_casdoor_token 异常:', error)
      }
    }

    // 只有在没有有效 Token 的情况下才处理授权码
    if (code && isBackPath && !isLoggedIn.value) {
      console.log('[DEBUG] 没有有效 Token，但有授权码，开始处理')
      loadingText.value = '正在换取身份凭证...'
      try {
        const result = await window.pywebview.api.get_user_by_code(code)
        if (result.success) {
          console.log('[DEBUG] 授权码验证成功')
          await window.pywebview.api.set_casdoor_token(result.token)
          isLoggedIn.value = true
          userInfo.value = result.user
          ElMessage.success('登录成功')
          
          // 前往应用界面：清理 URL 并跳转回首页，确保路由和资源加载正常
          if (window.location.pathname.includes('back')) {
            window.location.href = '/' 
          } else {
            window.history.replaceState({}, document.title, '/')
            isCheckingLogin.value = false
          }
          return
        } else {
          console.error('[DEBUG] 授权码验证失败:', result.message)
          ElMessage.error('登录凭证验证失败，请重新登录')
          // 清理无效 code
          window.history.replaceState({}, document.title, '/')
        }
      } catch (error) {
        console.error('[DEBUG] get_user_by_code 异常:', error)
        ElMessage.error('连接本地服务换取凭证失败')
      }
    } else if (code && isBackPath && isLoggedIn.value) {
      // 已有有效 Token，清理 URL 中的授权码，避免下次热重启时再次触发
      console.log('[DEBUG] 已有有效 Token，清理 URL 中的授权码')
      window.history.replaceState({}, document.title, '/')
    }

    // 最后：如果既没有有效 Token 也没有 code，说明真的没登录
    if (!isLoggedIn.value) {
      console.log('[DEBUG] 未登录且无有效凭证，准备跳转 Casdoor')
      loadingText.value = '正在跳转至登录页...'
      try {
        const url = await window.pywebview.api.get_casdoor_signin_url()
        if (url) {
          window.location.href = url
          return
        } else {
          isLoginFailed.value = true
          loginErrorMessage.value = '获取登录地址失败，请检查配置'
        }
      } catch (error) {
        console.error('[DEBUG] get_casdoor_signin_url 报错:', error)
        isLoginFailed.value = true
        loginErrorMessage.value = '无法连接认证服务器'
      }
    }
  } catch (e) {
    console.error('[DEBUG] checkLogin 全局异常:', e)
    isLoginFailed.value = true
    loginErrorMessage.value = '身份认证流程异常'
  } finally {
    isCheckingLogin.value = false
    isCheckLoginRunning = false // 解除锁定
  }
}

// 登录
const login = async () => {
  try {
    loadingText.value = '正在获取认证页面地址...'
    const url = await window.pywebview.api.get_casdoor_signin_url()
    if (url) {
      console.log('正在自动跳转至 Casdoor:', url)
      loadingText.value = '正在跳转至登录页面，请稍候...'
      window.location.href = url
    } else {
      ElMessage.error('获取登录地址失败，请检查配置')
      isLoginFailed.value = true
      loginErrorMessage.value = '获取登录地址失败'
    }
  } catch (error) {
    console.error('登录跳转失败:', error)
    ElMessage.error('跳转登录失败')
    isLoginFailed.value = true
    loginErrorMessage.value = '连接认证服务器异常'
  }
}

// 退出登录
const logout = async () => {
  try {
    loadingText.value = '正在注销会话...'
    // 1. 获取当前 Token 用于后续注销请求
    const tokenResult = await window.pywebview.api.get_casdoor_token()
    const currentToken = tokenResult.token
    
    // 2. 调用后端注销接口，清理后端 Token 状态
    await window.pywebview.api.logout()
    
    // 3. 清理前端状态（后端已经清理了数据库中的 Token）
    isLoggedIn.value = false
    userInfo.value = null
    ElMessage.success('已注销会话并退出')
    
    // 4. 获取 Casdoor 注销地址并跳转
    // 传入 currentToken 作为 id_token_hint，确保 Casdoor 能正确处理重定向
    loadingText.value = '正在同步注销认证服务器会话...'
    const signoutUrl = await window.pywebview.api.get_casdoor_signout_url(currentToken)
    if (signoutUrl) {
      console.log('[DEBUG] 跳转至 Casdoor 注销地址:', signoutUrl)
      window.location.href = signoutUrl
    } else {
      // 如果获取注销地址失败，尝试获取登录地址并跳转
      const loginUrl = await window.pywebview.api.get_casdoor_signin_url()
      if (loginUrl) {
        window.location.href = loginUrl
      }
    }
  } catch (error) {
    console.error('注销并跳转登录页失败:', error)
    // 即使出错也强制清理前端状态
    await window.pywebview.api.delete_casdoor_token()
    isLoggedIn.value = false
    userInfo.value = null
  }
}

// 处理用户下拉菜单命令
const handleUserCommand = (command) => {
  if (command === 'logout') {
    logout()
  }
}

// 统一的接口调用包装器，处理 401 错误
const callApi = async (method, ...args) => {
  if (!window.pywebview || !window.pywebview.api) {
    throw new Error('本地程序接口未就绪')
  }
  
  try {
    const result = await window.pywebview.api[method](...args)
    
    // 检查是否因为未登录或 Token 失效导致失败
    if (result && result.success === false && result.code === 401) {
      console.warn(`接口 ${method} 返回 401，准备重新登录:`, result.message)
      
      // 清理本地状态
      await window.pywebview.api.delete_casdoor_token()
      isLoggedIn.value = false
      userInfo.value = null
      
      // 如果不是正在检查登录的过程中，则触发重新登录流程
      if (!isCheckingLogin.value) {
        ElMessage.warning(result.message || '登录已过期，请重新登录')
        setTimeout(() => {
          checkLogin()
        }, 1000)
      }
      return result
    }
    
    return result
  } catch (error) {
    console.error(`调用接口 ${method} 异常:`, error)
    throw error
  }
}

// 当前激活的菜单
const activeMenu = ref('spider-control')

// 页面标题
const pageTitle = ref('爬虫控制')

// 搜索关键词
const searchKey = ref('')

// 筛选条件
const filterType = ref(-1)

// 筛选对话框可见性
const filterDialogVisible = ref(false)

// 筛选表单数据
const filterForm = ref({
  status: -1, // 导出状态：-1全部，0未导出，1已导出
  minPrice: null, // 最低价格
  maxPrice: null, // 最高价格
  minStar: 0, // 最低评分
  maxStar: 5, // 最高评分
  minCommentCount: null, // 最低评价数量
  maxCommentCount: null // 最高评价数量
})

// 配置表单数据
const configForm = ref({
  spiderName: '',
  crawlInterval: 10,
  maxConcurrency: 5,
  timeout: 60,
  useProxy: false,
  proxyAddress: '',
  retryCount: 3,
  savePath: '',
  browserPath: '', // 浏览器可执行文件路径
  browserUserDataPath: '' // 浏览器用户数据路径
})

// 爬虫状态
const spiderStatus = ref('idle') // idle: 空闲, running: 运行中, finished: 已完成
const spiderInfo = ref('')

// 爬虫配置
const spiderConfig = ref({
  baseUrl: '' // 类目网址或店铺网址
})

// 爬虫日志
const spiderLogs = ref([])

// 任务队列相关数据
const taskQueue = ref([])
const currentTask = ref(null)
const queueStatus = ref('idle')
const newTaskForm = ref({
  url: '',
  name: ''
})

// 批量添加任务对话框
const batchAddDialogVisible = ref(false)
const batchAddForm = ref({
  urlsText: ''
})

// 数据列表
const dataList = ref([])
// 数据总数量
const dataCount = ref(0)

// 菜单选项
const menuItems = [
  {
    index: 'spider-control',
    title: '爬虫控制',
    icon: 'el-icon-s-operation',
    description: '启动和管理爬虫任务'
  },
  {
    index: 'task-queue',
    title: '任务队列',
    icon: 'el-icon-s-order',
    description: '管理爬虫任务队列'
  },
  {
    index: 'data-query',
    title: '数据查询',
    icon: 'el-icon-s-data',
    description: '查询和展示爬取的数据'
  },
  {
    index: 'config-settings',
    title: '配置修改',
    icon: 'el-icon-setting',
    description: '修改爬虫配置参数'
  }
]

// 获取爬虫状态
const logScrollbar = ref(null)
const logLevelFilter = ref('all') // 日志级别过滤器

// 过滤后的日志列表
const filteredLogs = computed(() => {
  if (logLevelFilter.value === 'all') {
    return spiderLogs.value
  }
  return spiderLogs.value.filter(log => log.level === logLevelFilter.value)
})

const fetchSpiderStatus = async () => {
  try {
    const status = await callApi('get_spider_status')
    if (status && status.success !== false) {
      spiderStatus.value = status.status
      spiderInfo.value = status.info
    }
    
    // 获取日志
    const logs = await callApi('get_spider_logs')
    if (logs && Array.isArray(logs)) {
      spiderLogs.value = logs
    }
    
    // 获取任务队列状态
    const queueData = await callApi('get_task_queue')
    if (queueData && queueData.success !== false) {
      taskQueue.value = queueData.queue
      currentTask.value = queueData.current_task
      queueStatus.value = queueData.status
    }
    
    // 自动滚动到日志底部
    if (logScrollbar.value && logScrollbar.value.wrap) {
      // 使用 $nextTick 确保 DOM 更新后再滚动
      await nextTick()
      logScrollbar.value.wrap.scrollTop = logScrollbar.value.wrap.scrollHeight
    }
  } catch (error) {
    console.error('获取爬虫状态失败:', error)
  }
}

// 启动爬虫
const clearLogs = async () => {
  try {
    const result = await callApi('clear_logs')
    if (result && result.success !== false) {
      spiderLogs.value = []
      ElMessage.success('日志已清空')
    }
  } catch (error) {
    console.error('清空日志失败:', error)
    ElMessage.error('清空日志失败')
  }
}

const startSpider = async () => {
  // 验证输入的URL
  if (!spiderConfig.value.baseUrl) {
    ElMessage.error('请输入要爬取的类目网址或店铺网址')
    return
  }
  
  // 简单的URL格式验证
  if (!spiderConfig.value.baseUrl.startsWith('http://') && !spiderConfig.value.baseUrl.startsWith('https://')) {
    ElMessage.error('请输入有效的URL地址（以http://或https://开头）')
    return
  }
  
  try {
    const result = await callApi('start_spider', spiderConfig.value.baseUrl)
    if (result && result.success !== false) {
      ElMessage.success('爬虫启动成功')
      // 开始定期更新状态
      startStatusUpdate()
    }
  } catch (error) {
    console.error('启动爬虫失败:', error)
    ElMessage.error('启动爬虫失败')
  }
}

// 停止爬虫
const stopSpider = async () => {
  try {
    const result = await callApi('stop_spider')
    if (result && result.success !== false) {
      ElMessage.success('爬虫已停止')
      stopStatusUpdate()
      await fetchSpiderStatus()
    }
  } catch (error) {
    console.error('停止爬虫失败:', error)
    ElMessage.error('停止爬虫失败')
  }
}

// 状态更新定时器
let statusUpdateTimer = null

// 开始定期更新状态
const startStatusUpdate = () => {
  stopStatusUpdate() // 先停止之前的定时器
  statusUpdateTimer = setInterval(async () => {
    await fetchSpiderStatus()
  }, 1000) // 1秒更新一次
}

// 停止定期更新状态
const stopStatusUpdate = () => {
  if (statusUpdateTimer) {
    clearInterval(statusUpdateTimer)
    statusUpdateTimer = null
  }
}

// 任务队列相关方法
const addTaskToQueue = async () => {
  if (!newTaskForm.value.url) {
    ElMessage.error('请输入要爬取的类目网址或店铺网址')
    return
  }
  
  // 简单的URL格式验证
  if (!newTaskForm.value.url.startsWith('http://') && !newTaskForm.value.url.startsWith('https://')) {
    ElMessage.error('请输入有效的URL地址（以http://或https://开头）')
    return
  }
  
  try {
    const result = await callApi('add_task_to_queue', newTaskForm.value.url, newTaskForm.value.name)
    if (result && result.success) {
      ElMessage.success('任务已添加到队列')
      newTaskForm.value.url = ''
      newTaskForm.value.name = ''
      await fetchSpiderStatus()
    } else if (result && result.success === false) {
      ElMessage.error(result.message || '添加任务失败')
    }
  } catch (error) {
    console.error('添加任务失败:', error)
    ElMessage.error('添加任务失败')
  }
}

const removeTaskFromQueue = async (taskId) => {
  try {
    const result = await callApi('remove_task_from_queue', taskId)
    if (result && result.success) {
      ElMessage.success('任务已删除')
      await fetchSpiderStatus()
    } else if (result && result.success === false) {
      ElMessage.error(result.message || '删除任务失败')
    }
  } catch (error) {
    console.error('删除任务失败:', error)
    ElMessage.error('删除任务失败')
  }
}

const clearTaskQueue = async () => {
  try {
    await ElMessageBox.confirm('确定要清空队列中所有待执行的任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const result = await callApi('clear_task_queue')
    if (result && result.success) {
      ElMessage.success(`已清空 ${result.removed_count} 个待执行任务`)
      await fetchSpiderStatus()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空队列失败:', error)
      ElMessage.error('清空队列失败')
    }
  }
}

const startTaskQueue = async () => {
  try {
    const result = await callApi('start_task_queue')
    if (result && result.success) {
      ElMessage.success('任务队列已启动')
      startStatusUpdate()
      await fetchSpiderStatus()
    } else if (result && result.success === false) {
      ElMessage.error(result.message || '启动队列失败')
    }
  } catch (error) {
    console.error('启动队列失败:', error)
    ElMessage.error('启动队列失败')
  }
}

const stopTaskQueue = async () => {
  try {
    const result = await callApi('stop_task_queue')
    if (result && result.success) {
      ElMessage.success('任务队列已暂停')
      await fetchSpiderStatus()
    }
  } catch (error) {
    console.error('暂停队列失败:', error)
    ElMessage.error('暂停队列失败')
  }
}

// 获取任务状态的显示文本和类型
const getTaskStatusInfo = (status) => {
  const statusMap = {
    pending: { text: '待执行', type: 'info' },
    running: { text: '执行中', type: 'primary' },
    completed: { text: '已完成', type: 'success' },
    failed: { text: '失败', type: 'danger' }
  }
  return statusMap[status] || { text: '未知', type: 'info' }
}

// 打开批量添加对话框
const openBatchAddDialog = () => {
  batchAddForm.value.urlsText = ''
  batchAddDialogVisible.value = true
}

// 关闭批量添加对话框
const closeBatchAddDialog = () => {
  batchAddDialogVisible.value = false
}

// 批量添加任务
const addBatchTasks = async () => {
  if (!batchAddForm.value.urlsText.trim()) {
    ElMessage.error('请输入URL列表，每个URL占一行')
    return
  }
  
  try {
    const result = await callApi('add_batch_tasks_to_queue', batchAddForm.value.urlsText)
    if (result && result.success) {
      ElMessage.success(`批量添加成功，共添加 ${result.added_count} 个任务`)
      batchAddDialogVisible.value = false
      await fetchSpiderStatus()
    } else if (result && result.success === false) {
      ElMessage.error(result.message || '批量添加失败')
    }
  } catch (error) {
    console.error('批量添加任务失败:', error)
    ElMessage.error('批量添加失败')
  }
}

// 切换菜单
const handleMenuClick = async (index) => {
  activeMenu.value = index
  const menu = menuItems.find(item => item.index === index)
  pageTitle.value = menu ? menu.title : '未知页面'
  
  // 当切换到配置页面时，加载配置
  if (index === 'config-settings') {
    await loadConfig()
  }
  
  // 当切换到数据查询页面时，自动查询一次数据
  if (index === 'data-query') {
    await loadData()
  }
}

// 加载数据
const loadData = async () => {
  try {
    // 当选择"全部数据"时，不传递状态参数
    const status = filterType.value === -1 ? null : Number(filterType.value)
    const data = await callApi('search_data', null, 30, status)
    if (data && Array.isArray(data)) {
      dataList.value = data
    }
    // 获取数据总数量
    const countResult = await callApi('get_data_count', null, status)
    if (typeof countResult === 'number') {
      dataCount.value = countResult
      ElMessage.success(`加载完成，找到 ${countResult} 条数据`)
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  }
}

// 复制到剪贴板
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`已复制 ${text}`)
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 删除数据
const deleteData = async (row) => {
  try {
    const result = await callApi('storage_delete', row.sku)
    if (result && result.success !== false) {
      dataList.value = dataList.value.filter(item => item.sku !== row.sku)
      ElMessage.success(`成功删除数据 ${row.sku}`)
    }
  } catch (error) {
    console.error('删除数据失败:', error)
    ElMessage.error('删除数据失败')
  }
}

// 根据评分返回标签类型
const getStarType = (star) => {
  if (star >= 4.5) return 'success' // 4.5分及以上为绿色
  if (star >= 3.5) return 'warning' // 3.5-4.4分为黄色
  return 'danger' // 3.4分及以下为红色
}

// 删除当前筛选后的数据
const deleteSelectedData = async () => {
  try {
    // 显示确认提示
    await ElMessageBox.confirm('确定要删除当前筛选后的所有数据吗？此操作无法恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 构建筛选参数
    const filters = {
      status: filterForm.value.status === -1 ? null : Number(filterForm.value.status),
      minPrice: filterForm.value.minPrice,
      maxPrice: filterForm.value.maxPrice,
      minStar: filterForm.value.minStar,
      maxStar: filterForm.value.maxStar,
      minCommentCount: filterForm.value.minCommentCount,
      maxCommentCount: filterForm.value.maxCommentCount
    }
    
    // 调用后端API删除数据
    const result = await callApi('delete_filtered_data', filters)
    if (result && result.success) {
      // 删除成功后，重新加载数据
      await loadData()
      ElMessage.success(`成功删除 ${result.deletedCount} 条数据`)
    } else if (result && result.success === false && result.code !== 401) {
      ElMessage.error('删除数据失败')
    }
  } catch (error) {
    // 如果用户取消删除，不显示错误信息
    if (error !== 'cancel') {
      console.error('删除数据失败:', error)
      ElMessage.error('删除数据失败')
    }
  }
}

// 打开筛选对话框
const openFilterDialog = () => {
  filterDialogVisible.value = true
}

// 关闭筛选对话框
const handleFilterDialogClose = () => {
  filterDialogVisible.value = false
}

// 重置筛选表单
const resetFilterForm = () => {
  filterForm.value = {
    status: -1,
    minPrice: null,
    maxPrice: null,
    minStar: 0,
    maxStar: 5,
    minCommentCount: null,
    maxCommentCount: null
  }
}

// 应用筛选条件
const applyFilters = async () => {
  try {
    // 构建筛选参数
    const filters = {
      status: filterForm.value.status === -1 ? null : Number(filterForm.value.status),
      minPrice: filterForm.value.minPrice,
      maxPrice: filterForm.value.maxPrice,
      minStar: filterForm.value.minStar,
      maxStar: filterForm.value.maxStar,
      minCommentCount: filterForm.value.minCommentCount,
      maxCommentCount: filterForm.value.maxCommentCount
    }
    
    // 调用后端API获取筛选后的数据
    const data = await callApi('search_data', searchKey.value, 30, filters)
    if (data && Array.isArray(data)) {
      dataList.value = data
    }
    
    // 获取筛选后的数据总数量
    const countResult = await callApi('get_data_count', searchKey.value, filters)
    if (typeof countResult === 'number') {
      dataCount.value = countResult
      ElMessage.success(`筛选完成，找到 ${countResult} 条数据`)
    }
    
    // 关闭筛选对话框
    filterDialogVisible.value = false
  } catch (error) {
    console.error('筛选数据失败:', error)
    ElMessage.error('筛选数据失败')
  }
}

// 导出数据
const exportData = async () => {
  try {
    // 构建筛选参数
    const filters = {
      status: filterForm.value.status === -1 ? null : Number(filterForm.value.status),
      minPrice: filterForm.value.minPrice,
      maxPrice: filterForm.value.maxPrice,
      minStar: filterForm.value.minStar,
      maxStar: filterForm.value.maxStar,
      minCommentCount: filterForm.value.minCommentCount,
      maxCommentCount: filterForm.value.maxCommentCount
    }
    
    const result = await callApi('export_data', filters)
    if (result && result.success) {
      ElMessage.success(`数据导出成功！保存路径：${result.filePath}`)
      // 导出成功后刷新查询，以便用户可以看到状态已更新的数据
      await loadData()
    } else if (result && result.success === false && result.code !== 401) {
      ElMessage.error('数据导出失败')
    }
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出数据失败')
  }
}

// 搜索数据
const searchData = async () => {
  try {
    // 当选择"全部数据"时，不传递状态参数
    const status = filterType.value === -1 ? null : Number(filterType.value)
    const data = await callApi('search_data', searchKey.value, 30, status)
    if (data && Array.isArray(data)) {
      dataList.value = data
    }
    // 获取数据总数量
    const countResult = await callApi('get_data_count', searchKey.value, status)
    if (typeof countResult === 'number') {
      dataCount.value = countResult
      ElMessage.success(`搜索完成，找到 ${countResult} 条数据`)
    }
  } catch (error) {
    console.error('搜索数据失败:', error)
    ElMessage.error('搜索数据失败')
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    // 调用后端API保存配置
    await callApi('config_set', 'browserPath', configForm.value.browserPath)
    await callApi('config_set', 'browserUserDataPath', configForm.value.browserUserDataPath)
    await callApi('config_set', 'spiderName', configForm.value.spiderName)
    await callApi('config_set', 'crawlInterval', configForm.value.crawlInterval.toString())
    await callApi('config_set', 'maxConcurrency', configForm.value.maxConcurrency.toString())
    await callApi('config_set', 'timeout', configForm.value.timeout.toString())
    await callApi('config_set', 'useProxy', configForm.value.useProxy.toString())
    await callApi('config_set', 'proxyAddress', configForm.value.proxyAddress)
    await callApi('config_set', 'retryCount', configForm.value.retryCount.toString())
    await callApi('config_set', 'savePath', configForm.value.savePath)
    
    ElMessage.success('配置保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  }
}

// 重置默认配置
const resetConfig = () => {
  configForm.value = {
    spiderName: '',
    crawlInterval: 10,
    maxConcurrency: 5,
    timeout: 60,
    useProxy: false,
    proxyAddress: '',
    retryCount: 3,
    savePath: ''
  }
  ElMessage.info('配置已重置为默认值')
}

// 测试配置
const testConfig = async () => {
  ElMessage.info('正在尝试打开浏览器进行测试...')
  try {
    const result = await callApi('test_browser_config', configForm.value.browserPath, configForm.value.browserUserDataPath)
    if (result && result.success !== false) {
      ElMessage.success('浏览器已尝试启动')
    } else if (result && result.success === false && result.code !== 401) {
      ElMessage.error('浏览器启动失败，请检查路径是否正确')
    }
  } catch (error) {
    console.error('测试配置失败:', error)
    ElMessage.error('测试配置失败')
  }
}

// 加载配置
const loadConfig = async () => {
  try {
    // 调用后端API获取所有配置
    const config = await callApi('config_get_all')
    if (!config || config.success === false) return
    
    // 设置配置到前端
    if (config.browserPath) configForm.value.browserPath = config.browserPath
    if (config.browserUserDataPath) configForm.value.browserUserDataPath = config.browserUserDataPath
    if (config.spiderName) configForm.value.spiderName = config.spiderName
    if (config.crawlInterval) configForm.value.crawlInterval = parseInt(config.crawlInterval)
    if (config.maxConcurrency) configForm.value.maxConcurrency = parseInt(config.maxConcurrency)
    if (config.timeout) configForm.value.timeout = parseInt(config.timeout)
    if (config.useProxy) configForm.value.useProxy = config.useProxy === 'true'
    if (config.proxyAddress) configForm.value.proxyAddress = config.proxyAddress
    if (config.retryCount) configForm.value.retryCount = parseInt(config.retryCount)
    if (config.savePath) configForm.value.savePath = config.savePath
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败')
  }
}

// 页面加载时获取数据
onMounted(async () => {
  console.log('[DEBUG] App mounted, 路径:', window.location.pathname)
  
  let initialized = false
  const init = async () => {
    if (initialized) return
    initialized = true
    console.log('[DEBUG] 执行 init() 初始化逻辑...')
    await checkLogin()
    // 只有登录后才开始获取状态
    if (isLoggedIn.value) {
      await fetchSpiderStatus()
      await loadConfig()
    }
  }

  // 1. 立即检查
  if (window.pywebview && window.pywebview.api) {
    console.log('[DEBUG] pywebview 已就绪 (立即检查)')
    await init()
    return
  }

  // 2. 监听事件
  window.addEventListener('_pywebviewready', async () => {
    console.log('[DEBUG] 收到 _pywebviewready 事件')
    await init()
  })

  // 3. 轮询检查 (解决重定向后事件可能不触发的问题)
  const timer = setInterval(async () => {
    if (window.pywebview && window.pywebview.api) {
      console.log('[DEBUG] pywebview 已就绪 (轮询检查)')
      clearInterval(timer)
      await init()
    }
  }, 500)

  // 4. 安全保护：如果 10 秒后依然没初始化，强制显示错误并提供手动重试
  setTimeout(() => {
    if (!initialized) {
      console.error('[DEBUG] pywebview 初始化超时')
      clearInterval(timer)
      isCheckingLogin.value = false
      isLoginFailed.value = true
      loginErrorMessage.value = '本地程序接口连接超时，请尝试重启软件'
    }
  }, 10000)
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopStatusUpdate()
})
</script>

<template>
  <!-- 正在检查登录状态、跳转中或验证中 -->
  <div v-if="isCheckingLogin || !isLoggedIn" class="loading-overlay">
    <div class="loading-content">
      <el-icon class="is-loading" :size="50" color="#3b82f6"><el-icon-loading /></el-icon>
      <p>{{ loadingText }}</p>
      <!-- 如果验证失败，提供重试按钮 -->
      <div v-if="isLoginFailed" style="margin-top: 20px">
        <p style="color: #f56c6c; margin-bottom: 10px">{{ loginErrorMessage }}</p>
        <el-button type="primary" @click="checkLogin">重新尝试登录</el-button>
      </div>
    </div>
  </div>

  <div class="app-container" v-else>
    <!-- 左侧导航栏 -->
    <div class="sidebar">
      <div class="logo">
        <h2>OzonSpider</h2>
        <p class="subtitle">爬虫控制器</p>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="menu"
        router
        @select="handleMenuClick"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.index"
          :index="item.index"
        >
          <el-icon :class="item.icon"></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
      
      <div class="version-info">
        <p>版本: V1.3</p>
        <p>开发者: CJH</p>
      </div>
    </div>
    
    <!-- 右侧内容区域 -->
    <div class="main-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <h1>{{ pageTitle }}</h1>
        <div class="user-info-header">
          <el-dropdown @command="handleUserCommand">
            <div class="user-profile">
              <el-avatar :size="32" :src="userInfo?.avatar || ''" icon="el-icon-user" />
              <span class="username">{{ userInfo?.displayName || userInfo?.name || '用户' }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <!-- 页面内容 -->
      <div class="page-content">
        <!-- 爬虫控制页面 -->
        <div v-if="activeMenu === 'spider-control'" class="spider-control-page">
          <el-card class="control-card">
            <template #header>
              <div class="card-header">
                <span>爬虫任务控制</span>
                <el-tag
                  :type="spiderStatus === 'running' ? 'warning' : (spiderStatus === 'finished' ? 'success' : 'info')"
                >
                  {{ spiderStatus === 'running' ? '运行中' : (spiderStatus === 'finished' ? '已完成' : '待启动') }}
                </el-tag>
              </div>
            </template>
            
            <!-- 爬虫配置 -->
            <div class="spider-config">
              <el-form :model="spiderConfig" label-width="120px" size="small">
                <el-form-item label="爬取URL">
                  <el-input
                    v-model="spiderConfig.baseUrl"
                    placeholder="请输入类目网址或店铺网址"
                    clearable
                    :disabled="spiderStatus === 'running'"
                    style="width: 400px"
                  />
                </el-form-item>
              </el-form>
            </div>
            
            <!-- 爬虫信息 -->
            <div v-if="spiderInfo" class="spider-info">
              <el-alert
                :title="spiderInfo"
                :type="spiderStatus === 'running' ? 'warning' : (spiderStatus === 'finished' ? 'success' : 'info')"
                show-icon
              />
            </div>
            
            <div class="control-buttons">
              <el-button
                type="primary"
                size="large"
                @click="startSpider"
                :disabled="spiderStatus === 'running'"
              >
                <el-icon><el-icon-video-play /></el-icon>
                启动爬虫
              </el-button>
              <el-button
                type="danger"
                size="large"
                @click="stopSpider"
                :disabled="spiderStatus !== 'running'"
              >
                <el-icon><el-icon-video-pause /></el-icon>
                停止爬虫
              </el-button>
              <el-button
                type="warning"
                size="large"
                @click="fetchSpiderStatus"
              >
                <el-icon><el-icon-refresh /></el-icon>
                刷新状态
              </el-button>
            </div>
            
            <!-- 日志显示区域 -->
            <div class="log-area">
              <div class="log-header">
                <h3>爬虫运行日志</h3>
                <div class="log-controls">
                  <el-select 
                    v-model="logLevelFilter" 
                    size="small" 
                    style="width: 120px; margin-right: 10px;"
                  >
                    <el-option label="全部" value="all" />
                    <el-option label="信息" value="info" />
                    <el-option label="成功" value="success" />
                    <el-option label="警告" value="warning" />
                    <el-option label="错误" value="error" />
                  </el-select>
                  <el-button 
                    type="text" 
                    size="small" 
                    @click="clearLogs"
                    :disabled="spiderLogs.length === 0"
                  >
                    清空日志
                  </el-button>
                </div>
              </div>
              <el-scrollbar 
                ref="logScrollbar"
                wrap-class="scrollbar-wrap" 
                style="height: 300px;"
              >
                <div class="log-content">
                  <div 
                    v-for="(log, index) in filteredLogs" 
                    :key="index" 
                    class="log-item"
                    :class="`log-level-${log.level}`"
                  >
                    <span class="log-timestamp">{{ log.timestamp }}</span>
                    <span class="log-level">{{ log.level.toUpperCase() }}</span>
                    <span class="log-message">{{ log.message }}</span>
                  </div>
                  <div v-if="filteredLogs.length === 0" class="log-empty">
                    暂无匹配的日志
                  </div>
                </div>
              </el-scrollbar>
            </div>
            
          </el-card>
        </div>
        
        <!-- 任务队列页面 -->
        <div v-if="activeMenu === 'task-queue'" class="task-queue-page">
          <el-card class="queue-card">
            <template #header>
              <div class="card-header">
                <span>任务队列管理</span>
                <div>
                  <el-tag :type="queueStatus === 'running' ? 'success' : (queueStatus === 'paused' ? 'warning' : 'info')" style="margin-right: 10px;">
                    队列状态: {{ queueStatus === 'running' ? '运行中' : (queueStatus === 'paused' ? '已暂停' : '空闲') }}
                  </el-tag>
                  <el-tag type="primary">
                    队列长度: {{ taskQueue.length }}
                  </el-tag>
                </div>
              </div>
            </template>
            
            <!-- 添加任务表单 -->
            <div class="add-task-form">
              <h3>添加新任务</h3>
              <el-form :model="newTaskForm" inline>
                <el-form-item label="任务名称">
                  <el-input 
                    v-model="newTaskForm.name" 
                    placeholder="可选，任务别名" 
                    style="width: 200px"
                  />
                </el-form-item>
                <el-form-item label="爬取URL" required>
                  <el-input 
                    v-model="newTaskForm.url" 
                    placeholder="请输入类目网址或店铺网址" 
                    style="width: 500px"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="addTaskToQueue">
                    <el-icon><el-icon-plus /></el-icon>
                    添加到队列
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
            
            <!-- 队列控制按钮 -->
            <div class="queue-controls" style="margin: 20px 0;">
              <el-button 
                type="success" 
                @click="startTaskQueue"
                :disabled="queueStatus === 'running' || taskQueue.filter(t => t.status === 'pending').length === 0"
              >
                <el-icon><el-icon-video-play /></el-icon>
                启动队列
              </el-button>
              <el-button 
                type="warning" 
                @click="stopTaskQueue"
                :disabled="queueStatus !== 'running'"
              >
                <el-icon><el-icon-video-pause /></el-icon>
                暂停队列
              </el-button>
              <el-button 
                type="primary" 
                @click="openBatchAddDialog"
              >
                <el-icon><el-icon-document-add /></el-icon>
                批量添加
              </el-button>
              <el-button 
                type="danger" 
                @click="clearTaskQueue"
                :disabled="taskQueue.filter(t => t.status === 'pending').length === 0"
              >
                <el-icon><el-icon-delete /></el-icon>
                清空待执行任务
              </el-button>
              <el-button 
                type="info" 
                @click="fetchSpiderStatus"
              >
                <el-icon><el-icon-refresh /></el-icon>
                刷新队列
              </el-button>
            </div>
            
            <!-- 当前执行中的任务 -->
            <div class="current-task" v-if="currentTask">
              <h3>当前执行中的任务</h3>
              <el-alert
                :title="`正在执行: ${currentTask.name}`"
                :description="currentTask.url"
                type="warning"
                show-icon
              >
                <template #default>
                  <div style="margin-top: 10px;">
                    <span>开始时间: {{ currentTask.start_time }}</span>
                  </div>
                </template>
              </el-alert>
            </div>
            
            <!-- 任务队列列表 -->
            <div class="task-list">
              <h3>任务列表</h3>
              <el-table :data="taskQueue" style="width: 100%">
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="name" label="任务名称" min-width="150">
                  <template #default="scope">
                    <span>{{ scope.row.name || `任务 ${scope.row.id}` }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="url" label="URL" min-width="300" show-overflow-tooltip />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="getTaskStatusInfo(scope.row.status).type">
                      {{ getTaskStatusInfo(scope.row.status).text }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_time" label="创建时间" width="180" />
                <el-table-column prop="start_time" label="开始时间" width="180" />
                <el-table-column prop="end_time" label="结束时间" width="180" />
                <el-table-column label="操作" width="120">
                  <template #default="scope">
                    <el-button 
                      type="danger" 
                      size="small" 
                      @click="removeTaskFromQueue(scope.row.id)"
                      :disabled="scope.row.status === 'running'"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="empty-state" v-if="taskQueue.length === 0">
                 <el-empty description="暂无任务" />
               </div>
             </div>
          </el-card>
          
          <!-- 批量添加对话框 -->
          <el-dialog
            v-model="batchAddDialogVisible"
            title="批量添加任务"
            width="600px"
            :before-close="closeBatchAddDialog"
          >
            <div class="batch-add-content">
              <p class="dialog-tip">
                请输入多个URL，<strong>每个URL占一行</strong>，空行自动忽略。如果任何一行URL无效，全部任务都不会添加。任务名称留空自动生成。
              </p>
              <el-input
                v-model="batchAddForm.urlsText"
                type="textarea"
                :rows="12"
                placeholder="https://www.ozon.ru/seller/example-shop-12345/
https://www.ozon.ru/category/example-category-12345/"
              />
            </div>
            
            <template #footer>
              <span class="dialog-footer">
                <el-button @click="closeBatchAddDialog">取消</el-button>
                <el-button type="primary" @click="addBatchTasks">确认添加</el-button>
              </span>
            </template>
          </el-dialog>
        </div>
        
          <!-- 数据查询页面 -->
        <div v-if="activeMenu === 'data-query'" class="data-query-page">
          <el-card class="query-card">
            <template #header>
              <div class="card-header">
                <span>数据查询</span>
                <el-tag type="success">数据总量: {{ dataCount }}</el-tag>
              </div>
            </template>
            
            <div class="search-box">
              <el-input
                v-model="searchKey"
                placeholder="搜索产品SKU或名称"
                style="width: 300px"
                clearable
                @clear="loadData"
              >
                <template #append>
                  <el-button @click="searchData">搜索</el-button>
                </template>
              </el-input>
              
              <el-button type="info" style="margin-left: 10px" @click="openFilterDialog">
                <el-icon><el-icon-setting /></el-icon>
                筛选
              </el-button>
              
              <el-button type="primary" style="margin-left: 10px" @click="exportData">
                <el-icon><el-icon-download /></el-icon>
                导出数据
              </el-button>
              
              <el-button type="danger" style="margin-left: 10px" @click="deleteSelectedData">
                <el-icon><el-icon-delete /></el-icon>
                删除数据
              </el-button>
            </div>
            
            <!-- 筛选对话框 -->
            <el-dialog
              v-model="filterDialogVisible"
              title="筛选条件"
              width="500px"
              :before-close="handleFilterDialogClose"
            >
              <el-form :model="filterForm" label-width="100px">
                <el-form-item label="导出状态">
                  <el-select v-model="filterForm.status" placeholder="全部" style="width: 100%">
                    <el-option label="全部" :value="-1" />
                    <el-option label="已导出" :value="1" />
                    <el-option label="未导出" :value="0" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="价格范围">
                  <el-input-number
                    v-model="filterForm.minPrice"
                    placeholder="最低价格"
                    :min="0"
                    style="width: 100%"
                  />
                  <span style="padding: 0 10px">-</span>
                  <el-input-number
                    v-model="filterForm.maxPrice"
                    placeholder="最高价格"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
                
                <el-form-item label="评分范围">
                  <el-input-number
                    v-model="filterForm.minStar"
                    placeholder="最低评分"
                    :min="0"
                    :max="5"
                    :step="0.1"
                    style="width: 100%"
                  />
                  <span style="padding: 0 10px">-</span>
                  <el-input-number
                    v-model="filterForm.maxStar"
                    placeholder="最高评分"
                    :min="0"
                    :max="5"
                    :step="0.1"
                    style="width: 100%"
                  />
                </el-form-item>
                
                <el-form-item label="评价数量">
                  <el-input-number
                    v-model="filterForm.minCommentCount"
                    placeholder="最低评价数"
                    :min="0"
                    style="width: 100%"
                  />
                  <span style="padding: 0 10px">-</span>
                  <el-input-number
                    v-model="filterForm.maxCommentCount"
                    placeholder="最高评价数"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-form>
              
              <template #footer>
                <span class="dialog-footer">
                  <el-button @click="resetFilterForm">重置</el-button>
                  <el-button type="primary" @click="applyFilters">确定</el-button>
                </span>
              </template>
            </el-dialog>
            
            <div class="data-list">
              <el-table :data="dataList" style="width: 100%">
                <el-table-column prop="sku" label="SKU" width="200">
                  <template #default="scope">
                    <span class="selectable-text" @click="copyToClipboard(scope.row.sku)">{{ scope.row.sku }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="price" label="价格" width="120">
                  <template #default="scope">
                    <el-tag type="danger">{{ scope.row.price }} 卢布</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="star" label="评分" width="100">
                  <template #default="scope">
                    <el-tag :type="getStarType(scope.row.star)">{{ scope.row.star.toFixed(1) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="comment_count" label="评价数量" width="120">
                  <template #default="scope">
                    <el-tag type="info">{{ scope.row.comment_count }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="120">
                  <template #default="scope">
                    <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">
                      {{ scope.row.status === 1 ? '已导出' : '未导出' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="updated_at" label="更新时间" width="180" />

              </el-table>
              
              <div class="empty-state" v-if="dataList.length === 0">
                <el-empty description="暂无数据" />
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 配置修改页面 -->
        <div v-if="activeMenu === 'config-settings'" class="config-settings-page">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span>爬虫配置管理</span>
                <el-tag type="info">当前配置: 默认配置</el-tag>
              </div>
            </template>
            
            <el-form :model="configForm" label-width="120px" class="config-form">
              <el-form-item label="浏览器路径">
                <el-input v-model="configForm.browserPath" placeholder="请输入浏览器路径" />
              </el-form-item>

              <el-form-item label="浏览器用户数据路径">
                <el-input v-model="configForm.browserUserDataPath" placeholder="请输入浏览器用户数据路径" />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="saveConfig">保存配置</el-button>
                <el-button @click="resetConfig">重置默认</el-button>
                <el-button type="danger" @click="testConfig">测试配置</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  background-color: #f5f7fa;
}

/* 左侧导航栏 */
.sidebar {
  width: 250px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #3b82f6;
}

.logo .subtitle {
  margin: 5px 0 0 0;
  font-size: 14px;
  color: #95a5a6;
}

.menu {
  flex: 1;
  background-color: transparent;
  border-right: none;
}

.menu :deep(.el-menu-item) {
  color: #ecf0f1;
  border-right: 3px solid transparent;
}

.menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1);
  color: #3b82f6;
}

.menu :deep(.el-menu-item.is-active) {
  background-color: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  border-right-color: #3b82f6;
}

.version-info {
  padding: 15px;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: #95a5a6;
  font-size: 12px;
}

.version-info p {
  margin: 5px 0;
}

/* 右侧内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  padding: 20px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-profile {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 10px;
  font-size: 14px;
  color: #606266;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: #f5f7fa;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
}

.loading-content {
  text-align: center;
  color: #3b82f6;
}

.loading-content p {
  margin-top: 15px;
  font-size: 16px;
  color: #606266;
}

.login-page {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: #f5f7fa;
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-card-container {
  width: 100%;
  max-width: 400px;
}

.login-card {
  text-align: center;
  padding: 20px;
}

.login-header {
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 15px 0 5px;
  color: #2c3e50;
}

.login-header p {
  color: #909399;
}

.login-action {
  margin-top: 20px;
}


.page-header h1 {
  margin: 0;
  color: #2c3e50;
}

.user-info {
  display: flex;
  align-items: center;
}

/* 页面内容 */
.page-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-card, .query-card, .config-card, .queue-card {
  margin-bottom: 20px;
}

/* 爬虫控制页面 */
.spider-control-page {
  /* 页面样式 */
}

/* 任务队列页面 */
.task-queue-page {
  /* 页面样式 */
}

.add-task-form {
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 20px;
}

.add-task-form h3, .queue-controls h3, .current-task h3, .task-list h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 16px;
}

.current-task {
  margin-bottom: 20px;
}

.batch-add-content {
  .dialog-tip {
    color: #909399;
    margin-bottom: 15px;
    font-size: 13px;
    line-height: 1.5;
  }
}

.spider-config {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.spider-info {
  margin-bottom: 20px;
}

.control-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

/* 日志显示区域 */
.log-area {
  margin-top: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-header h3 {
  margin: 0;
  color: #2c3e50;
}

.log-controls {
  display: flex;
  align-items: center;
}

.log-area h3 {
  margin-bottom: 10px;
  color: #2c3e50;
}

.log-content {
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.log-item {
  margin-bottom: 5px;
  padding: 5px;
  border-radius: 3px;
}

.log-level-info {
  background-color: #e3f2fd;
  color: #1976d2;
}

.log-level-success {
  background-color: #e8f5e9;
  color: #388e3c;
}

.log-level-warning {
  background-color: #fff3e0;
  color: #f57c00;
}

.log-level-error {
  background-color: #ffebee;
  color: #d32f2f;
}

.log-timestamp {
  margin-right: 10px;
  color: #95a5a6;
  font-size: 11px;
}

.log-level {
  margin-right: 10px;
  font-weight: bold;
  text-transform: uppercase;
  font-size: 10px;
}

.log-message {
  flex: 1;
}

.log-empty {
  text-align: center;
  color: #7f8c8d;
  padding: 20px;
  font-style: italic;
}

.task-list {
  margin-top: 20px;
}

.empty-state {
  margin-top: 20px;
  text-align: center;
}

/* 数据查询页面 */
.data-query-page {
  /* 页面样式 */
}

.search-box {
  margin-bottom: 20px;
}

.data-list {
  margin-top: 20px;
}

/* 配置修改页面 */
.config-settings-page {
  /* 页面样式 */
}

.config-form {
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .sidebar {
    width: 200px;
  }
  
  .logo h2 {
    font-size: 20px;
  }
  
  .logo .subtitle {
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    height: auto;
  }
  
  .main-content {
    width: 100%;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .search-box {
    flex-direction: column;
  }
}
</style>