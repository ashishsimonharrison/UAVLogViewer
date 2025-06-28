<!-- <template>
  <div>
    <button
      class="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 shadow-lg hover:bg-blue-700 focus:outline-none"
      @click="toggle"
      :aria-expanded="open.toString()"
    >
      <svg
        v-if="!open"
        xmlns="http://www.w3.org/2000/svg"
        class="h-7 w-7 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4 8-9 8a9.77 9.77 0 01-4-.83L3 20l1.37-3.63A7.998 7.998 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      <svg
        v-else
        xmlns="http://www.w3.org/2000/svg"
        class="h-7 w-7 text-white"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </button>

    <transition name="slide-fade">
      <div
        v-if="open"
        class="fixed bottom-24 right-6 z-40 flex h-[420px] w-96 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-gray-200 dark:bg-gray-800"
      >
        <ChatPanel :file-id="fileId" @close="toggle" />
      </div>
    </transition>
  </div>
</template>

<script>
import ChatPanel from "./ChatPanel.vue"; 

export default {
  name: "ChatWidget",
  components: { ChatPanel },
  props: {
    /* Pass the uploaded file identifier down from a parent component.
       If you don’t need it, remove this prop in ChatPanel too. */
    fileId: { type: String, required: false },
  },
  data() {
    return { open: false };
  },
  methods: {
    toggle() {
      this.open = !this.open;
    },
  },
};
</script>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s ease;
}
.slide-fade-enter,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
</style> -->

<template>
  <!-- single root wrapper (required in Vue 2) -->
  <div>
    <!-- Floating Action Button (FAB) -->
    <button
      class="chat-fab"
      @click="toggle"
      :aria-expanded="open.toString()"
    >
      <!-- chat-bubble icon (closed state) -->
      <svg
        v-if="!open"
        xmlns="http://www.w3.org/2000/svg"
        width="24" height="24"
        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round"
      >
        <path d="M8 10h.01M12 10h.01M16 10h.01"/>
        <path d="M21 12c0 4.418-4 8-9 8a9.77 9.77 0 0 1-4-.83L3 20l1.37-3.63A7.998 7.998 0 0 1 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
      </svg>

      <!-- × icon (open state) -->
      <svg
        v-else
        xmlns="http://www.w3.org/2000/svg"
        width="24" height="24"
        viewBox="0 0 20 20" fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M4.293 4.293a1 1 0 0 1 1.414 0L10 8.586l4.293-4.293a1 1 0 1 1 1.414 1.414L11.414 10l4.293 4.293a1 1 0 0 1-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 0 1-1.414-1.414L8.586 10 4.293 5.707a1 1 0 0 1 0-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </button>

    <!-- Slide-up chat panel -->
    <transition name="slide-fade">
      <div
        v-show="open"
        class="chat-widget-panel"
        :style="panelVars"
      >
        <!-- your existing chat component -->
        <ChatPanel :file-id="fileId" @close="toggle"/>
      </div>
    </transition>
  </div>
</template>

<script>
import ChatPanel from "./ChatPanel.vue";

export default {
  name: "ChatWidget",
  components: { ChatPanel },
  props: {
    fileId:      { type: String, Number, required: false },
    panelWidth:  { type: [String, Number], default: 384 }, // px or any CSS unit
    panelHeight: { type: [String, Number], default: 420 }
  },
  data() {
    return { open: false };
  },
  computed: {
    /* converts numeric props to “###px”, keeps strings as-is */
    panelVars() {
      const w = typeof this.panelWidth  === "number" ? `${this.panelWidth}px`  : this.panelWidth;
      const h = typeof this.panelHeight === "number" ? `${this.panelHeight}px` : this.panelHeight;
      /* CSS custom properties let the style block read the values cleanly */
      return { "--panel-width": w, "--panel-height": h };
    }
  },
  methods: {
    toggle() { this.open = !this.open; }
  }
};
</script>

<style scoped>
/* ------------------------------------------------------------------
   Floating Action Button
-------------------------------------------------------------------*/
.chat-fab {
  position: fixed;
  bottom: 24px;          /* 1.5 × 16 px */
  right: 24px;
  width: 56px;           /* 3.5 × 16 px */
  height: 56px;
  border-radius: 50%;
  background-color: #0d6efd;        /* same blue as Bootstrap primary */
  color: #fff;
  border: none;
  outline: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  transition: background-color 0.2s ease;
  z-index: 1101;         /* above Bootstrap modals (1050) */
}

.chat-fab:hover {
  background-color: #0b5ed7;        /* slightly darker blue on hover */
}

/* ------------------------------------------------------------------
   Slide-up chat panel
-------------------------------------------------------------------*/
.chat-widget-panel {
  position: fixed;
  bottom: 96px;          /* 56 px FAB + 16 px gap * 2 */
  right: 24px;
  width:  var(--panel-width);
  height: var(--panel-height);
  background-color: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 1100;
}

/* ------------------------------------------------------------------
   enter/leave transition
-------------------------------------------------------------------*/
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.slide-fade-enter,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
</style>
