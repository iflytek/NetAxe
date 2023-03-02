<template>
  <n-space vertical>
    <n-card>
      <div class="text-lg">
        当前版本号：{{ version }}
        <n-button class="ml-4" type="primary" @click="showContact = true">获取源码</n-button>
      </div>
    </n-card>
    <n-card title="依赖">
      <n-descriptions
        label-placement="top"
        bordered
        :column="4"
        :label-style="{ 'font-weight': 'bold', 'font-size': '16px' }"
      >
        <n-descriptions-item :label="item.label" v-for="item of dependenciesList" :key="item.label">
          {{ item.value }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>
    <n-card title="开发依赖">
      <n-descriptions
        label-placement="top"
        bordered
        :column="4"
        :label-style="{ 'font-weight': 'bold', 'font-size': '16px' }"
      >
        <n-descriptions-item
          :label="item.label"
          v-for="item of devDependenciesList"
          :key="item.label"
        >
          {{ item.value }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>
  </n-space>
</template>

<script lang="ts" setup>
  import { useLayoutStore } from '@/components'
  import useAppInfo from '@/hooks/useAppInfo'
  import { onMounted, reactive, ref } from 'vue'
  import { Close } from '@vicons/ionicons5'
  const { version, dependencies, devDependencies } = useAppInfo()
  const showContact = ref(false)
  const state = useLayoutStore().state
  const dependenciesList = reactive<Record<string, string>[]>([])
  const devDependenciesList = reactive<Record<string, string>[]>([])
  onMounted(() => {
    const depValues = Object.values(dependencies)
    Object.keys(dependencies).map((it, index) => {
      dependenciesList.push({
        label: it,
        value: depValues[index],
      })
    })
    const devDepValues = Object.values(devDependencies)
    Object.keys(devDependencies).map((it, index) => {
      devDependenciesList.push({
        label: it,
        value: devDepValues[index],
      })
    })
  })
</script>
