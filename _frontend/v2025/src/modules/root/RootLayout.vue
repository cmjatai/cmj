<template>
  <div :class="['root-layout',]">
    <header>

      <div class="header-left d-lg-none">
        <slot name="header-left"></slot>
      </div>

      <div class="header-main">
        <div class="brand">
          <slot name="brand"></slot>
        </div>
        <div class="header-detail">
          <slot name="header-detail"></slot>
        </div>
      </div>

      <div class="header-right">
        <slot name="header-right"></slot>
      </div>

    </header>

    <aside class="sideleft">
      <slot name="sideleft"></slot>
    </aside>

    <main class="main">
      <slot name="main"></slot>
    </main>

    <div class="sideright">
      <slot name="sideright"></slot>
    </div>
  </div>
</template>

<script setup>
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
body {
  overflow: hidden;
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
  position: fixed;

  grid-template-areas:
    "header header header"
    "sideleft main sideright";
  grid-template-rows: 3em 1fr;
  grid-template-columns: 0 1fr auto;
}

header {
  grid-area: header;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--bs-border-color-translucent);
  // background-color: var(--bs-body-bg);
  z-index: 1000;
  // background-color: #ddd;
  .header-left, .header-right {
    width: 3em;
    height: 3em;
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
    height: 100%;
    .brand {
      height: 100%;
      display: flex;
      width: 100%;
    }
  }
}

main {
  grid-area: main;
  // background-color: #eee;
  overflow-y: auto;
}

aside {
  grid-area: sideleft;
}

@media screen and (min-width: 992px) {
  .root-layout {
    grid-template-columns: 3em 1fr auto;
  }
}
</style>
