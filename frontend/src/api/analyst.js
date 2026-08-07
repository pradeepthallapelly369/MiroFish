import service, { requestWithRetry } from './index'

/**
 * 获取 analyst_fish 默认人设
 */
export const getAnalystPersona = () => {
  return service.get('/api/analyst/persona')
}

/**
 * 与 analyst_fish 对话
 * @param {Object} data - { message, chat_history?, market_context?, persona? }
 */
export const chatWithAnalyst = (data) => {
  return requestWithRetry(() => service.post('/api/analyst/chat', data), 2, 800)
}
