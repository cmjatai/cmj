<template>
  <div
    class="offcanvas offcanvas-start d-lg-none"
    tabindex="-1"
    id="menuSideLeft"
    aria-labelledby="menuSideLeftLabel"
  >
    <div class="offcanvas-header">
      <h5 id="menuSideLeftLabel">Menu</h5>
      <button
        type="button"
        class="btn-close"
        data-bs-dismiss="offcanvas"
        aria-label="Fechar"
      />
    </div>
    <div class="offcanvas-body">
      <ul class="nav flex-column">
        <li class="nav-item">
          <a class="nav-link" href="#">
            <i class="bi bi-house"></i> <span class="sidebar-label">Home</span>
          </a>
        </li>
        <!-- Outras opções -->
      </ul>
    </div>
  </div>
  <div id="sidebar" class="sidebar d-none d-lg-flex flex-column collapsed">
    <ul class="nav flex-column">
      <li id="toggleSidebar" class="nav-item toggle-btn">
        <span class="nav-link">☰</span>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="#">
          <i class="bi bi-house"></i> <span class="sidebar-label">Sessão Plenária</span>
        </a>
        <a class="nav-link" href="#">
          <i class="bi bi-house"></i> <span class="sidebar-label">Eventos e Paineis</span>
        </a>
      </li>
      <!-- Outras opções -->
    </ul>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // converter para evento vue
  const sidebar = document.getElementById('sidebar')
  const toggleBtn = document.getElementById('toggleSidebar')
  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed')
  })
})

// 1. Imports

// 2. Composables

// 3. Props & Emits

// 4. State & Refs

// 5. Computed Properties

// 6. Watchers

// 7. Events & Lifecycle Hooks

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
