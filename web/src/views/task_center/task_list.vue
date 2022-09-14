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

          <template #search-content>
            <DataForm
                ref="searchForm"
                :form-config="{
                labelWidth: 60,
              }"
                :options="conditionItems"
                preset="grid-item"
            />

          </template>
          <template #table-config>
            <TableConfig @update-border="onUpdateBorder" @refresh="doRefresh"/>
            <SortableTable class="ml-4" :columns="tableColumns" @update="onUpdateTable"/>
          </template>
          <template #top-right>
            <!--            <n-button type="primary" @click="new_address_func" size="small">新建CELERY任务</n-button>-->
            <!--            <n-button type="info" @click="task_monitor" size="small">任务监控</n-button>-->
            <!--            <n-button type="primary" @click="export_excel" size="small">导出EXCEL</n-button>-->
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
        <n-space style="float: right;padding-bottom: 20px">
          <n-button style="float: right" size="small" type="info" @click="onSearch()">查询</n-button>
          <n-button style="float: right" size="small" type="success" @click="onResetSearch()">重置</n-button>
          <n-button type="primary" @click="new_address_func" size="small">新建定时任务</n-button>
          <n-button type="info" @click="task_monitor" size="small">任务监控</n-button>
          <n-button type="primary" @click="export_excel" size="small">导出EXCEL</n-button>
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
        <TableFooter :pagination="pagination"/>
      </template>
    </TableBody>
    <ModalDialog ref="modalDialog" title="新建定时任务" @confirm="CreateSubmitConfirm"
                 :style="{ height: '600px',width:'1000px' }">
      <template #content>
        <DataForm ref="itemDataFormRef"
                  preset="grid-two-item"
                  :options="itemFormOptions"
                  :form-config="{
                labelWidth: 120,
                labelAlign:'left'
              }"/>
      </template>
    </ModalDialog>
    <ModalDialog ref="EditmodalDialog" title="编辑celery任务" @confirm="EditFormConfirm"
                 :style="{ height: '600px',width:'500px' }">
      <template #content>
        <DataForm ref="EdititemDataFormRef" :options="EdititemFormOptions"
                  :form-config="{
                labelWidth: 80,
              }"/>
      </template>
    </ModalDialog>
    <ModalDialog ref="WebsshmodalDialog" title="Webssh">
      <template>
        <div class="console" id="terminal">
        </div>
      </template>
    </ModalDialog>
  </div>
</template>

<script lang="ts">
import {
  getperiodic_taskList,
  jobcenterTaskUrl,
  getdispach,
  getinterval_schedule,
} from '@/api/url'
import { TableActionModel, useTable, useRenderAction, useTableColumn, usePagination } from '@/hooks/table'
import { defineComponent, h, nextTick, onMounted, reactive, ref, shallowReactive } from 'vue'
import _ from 'lodash'
import { DataTableColumn, NInput, NSelect, SelectOption, useDialog, useMessage, NButton, NPopconfirm ,NDatePicker} from 'naive-ui'
import { DataFormType, ModalDialogType, FormItem, TablePropsType } from '@/types/components'
import usePost from '@/hooks/usePost'
import { renderTag } from '@/hooks/form'
import useGet from '@/hooks/useGet'
import usePatch from '@/hooks/usePatch'
import useDelete from '@/hooks/useDelete'
import { sortColumns } from '@/utils'

import Cookies from 'js-cookie'

