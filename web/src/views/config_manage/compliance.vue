<template>
  <div class="main-container">
    <n-card>
      <n-tabs
        class="card-tabs"
        default-value="compliance_rule"
        @update:value="tab_change"
        size="large"
        animated
        style="margin: 0 -4px"
        pane-style="padding-left: 4px; padding-right: 4px; box-sizing: border-box;"
      >
        <n-tab-pane name="compliance_rule" display-directive="show" tab="规则配置">
          <n-modal
            v-model:show="add_config_part_modal_show"
            preset="dialog"
            :title="config_rule_title"
          >
            <n-form
              ref="formRef"
              :model="config_compliance_model"
              label-placement="left"
              label-width="auto"
              require-mark-placement="right-hanging"
              size="small"
              :style="{
                maxWidth: '640px',
              }"
            >
              <n-form-item label="名称" path="inputName">
                <n-input v-model:value="config_compliance_model.name" placeholder="Input" />
              </n-form-item>
              <n-form-item label="厂家" path="inputVendor">
                <n-select
                  v-model:value="config_compliance_model.vendor"
                  placeholder="Select"
                  :options="vendorOption"
                />
              </n-form-item>
              <n-form-item label="类型" path="inputCategory">
                <n-select
                  v-model:value="config_compliance_model.category"
                  placeholder="Select"
                  :options="categoryOption"
                />
              </n-form-item>
              <n-form-item label="模式" path="inputPattern">
                <n-select
                  v-model:value="config_compliance_model.pattern"
                  placeholder="Select"
                  :options="patternOption"
                />
              </n-form-item>
              <n-form-item label="表达式" path="inputRegex">
                <n-input
                  v-model:value="config_compliance_model.regex"
                  placeholder="支持配置块也支持正则表达式"
                  type="textarea"
                  :autosize="{
                    minRows: 1,
                    maxRows: 50,
                  }"
                />
              </n-form-item>
              <n-form-item label="是否修正" path="inputRepair">
                <n-switch v-model:value="config_compliance_model.is_repair" />
              </n-form-item>
              <n-form-item label="修复命令" path="inputRepair_cmds">
                <n-input
                  v-model:value="config_compliance_model.repair_cmds"
                  placeholder="修复配置命令"
                  type="textarea"
                  :autosize="{
                    minRows: 1,
                    maxRows: 50,
                  }"
                />
              </n-form-item>
            </n-form>

            <template #action>
              <div style="display: flex; justify-content: flex-end">
                <n-button round type="primary" @click="config_rule_btn"> 确认 </n-button>
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
                  :options="vendorOption"
                  @update:value="select_config_compliance"
                />
              </n-space>
              <n-divider />
              <n-space vertical :size="12">
                <n-button type="info" size="small" @click="add_config_rule"> 添加合规项 </n-button>
                <TableBody>
                  <template #header> </template>
                  <template #default>
                    <n-data-table
                      :columns="configParttableColumns"
                      :data="config_part_table_data"
                      :pagination="pagination"
                      :row-key="rowKey"
                      default-expand-all
                    />
                  </template>
                </TableBody>
              </n-space>
            </n-grid-item>
          </n-grid>
        </n-tab-pane>
        <n-tab-pane name="compliance_result" display-directive="show" tab="检查结果">
          <Compliance_table />
        </n-tab-pane>
        <n-tab-pane name="regex_test" display-directive="show" tab="测试规则">
          <RegexTest />
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>
<script setup lang="ts">
  import { ref, onMounted, h, nextTick } from 'vue'
  import _ from 'lodash'
  import { NTag, NButton, useMessage, DataTableColumn, NPopconfirm, useDialog } from 'naive-ui'
  import { useTableColumn } from '@/hooks/table'
  import useGet from '@/hooks/useGet'
  import usePost from '@/hooks/usePost'
  import usePut from '@/hooks/usePut'
  import usePatch from '@/hooks/usePatch'
  import useDelete from '@/hooks/useDelete'
  import { config_compliance } from '@/api/url'
  import Compliance_table from './compliance_table.vue'
  import RegexTest from './regexTest.vue'
  type ConfigComplianceRowData = {
    id: number
    name: string
    vendor: string
    category: string
    pattern: string
    datetime: string
    is_repair: boolean
    repair_cmds: string
  }
  const add_config_part_modal_show = ref(false)
  const config_compliance_model = ref({
    id: 0,
    name: '',
    vendor: '',
    category: '',
    regex: '',
    pattern: '',
    is_repair: false,
    repair_cmds: '',
  })
  const config_part_table_data = ref([])
  const select_config_vendor = ref('H3C')
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
      label: 'Cisco',
      value: 'Cisco',
    },
  ])
  const categoryOption = ref([
    {
      label: '交换机',
      value: 'switch',
    },
    {
      label: '防火墙',
      value: 'firewall',
    },
    {
      label: '路由器',
      value: 'router',
    },
  ])
  const patternOption = ref([
    {
      label: '匹配-合规 反之 不合规',
      value: 'match-compliance',
    },
    {
      label: '不匹配-合规 反之 不合规',
      value: 'mismatch-compliance',
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
        title: '类型',
        key: 'category',
        render: (rowData) => {
          return rowData.category
        },
      },
      {
        title: '模式',
        key: 'pattern',
      },
      {
        title: '更新时间',
        key: 'datetime',
      },
      {
        title: '是否修正',
        key: 'is_repair',
        render: (rowData) => {
          if (rowData.is_repair) {
            return '是'
          }
          return '否'
        },
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
  const config_rule_title = ref('新建规则')
  function tab_change(value) {
    console.log(value)
  }
  // 选择一个配置集合
  function select_config_compliance() {
    get({
      url: config_compliance,
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
      config_rule_title.value = '编辑规则'
      add_config_part_modal_show.value = true
      config_compliance_model.value.name = row.name
      config_compliance_model.value.id = row.id
      config_compliance_model.value.vendor = row.vendor
      config_compliance_model.value.category = row.category
      config_compliance_model.value.regex = row.regex
      config_compliance_model.value.pattern = row.pattern
      config_compliance_model.value.is_repair = row.is_repair
      config_compliance_model.value.repair_cmds = row.repair_cmds
    } else {
      message.warning('请选择一个配置集')
    }
  }
  // 删除配置模板按钮
  function delete_config_part_row(row) {
    api_delete({
      url: config_compliance + '/' + row.id + '/',
      data: {},
    }).then((res) => {
      if (res.code == 204) {
        message.success(res.message)
        nextTick(() => {
          select_config_compliance()
        })
      } else {
        message.error(res.message)
      }
    })
  }
  // 添加配置项模态框的确认按钮
  function config_rule_btn() {
    if (config_rule_title.value == '编辑规则') {
      patch({
        url: config_compliance + '/' + config_compliance_model.value.id + '/',
        data: {
          name: config_compliance_model.value.name,
          vendor: config_compliance_model.value.vendor,
          category: config_compliance_model.value.category,
          regex: config_compliance_model.value.regex,
          pattern: config_compliance_model.value.pattern,
        },
      }).then((res) => {
        if (res.code == 200) {
          message.success(res.message)
          nextTick(() => {
            select_config_compliance()
            add_config_part_modal_show.value = false
          })
        } else {
          message.error(res.message)
        }
      })
    } else {
      post({
        url: config_compliance + '/',
        data: config_compliance_model.value,
      }).then((res) => {
        if (res.code == 201) {
          message.success(res.message)
          nextTick(() => {
            select_config_compliance()
            add_config_part_modal_show.value = false
          })
        } else {
          message.error(res.message)
        }
      })
    }
  }
  // 添加配置项按钮，打开模态框
  function add_config_rule() {
    if (select_config_vendor.value) {
      config_rule_title.value = '新建规则'
      add_config_part_modal_show.value = true
    } else {
      message.warning('请选择一个配置集')
    }
  }
  onMounted(select_config_compliance)
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
