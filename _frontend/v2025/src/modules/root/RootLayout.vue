<template>
  <div :class="['root-layout',]">
    <header>
      <div class="header-left d-lg-none">
        <slot name="header-left" />
      </div>

      <div class="header-main">
        <div class="brand">
          <slot name="brand" />
        </div>
        <div class="header-detail">
          <slot name="header-detail" />
        </div>
      </div>

      <div class="header-right">
        <slot name="header-right" />
      </div>
    </header>

    <aside class="sideleft">
      <slot name="sideleft" />
    </aside>

    <main class="main">
      <slot name="main" />
    </main>

    <div class="sideright">
      <slot name="sideright" />
    </div>
  </div>
</template>

<script setup>
// 1. Imports
import { onMounted, inject } from 'vue'

const EventBus = inject('EventBus')

// 2. Composables

// 3. Props & Emits

// 4. State & Refs

// 5. Computed Properties

// 6. Watchers

// 7. Events & Lifecycle Hooks
onMounted(() => {
  document.addEventListener('wheel', handleDisableAutoRolagem, { passive: true })
  document.addEventListener('touchmove', handleDisableAutoRolagem, { passive: true })
})
const handleDisableAutoRolagem = (event) => {
  EventBus.emit('disable-auto-rolagem')
}

// 8. Functions
</script>
<style lang="scss">
body {
  overflow-x: hidden;
}
.root-layout {
  user-select: none;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;

  font-size: 1rem;
  line-height: 1;

  display: grid;

  grid-template-areas:
    "header header header"
    "sideleft main sideright";
  grid-template-rows: auto 1fr;
  grid-template-columns: 0 1fr 0;

  header {
    grid-area: header;
    display: flex;
    align-items: center;
    position: fixed;
    left: 0;
    right: 0;
    justify-content: space-between;
    background-color: var(--cmj-background-color);
    border-bottom: 1px solid var(--bs-border-color-translucent);
    z-index: 3;
    .header-left, .header-right {
      width: 3em;
      height: 3em;
      z-index: 1;
    }
    .header-left {
      height: 100%;
      button {
        width: 100%;
        height: 100%;
        border: 0;
        background: none;
        &:hover {
          background-color: var(--bs-body-bg);
        }
      }
    }
    .header-main {
      flex-grow: 2;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
    }
    .header-detail {
      display: flex;
      justify-content: flex-end;
      gap: 0.5em;
      height: 100%;
      margin-top: -0.5em;
      padding-right: 0.5em;
      .accessibility {
        .btn {
          padding: 0 0.7em;
        }
      }
    }
  }

  main {
    grid-area: main;
    // background-color: #eee;
    margin-top: 3em;
  }

  aside {
    grid-area: sideleft;
    position: relative;
    display: none
  }
  .sideright {
    grid-area: sideright;
    position: relative;
    display: none;
  }
}

@media screen and (min-width: 480px) {
  .root-layout {
    .header-main {
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
    }
  }
}

@media screen and (min-width: 768px) {
  .root-layout {
    grid-template-columns: 3em 1fr 3em;

    aside {
      display: flex;
    }
    .sideright {
      display: flex;
    }
  }
}
</style>
