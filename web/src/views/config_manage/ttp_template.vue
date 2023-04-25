<template>
  <div class="main-container">
    <n-modal v-model:show="add_ttp_modal_show" preset="dialog" :title="ttp_template_title">
      <n-form
        ref="formRef"
        :model="add_ttp_model"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
        size="small"
        :style="{
          maxWidth: '640px',
        }"
      >
        <n-form-item label="名称" path="inputConfigPartName">
          <n-input v-model:value="add_ttp_model.name" placeholder="Input" />
        </n-form-item>
        <n-form-item label="厂商" path="inputConfigVendor">
          <n-select
            v-model:value="add_ttp_model.vendor"
            filterable
            placeholder="厂商"
            :options="config_set_options"
          />
        </n-form-item>
      </n-form>

      <template #action>
        <div style="display: flex; justify-content: flex-end">
          <n-button round type="primary" @click="ttp_template_modal_btn"> 确认 </n-button>
        </div>
      </template>
    </n-modal>
    <n-grid cols="1" item-responsive>
      <n-grid-item span="1 400:1 1300:1">
        <n-space>
          <n-select
            v-model:value="select_config_vendor"
            filterable
            placeholder="选择厂家"
            :options="config_set_options"
            @update:value="select_config_set"
          />
        </n-space>
        <n-divider />
        <n-space vertical :size="12">
          <n-button type="info" size="small" @click="add_ttp_template"> 添加TTP解析模板 </n-button>
          <TableBody>
            <template #header> </template>
            <template #default>
              <n-data-table
                :columns="configParttableColumns"
                :data="config_part_table_data"
                :pagination="pagination"
                :row-key="rowKey"
                :row-props="ConfigPartRowProps"
                default-expand-all
              />
            </template>
          </TableBody>
        </n-space>
      </n-grid-item>
    </n-grid>
    <n-grid cols="3" item-responsive v-if="show_config_part_frame">
      <n-grid-item span="1 400:1 1300:1">
        <n-card title="测试文本" size="huge" :bordered="false" content-style="padding: 0;">
          <v-ace-editor
            v-model:value="device_test_content"
            lang="text"
            theme="monokai"
            style="height: 820px"
            :options="ace_option"
          />
        </n-card>
      </n-grid-item>
      <n-grid-item span="1 400:1 1300:1">
        <n-card title="TTP模板" size="huge" :bordered="false" content-style="padding: 0;">
          <template #header-extra>
            <n-space>
              <n-button type="success" size="small" @click="ttp_render"> 解析测试 </n-button>
            </n-space>
          </template>
          <v-ace-editor
            v-model:value="device_ttp_content"
            lang="nunjucks"
            theme="monokai"
            style="height: 820px"
            :options="ace_option"
          />
          <template #footer></template>
          <template #action> </template>
        </n-card>
      </n-grid-item>
      <n-grid-item span="1 400:1 1300:1">
        <n-card title="解析结果" size="huge" :bordered="false" content-style="padding: 0;">
          <template #header-extra>
            <n-space>
              <n-button type="info" size="small" @click="save_ttp_template"> 保存 </n-button>
            </n-space>
          </template>
          <v-ace-editor
            v-model:value="device_config_render_res"
            lang="json"
            theme="monokai"
            style="height: 820px"
            :wrap="true"
            :options="ace_option"
          />
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>
<script setup lang="ts">
  import { ref, onMounted, h, nextTick } from 'vue'
  import _ from 'lodash'
  import {
    NTag,
    NButton,
    FormInst,
    useMessage,
    FormItemRule,
    DataTableColumn,
    NPopconfirm,
    useDialog,
  } from 'naive-ui'
  import { ModalDialogType } from '@/types/components'
  import { useTableColumn } from '@/hooks/table'
  import useGet from '@/hooks/useGet'
  import usePost from '@/hooks/usePost'
  import usePut from '@/hooks/usePut'
  import usePatch from '@/hooks/usePatch'
  import useDelete from '@/hooks/useDelete'
  import { VAceEditor } from 'vue3-ace-editor'
  import { Terminal } from 'xterm'
  import { FitAddon } from 'xterm-addon-fit'
  import 'xterm/css/xterm.css'
  import 'ace-builds/src-noconflict/mode-yaml'
  import 'ace-builds/src-noconflict/mode-html'
  import 'ace-builds/src-noconflict/theme-chrome'
  import { config_center_api, ttp_parse } from '@/api/url'
  import ace from 'ace-builds'
  import modeYamlUrl from 'ace-builds/src-noconflict/mode-yaml?url'
  ace.config.setModuleUrl('ace/mode/yaml', modeYamlUrl)
  import modenunjucksUrl from 'ace-builds/src-noconflict/mode-nunjucks?url'
  ace.config.setModuleUrl('ace/mode/nunjucks', modenunjucksUrl)
  import modeJsonUrl from 'ace-builds/src-noconflict/mode-json?url'
  ace.config.setModuleUrl('ace/mode/json', modeJsonUrl)
  import themeMonokaiUrl from 'ace-builds/src-noconflict/theme-monokai?url'
  ace.config.setModuleUrl('ace/theme/monokai', themeMonokaiUrl)

  type ConfigPartRowData = {
    id: number
    config_set: number
    name: string
    datetime: string
    method: string
    config_yaml: string
    config_jinja2: string
    config_text: string
  }
  const term: any = ref(null)
  const fitAddon = new FitAddon()
  const term_window = ref()
  const add_config_set_modal_show = ref(false)
  const add_config_set_model = ref({
    name: null,
    vendor: 'H3C',
  })
  const show_config_part_frame = ref(false)
  const add_ttp_modal_show = ref(false)
  const add_ttp_model = ref({
    id: 0,
    name: '',
    ttp_content: '',
    vendor: 'H3C',
  })
  const device_test_content = ref('')
  const device_config_render_res = ref('')
  const device_ttp_content = ref('')
  const config_part_table_data = ref([])
  const select_config_vendor = ref('H3C')
  const select_config_vendor_id = ref(0)
  // 配置模板可选厂家名
  const config_set_options = ref([
    {
      label: 'H3C',
      value: 'H3C',
    },
    {
      label: 'HUAWEI',
      value: 'HUAWEI',
    },
    {
      label: 'Hillstone',
      value: 'Hillstone',
    },
    {
      label: 'Ruijie',
      value: 'Ruijie',
    },
    {
      label: 'Cisco_ios',
      value: 'Cisco_ios',
    },
  ])
  const ace_option = ref({ fontSize: 14 })
  const vendorOption = ref([
    {
      label: 'H3C',
      value: 'H3C',
    },
    {
      label: 'HUAWEI',
      value: 'HUAWEI',
    },
    {
      label: 'Hillstone',
      value: 'Hillstone',
    },
    {
      label: 'Ruijie',
      value: 'Ruijie',
    },
    {
      label: 'Cisco_ios',
      value: 'Cisco_ios',
    },
  ])
  const message = useMessage()
  const dialog = useDialog()
  const get = useGet()
  const put = usePut()
  const post = usePost()
  const api_delete = useDelete()
  const patch = usePatch()
  const pagination = {
    pageSize: 10,
  }
  // 配置模板表模型
  const configParttableColumns = useTableColumn(
    [
      {
        title: '名称',
        key: 'name',
      },
      {
        title: '厂家',
        key: 'vendor',
      },
      {
        title: '更新时间',
        key: 'datetime',
      },
      {
        title: '配置',
        key: 'id',
        render: (rowData) => {
          const del_id = [
            h(
              NButton,
              {
                type: 'info',
                size: 'tiny',
                onClick: edit_config_part.bind(null, rowData),
              },
              () => h('span', {}, '编辑')
            ),
            h(
              NPopconfirm,
              {
                onPositiveClick: () => delete_config_part_row(rowData),
                negativeText: '取消',
                positiveText: '确认',
              },
              {
                trigger: () =>
                  h(
                    NButton,
                    {
                      size: 'tiny',
                      type: 'warning',
                      style: { marginRight: '12px' },
                    },
                    { default: () => '删除' }
                  ),
                default: () => h('span', {}, { default: () => '确认删除？' }),
              }
            ),
          ]
          return del_id
        },
      },
    ],
    {
      align: 'center',
    } as DataTableColumn
  )
  // 新建集群模态框表单模型
  const cluster_model = ref({
    name: '',
    spine: 2,
    leaf: 4,
    vendor: 'H3C',
  })
  const ttp_template_title = ref('添加配置模板')
  // 选择一个配置集合
  function select_config_set() {
    show_config_part_frame.value = false
    get({
      url: config_center_api + 'ttp_template/',
      data: () => {
        return {
          vendor: select_config_vendor.value,
        }
      },
    }).then((res) => {
      if (res.code == 404) {
        message.warning('没有配置项数据')
        config_part_table_data.value = []
      } else {
        config_part_table_data.value = res.results
      }
    })
  }
  function rowKey(rowData: any) {
    return rowData.id
  }
  // 编辑配置模板按钮 打开模态框
  function edit_config_part(row) {
    if (select_config_vendor.value) {
      ttp_template_title.value = '编辑配置模板'
      add_ttp_modal_show.value = true
      add_ttp_model.value.name = row.name
      add_ttp_model.value.id = row.id
    } else {
      message.warning('请选择一个配置集')
    }
  }
  // 删除配置模板按钮
  function delete_config_part_row(row) {
    api_delete({
      url: config_center_api + 'ttp_template/' + row.id + '/',
      data: {},
    }).then((res) => {
      console.log(res)
      if (res.code == 204) {
        message.success(res.message)
        nextTick(() => {
          select_config_set()
        })
      } else {
        message.error(res.message)
      }
    })
  }
  // 添加配置项模态框的确认按钮
  function ttp_template_modal_btn() {
    if (ttp_template_title.value == '编辑配置模板') {
      patch({
        url: config_center_api + 'ttp_template/' + add_ttp_model.value.id + '/',
        data: {
          name: add_ttp_model.value.name,
          vendor: add_ttp_model.value.vendor,
        },
      }).then((res) => {
        if (res.code == 200) {
          message.success(res.msg)
          nextTick(() => {
            select_config_set()
            add_ttp_modal_show.value = false
          })
        } else {
          message.error(res.msg)
        }
      })
    } else {
      post({
        url: config_center_api + 'ttp_template/',
        data: {
          name: add_ttp_model.value.name,
          vendor: add_ttp_model.value.vendor,
        },
      }).then((res) => {
        console.log(res)
        if (res.code == 201) {
          message.success(res.message)
          nextTick(() => {
            select_config_set()
            add_ttp_modal_show.value = false
          })
        } else {
          message.error(res.message)
        }
      })
    }
  }
  // 配置项表格  行点击事件
  const ConfigPartRowProps = (row: ConfigPartRowData) => {
    return {
      style: 'cursor: pointer;',
      onClick: () => {
        show_config_part_frame.value = true
        device_test_content.value = ''
        device_ttp_content.value = row.ttp_content
        device_config_render_res.value = ''
        select_config_vendor_id.value = row.id
      },
    }
  }
  // jinja2模板渲染事件
  function ttp_render() {
    post({
      url: ttp_parse,
      data: {
        test_content: device_test_content.value,
        ttp_template: device_ttp_content.value,
      },
    }).then((res) => {
      console.log(res)
      if (res.code == 200) {
        message.success(res.msg)
        device_config_render_res.value = res.data
      } else {
        message.error(res.msg)
      }
    })
  }
  // 保存jinja2模板
  function save_ttp_template() {
    patch({
      url: config_center_api + 'ttp_template/' + select_config_vendor_id.value + '/',
      data: {
        ttp_content: device_ttp_content.value,
      },
    }).then((res) => {
      if (res.code == 200) {
        message.success(res.message)
      } else {
        message.error(res.message)
      }
    })
  }
  function initTerm() {
    term.value = new Terminal({
      rendererType: 'canvas', //渲染类型
      rows: 40, //行数
      cols: 100, // 不指定行数，自动回车后光标从下一行开始
      convertEol: true, //启用时，光标将设置为下一行的开头
      // scrollback: 50, //终端中的回滚量
      disableStdin: false, //是否应禁用输入
      windowsMode: true, // 根据窗口换行
      cursorStyle: 'underline', //光标样式
      cursorBlink: true, //光标闪烁
      fontFamily: "Monaco, Menlo, Consolas, 'Courier New', monospace",
      theme: {
        foreground: '#ECECEC', //字体
        background: '#181d28', //背景色
        cursor: 'help', //设置光标
        // lineHeight: 20,
      },
    })
    term.value.open(term_window.value)
    term.value.loadAddon(fitAddon)
    // 不能初始化的时候fit,需要等terminal准备就绪,可以设置延时操作
    setTimeout(() => {
      fitAddon.fit()
    }, 5)
    // term.value.reset()
  }
  // 添加配置项按钮，打开模态框
  function add_ttp_template() {
    if (select_config_vendor.value) {
      add_ttp_modal_show.value = true
    } else {
      message.warning('请选择一个配置集')
    }
  }
  onMounted(select_config_set)
</script>
<style lang="scss" scoped>
  .n-form.n-form--inline {
    width: 100%;
    display: inline-flex;
    align-items: flex-start;
    align-content: space-around;
    height: 5px;
  }
</style>
