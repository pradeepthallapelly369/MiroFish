<template>
  <div class="analyst-page">
    <header class="analyst-header">
      <button class="brand-button" @click="router.push('/')">MIROFISH</button>
      <div class="header-actions">
        <div class="header-tag">Agent / analyst_fish</div>
        <button class="back-button" @click="router.push('/')">Back to Home</button>
      </div>
    </header>

    <main class="analyst-layout">
      <section class="persona-panel">
        <div class="panel-kicker">Retail Momentum Analyst</div>
        <h1 class="panel-title">analyst_fish</h1>
        <p class="panel-summary">
          A trading-desk-style market persona. By default, this is a high-risk, strongly bullish, emotion-driven Indian retail options trader built for roleplay and market-reaction simulation.
        </p>

        <div class="persona-card" v-if="persona">
          <div class="persona-meta">
            <span>{{ persona.profession }}</span>
            <span>{{ persona.country }}</span>
            <span>{{ persona.mbti }}</span>
          </div>
          <p class="persona-bio">{{ persona.bio }}</p>
          <p class="persona-text">{{ persona.persona }}</p>

          <div class="topic-wrap" v-if="persona.interested_topics?.length">
            <span
              v-for="topic in persona.interested_topics"
              :key="topic"
              class="topic-pill"
            >
              {{ topic }}
            </span>
          </div>
        </div>

        <div class="quick-prompts">
          <div class="prompt-label">Quick Prompts</div>
          <button
            v-for="prompt in quickPrompts"
            :key="prompt"
            class="prompt-chip"
            @click="usePrompt(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
      </section>

      <section class="chat-panel">
        <div class="chat-header">
          <div>
            <div class="chat-title">Live Desk</div>
            <div class="chat-subtitle">Talk directly with analyst_fish</div>
          </div>
          <div class="chat-status" :class="{ busy: loading }">
            {{ loading ? 'Generating' : 'Ready' }}
          </div>
        </div>

        <div ref="messagesContainer" class="messages">
          <div v-for="item in messages" :key="item.id" class="message-row" :class="item.role">
            <div class="message-label">{{ item.role === 'user' ? 'You' : 'analyst_fish' }}</div>
            <div class="message-bubble">{{ item.content }}</div>
          </div>

          <div v-if="loading" class="message-row assistant">
            <div class="message-label">analyst_fish</div>
            <div class="message-bubble typing">Reading sentiment, momentum, and retail psychology...</div>
          </div>
        </div>

        <div class="composer">
          <textarea
            v-model="draftMessage"
            class="message-input"
            rows="5"
            :disabled="loading"
            placeholder="Example: BankNifty opened down 2%, then printed a strong 15-minute reversal candle on rising volume. What would you do?"
            @keydown.enter.exact.prevent="sendMessage"
          />

          <textarea
            v-model="marketContext"
            class="context-input"
            rows="4"
            :disabled="loading"
            placeholder='Optional market context in natural language or JSON, for example: {"index":"Nifty","move_pct":-1.8,"trigger":"RBI hike"}'
          />

          <div v-if="error" class="error-box">{{ error }}</div>

          <div class="composer-actions">
            <button class="ghost-button" @click="clearChat" :disabled="loading">Clear Chat</button>
            <button class="send-button" @click="sendMessage" :disabled="loading || !draftMessage.trim()">
              {{ loading ? 'Sending...' : 'Send to analyst_fish' }}
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { chatWithAnalyst, getAnalystPersona } from '../api/analyst'

const router = useRouter()

const persona = ref(null)
const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: 'Give me the tape, the sentiment, and the trigger. I will answer in analyst_fish style with a direct trading reaction.'
  }
])
const draftMessage = ref('')
const marketContext = ref('')
const loading = ref(false)
const error = ref('')
const messagesContainer = ref(null)