export default defineComponent({
  name: 'networkdevice',
  setup() {
    const itemFormOptions = [
      {
        key: 'name',
        label: '名称',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (newVal: any) => {
              formItem.value.value = newVal
            },
            maxlength: 50,
            placeholder: '',
          })
        },
      },
      {
        key: 'task',
        label: '任务函数',
        value: ref(''),
        optionItems: [],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择任务函数',
            filterable:true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        label: '参数(列表格式)',
        key: 'args',
        value: ref('[]'),
        render: (formItem) => {
          return h(
              NInput,
              {
                value: formItem.value.value,
                onUpdateValue: (val: any) => {
                  formItem.value.value = val
                },
                placeholder: '',
              },
              // {
              //   prefix: () => DP_CODE_FLAG,
              // },
          )
        },
        validator: (formItem, message) => {
          if (!formItem.value.value) {
            message.error('请输入部门编号')
            return false
          }
          return true
        },
      },
      {
        label: '参数(字典格式)',
        key: 'kwargs',
        value: ref('{}'),
        render: (formItem) => {
          return h(
              NInput,
              {
                value: formItem.value.value,
                onUpdateValue: (val: any) => {
                  formItem.value.value = val
                },
                placeholder: '',
              },
              // {
              //   prefix: () => DP_CODE_FLAG,
              // },
          )
        },
        
      },
      {
        key: 'queue',
        label: '队列',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'expires',
        label: '过期时间',
        value: ref(null),
        optionItems: [],
        render: (formItem) => {
          return h(NDatePicker, {
            value: formItem.value.value,
            placeholder: '请选择日期',
            style: 'width: 100%',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            type: 'date',
          })
        },
      },
      {
        key: 'enabled',
        label: '任务状态',
        value: ref(''),
        optionItems: [
          {value:true,label:'启用'},
          {value:false,label:'禁用'},
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'crontab',
        label: 'Crontab调度',
        value: ref(''),
        optionItems: [],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            disabled: checkedValueRef.value === 'interval调度',
            placeholder: '',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            'on-update:value':
                      crontab_func.bind(formItem.value.value),
          })
        },
      },
      {
        key: 'interval',
        label: 'Interval调度',
        value: ref(''),
        optionItems: [],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '',
            disabled: checkedValueRef.value === 'crontab调度',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            'on-update:value':
                      interval_func.bind(formItem.value.value),
          })
        },
      },
      {
        key: 'description',
        label: '任务描述',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (newVal: any) => {
              formItem.value.value = newVal
            },
            maxlength: 50,
            placeholder: '',
          })
        },
      },

    ] as Array<FormItem>
    const EdititemFormOptions = [
      {
        key: 'name',
        label: '名称',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (newVal: any) => {
              formItem.value.value = newVal
            },
            maxlength: 50,
            placeholder: '',
          })
        },
      },
      {
        key: 'task',
        label: '任务函数',
        value: ref(''),
        optionItems: [],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择任务函数',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        label: '参数(列表格式)',
        key: 'args',
        value: ref('[]'),
        render: (formItem) => {
          return h(
              NInput,
              {
                value: formItem.value.value,
                onUpdateValue: (val: any) => {
                  formItem.value.value = val
                },
                placeholder: '',
              },
              // {
              //   prefix: () => DP_CODE_FLAG,
              // },
          )
        },
        validator: (formItem, message) => {
          if (!formItem.value.value) {
            message.error('请输入部门编号')
            return false
          }
          return true
        },
      },
      {
        label: '参数(字典格式)',
        key: 'kwargs',
        value: ref('{}'),
        render: (formItem) => {
          return h(
              NInput,
              {
                value: formItem.value.value,
                onUpdateValue: (val: any) => {
                  formItem.value.value = val
                },
                placeholder: '',
              },
              // {
              //   prefix: () => DP_CODE_FLAG,
              // },
          )
        },
        validator: (formItem, message) => {
          if (!formItem.value.value) {
            message.error('请输入部门编号')
            return false
          }
          return true
        },
      },
      {
        key: 'queue',
        label: '队列',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择队列',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'expires',
        label: '过期时间',
        value: ref(null),
       
        render: (formItem) => {
          return h(NDatePicker, {
            value: formItem.value.value,
            placeholder: '请选择日期',
            style: 'width: 100%',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            type: 'date',
          })
        },
      },
      {
        key: 'enabled',
        label: '任务状态',
        value: ref(''),
        optionItems: [
          {value:true,label:'启用'},
          {value:false,label:'禁用'},
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'crontab',
        label: 'Crontab调度',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'interval',
        label: 'Interval调度',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'description',
        label: '任务描述',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (newVal: any) => {
              formItem.value.value = newVal
            },
            maxlength: 50,
            placeholder: '',
          })
        },
      },

    ] as Array<FormItem>
    const conditionItems: Array<FormItem> = [
      {
        key: 'name',
        label: '任务名称',
        value: ref(''),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            onKeyup: (Event) => {
              if (Event.keyCode == 13) {
                onSearch()
              }

            },
            placeholder: '',
          })
        },
      },

      {
        key: 'task',
        label: '任务函数',
        value: ref(''),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            onKeyup: (Event) => {
              if (Event.keyCode == 13) {
                onSearch()
              }

            },
            placeholder: '',
          })
        },
      },

    ]
    const table = useTable()
    const pagination = usePagination(doRefresh)
    pagination.pageSize = 10
    pagination.limit = 10
    pagination.start = 0
    const searchForm = ref<DataFormType | null>(null)
    const message = useMessage()
    const naiveDailog = useDialog()
    const config_detail = ref('')
    const checkedValueRef = ref('')
    const tableColumns = reactive(
        useTableColumn(
            [
              {
                title: '任务名称',
                key: 'name',
              },
              {
                title: '任务函数',
                key: 'task',
              },
              {
                title: '过期时间',
                key: 'expires',
                render: (rowData) => {
                  if (!rowData.expires) {
                    return '永不过期'
                  }
                },
              },
              {
                title: '任务状态',
                key: 'enabled',
                render: (rowData) => {
                  if (!rowData.enabled) {
                    return h(NButton, { type: 'error', size: 'tiny' }, () => h('span', {}, '未启用'))
                  } else {
                    return h(NButton, { type: 'primary', size: 'tiny' }, () => h('span', {}, '已启用'))
                  }
                },
              },
              {
                title: '任务描述',
                key: 'description',
              },

              {
                title: '操作',
                key: 'actions',
                render: (rowData) => {
                  return h(NButton, {
                    type: 'info',
                    size: 'tiny',
                    onClick: edit_task.bind(null, rowData),
                  }, () => h('span', {}, '详细/修改'))
                },
                // render: (rowData) => {
                //   return useRenderAction([
                //     {
                //       label: '详细/修改',
                //       // onClick: show_config.bind(null, rowData),
                //     },
                //
                //   ] as TableActionModel[])
                // },
              },
              {
                title: '启停操作',
                key: 'config_file',
                // render:(rowData)=>{
                //  return  h('a', {
                //    href:rowData.config_file,
                //   }, '下载配置')
                render: (rowData) => {
                  if (rowData.enabled) {
                    return h(NPopconfirm, {
                      onPositiveClick: () => stop_task(rowData),
                      negativeText: '取消',
                      positiveText: '确认',
                    }, {
                      trigger: () => h(NButton, { type: 'warning', size: 'tiny' }, () => h('span', {}, '停止')),
                      default: () => h('span', {}, '请确认停止任务操作?'),
                    })
                  } else {
                    return h(NPopconfirm, {
                      // onPositiveClick: () => delete_address_detail(rowData),
                      onPositiveClick: () => open_task(rowData),
                      negativeText: '取消',
                      positiveText: '确认',
                    }, {
                      trigger: () => h(NButton, { type: 'success', size: 'tiny' }, () => h('span', {}, '开启')),
                      default: () => h('span', {}, '请确认开启任务操作?'),
                    })
                  }

                  // return useRenderAction([
                  //   {
                  //     label: '删除',
                  //     type:"error",
                  //     onClick: delete_service_detail.bind(null, rowData),
                  //   },
                  //
                  // ] as TableActionModel[])
                },
                // render: (rowData) => {
                //   return h(NButton, { type: 'warning', size: 'tiny' }, '停止')
                // },
              },
              {
                title: '删除',
                key: 'config_file',
                // render:(rowData)=>{
                //  return  h('a', {
                //    href:rowData.config_file,
                //   }, '下载配置')
                render: (rowData) => {
                  // return h(NButton, { type: 'error', size: 'tiny' }, '删除')
                  return h(NPopconfirm, {
                    onPositiveClick: () => delete_task(rowData),
                    negativeText: '取消',
                    positiveText: '确认',
                  }, {
                    trigger: () => h(NButton, { type: 'error', size: 'tiny' }, () => h('span', {}, '删除')),
                    default: () => h('span', {}, '请确认删除任务操作?'),
                  })
                },
              },
              {
                title: '运行',
                key: 'config_file',
                // render:(rowData)=>{
                //  return  h('a', {
                //    href:rowData.config_file,
                //   }, '下载配置')
                render: (rowData) => {
                  return h(NButton, {
                    type: 'info',
                    size: 'tiny',
                    onClick: run_task.bind(null, rowData),
                  }, () => h('span', {}, '运行'))
                  // return h(NPopconfirm, {
                  //   onPositiveClick: () => run_task(rowData),
                  //   negativeText: '取消',
                  //   positiveText: '确认',
                  // }, {
                  //   trigger: () => h(NButton, { type: 'info', size: 'tiny' },()=> h('span', {}, '运行')),
                  //   default: () => h('span', {}, '请先确认任务状态是否开启再进行操作?'),
                  // })
                },
              },
            ],
            {
              align: 'center',
            } as DataTableColumn),
    )
    const itemDataFormRef = ref<DataFormType | null>(null)
    const EdititemDataFormRef = ref<DataFormType | null>(null)
    const searchDataFormRef = ref<DataFormType | null>(null)
    const modalDialog = ref<ModalDialogType | null>(null)
    const EditmodalDialog = ref<ModalDialogType | null>(null)
    const WebsshmodalDialog = ref<ModalDialogType | null>(null)
    const get = useGet()
    const post = usePost()
    const patch = usePatch()
    const delete_fun = useDelete()
    const current_task = ref(null)
    function crontab_func(item){
       //console.log(item)
      if(item){
        checkedValueRef.value = 'crontab调度'
      }else{
        checkedValueRef.value = ''
      }
      
      }

    function interval_func(item){
      if(item){
        checkedValueRef.value = 'interval调度'
      }else{
        checkedValueRef.value = ''
      }
      
      }
    function onSearch() {
       //console.log(searchForm.value?.generatorParams())
      const search_form = searchForm.value?.generatorParams()
      searchDataFormRef.value = search_form
      get({
        url: getperiodic_taskList + '?name=' + search_form.name + '&task=' + search_form.task,
        data: () => {
          return {
            start: (pagination.page - 1) * 10,
            // pageSize: pagination.pageSize,
            limit: pagination.pageSize,
            _: Date.now(),
          }
        },
      })

          .then((res) => {

            // message.success('查询失败:' + res.msg)
            table.handleSuccess(res)
            pagination.setTotalSize(res.count || 10)


          })

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
       //console.log(searchDataFormRef.value)
      let request_url = ''
      if (searchDataFormRef.value === null) {
        request_url = getperiodic_taskList + '?name=' + '&task='
      } else {
        request_url = getperiodic_taskList + '?name=' + searchDataFormRef.value.name + '&task=' + searchDataFormRef.value.task
      }
      get({
        url: request_url,
        data: () => {
          return {
            start: (pagination.page - 1) * pagination.pageSize,
            // pageSize: pagination.pageSize,
            limit: pagination.pageSize,
            _: Date.now(),
          }
        },
      })

          .then((res) => {
            //  //console.log(res)
             //console.log('res.results', res.results)
            table.handleSuccess(res)
            pagination.setTotalSize(res.count || 10)
          })
    }

    
   
   
    function onAddItem() {
      modalDialog.value?.toggle()
      nextTick(() => {
        itemDataFormRef.value?.reset()
      })
    }
