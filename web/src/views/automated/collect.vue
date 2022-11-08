<template>
  <div class="main-container">
    <TableBody>
      <template #header>
        <TableHeader
          :show-filter="false"
          title="查询条件"
          @search="onSearch"
          @reset-search="onResetSearch"
        >
          <template #search-content> </template>
          <template #table-config>
            <TableConfig @update-border="onUpdateBorder" @refresh="doRefresh" />
            <SortableTable class="ml-4" :columns="tableColumns" @update="onUpdateTable" />
          </template>
          <template #top-right>
            <n-button type="info" size="small" @click="new_collect_show = true"
              >新建采集方案</n-button
            >
            <n-button type="warning" size="small" @click="chart_show = true"
              >采集方案运营数据
            </n-button>
          </template>
        </TableHeader>
      </template>
      <template #default>
        <DataForm
          ref="searchForm"
          :form-config="{
            labelWidth: 60,
          }"
          :options="conditionItems"
          preset="grid-item"
        />
        <n-space class="control_button">
          <n-button type="info" size="small" @click="doRefresh()">查询</n-button>
          <n-button type="warning" size="small">重置</n-button>
        </n-space>
        <n-data-table
          :loading="tableLoading"
          :data="dataList"
          :columns="tableColumns"
          :single-line="!bordered"
          :row-key="rowKey"
        />
      </template>
      <template #footer>
        <TableFooter :pagination="pagination" />
      </template>
    </TableBody>
    <ModalDialog
      ref="modalDialog"
      title="采集命令修改"
      @confirm="changeCommandsConfirm"
      :style="{ height: '620px', width: '500px' }"
    >
      <template #content>
        <!-- <DataForm ref="itemDataFormRef"
                          :form-config="{ labelWidth: 60}"
                          preset="form-item" :options="itemFormOptions"/> -->
        <v-ace-editor
          v-model:value="commands_value"
          lang="yaml"
          theme="monokai"
          style="height: 500px"
          :options="ace_option"
        />
      </template>
    </ModalDialog>
    <ModalDialog
      ref="edit_modalDialog"
      title="编辑采集方案"
      @confirm="EditConfirm"
      :style="{ height: '600px', width: '500px' }"
    >
      <template #content>
        <DataForm
          ref="itemDataFormRef"
          :form-config="{ labelWidth: 100 }"
          preset="form-item"
          :options="itemFormOptions"
          label-align="left"
        />
      </template>
    </ModalDialog>
    <n-modal
      v-model:show="chart_show"
      preset="dialog"
      header-style="padding: 10px 20px"
      title="采集方案运营数据"
      :style="{ height: '380px', width: '1300px' }"
    >
      <n-grid x-gap="12" :cols="1">
        <n-gi>
          <CollectionPlanChart ref="collectionPlanChart" />
        </n-gi>
      </n-grid>
    </n-modal>
    <n-modal
      v-model:show="new_collect_show"
      preset="card"
      header-style="padding: 10px 20px"
      title="新建采集方案"
      :style="{ height: '580px', width: '500px' }"
    >
      <n-form label-align="left" label-placement="left" :model="new_collect_form" label-width="120">
        <n-form-item label="厂商">
          <n-select
            v-model:value="new_collect_form.vendor"
            filterable
            placeholder="勾选厂商"
            @update:value="get_class_by_vendor()"
            :options="vendor_options"
          >
          </n-select>
        </n-form-item>
        <n-form-item label="方案名称">
          <n-input v-model:value="new_collect_form.name" clearable />
        </n-form-item>
        <n-form-item label="备注">
          <n-input v-model:value="new_collect_form.memo" clearable />
        </n-form-item>
        <n-form-item label="Netconf连接类">
          <n-select
            v-model:value="new_collect_form.netconf_class"
            filterable
            placeholder="勾选Netconf连接类"
            @update:value="select_class_get_method_"
            :options="class_options"
          >
          </n-select>
        </n-form-item>
        <n-form-item label="Netconf方法">
          <n-select
            v-model:value="new_collect_form.netconf_method"
            filterable
            multiple
            placeholder="勾选Netconf方法"
            :options="method_options"
          >
          </n-select>
        </n-form-item>
      </n-form>

      <n-space style="float: right; padding-top: 20px">
        <n-button type="warning" size="tiny"> 取消</n-button>
        <n-button type="info" size="tiny" @click="new_collect_submit()"> 确认</n-button>
      </n-space>
    </n-modal>
  </div>
</template>

