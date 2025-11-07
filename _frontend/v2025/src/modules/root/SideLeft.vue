<template>
  <div
    class="offcanvas offcanvas-start d-lg-none"
    tabindex="-1"
    id="menuSideLeft"
    aria-labelledby="menuSideLeftLabel"
  >
    <div class="offcanvas-header">
      <h5 id="menuSideLeftLabel">
        Menu
      </h5>
      <button
        type="button"
        class="btn-close"
        data-bs-dismiss="offcanvas"
        aria-label="Fechar"
      />
    </div>
    <div class="offcanvas-body">
      <ul class="nav flex-column">
        <li
          class="nav-item"
          v-for="link in linksAtivos"
          :key="link.texto"
        >
          <router-link :to="{ name: link.route }" class="nav-link">
            <b-img
              v-if="link.image"
              :src="link.image"
              fluid
              rounded="0"
              class="me-2"
            />
            <i
              v-else-if="link.icon"
              :class="link.icon + ' me-2'"
            />
          </router-link>
        </li>
      </ul>
    </div>
  </div>
  <div
    ref="sidebar"
    class="sidebar d-none d-lg-flex flex-column collapsed"
  >
    <ul class="nav flex-column">
      <li
        ref="toggleSidebar"
        class="nav-item toggle-btn"
      >
        <span class="nav-link">☰</span>
      </li>
      <li
        class="nav-item"
        v-for="link in linksAtivos"
        :key="link.texto"
      >
        <router-link :to="{ name: link.route }" class="nav-link">
          <b-img
            v-if="link.image"
            :src="link.image"
            fluid
            rounded="0"
            class="me-2"
          />
          <i
            v-else-if="link.icon"
            :class="link.icon + ' me-2'"
          />
        </router-link>
      </li>
      <!-- Outras opções -->
    </ul>
  </div>
</template>

<script setup>
// 1. Imports
import { onMounted, ref, computed } from 'vue'

// 2. Composables

// 3. Props & Emits

// 4. State & Refs
const sidebar = ref(null)
const toggleSidebar = ref(null)
const links = ref([
  {
    image: '/static/imgs/icon_mesa_diretora.png',
    route: '',
    texto: 'Mesa Diretora'
  },
  {
    image: '/static/imgs/icon_comissoes.png',
    route: '',
    texto: 'Comissões'
  },
  {
    image: '/static/imgs/icon_parlamentares.png',
    route: '',
    texto: 'Parlamentares'
  },
  {
    image: '/static/imgs/icon_pautas.png',
    route: '',
    texto: 'Pautas'
  },
  {
    image: '/static/imgs/icon_plenarias.png',
    route: 'sessao_module_view',
    texto: 'Sessões Plenárias'
  },
  {
    image: '/static/imgs/icon_materia_legislativa.png',
    route: '',
    texto: 'Matérias Legislativas'
  },
  {
    image: '/static/imgs/icon_normas_juridicas.png',
    route: '',
    texto: 'Normas Jurídicas'
  },
  {
    image: '/static/imgs/icon_relatorios.png',
    route: '',
    texto: 'Relatórios'
  },
  {
    icon: 'fas fa-columns',
    route: '',
    texto: 'Eventos e Painéis'
  }
])

// 5. Computed Properties
const linksAtivos = computed(() => {
  return links.value.filter(link => link.route !== '')
})

// 6. Watchers

// 7. Events & Lifecycle Hooks
onMounted(() => {
  toggleSidebar.value.addEventListener('click', () => {
    sidebar.value.classList.toggle('collapsed')
  })
})

// 8. Functions
</script>
<style lang="scss">
  .sidebar {
    position: fixed;
    transition: all 0.2s;
    border-right: 1px solid var(--bs-border-color-translucent);
    z-index: 1020;
    bottom: 0;
    top: 3em;
    width: 15em;
    background-color: var(--bs-body-bg);
    justify-content: flex-start;
    align-items: flex-start;
    .toggle-btn {
      text-align: center;
      cursor: pointer;
    }
  }
  .sidebar.collapsed {
    width: 3em;
  }
  .sidebar.collapsed .sidebar-label {
    font-size: 0em;
  }
  .sidebar-label {
    transition: all 0.2s;
    font-size: 1em;
  }
  .nav-link {
    display: flex;
    align-items: center;
    gap: 0.5em;
  }
</style>
