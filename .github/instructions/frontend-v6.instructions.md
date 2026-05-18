---
description: "Use when writing, editing or reviewing Vue 3 components, stores, or composables in the frontend v6 (_frontend/v6/). Covers component structure, store usage (SyncStore, AuthStore, MessageStore), HTTP calls via Resources.Utils, EventBus, and cache access patterns."
applyTo: "_frontend/v6/**"
---

# Frontend v6 — Vue 3 Conventions

## Component Structure

Always use `<script setup>`. Follow this comment order inside the script block:

```vue
<script setup>
// 1. Importações
// 2. Composables (stores, router, EventBus)
// 3. Props & Emits
// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
```

## Import Aliases

| Alias | Resolves to |
|-------|------------|
| `~@/` | `src/` |

```js
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resources from '~@/utils/resources'
```

## Stores

**SyncStore** — cache centralizado + WebSocket:
```js
const syncStore = useSyncStore()

// Buscar dados (atualiza cache automaticamente)
await syncStore.fetchSync({ app: 'arq', model: 'draft', params: { o: 'descricao', get_all: 'True' } })

// Ler do cache — chave = 'app_model'
const item = computed(() => syncStore.data_cache?.arq_draft?.[props.id] || null)
const list = computed(() => Object.values(syncStore.data_cache?.arq_draft || {}))
```

**AuthStore** — autenticação:
```js
const authStore = useAuthStore()
authStore.isAuthenticated   // boolean
authStore.hasPermission('app.change_model')
```

**MessageStore** — notificações:
```js
const messageStore = useMessageStore()
messageStore.addMessage({ type: 'success', text: 'Salvo!', timeout: 5000 })
// type: 'success' | 'danger' | 'info' | 'warning'
```

## HTTP Calls (Resources.Utils)

```js
// GET lista
Resources.Utils.fetch({ app: 'arq', model: 'arqdoc', query_string: 'o=-data&page=1' })

// GET item por id
Resources.Utils.fetch({ app: 'arq', model: 'arqclasse', id: classeId })

// POST
Resources.Utils.postModel({ app: 'arq', model: 'draft', form: { descricao: 'Novo' } })

// PATCH
Resources.Utils.patchModel({ app: 'arq', model: 'draft', id: item.id, form: { descricao: valor } })

// DELETE
Resources.Utils.deleteModel({ app: 'arq', model: 'draft', id: item.id })
```

Prefira `syncStore.fetchSync()` para dados que precisam de cache/WebSocket. Use `Resources.Utils.fetch()` diretamente para buscas ad-hoc ou fora do padrão REST.

## EventBus

```js
// Composition API
const EventBus = inject('EventBus')
EventBus.on('side:close-sideleft', handler)
EventBus.emit('side:close-sideleft')
// Lembre de remover listener em onUnmounted()
```

## Lodash

`_` está disponível globalmente (sem importação). Use `_.orderBy`, `_.filter`, `_.each`, etc.

## Padrões a evitar

- Não usar Options API com `this.` em componentes novos — use `<script setup>`
- Não usar `this.$set` — atribua propriedades diretamente no Vue 3
- Não usar `import _ from 'lodash'` — já é global
- Não acessar `data_cache` sem optional chaining (`?.`) — o cache pode não estar populado

## Detalhes adicionais

Ver [`/memories/repo/v6_frontend_patterns.md`](/memories/repo/v6_frontend_patterns.md) para referência completa de SyncStore actions, TeleportStore e padrões de roteamento.
