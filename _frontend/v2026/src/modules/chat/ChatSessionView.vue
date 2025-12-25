<template>
  <div class="chat-session-view">
    <div class="chat-header">
      <h3>
        <FontAwesomeIcon icon="hat-wizard" />
        LegisBee
      </h3>
      <h6>
        Fonte de Dados da LegisBee:
        <a
          href="/norma/destaques"
          target="_blank"
          title="Inicialmente, apenas as normas de destaque estão disponíveis para pesquisa"
        >
          Normas de Destaque
        </a>
      </h6>
      <span
        class="status-indicator"
        :class="{ connected: isConnected }"
      />
    </div>

    <div
      class="chat-messages"
      ref="messagesContainer"
    >
      <div
        v-if="messages.length === 0 && userCanUserChat"
        class="empty-state"
      >
        <p>Olá! Como posso ajudar você hoje?</p>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message-wrapper"
        :class="msg.role"
      >
        <div class="message-bubble">
          <div
            class="message-content"
            v-html="formatMessage(msg.content)"
          />
        </div>
      </div>

      <div
        v-if="isLoading"
        class="message-wrapper model loading"
      >
        <div class="message-bubble">
          <span class="typing-dot" />
          <span class="typing-dot" />
          <span class="typing-dot" />
        </div>
      </div>
    </div>

    <div
      v-if="userCanUserChat"
      class="chat-input-area"
    >
      <div class="input-wrapper">
        <span
          class="char-counter"
          :class="{ 'limit-reached': inputMessage.length >= maxMessageLength }"
        >
          {{ inputMessage.length }} / {{ maxMessageLength }}
        </span>
        <textarea
          v-model="inputMessage"
          @keydown.enter.prevent="sendMessage"
          placeholder="Digite sua mensagem..."
          :disabled="!isConnected || isLoading"
          rows="2"
          ref="inputRef"
          :maxlength="maxMessageLength"
        />
      </div>
      <button
        @click="sendMessage"
        :disabled="!isConnected || !inputMessage.trim() || isLoading"
        class="send-btn"
      >
        <FontAwesomeIcon icon="paper-plane" />
      </button>
    </div>
    <div
      v-else
      class="chat-input-area permission-denied"
    >
      <p>LegisBee está em desenvolvimento.</p>
      <p v-if="false">
        Você não tem permissão para acessar o chat.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '~@/stores/AuthStore'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true
})

const authStore = useAuthStore()
const route = useRoute()

const EventBus = inject('EventBus')

// Props
const props = defineProps({
  wsEndpoint: {
    type: String,
    default: '/ws/chat/'
  }
})

// State
const messages = ref([])
const inputMessage = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const socket = ref(null)
const messagesContainer = ref(null)
const inputRef = ref(null)
const maxMessageLength = ref(250)

// Computed Session ID from Route
const sessionId = computed(() => {
  return route.params.sessionId || 'session_' + Math.random().toString(36).substr(2, 9)
})

// WebSocket Connection
const connectWebSocket = () => {
  if (!userCanUserChat.value) return

  // Close existing connection if any
  if (socket.value) {
    socket.value.close()
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const url = `${protocol}//${host}${props.wsEndpoint}${sessionId.value}/`

  console.log('Connecting to Chat WS:', url)

  socket.value = new WebSocket(url)

  socket.value.onopen = () => {
    isConnected.value = true
    console.log('Chat WebSocket Connected')
  }

  socket.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleSocketMessage(data)
    } catch (e) {
      console.error('Error parsing WS message:', e)
    }
  }

  socket.value.onclose = (e) => {
    isConnected.value = false
    console.log('Chat WebSocket Closed', e.code, e.reason)
  }

  socket.value.onerror = (error) => {
    console.error('Chat WebSocket Error:', error)
    isConnected.value = false
  }
}

