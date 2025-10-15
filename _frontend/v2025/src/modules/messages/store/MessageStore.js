import { defineStore } from "pinia";

export const useMessageStore = defineStore("messageStore", {
  state: () => ({
    messages: [],
    id: 0,
  }),
  getters: {
    getMessages: (state) => state.messages,
  },
  actions: {
    addMessage(message) {
      message.id = this.id++;
      this.messages.unshift(message);
    },
    shiftMessage() {
      return this.messages.shift();
    },
    removeMessage(id) {
      this.messages = this.messages.filter((message) => message.id !== id);
    },
  },
})
