import { ref, watchEffect } from 'vue'

const key = 'directory-language'
export const language = ref(localStorage.getItem(key) === 'zh' ? 'zh' : 'en')

export function toggleLanguage() {
  language.value = language.value === 'en' ? 'zh' : 'en'
  localStorage.setItem(key, language.value)
}

const english = {
  '搜索联系人': 'Search contacts',
  '搜索姓名、电话、地址或备注': 'Search by name, phone, address or notes',
  '清除搜索': 'Clear search',
  '没有匹配的联系人': 'No matching contacts',
  '下载 Excel 模板': 'Download Excel template',
  '复制': 'Copy',
  '已复制': 'Copied',
  '复制失败': 'Copy failed',
  '通讯录': 'Address book',
  '退出登录': 'Sign out',
  '切换至浅色模式': 'Use light theme',
  '切换至深色模式': 'Use dark theme',
  '正在读取账号…': 'Checking your session…',
  '你的个人通讯录': 'Your personal address book',
  '注册账号': 'Create an account',
  '登录': 'Sign in',
  '用户名': 'Username',
  '密码': 'Password',
  '密码长度为 8–128 个字符。': 'Use 8–128 characters.',
  '确认密码': 'Confirm password',
  '正在处理…': 'Please wait…',
  '注册并登录': 'Create account and sign in',
  '已有账号，去登录': 'Already registered? Sign in',
  '创建新账号': 'Create an account',
  '无法连接账号服务，请检查后端是否已启动。': 'Cannot reach the account service. Check that the server is running.',
  '两次输入的密码不一致。': 'The passwords do not match.',
  '网络连接失败，请重试。': 'Network connection failed. Please try again.',
  '请求失败，请重试。': 'Request failed. Please try again.',
  '操作失败，请重试。': 'Something went wrong. Please try again.',
  '联系人筛选': 'Filter contacts',
  '全部联系人': 'All contacts',
  '我的收藏': 'Favorites',
  '置顶收藏': 'Pinned favorites',
  '其他联系人': 'Other contacts',
  '新增联系人': 'Add contact',
  '编辑联系人': 'Edit contact',
  '导入 Excel': 'Import Excel',
  '导出 Excel': 'Export Excel',
  '正在读取联系人…': 'Loading contacts…',
  '暂时无法读取联系人': 'Could not load contacts',
  '请确认通讯录服务已启动，然后重试。': 'Check that the contact service is running and try again.',
  '重新加载': 'Retry',
  '暂无收藏联系人': 'No favorites yet',
  '通讯录为空': 'No contacts yet',
  '已收藏': 'Favorite',
  '取消收藏': 'Unfavorite',
  '收藏': 'Favorite',
  '编辑': 'Edit',
  '删除': 'Delete',
  '电话': 'Phone',
  '地址': 'Address',
  '邮箱': 'Email',
  '微信': 'WeChat',
  '个人网站': 'Website',
  '社交账号': 'Social account',
  '社交账号（旧记录）': 'Social account (legacy)',
  '姓名': 'Name',
  '备注': 'Notes',
  '请输入以 https:// 或 http:// 开头的完整网址': 'Enter a full URL beginning with https:// or http://',
  '请输入联系方式': 'Enter a contact detail',
  '移除': 'Remove',
  '＋ 添加联系方式': '＋ Add contact method',
  '保存中…': 'Saving…',
  '保存联系人': 'Save contact',
  '返回通讯录': 'Back to contacts',
  '有未保存的修改': 'Unsaved changes',
  '放弃尚未保存的修改并返回通讯录？': 'Discard your unsaved changes and return to contacts?',
  '请提交用户名和密码。': 'Enter your username and password.',
  '请输入用户名和密码。': 'Enter your username and password.',
  '用户名限 1–40 字，密码限 8–128 个字符。': 'Use 1–40 characters for the username and 8–128 for the password.',
  '这个用户名已被使用。': 'This username is already taken.',
  '用户名或密码有误。': 'Incorrect username or password.',
  '请使用 JSON 请求。': 'Send a JSON request.',
  '缺少 Contacts 工作表。': 'The Contacts worksheet is missing.',
  '无法读取该 XLSX 工作簿。': 'This XLSX workbook could not be read.',
  'G 列右侧不能包含数据。': 'Remove data to the right of column G.',
  '不接受公式或 Excel 错误值。': 'Formulas and Excel error values are not supported.',
  '收藏状态必须是布尔值、TRUE、FALSE 或空白。': 'Enter TRUE, FALSE, a boolean, or leave the cell blank.',
  '请将原值以文本格式重新录入。': 'Re-enter the original value as text.',
  '请先登录。': 'Please sign in.',
  '联系人不存在。': 'This contact no longer exists.',
  '只接受 .xlsx 文件。': 'Select an .xlsx file.',
  '未选择上传文件。': 'Choose a file to upload.',
  '工作簿校验失败，未导入任何联系人。': 'Workbook validation failed. No contacts were imported.',
  '联系人数超出一个 Excel 工作表的容纳上限。': 'There are too many contacts for one worksheet.',
  '联系人数据校验失败。': 'Check the contact details.',
  '请求无法完成。': 'The request could not be completed.',
  '服务器处理请求时发生错误。': 'The server could not complete the request.',
  '联系方式': 'Contact detail',
  '同一类型最多保存 20 条。': 'Each contact method type allows up to 20 entries.',
  '同一类型的值不能重复。': 'Duplicate values of the same type are not allowed.',
  '电话号码格式无效，必须包含至少一个数字。': 'Enter a valid phone number with at least one digit.',
  '邮箱格式无效。': 'Enter a valid email address.',
  '请在 file 字段上传一个文件。': 'Upload one file in the file field.',
  '请求格式无效。': 'Invalid request format.',
  '联系人或 API 路径不存在。': 'Contact or API route not found.',
  '此 API 路径不支持该请求方法。': 'Unsupported request method.',
  '请求的媒体类型不受支持。': 'Unsupported media type.',
  '联系方式类型无效。': 'Invalid contact method type.',
}

export function t(message) {
  if (language.value === 'zh' || !message) return message
  if (Object.hasOwn(english, message)) return english[message]
  const imported = /^已导入 (\d+) 位联系人。$/.exec(message)
  if (imported) return 'Imported ' + imported[1] + (imported[1] === '1' ? ' contact.' : ' contacts.')
  const header = /^表头必须为 (.+)。$/.exec(message)
  if (header) return 'Expected column header: ' + header[1]
  const invalid = /^(姓名|备注|联系方式)(不能为空|必须是文本|包含无效字符|不能包含换行|最多包含 (\d+) 个字符)。$/.exec(message)
  if (invalid) {
    const reasons = { '不能为空': ' is required.', '必须是文本': ' must be text.', '包含无效字符': ' contains invalid characters.', '不能包含换行': ' must be on one line.' }
    return english[invalid[1]] + (reasons[invalid[2]] || ' must be at most ' + invalid[3] + ' characters.')
  }
  return message
}

watchEffect(() => {
  document.documentElement.lang = language.value === 'en' ? 'en' : 'zh-CN'
  document.title = t('通讯录')
})
