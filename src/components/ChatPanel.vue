<template>
  <div class="chat-panel">
    <div class="messages">
      <div v-for="m in messages" :key="m.id"
           :class="['bubble', m.role]">
        <span v-html="m.text"></span>
      </div>
    </div>

    <form class="input-row" @submit.prevent="handleSend">
      <input v-model="draft"
             placeholder="Ask a question about the flight…"
             autocomplete="off" />
      <button :disabled="sending">Send</button>
    </form>
  </div>
</template>

<script>
let nextId = 0

export default {
    name: 'ChatPanel',
    props: {
        fileId: { type: String, required: true } // passed in from parent view
    },
    data () {
        return {
            draft: '',
            sending: false,
            messages: [
                {
                    id: nextId++,
                    role: 'assistant',
                    text: 'Hello! I can answer questions about your flight. ' +
                          'Just ask me anything you want to know.'
                }
            ]
        }
    },
    methods: {
        async handleSend () {
            const q = this.draft.trim()
            if (!q) return
            this.messages.push({ id: nextId++, role: 'user', text: q })
            this.draft = ''
            this.sending = true

            try {
                const res = await fetch(`/chat/${this.fileId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ q })
                })
                const data = await res.json()
                this.messages.push({
                    id: nextId++, role: 'assistant', text: data.answer || '(no reply)'
                })
            } catch (err) {
                this.messages.push({
                    id: nextId++,
                    role: 'assistant',
                    text: '⚠️ Error talking to backend: ' + err.message
                })
            } finally {
                this.sending = false
                this.$nextTick(() => {
                    const box = this.$el.querySelector('.messages')
                    box.scrollTop = box.scrollHeight
                })
            }
        }
    }
}
</script>

<style scoped>
.chat-panel { display:flex; flex-direction:column; height:100%; }
.messages   { flex:1; overflow:auto; padding:8px; }
.bubble     { max-width:80%; margin:4px 0; padding:6px 10px; border-radius:8px; }
.bubble.user       { background:#409EFF; color:rgb(0, 0, 0); margin-left:auto; }
.bubble.assistant  { background:#06a7e7; }
.input-row { display:flex; border-top:1px solid #eee; }
input { flex:1; padding:8px; border:none; outline:none; }
button{ padding:8px 12px; }
</style>
