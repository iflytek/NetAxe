<template>
  <n-notification-provider>
    <n-message-provider placement="bottom-right">
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
