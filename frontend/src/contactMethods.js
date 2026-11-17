export const methodLabels = {
  phone: '电话', address: '地址', email: '邮箱', qq: 'QQ', wechat: '微信', website: '个人网站',
}

// Keep the platform label when exchanging links and handles through the socials column.
const platforms = { qq: 'QQ：', wechat: '微信：', website: '个人网站：' }

export function websiteHref(value) {
  if (!/^https?:\/\//i.test(value) || !URL.canParse(value)) return null
  return new URL(value).href
}

export function displayMethod(method) {
  if (method.type === 'social') {
    for (const [type, prefix] of Object.entries(platforms)) {
      if (method.value.startsWith(prefix) && method.value.length > prefix.length) {
        return { type, value: method.value.slice(prefix.length) }
      }
    }
  }
  return { type: method.type, value: method.value }
}

export function storedMethod({type, value}) {
  if (Object.hasOwn(platforms, type)) {
    return { type: 'social', value: platforms[type] + value.trim() }
  }
  return { type, value }
}
