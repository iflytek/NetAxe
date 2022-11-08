<template>
  <n-grid cols="3" item-responsive>
    <n-grid-item span="1 400:1 1300:1">
      <n-card title="匹配内容" size="small" :bordered="false" content-style="padding: 5px;">
        <v-ace-editor
          v-model:value="regex_content"
          lang="yaml"
          theme="monokai"
          style="height: 600px"
          :options="ace_option"
        />
      </n-card>
    </n-grid-item>
    <n-grid-item span="1 400:1 1300:1">
      <n-card title="正则表达式" size="small" :bordered="false" content-style="padding: 5px;">
        <template #header-extra>
          <n-space>
            <n-button type="success" size="small" @click="test_regex"> 验证 </n-button>
          </n-space>
        </template>
        <v-ace-editor
          v-model:value="regex_rule"
          lang="yaml"
          theme="monokai"
          style="height: 600px"
          :options="ace_option"
        /> </n-card
    ></n-grid-item>
    <n-grid-item span="1 400:1 1300:1">
      <n-card title="匹配结果" size="small" :bordered="false" content-style="padding: 5px;">
        <v-ace-editor
          v-model:value="regex_result"
          lang="yaml"
          theme="monokai"
          style="height: 600px"
          :options="ace_option"
        />
      </n-card>
    </n-grid-item>
  </n-grid>
</template>

<script setup lang="ts">
  import { ref, onMounted, h, nextTick } from 'vue'
  import { config_center } from '@/api/url'
  import usePut from '@/hooks/useGet'
  import usePatch from '@/hooks/usePatch'
  import usePost from '@/hooks/usePost'
  import { useMessage } from 'naive-ui'
  import { VAceEditor } from 'vue3-ace-editor'
  import 'ace-builds/src-noconflict/mode-yaml'
  import 'ace-builds/src-noconflict/mode-html'
  import 'ace-builds/src-noconflict/theme-chrome'
  import ace from 'ace-builds'
  import modeYamlUrl from 'ace-builds/src-noconflict/mode-yaml?url'
  ace.config.setModuleUrl('ace/mode/yaml', modeYamlUrl)
  import modenunjucksUrl from 'ace-builds/src-noconflict/mode-nunjucks?url'
  ace.config.setModuleUrl('ace/mode/nunjucks', modenunjucksUrl)
  import modeJsonUrl from 'ace-builds/src-noconflict/mode-json?url'
  ace.config.setModuleUrl('ace/mode/json', modeJsonUrl)
  import themeMonokaiUrl from 'ace-builds/src-noconflict/theme-monokai?url'
  ace.config.setModuleUrl('ace/theme/monokai', themeMonokaiUrl)
  const message = useMessage()
  const patch = usePatch()
  const post = usePost()
  const ace_option = ref({ fontSize: 14 })
  const regex_content = ref('')
  const regex_result = ref('')
  const regex_rule = ref('')
  function test_regex() {
    post({
      url: config_center + '/test_regex',
      data: {
        content: regex_content.value,
        regex: regex_rule.value,
      },
    }).then((res) => {
      // console.log(res)
      if (res.code == 200) {
        if (res.data.length > 0) {
          message.success('匹配成功')
          regex_result.value = ''
          res.data.forEach((item) => {
            regex_result.value += item.toString() + '\n'
          })
        } else {
          message.error('匹配失败')
          regex_result.value = ''
        }
      } else {
        regex_result.value = ''
        message.error('解析失败，请检查正则表达式写法问题')
      }
    })
  }
</script>

<style lang="scss" scoped></style>