<script lang="ts">
  import { deviceCollect, getCollection_planList } from '@/api/url'
  import {
    TableActionModel,
    useTable,
    useRenderAction,
    useTableColumn,
    usePagination,
  } from '@/hooks/table'
  import { defineComponent, h, nextTick, onMounted, reactive, ref, shallowReactive } from 'vue'
  import _ from 'lodash'
  import {
    DataTableColumn,
    NInput,
    NSelect,
    SelectOption,
    useDialog,
    useMessage,
    NForm,
    NFormItem,
    NButton,
  } from 'naive-ui'
  import { DataFormType, ModalDialogType, FormItem, TablePropsType } from '@/types/components'
  import usePost from '@/hooks/usePost'
  import { renderTag } from '@/hooks/form'
  import useGet from '@/hooks/useGet'
  import usePatch from '@/hooks/usePatch'
  import usePut from '@/hooks/usePut'
  import { sortColumns } from '@/utils'
  import { Terminal } from 'xterm'
  import CollectionPlanChart from './chart/CollectionPlanChart.vue'
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

  export default defineComponent({
    name: 'collect',
    components: {
      CollectionPlanChart,
      VAceEditor,
    },
    setup() {
      const ace_option = ref({ fontSize: 14 })
      const commands_value = ref('')
      const vendor_options = [
        { value: '', label: '' },
        { value: 'H3C', label: '华三' },
        { value: 'Huawei', label: '华为' },
        { value: 'Hillstone', label: '山石网科' },
        { value: 'Maipu', label: '迈普' },
        { value: 'Ruijie', label: '锐捷' },
        { value: 'Centec', label: '盛科' },
        { value: 'Mellanox', label: 'Mellanox' },
        { value: 'Cisco', label: '思科' },
      ]
      const class_options = shallowReactive([]) as Array<any>
      const method_options = shallowReactive([]) as Array<any>
      const selectValues = ref('')
      const itemFormOptions = [
        {
          key: 'vendor',
          label: '厂商',
          value: ref(null),
          optionItems: [
            { value: '', label: '' },
            { value: 'H3C', label: '华三' },
            { value: 'Huawei', label: '华为' },
            { value: 'Hillstone', label: '山石网科' },
            { value: 'Maipu', label: '迈普' },
            { value: 'Ruijie', label: '锐捷' },
            { value: 'Centec', label: '盛科' },
            { value: 'Mellanox', label: 'Mellanox' },
            { value: 'Cisco', label: '思科' },
          ],
          render: (formItem) => {
            return h(NSelect, {
              options: formItem.optionItems as Array<SelectOption>,
              value: formItem.value.value,
              placeholder: '请选择厂商',
              filterable: true,
              onUpdateValue: (val) => {
                formItem.value.value = val
              },
            })
          },
        },
        {
          key: 'name',
          label: '方案名',
          value: ref(''),
          render: (formItem) => {
            return h(NInput, {
              value: formItem.value.value,
              onUpdateValue: (val) => {
                formItem.value.value = val
              },
              placeholder: '',
            })
          },
        },
        {
          key: 'memo',
          label: '备注',
          value: ref(''),
          render: (formItem) => {
            return h(NInput, {
              value: formItem.value.value,
              onUpdateValue: (val) => {
                formItem.value.value = val
              },
              placeholder: '',
            })
          },
        },
        {
          key: 'netconf_class',
          label: 'Netconf连接类',
          value: ref(null),
          optionItems: shallowReactive([] as Array<SelectOption>),
          render: (formItem) => {
            return h(NSelect, {
              options: formItem.optionItems as Array<SelectOption>,
              value: formItem.value.value,
              required: true,
              filterable: true,
              placeholder: '请选择Netconf连接类',
              onUpdateValue: (val) => {
                formItem.value.value = val
              },
              'on-update:value': get_method_by_class.bind(formItem.value.value),
            })
          },
        },
        {
          key: 'netconf_method',
          label: 'Netconf方法',
          value: ref(null),
          optionItems: shallowReactive([] as Array<SelectOption>),
          render: (formItem) => {
            return h(NSelect, {
              options: formItem.optionItems as Array<SelectOption>,
              value: formItem.value.value,
              filterable: true,
              maxTagCount: 3,
              multiple: true,
              required: true,
              placeholder: '请选择netconf_method',
              onUpdateValue: (val) => {
                formItem.value.value = val
              },
            })
          },
        },
      ] as Array<FormItem>
      const new_collect_show = ref(false)
      const new_collect_form = ref({
        vendor: '',
        name: '',
        memo: '',
        netconf_class: '',
        netconf_method: '[]',
      })
      const conditionItems: Array<FormItem> = [
        {
          key: 'vendor',
          label: '供应商',
          value: ref(null),
          optionItems: [
            { value: '', label: '' },
            { value: 'H3C', label: '华三' },
            { value: 'Huawei', label: '华为' },
            { value: 'Hillstone', label: '山石网科' },
            { value: 'Maipu', label: '迈普' },
            { value: 'Ruijie', label: '锐捷' },
            { value: 'Centec', label: '盛科' },
            { value: 'Mellanox', label: 'Mellanox' },
            { value: 'Cisco', label: '思科' },
          ],
          render: (formItem) => {
            return h(NSelect, {
              options: formItem.optionItems as Array<SelectOption>,
              value: formItem.value.value,
              filterable: true,
              placeholder: '请选择供应商',
              onUpdateValue: (val) => {
                formItem.value.value = val
              },
              'on-update:value': get_info_by_vendor.bind(formItem.value.value),
            })
          },
        },
      ]
      const table = useTable()
      const pagination = usePagination(doRefresh)
      pagination.pageSize = 10
      pagination.page = 1
      // pagination.limit = 10
      // pagination.start = 0
      const chart_show = ref(false)
      const searchForm = ref<DataFormType | null>(null)
      const message = useMessage()
      const naiveDailog = useDialog()
      const tableColumns = reactive(
        useTableColumn(
          [
            {
              title: '厂商',
              key: 'vendor',
              width: '100px',
            },
            {
              title: '方案名称',
              key: 'name',
              width: '150px',
            },
            {
              title: 'Netconf类',
              key: 'netconf_class',
              width: '150px',
            },

            {
              title: 'CMD命令',
              key: 'commands',
              width: 250,
              render: (rowData) => {
                rowData.commands = JSON.parse(rowData.commands)
                // return rowData.commands
                // return h('div',null,rowData.commands)
                if (typeof rowData.commands === 'object') {
                  // return rowData.ans_group_hosts.map((item) =>{return (`<li>{{$item}}}</li>`) })
                  return h(
                    'div',
                    {},
                    rowData.commands.map((item) => {
                      return h('p', {}, item)
                    })
                  )
                }
              },
            },
            {
              title: 'netconf方法',
              key: 'netconf_method',
              render: (rowData) => {
                // rowData.netconf_method = JSON.parse(rowData.netconf_method).join(',').replaceAll(/,/g, '\n')
                // return rowData.netconf_method
                rowData.netconf_method = JSON.parse(rowData.netconf_method)
                // return rowData.commands
                // return h('div',null,rowData.commands)
                if (typeof rowData.netconf_method === 'object') {
                  // return rowData.ans_group_hosts.map((item) =>{return (`<li>{{$item}}}</li>`) })
                  return h(
                    'div',
                    {},
                    rowData.netconf_method.map((item) => {
                      return h('p', {}, item)
                    })
                  )
                }
              },
            },
            {
              title: '备注',
              key: 'memo',
              width: '150px',
            },

            {
              title: '修改下发命令',
              key: 'actions',
              render: (rowData) => {
                return h(
                  NButton,
                  { onClick: change_commands.bind(null, rowData), type: 'info', size: 'tiny' },
                  () => h('span', {}, '修改下发命令')
                )
              },
            },
            {
              title: '编辑采集方案',
              key: 'actions',
              render: (rowData) => {
                return h(
                  NButton,
                  { onClick: edit_collect_info.bind(null, rowData), type: 'warning', size: 'tiny' },
                  () => h('span', {}, '编辑采集方案')
                )
              },
            },
          ],
          {
            align: 'center',
          } as DataTableColumn
        )
      )
      const itemDataFormRef = ref<DataFormType | null>(null)
      const searchDataFormRef = ref<DataFormType | null>(null)
      const modalDialog = ref<ModalDialogType | null>(null)
      const edit_modalDialog = ref<ModalDialogType | null>(null)
      const current_row = ref({
        name: ref(''),
        memo: ref(''),
        vendor: ref(''),
        netconf_class: ref(''),
        netconf_method: ref(null),
        id: ref(0),
      })
      const WebsshmodalDialog = ref<ModalDialogType | null>(null)
      const show_password_modalDialog = ref<ModalDialogType | null>(null)
      const account_modalDialog = ref<ModalDialogType | null>(null)
      const rowData = ref<Object | null>(null)
      const second_password = ref('')
      const get = useGet()
      const post = usePost()
      const patch = usePatch()
      const put = usePut()

      function onSearch() {
        //console.log(searchForm.value?.generatorParams())
      }

      function onResetSearch() {
        searchForm.value?.reset()
      }

      function onUpdateBorder(isBordered: boolean) {
        table.bordered.value = isBordered
      }

      function onUpdateTable(newColumns: Array<TablePropsType>) {
        sortColumns(tableColumns, newColumns)
      }

      function doRefresh() {
        get({
          url: getCollection_planList,
          data: () => {
            return {
              start: (pagination.page - 1) * pagination.pageSize,
              limit: pagination.pageSize,
              _: Date.now(),
            }
          },
        }).then((res) => {
          //  //console.log(res)
          table.handleSuccess(res)
          pagination.setTotalSize(res.count || 10)
        })
      }

      function changeCommandsConfirm() {
        //console.log(current_row.value)
        console.log('commands_value', commands_value.value.replaceAll('\n', ',').split(','))
        var commands_array = commands_value.value.replaceAll('\n', ',').split(',')
        var post_data = new FormData()
        post_data.append('commands', JSON.stringify(commands_array))
        post_data.append('name', current_row.value['name'])
        patch({
          url: getCollection_planList + '/' + current_row.value['id'] + '/',
          data: post_data,
        }).then((res) => {
          if (res.code === 200) {
            message.success(res.message)
            modalDialog.value!.toggle()
            doRefresh()
          } else {
            message.error(res.message)
          }
        })
      }

      function EditConfirm() {
        console.log(current_row.value)
        // console.log('commands_value', commands_value.value.replaceAll('\n', ',').split(','))
        // var commands_array = commands_value.value.replaceAll('\n', ',').split(',')
        let edit_form = itemDataFormRef.value.generatorParams()
        console.log('edit_form', edit_form)
        var post_data = new FormData()
        post_data.append('netconf_method', JSON.stringify(edit_form['netconf_method']))
        post_data.append('name', edit_form['name'])
        post_data.append('vendor', edit_form['vendor'])
        post_data.append('memo', edit_form['memo'])
        if (edit_form['netconf_class'] != null) {
          post_data.append('netconf_class', edit_form['netconf_class'])
        }
        put({
          url: getCollection_planList + '/' + current_row.value['id'] + '/',
          data: post_data,
        }).then((res) => {
          if (res.code === 200) {
            message.success(res.message)
            edit_modalDialog.value!.toggle()
            doRefresh()
          } else {
            message.error(res.message)
          }
        })
      }

      function edit_collect_info(item: any) {
        //console.log('编辑采集方案', item)
        console.log('row', item)
        current_row.value = item
        edit_modalDialog.value?.toggle()
        itemFormOptions.forEach((it) => {
          const key = it.key
          const propName = item[key]
          it.value.value = propName
        })
        // 点击编辑获取连接类itemFormOptions[3]
        get({
          url: deviceCollect,
          data: () => {
            return {
              vendor: item.vendor,
              netconf_class: 1,
            }
          },
        }).then((res) => {
          itemFormOptions[3].optionItems.length = 0
          res.data.forEach((ele) => {
            var dict = {
              value: ele,
              label: ele,
            }
            itemFormOptions[3].optionItems.push(dict)
          })
          nextTick(() => {
            itemFormOptions[3].optionItems.splice(0, 0, { value: '', label: '' })
          })
        })
        // 根据netconf_class 获取方法
        get({
          url: deviceCollect,
          data: () => {
            return {
              netconf_class: item.netconf_class,
              get_method: 1,
            }
          },
        }).then((res) => {
          itemFormOptions[4].optionItems.length = 0
          res.data.forEach((ele) => {
            var dict = {
              value: ele,
              label: ele,
            }
            itemFormOptions[4].optionItems.push(dict)
          })
          nextTick(() => {
            itemFormOptions[4].optionItems.splice(0, 0, { value: '', label: '' })
          })
        })
      }

      function change_commands(item) {
        current_row.value = item
        modalDialog.value?.toggle()
        //  //console.log('修改当前行命令', item.commands)
        commands_value.value = item.commands.join(',').replaceAll(',', '\n')
      }

      function get_method_by_class(item) {
        //console.log('当前选中class', item)
        get({
          url: deviceCollect,
          data: () => {
            return {
              netconf_class: item,
              get_method: 1,
            }
          },
        }).then((res) => {
          itemFormOptions[4].optionItems.length = 0
          res.data.forEach((ele) => {
            var dict = {
              value: ele,
              label: ele,
            }
            itemFormOptions[4].optionItems.push(dict)
          })
          // nextTick(() => {
          //   itemFormOptions[4].optionItems.splice(0, 0, { value: '', label: '' })
          // })
        })
      }

      function rowKey(rowData) {
        return rowData.id
      }

      function get_class_by_vendor() {
        //console.log(new_collect_form.value.vendor)
        get({
          url: deviceCollect,
          data: () => {
            return {
              netconf_class: 1,
              vendor: new_collect_form.value.vendor,
            }
          },
        }).then((res) => {
          class_options.length = 0
          res.data.forEach((ele) => {
            var dict = {
              value: ele,
              label: ele,
            }
            class_options.push(dict)
          })
          nextTick(() => {
            class_options.splice(0, 0, { value: '', label: '不启用' })
          })
        })
      }

      function select_class_get_method_() {
        //console.log(new_collect_form.value.netconf_class)
        get({
          url: deviceCollect,
          data: () => {
            return {
              get_method: 1,
              netconf_class: new_collect_form.value.netconf_class,
            }
          },
        }).then((res) => {
          method_options.length = 0
          res.data.forEach((ele) => {
            var dict = {
              value: ele,
              label: ele,
            }
            method_options.push(dict)
          })
          // nextTick(() => {
          //   method_options.splice(0, 0, { value: '', label: '不启用' })
          // })
        })
      }

      function new_collect_submit() {
        //console.log('提交新增', new_collect_form.value)
        //console.log('提交新增', JSON.stringify(new_collect_form.value.netconf_method))
        var new_data = new FormData()
        new_data.append('name', new_collect_form.value.name)
        new_data.append('memo', new_collect_form.value.memo)
        new_data.append('vendor', new_collect_form.value.vendor)
        if (new_collect_form.value.netconf_class != null) {
          new_data.append('netconf_class', new_collect_form.value.netconf_class)
        }
        new_data.append('netconf_method', JSON.stringify(new_collect_form.value.netconf_method))
        if (new_collect_form.value.netconf_class) {
          post({
            url: getCollection_planList,
            data: new_data,
          }).then((res) => {
            if (res.code === 201) {
              message.success('新建方案成功')
              new_collect_show.value = false
              doRefresh()
            }
          })
        } else {
          var not_activte_data = new FormData()
          not_activte_data.append('name', new_collect_form.value.name)
          not_activte_data.append('memo', new_collect_form.value.memo)
          not_activte_data.append('vendor', new_collect_form.value.vendor)
          // not_activte_data.append('netconf_class', new_collect_form.value.netconf_class)
          not_activte_data.append('netconf_method', '[]')
          post({
            url: getCollection_planList,
            data: not_activte_data,
          }).then((res) => {
            if (res.code === 201) {
              message.success('新建方案成功')
              new_collect_show.value = false
              doRefresh()
            }
          })
        }
      }

      function get_info_by_vendor(vendor) {
        console.log(vendor)
        get({
          url: getCollection_planList,
          data: () => {
            return {
              start: (pagination.page - 1) * pagination.pageSize,
              // pageSize: pagination.pageSize,
              limit: pagination.pageSize,
              status: 0,
              _: Date.now(),
              vendor: vendor,
            }
          },
        }).then((res) => {
          //  //console.log(res)
          table.handleSuccess(res)
          pagination.setTotalSize(res.count || 10)
        })
      }

      onMounted(doRefresh)

      return {
        EditConfirm,
        get_info_by_vendor,
        new_collect_submit,
        select_class_get_method_,
        get_class_by_vendor,
        vendor_options,
        class_options,
        method_options,
        selectValues,
        new_collect_show,
        new_collect_form,
        patch,
        post,
        current_row,
        edit_modalDialog,
        edit_collect_info,
        commands_value,
        itemDataFormRef,
        searchDataFormRef,
        changeCommandsConfirm,
        second_password,
        rowData,
        show_password_modalDialog,
        tableColumns,
        change_commands,
        pagination,
        searchForm,
        onResetSearch,
        onSearch,
        ...table,
        itemFormOptions,
        ace_option,
        rowKey,
        modalDialog,
        WebsshmodalDialog,
        conditionItems,
        onUpdateTable,
        onUpdateBorder,
        doRefresh,
        chart_show,
      }
    },
  })
</script>

<style lang="scss">
  .control_button {
    float: right;
    padding-bottom: 10px;
  }
</style>