//dateTime：时间戳；  flag：取值为true/false，用于判断是否需要显示时分秒
    function getFormtTime(dateTime) {
      if (dateTime != null) {
        //若传入的dateTime为字符串类型，需要进行转换成数值，若不是无需下面注释代码
        //var time = parseInt(dateTime)
        var date = new Date(dateTime)
        //获取年份
        var YY = date.getFullYear()
        //获取月份
        var MM = (date.getMonth() + 1 < 10 ? '0' + (date.getMonth() + 1) : date.getMonth() + 1)
        //获取日期
        var DD = (date.getDate() < 10 ? '0' + date.getDate() : date.getDate())
         var hh = (date.getHours() < 10 ? '0' + date.getHours() : date.getHours()) + ':'
        var mm = (date.getMinutes() < 10 ? '0' + date.getMinutes() : date.getMinutes()) + ':'
        var ss = date.getSeconds() < 10 ? '0' + date.getSeconds() : date.getSeconds()
        //返回时间格式： 2020-11-09
        return YY + '-' + MM + '-' + DD +' ' +hh +mm+ss

      } else {
        return ''
      }
    }
    function CreateSubmitConfirm() {
      // if (itemDataFormRef.value?.validator()) {
        // modalDialog.value?.toggle()
         //console.log('新建任务参数', itemDataFormRef.value.generatorParams())
         console.log('create_info',itemDataFormRef.value.generatorParams())
         var create_info = itemDataFormRef.value.generatorParams()
        var formdata = new FormData()
        formdata.append('name',create_info['name'])
        formdata.append('task',create_info['task'])
        formdata.append('args',create_info['args'])
        formdata.append('kwargs',create_info['kwargs'])
        formdata.append('queue',create_info['queue'])
        formdata.append('expires',getFormtTime(create_info['expires']))
        formdata.append('enabled',create_info['enabled'])
        formdata.append('crontab',create_info['crontab']?create_info['crontab']:'')
        formdata.append('interval',create_info['interval']?create_info['interval']:'')
        formdata.append('description',create_info['description'])
        post({
          url:getperiodic_taskList,
          data:formdata,
        }).then((res)=>{
          console.log(res)
          // if(res.code===201){
            message.success('新建任务成功')
            modalDialog.value!.toggle()
            doRefresh()
          // }
        })

        // naiveDailog.success({
        //   title: '提示',
        //   positiveText: '确定',
        //   content:
        //       '模拟部门添加/编辑成功，数据为：' +
        //       JSON.stringify(itemDataFormRef.value.generatorParams()),
        // })
      // }
    }


    function rowKey(rowData: any) {
      return rowData.id
    }

    function new_address_func() {
       //console.log('新建CELERY任务')
      modalDialog.value?.toggle()
    }

    function task_monitor() {
      window.open('http://10.254.12.169:30055/')
    }

    function run_task(item) {
       //console.log('当前行', item)
      if (!item.enabled) {
        message.error('请确认任务为启用状态才可以运行')
      } else {
        let payload_data = new FormData()
        let csrf_token = Cookies.get('csrftoken')
        payload_data.append('data', JSON.stringify(item))
        payload_data.append('csrfmiddlewaretoken', csrf_token)
        post({
          url: jobcenterTaskUrl,
          data: payload_data,
        }).then((res) => {
          if (res.code === 200) {
            message.success('SUCCESS' + '任务ID:' + res.data)
          }
        })

      }
    }

    function stop_task(item) {
      let patch_data = new FormData()
      patch_data.append('enabled', false)
      patch({
        url: getperiodic_taskList + '/' + item.id + '/',
        data: patch_data,
      }).then((res) => {
        message.success('任务停用成功')
        doRefresh()
      })
    }

    function open_task(item) {
      let patch_data = new FormData()
      patch_data.append('enabled', true)
      patch({
        url: getperiodic_taskList + '/' + item.id + '/',
        data: patch_data,
      }).then((res) => {
        message.success('任务开启成功')
        doRefresh()
      })
    }

    function delete_task(item) {
       //console.log('删除任务')
      // let patch_data = new FormData()
      // patch_data.append('enabled', true)
      delete_fun({
        url: getperiodic_taskList + '/' + item.id + '/',
      }).then((res) => {
        message.success('任务删除成功')
        doRefresh()
      })
    }

    function get_queue() {
      get({
        url: jobcenterTaskUrl,
        data: () => {
          return {
            get_queues: 1,
          }
        },
      }).then((res) => {
         //console.log('queue_list', res.data)
        let queue_list = []
        res.data.forEach((item) => {
          const dict = {
            value: item,
            label: item,
          }
          queue_list.push(dict)
        })
        EdititemFormOptions[4].optionItems.push(...queue_list)
        itemFormOptions[4].optionItems.push(...queue_list)
        nextTick(()=>{
          EdititemFormOptions[4].optionItems.splice(0,0,{value:'',label:'-----'})
          itemFormOptions[4].optionItems.splice(0,0,{value:'',label:'-----'})
        })
      })
    }

    function export_excel() {
      //  //console.log('选中哪几行', checkedRowKeysRef.value)
      get({
        url: getperiodic_taskList,
        data: () => {
          return {
            start: (pagination.page - 1) * 10,
            // pageSize: pagination.pageSize,
            limit: 1000,
            _: Date.now(),
          }
        },
      })

          .then((res) => {
            //  //console.log(res)
            let check_list = res.results
            let export_str = '任务名称,任务函数,过期时间,任务状态\n'
            for (let i = 0; i < check_list.length; i++) {
              let status = ''
              if (check_list[i].enabled) {
                status = '启用'
              } else {
                status = '禁用'
              }
              if (!check_list[i].expires) {
                check_list[i].expires = '永不过期'
              }
              export_str =
                  export_str +
                  check_list[i].name +
                  ',' +
                  check_list[i].task +
                  ',' +
                  check_list[i].expires +
                  ',' +
                  status +

                  '\n'
            }
            export_str = encodeURIComponent(export_str)
            const link = document.createElement('a')
            link.href = 'data:text/csv;charset=utf-8,\ufeff' + export_str
            // link.style = 'visibility:hidden'
            link.download = '自动化任务表.csv'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
          })


    }

    function edit_task(item) {
      current_task.value = item
       console.log('打开编辑任务对话框',item)
      nextTick(() => {
        get({
          url: getdispach,
        }).then((res) => {
          let crontab_list = []
          let interval_list = []
          res.crontab_data.forEach((item) => {
            const dict = {
              value: item.id,
              label: item.hour,
            }
            crontab_list.push(dict)

          })
          // if (EdititemFormOptions[7].optionItems !== undefined) {
          //   EdititemFormOptions[7].optionItems.push(...crontab_list)
          // }

          res.interval_data.forEach((item) => {
            const dict = {
              value: item.id,
              label: item.every + item.period,
            }
            interval_list.push(dict)

          })
          if (EdititemFormOptions[8].optionItems !== undefined) {
            EdititemFormOptions[8].optionItems.push(...interval_list)
          }
        })
      })
      EditmodalDialog.value?.toggle()
      EdititemFormOptions.forEach((it) => {
        const key = it.key
        const propName = item[key]
        if (key === 'u_location') {
          it.value.value = item['u_location_start'] + '-' + item['u_location_end']
        } else {
          it.value.value = propName
        }

      })
    }

    function EditFormConfirm() {
       //console.log('编辑确认', EdititemDataFormRef.value.generatorParams())
       var edit_info = EdititemDataFormRef.value.generatorParams()
       var formdata = new FormData()
        formdata.append('name',edit_info['name'])
        formdata.append('task',edit_info['task'])
        formdata.append('args',edit_info['args'])
        formdata.append('kwargs',edit_info['kwargs'])
        formdata.append('queue',edit_info['queue'])
        formdata.append('expires',getFormtTime(edit_info['expires']))
        formdata.append('enabled',edit_info['enabled'])
        formdata.append('crontab',edit_info['crontab']?edit_info['crontab']:'')
        formdata.append('interval',edit_info['interval']?edit_info['interval']:'')
        formdata.append('description',edit_info['description'])
        patch({
          url:getperiodic_taskList +'/'+current_task.value['id']+'/',
          data:formdata,
        }).then((res)=>{
          console.log(res)
          // if(res.code===201){
            message.success('编辑任务成功')
            EditmodalDialog.value!.toggle()
            doRefresh()
          // }
        })
    }

    function get_current_task() {

      get({
        url: jobcenterTaskUrl,
        data: () => {
          return {
            current_tasks: 1,
          }
        },
      }).then((res) => {
         //console.log(res)
        let current_task_list = []
        res.data.forEach((item) => {
          const dict = {
            value: item,
            label: item,
          }
          current_task_list.push(dict)
        })
        EdititemFormOptions[1].optionItems.push(...current_task_list)
        itemFormOptions[1].optionItems.push(...current_task_list)
      })
    }
    function get_crontab_schedules() {

      get({
        url: jobcenterTaskUrl,
        data: () => {
          return {
            crontab_schedules: 1,
          }
        },
      }).then((res) => {
         //console.log(res)
        let crontab_schedules_list = []
        res.data.forEach((item) => {
          const dict = {
            value: item.pk,
            label: item.fields.hour +'--' +item.fields.minute +"--时区  " +item.fields.timezone,
          }
          crontab_schedules_list.push(dict)
        })
        EdititemFormOptions[7].optionItems.push(...crontab_schedules_list)
        itemFormOptions[7].optionItems.push(...crontab_schedules_list)
        nextTick(()=>{
          EdititemFormOptions[7].optionItems.splice(0,0,{value:'',label:'-----'})
          itemFormOptions[7].optionItems.splice(0,0,{value:'',label:'-----'})
        })
      })
    }
    function get_interval_schedule() {

      get({
        url: getinterval_schedule,
        data: () => {
          return {
            limit: 1000,
          }
        },
      }).then((res) => {
         //console.log(res)
        let interval_schedules_list = []
        res.results.forEach((item) => {
          const dict = {
            value: item.id,
            label: item.every + item.period,
          }
          interval_schedules_list.push(dict)
        })
        EdititemFormOptions[8].optionItems.push(...interval_schedules_list)
        itemFormOptions[8].optionItems.push(...interval_schedules_list)
        nextTick(()=>{
          EdititemFormOptions[8].optionItems.splice(0,0,{value:'',label:'-----'})
          itemFormOptions[8].optionItems.splice(0,0,{value:'',label:'-----'})
        })
      })
    }

    onMounted(doRefresh)
    onMounted(get_queue)
    onMounted(get_current_task)
    onMounted(get_crontab_schedules)
    onMounted(get_interval_schedule)
    // onMounted(doIdc)
    // onMounted(doVendor)
    // onMounted(doRole)
    // onMounted(doCagetory)
    return {
      current_task,
      getFormtTime,
      get_current_task,
      get_crontab_schedules,
      get_interval_schedule,
      get_queue,
      run_task,
      stop_task,
      open_task,
      edit_task,
      delete_task,
      new_address_func,
      task_monitor,
      export_excel,
      itemDataFormRef,
      EdititemDataFormRef,
      searchDataFormRef,
      CreateSubmitConfirm,
      EditFormConfirm,
      tableColumns,
      config_detail,
      pagination,
      searchForm,
      onResetSearch,
      onSearch,
      ...table,
      onAddItem,
      itemFormOptions,
      EdititemFormOptions,
      rowKey,
      modalDialog,
      EditmodalDialog,
      WebsshmodalDialog,
      conditionItems,
      onUpdateTable,
      onUpdateBorder,
      doRefresh,
      checkedValueRef,
      crontab_func,
      interval_func,
    }
  },
})
</script>
