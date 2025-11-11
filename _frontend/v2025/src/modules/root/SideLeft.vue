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
          <router-link
            :to="{ name: link.route }"
            class="nav-link"
            @click="closeOffCanvas('#menuSideLeft')"
            >
            <b-img
              v-if="link.image"
              :src="link.image"
              fluid
              rounded="0"
              class=""
            />
            <FontAwesomeIcon
              v-else-if="link.icon"
              :icon="link.icon"
              class=""
            />
            <span>{{ link.texto }}</span>
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
        class="nav-item"
      >
        <span class="toggle-btn">☰</span>
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
            class=""
          />
          <FontAwesomeIcon
            v-else-if="link.icon"
            :icon="link.icon"
            class=""
          />
          <span class="sidebar-label">{{ link.texto }}</span>
        </router-link>
      </li>
      <!-- Outras opções -->
    </ul>
  </div>
</template>

<script setup>
// 1. Imports
import { onMounted, ref, computed } from 'vue'
import * as bootstrap from 'bootstrap'
// 2. Composables

// 3. Props & Emits

// 4. State & Refs
const sidebar = ref(null)
const toggleSidebar = ref(null)
const links = ref([
  {
    icon: 'home',
    route: 'app_vue_v2025',
    texto: 'Início'
  },
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
    route: 'sessao_plenaria_list_link',
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
const closeOffCanvas = (selector) => {
    const offcanvasElement = document.getElementById(selector.replace('#', ''))
    const offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(offcanvasElement)
    offcanvasInstance.hide()
}
</script>
<style lang="scss">
  .sidebar {
    position: fixed;
    top: 3em;
    transition: all 0.2s;
    background-color: var(--cmj-background-color);
    border-right: 1px solid var(--bs-border-color-translucent);
    bottom: 0;
    z-index: 2;
    .toggle-btn {
      cursor: pointer;
      padding: 0.5em;
      display: block;
      &:hover {
        background-color: var(--nav-bg-hover-color);
        color: var(--nav-text-hover-color);
      }
    }

    .nav-item {
      text-align: center;
    }

    .nav-link {
      margin: 0;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      height: 2em;
      white-space: nowrap;

      img {
        padding: 0.5em;
        width: 3em;
      }

      svg {
        width: 3em;
      }

      &:hover {
        background-color: var(--nav-bg-hover-color);
        color: var(--nav-text-hover-color);
      }
    }

    &.collapsed {
      width: 3em;
      .sidebar-label {
        font-size: 0em;
      }
    }

    .sidebar-label {
      transition: all 0.2s;
      font-size: 1em;
      padding-right: 1em;
    }
  }
</style>
