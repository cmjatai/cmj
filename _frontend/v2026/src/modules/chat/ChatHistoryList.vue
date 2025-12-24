<template>
  <div class="chat-history-list">
    <div class="history-header">
      <h4>Histórico</h4>
      <button
        class="btn btn-sm btn-outline-primary"
        @click="createNewChat"
      >
        <i class="fas fa-plus" /> Nova Conversa
      </button>
    </div>

    <div class="history-content">
      <div
        v-if="loading"
        class="text-center p-3"
      >
        <div
          class="spinner-border spinner-border-sm"
          role="status"
        >
          <span class="visually-hidden">Carregando...</span>
        </div>
      </div>

      <div
        v-else-if="sessions.length === 0"
        class="text-center p-3 text-muted"
      >
        <small>Nenhuma conversa anterior.</small>
      </div>

      <ul
        v-else
        class="list-group list-group-flush"
      >
        <li
          v-for="session in sessions"
          :key="session.session_id"
          class="list-group-item list-group-item-action"
          :class="{ active: currentSessionId === session.session_id }"
          @click="selectSession(session.session_id)"
        >
          <div class="d-flex w-100 justify-content-between">
            <h6 class="mb-1 text-truncate">
              {{ session.title }}
            </h6>
            <small>{{ formatDate(session.created_at) }}</small>
          </div>
          <small v-if="false" class="text-muted text-truncate d-block">
            {{ getLastMessage(session) }}
          </small>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const EventBus = inject('EventBus')

const router = useRouter()
const route = useRoute()

const sessions = ref([])
const loading = ref(false)

const currentSessionId = computed(() => route.params.sessionId)

const fetchSessions = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/search/chatsession/')
    sessions.value = response.data.results
  } catch (error) {
    console.error('Erro ao carregar histórico:', error)
  } finally {
    loading.value = false
  }
}

EventBus.on('chat:init:conversation', () => {
  fetchSessions()
})

const createNewChat = () => {
  const newSessionId = 'session_' + Math.random().toString(36).substr(2, 9)
  router.push({ name: 'chat_session_view', params: { sessionId: newSessionId } })
}

const selectSession = (sessionId) => {
  router.push({ name: 'chat_session_view', params: { sessionId } })
}

const getSessionTitle = (session) => {
  // Tenta pegar a primeira mensagem do usuário como título
  const firstMsg = session.messages?.find(m => m.role === 'user')
  return firstMsg ? firstMsg.content : `Conversa ${session.id}`
}

const getLastMessage = (session) => {
  if (!session.messages || session.messages.length === 0) return 'Sem mensagens'
  const lastMsg = session.messages[session.messages.length - 1]
  return lastMsg.content
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.chat-history-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #dee2e6;
  background-color: #f8f9fa;
}

.history-header {
  padding: 15px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #495057;
}

.history-content {
  flex: 1;
  overflow-y: auto;
}

.list-group-item {
  cursor: pointer;
  border-left: none;
  border-right: none;
  border-radius: 0;
  transition: background-color 0.2s;
}

.list-group-item:first-child {
  border-top: none;
}

.list-group-item.active {
  background-color: #e9ecef;
  color: #212529;
  border-color: #dee2e6;
}

.list-group-item:hover:not(.active) {
  background-color: #f1f3f5;
}
</style>
