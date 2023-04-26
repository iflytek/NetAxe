<template>
  <n-notification-provider>
    <n-message-provider container-style="top:55px">
      <router-view />
    </n-message-provider>
  </n-notification-provider>
</template>

<script lang="ts">
  import { defineComponent } from 'vue'

  export default defineComponent({
    name: 'App',
  })
</script>
