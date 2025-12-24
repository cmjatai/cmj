<template>
  <div class="chat-module-layout">
    <!-- Sidebar / Offcanvas for Mobile -->
    <div class="chat-sidebar d-none d-md-block">
      <ChatHistoryList />
    </div>

    <!-- Mobile Toggle Button (Visible only on small screens) -->
    <button
      class="btn btn-primary d-md-none position-fixed m-3"
      style="z-index: 1050; bottom: 0; right: 0;"
      type="button"
      data-bs-toggle="offcanvas"
      data-bs-target="#chatHistoryOffcanvas"
      aria-controls="chatHistoryOffcanvas"
    >
      <FontAwesomeIcon icon="history" />
    </button>

    <!-- Offcanvas for Mobile -->
    <div
      class="offcanvas offcanvas-start d-md-none"
      tabindex="-1"
      id="chatHistoryOffcanvas"
      aria-labelledby="chatHistoryOffcanvasLabel"
    >
      <div class="offcanvas-header">
        <h5
          class="offcanvas-title"
          id="chatHistoryOffcanvasLabel"
        >
          Histórico
        </h5>
        <button
          type="button"
          class="btn-close text-reset"
          data-bs-dismiss="offcanvas"
          aria-label="Close"
        />
      </div>
      <div class="offcanvas-body p-0">
        <ChatHistoryList />
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="chat-main-content">
      <router-view v-slot="{ Component }">
        <component :is="Component" />
      </router-view>
    </div>
  </div>
</template>

<script setup>
import ChatHistoryList from './ChatHistoryList.vue'
</script>

<style scoped>
.chat-module-layout {
  display: flex;
  height: 100%; /* Ensure it takes full height of parent */
  width: 100%;
  overflow: hidden;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.chat-sidebar {
  width: 300px;
  flex-shrink: 0;
  border-right: 1px solid #dee2e6;
  height: 100%;
  overflow-y: auto;
}

.chat-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  position: relative;
}
</style>