const quickPrompts = [
  'Nifty has rallied for three straight sessions on rising volume. Is it still worth chasing higher?',
  'If the RBI suddenly hikes rates, what is Rahul’s first reaction as a trader?',
  'Why would someone still refuse to cut losses after an IT earnings blowup?',
  'BankNifty made a false breakout and snapped back fast. How do you read the sentiment shift?'
]

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const parseMarketContext = (value) => {
  const text = value.trim()
  if (!text) return undefined

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

const loadPersona = async () => {
  const res = await getAnalystPersona()
  persona.value = res.data.persona
}

const usePrompt = (prompt) => {
  draftMessage.value = prompt
}

const clearChat = () => {
  messages.value = [
    {
      id: 1,
      role: 'assistant',
      content: 'Give me the tape, the sentiment, and the trigger. I will answer in analyst_fish style with a direct trading reaction.'
    }
  ]
  error.value = ''
}

const sendMessage = async () => {
  const content = draftMessage.value.trim()
  if (!content || loading.value) return

  error.value = ''
  const nextId = messages.value.length + 1
  const history = messages.value.map(item => ({
    role: item.role === 'assistant' ? 'assistant' : 'user',
    content: item.content
  }))

  messages.value.push({
    id: nextId,
    role: 'user',
    content
  })

  draftMessage.value = ''
  await scrollToBottom()
  loading.value = true

  try {
    const res = await chatWithAnalyst({
      message: content,
      chat_history: history,
      market_context: parseMarketContext(marketContext.value)
    })

    messages.value.push({
      id: messages.value.length + 1,
      role: 'assistant',
      content: res.data.reply
    })
  } catch (err) {
    error.value = err.message || 'Request failed'
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

onMounted(async () => {
  try {
    await loadPersona()
  } catch (err) {
    error.value = err.message || 'Failed to load analyst_fish persona'
  }
  scrollToBottom()
})
</script>

<style scoped>
.analyst-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(255, 69, 0, 0.08), transparent 30%),
    linear-gradient(180deg, #fffdf8 0%, #ffffff 100%);
  color: #111111;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.analyst-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 28px;
  border-bottom: 1px solid #e8e1d7;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand-button,
.back-button,
.prompt-chip,
.ghost-button,
.send-button {
  border: none;
  cursor: pointer;
}

.brand-button {
  background: transparent;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-tag,
.back-button {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
}

.header-tag {
  border: 1px solid #e2d3c0;
  background: #fff6ec;
  padding: 9px 12px;
}

.back-button {
  background: #111111;
  color: #ffffff;
  padding: 10px 14px;
}

.analyst-layout {
  max-width: 1440px;
  margin: 0 auto;
  padding: 32px 28px 40px;
  display: grid;
  grid-template-columns: minmax(320px, 420px) 1fr;
  gap: 24px;
}

.persona-panel,
.chat-panel {
  border: 1px solid #eadfd2;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 24px 60px rgba(21, 21, 21, 0.06);
}

.persona-panel {
  padding: 28px;
}

.panel-kicker,
.prompt-label,
.chat-subtitle,
.message-label,
.chat-status,
.persona-meta {
  font-family: 'JetBrains Mono', monospace;
}

.panel-kicker {
  color: #d25a1c;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.panel-title {
  font-size: 3rem;
  line-height: 0.95;
  margin: 10px 0 16px;
}

.panel-summary {
  color: #4f4a43;
  line-height: 1.7;
  margin-bottom: 24px;
}

.persona-card {
  border: 1px solid #efe4d5;
  background: linear-gradient(180deg, #fff8ef 0%, #fff 100%);
  padding: 18px;
}

.persona-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: #8b5b3b;
  font-size: 0.72rem;
  margin-bottom: 14px;
}

.persona-bio {
  font-size: 1.02rem;
  font-weight: 600;
  line-height: 1.6;
  margin-bottom: 12px;
}

.persona-text {
  color: #4f4a43;
  line-height: 1.7;
  font-size: 0.95rem;
}

.topic-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.topic-pill,
.prompt-chip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.73rem;
}

.topic-pill {
  background: #111111;
  color: #ffffff;
  padding: 7px 9px;
}

.quick-prompts {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.prompt-label {
  color: #7c746b;
  font-size: 0.72rem;
}

.prompt-chip {
  text-align: left;
  background: #f7f2ec;
  border: 1px solid #eadfd2;
  padding: 11px 12px;
}

.prompt-chip:hover {
  background: #fff3e4;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 150px);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 16px;
  border-bottom: 1px solid #efe4d5;
}

.chat-title {
  font-size: 1.4rem;
  font-weight: 700;
}

.chat-subtitle {
  margin-top: 4px;
  color: #85776a;
  font-size: 0.74rem;
}

.chat-status {
  background: #eef7ef;
  color: #24613b;
  padding: 8px 10px;
  font-size: 0.72rem;
}

.chat-status.busy {
  background: #fff2e8;
  color: #c4571c;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.message-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 88%;
}

.message-row.user {
  align-self: flex-end;
}

.message-row.assistant {
  align-self: flex-start;
}

.message-bubble {
  padding: 15px 16px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.message-row.user .message-bubble {
  background: #111111;
  color: #ffffff;
}

.message-row.assistant .message-bubble {
  background: #fff7f0;
  border: 1px solid #efdcca;
  color: #1b1b1b;
}

.typing {
  color: #8c5d3d;
  font-style: italic;
}

.composer {
  border-top: 1px solid #efe4d5;
  padding: 18px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-input,
.context-input {
  width: 100%;
  border: 1px solid #e6d8c8;
  padding: 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  resize: vertical;
  outline: none;
  background: #fffdfa;
}

.message-input:focus,
.context-input:focus {
  border-color: #d25a1c;
}

.error-box {
  border: 1px solid #f0c7bc;
  background: #fff3f1;
  color: #9a3412;
  padding: 12px;
  font-size: 0.9rem;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.ghost-button,
.send-button {
  padding: 12px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.ghost-button {
  background: #f7f2ec;
  color: #3f3730;
}

.send-button {
  background: #d25a1c;
  color: #ffffff;
}

.send-button:disabled,
.ghost-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1100px) {
  .analyst-layout {
    grid-template-columns: 1fr;
  }

  .chat-panel {
    min-height: 70vh;
  }
}

@media (max-width: 700px) {
  .analyst-header,
  .analyst-layout {
    padding-left: 16px;
    padding-right: 16px;
  }

  .header-actions {
    flex-direction: column;
    align-items: flex-end;
  }

  .panel-title {
    font-size: 2.1rem;
  }

  .messages,
  .composer,
  .persona-panel {
    padding-left: 16px;
    padding-right: 16px;
  }

  .message-row {
    max-width: 100%;
  }

  .composer-actions {
    flex-direction: column;
  }
}
</style>