const handleSocketMessage = (data) => {
  switch (data.type) {
    case 'connection_established':
      console.log('Session established:', data.session_id)
      if (data.max_length) {
        maxMessageLength.value = data.max_length
      }
      if (data.history && Array.isArray(data.history)) {
        messages.value = data.history
        scrollToBottom()
      }
      break

    case 'chat_message':
      isLoading.value = false
      if (messages.value.length === 1) {
        EventBus.emit('chat:init:conversation')
      }
      messages.value.push({
        role: data.role, // 'model'
        content: data.message
      })
      scrollToBottom()
      break

    case 'error':
      isLoading.value = false
      messages.value.push({
        role: 'system',
        content: `Erro: ${data.message}`
      })
      break

    default:
      console.warn('Unknown message type:', data.type)
  }
}

const userCanUserChat = computed(() => {
  return authStore.hasPermission('search.can_use_chat_module')
})

// Actions
const sendMessage = () => {
  const text = inputMessage.value.trim()
  if (!text || !isConnected.value) return

  // Adiciona mensagem do usuário localmente
  messages.value.push({
    role: 'user',
    content: text
  })

  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()

  // Envia para o backend
  socket.value.send(JSON.stringify({
    message: text
  }))

  // Reset altura do textarea
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
}

const formatMessage = (text) => {
  return md.render(text)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Auto-resize textarea
watch(inputMessage, () => {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
      inputRef.value.style.height = inputRef.value.scrollHeight + 'px'
    }
  })
})

// Watch for session changes
watch(sessionId, () => {
  messages.value = [] // Clear messages on session change
  if (userCanUserChat.value) {
    connectWebSocket()
  }
})

// Lifecycle
onMounted(() => {
  if (userCanUserChat.value) {
    connectWebSocket()
  }
})

watch(userCanUserChat, (newValue) => {
  if (newValue && !isConnected.value) {
    connectWebSocket()
  } else if (!newValue && isConnected.value) {
    if (socket.value) {
      socket.value.close()
    }
  }
})

onUnmounted(() => {
  if (socket.value) {
    socket.value.close()
  }
})
</script>

<style scoped lang="scss">
.chat-session-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  overflow: hidden;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.chat-header {
  padding: 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;

  h3 {
    margin: 0;
    font-size: 1.3rem;
    color: #0056b3;
  }
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #dc3545;
  transition: background-color 0.3s;

  &.connected {
    background-color: #28a745;
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.empty-state {
  text-align: center;
  color: #6c757d;
  margin-top: 40px;
}

.message-wrapper {
  display: flex;
  max-width: 80%;

  &.user {
    align-self: flex-end;
    justify-content: flex-end;
  }

  &.model {
    align-self: flex-start;
    justify-content: flex-start;
  }

  &.system {
    align-self: center;
    max-width: 90%;
  }
}

.message-bubble {
  padding: 10px 15px;
  border-radius: 15px;
  font-size: 0.95rem;
  line-height: 1.4;
  word-wrap: break-word;

  .user & {
    background-color: #007bff;
    color: white;
    border-bottom-right-radius: 2px;
  }

  .model & {
    background-color: #f1f0f0;
    color: #333;
    border-bottom-left-radius: 2px;
  }

  .system & {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeeba;
  }
}

.chat-input-area {
  padding: 15px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 10px;
  background: #f8f9fa;
  align-items: flex-end;

  &.permission-denied {
    justify-content: center;
    color: #dc3545;
    font-weight: 500;
    align-items: center;
  }
}

textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 20px;
  resize: none;
  outline: none;
  font-family: inherit;
  max-height: 100px;
  overflow-y: auto;

  &.permission-denied::placeholder {
    color: #dc3545;
  }

  &:focus {
    border-color: #80bdff;
  }
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background-color: #007bff;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;

  &:hover:not(:disabled) {
    background-color: #0056b3;
  }

  &:disabled {
    background-color: #6c757d;
    cursor: not-allowed;
    opacity: 0.7;
  }
}

/* Loading animation */
.typing-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 3px;
  background-color: #666;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;

  &:nth-child(1) { animation-delay: -0.32s; }
  &:nth-child(2) { animation-delay: -0.16s; }
}

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-wrapper {
  position: relative;
  flex: 1;
  display: flex;
}

.char-counter {
  position: absolute;
  right: 12px;
  top: 3px;
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
  pointer-events: none;

  &.limit-reached {
    color: #dc3545;
  }
}
</style>
