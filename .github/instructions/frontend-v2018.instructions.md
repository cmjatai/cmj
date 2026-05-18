---
description: "Use when writing, editing or reviewing Vue 2 components, Vuex stores, or utilities in the frontend v2018 (_frontend/v2018/). Covers Options API, Vuex modules, Resources.Utils, EventBus e BootstrapVue."
applyTo: "_frontend/v2018/**"
---

# Frontend v2018 — Vue 2 Conventions

> **Modo manutenção.** Não migre para Vue 3, Pinia ou Composition API. Corrija bugs e faça ajustes pontuais mantendo os padrões existentes.

## Estrutura de componentes

Use **exclusivamente Options API**. Não usar `<script setup>` nem `defineComponent` com Composition API.

```vue
<template>...</template>

<script>
import { mapState, mapActions } from 'vuex'
import { EventBus } from '@/event-bus'

export default {
  name: 'MeuComponente',
  components: { /* imports locais */ },
  props: { ... },
  data() {
    return { ... }
  },
  computed: {
    ...mapState('store__sync', ['data_cache', 'wsConnected']),
    ...mapState('store__auth', { user: state => state.data_connect }),
  },
  watch: { ... },
  methods: {
    ...mapActions('store__sync', ['fetchSync']),
    ...mapActions(['sendMessage']),
  },
  mounted() { ... },
  beforeDestroy() {
    EventBus.$off('evento', this.handler)  // sempre remover listeners
  }
}
</script>
```

## Import alias

`@/` aponta para `src/`. Usar `@/` (não `~@/` — esse é o alias do v6).

## Vuex — módulos disponíveis

| Módulo | Acesso | Conteúdo |
|--------|--------|----------|
| `store__sync` | `mapState('store__sync', [...])` | `data_cache`, `wsConnected`, `fetchSync` |
| `store__auth` | `mapState('store__auth', [...])` | `data_connect` (user + permissions) |
| `store__message` | `mapActions(['sendMessage'])` | notificações |
| `store__online` | `mapState('store__online', [...])` | status conexão |

**Acessar cache:**
```javascript
// No template ou computed:
this.data_cache['loa_orgao']       // objeto indexado por id
this.data_cache['loa_orgao'][42]   // item por id
```

**Buscar dados:**
```javascript
this.fetchSync({ app: 'loa', model: 'orgao', action: '', query_string: '' })
```

## HTTP (Resources.Utils)

```javascript
import Resources from '@/resources'

// Assinaturas posicionais (diferente do v6 que usa objeto {app, model, id, form})
Resources.Utils.getModel(app, model, id)
Resources.Utils.getModelList(app, model, page = 1, query_string = '')
Resources.Utils.getModelOrderedList(app, model, ordering = '', page = 1, query_string = '')
Resources.Utils.getModelAction(app, model, id, action, query_string = '')
Resources.Utils.getModelListAction(app, model, action, page = 1)
Resources.Utils.postModel(app, model, form)
Resources.Utils.postModelAction(app, model, id, action, form, progress = {})
Resources.Utils.patchModel(app, model, id, form)
Resources.Utils.patchModelAction(app, model, id, action, form, progress = {})
Resources.Utils.deleteModel(app, model, id)

// fetch(m) aceita objeto — mesmo padrão do v6
Resources.Utils.fetch({ app, model, id?, action?, params?, query_string? })
```

## EventBus

```javascript
import { EventBus } from '@/event-bus'

// Publicar
EventBus.$emit('nome-do-evento', payload)

// Assinar
EventBus.$on('nome-do-evento', this.handler)

// Remover sempre em beforeDestroy
EventBus.$off('nome-do-evento', this.handler)
```

## Bootstrap

Usa **BootstrapVue** (não Bootstrap 5 nativo). Componentes disponíveis sem importação:
`<b-button>`, `<b-form-select>`, `<b-modal>`, `<b-table>`, `<b-form-input>`, etc.

## Reatividade Vue 2

Para adicionar propriedades reativas a objetos existentes usar `this.$set`:
```javascript
this.$set(this.obj, 'novaChave', valor)  // Vue 2 — necessário para reatividade
```
Não usar atribuição direta `obj.novaChave = valor` em objetos já reativos.

## Padrões a evitar

- Não usar `ref()`, `reactive()`, `computed()` importados de `'vue'` — isso é Vue 3
- Não usar `inject('EventBus')` — usar import direto de `@/event-bus`
- Não usar Pinia — usar Vuex com `mapState`/`mapActions`
- Não usar `~@/` — usar `@/`
