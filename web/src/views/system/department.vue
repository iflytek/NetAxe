<template>
  <div class="main-container">
    <TableBody>
      <template #header>
        <TableHeader :show-filter="false">
          <template #top-right>
            <AddButton @add="onAddItem" />
          </template>
        </TableHeader>
      </template>
      <template #default>
        <n-data-table
          :loading="tableLoading"
          :data="dataList"
          :columns="tableColumns"
          :row-key="rowKey"
        />
      </template>
    </TableBody>
    <ModalDialog ref="modalDialog" @confirm="onDataFormConfirm">
      <template #content>
        <DataForm ref="itemDataFormRef" :options="itemFormOptions" />
      </template>
    </ModalDialog>
  </div>
</template>

<script lang="ts">
  import _ from 'lodash'
  import { getDepartmentList } from '@/api/url'
  import { TableActionModel, useTable, useRenderAction, useTableColumn } from '@/hooks/table'
  import { defineComponent, h, nextTick, onMounted, ref, shallowReactive } from 'vue'
  import { DataTableColumn, NInput, SelectOption, useDialog, useMessage } from 'naive-ui'
  import { DataFormType, ModalDialogType, FormItem } from '@/types/components'
  import { get, post, put, delete_fun } from '@/api/http'
  import { renderTag, renderTreeSelect } from '@/hooks/form'
  import { useRowKey } from '@/hooks/table'
  import { transformTreeSelect } from '@/utils'
  interface Department {
    id: number
    name: string
    key: string
    sort: number
    status: number
    parentId: number
    children: Array<Department>
  }
  
  const DP_CODE_FLAG = 'dp_code_'
  export default defineComponent({
    name: 'Department',
    setup() {
      let id = 0
      let actionModel = 'add'
      const table = useTable()
      const message = useMessage()
      const rowKey = useRowKey('id')
      const naiveDailog = useDialog()
      const tableColumns = useTableColumn(
        [
          {
            title: '部门名称',
            key: 'name',
          },
          {
            title: '部门编号',
            key: 'key',
          },
          {
            title: '排序',
            key: 'sort',
          },
          {
            title: '状态',
            key: 'status',
            render: (rowData) =>
              renderTag(!!rowData.status ? '正常' : '禁用', {
                type: !!rowData.status ? 'success' : 'error',
                size: 'small',
              }),
          },
          {
            title: '操作',
            key: 'actions',
            render: (rowData) => {
              return useRenderAction([
                {
                  label: '编辑',
                  onClick: onUpdateItem.bind(null, rowData),
                },
                {
                  label: '删除',
                  type: 'error',
                  onClick() {
                    onDeleteItem(rowData)
                  },
                },
              ] as TableActionModel[])
            },
          },
        ],
        {
          align: 'center',
        } as DataTableColumn
      )

      const itemFormOptions = [
        {
          key: 'parent',
          label: '父级部门',
          value: ref(null),
          optionItems: shallowReactive([] as Array<SelectOption>),
          render: (formItem) => {
            return renderTreeSelect(
                  formItem.value,
                  transformTreeSelect(table.dataList, 'name', 'id'),
                  {
                    showPath: true,
                  }
                )
          },
        },
        {
          key: 'name',
          label: '部门名称',
          type: 'input',
          value: ref(null),
          render: (formItem) => {
            return h(NInput, {
              value: formItem.value.value,
              onUpdateValue: (newVal: any) => {
                formItem.value.value = newVal
              },
              maxlength: 50,
              placeholder: '请输入部门名称',
            })
          },
          validator: (formItem, message) => {
            if (!formItem.value.value) {
              message.error('请输入部门名称')
              return false
            }
            return true
          },
        },
        {
          label: '部门编号',
          key: 'key',
          value: ref(null),
          render: (formItem) => {
            return h(
              NInput,
              {
                value: formItem.value.value,
                onUpdateValue: (val: any) => {
                  formItem.value.value = val
                },
                placeholder: '请输入部门编号',
              },
              {
                prefix: () => DP_CODE_FLAG,
              }
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
      ] as Array<FormItem>

      const itemDataFormRef = ref<DataFormType | null>(null)
      const searchDataFormRef = ref<DataFormType | null>(null)
      const modalDialog = ref<ModalDialogType | null>(null)

      function doRefresh() {
        get({
          url: getDepartmentList,
          data: {parent__isnull:true}
        }).then((res) => {
          table.handleSuccess(res)
        })
      }

      function onAddItem() {
        actionModel = 'add'
        modalDialog.value?.toggle()
        nextTick(() => {
          itemDataFormRef.value?.reset()
        })
      }

      function onUpdateItem(item: any) {
        id = item.id
        actionModel = 'edit'
        modalDialog.value?.toggle()
        nextTick(() => {
          itemFormOptions.forEach((it) => {
            const key = it.key
            const propName = item[key]
            if (propName) {
              if (it.key === 'key') {
                it.value.value = propName.replace(DP_CODE_FLAG, '')
              } else {
                it.value.value = propName
              }
            }
          })
        })
      }

      function onDataFormConfirm() {
        modalDialog.value?.toggle()
        if (actionModel === 'add'){
          if (itemDataFormRef.value?.validator()) {
            post({
              url: getDepartmentList,
              data: itemDataFormRef.value.generatorParams(),
            }).then((res) => {
              table.handleSuccess(res.data)
              message.success('新增成功')
              doRefresh()
            }).catch(console.log)
          }
        }else{
          if (itemDataFormRef.value?.validator()) {
            put({
                url: getDepartmentList + id + "/",
                data: itemDataFormRef.value?.generatorParams(),
              }).then((res) => {
                table.handleSuccess(res.data)
                message.success('更新成功')
                doRefresh()
              }).catch(console.log)
          }
        itemDataFormRef.value?.reset()
        }
      }

      const onDeleteItem = (item: any) => {
        naiveDailog.warning({
          title: '提示',
          content: '确定要删除此信息，删除后不可恢复？',
          positiveText: '删除',
          negativeText: '再想想',
          onPositiveClick: () => {
            delete_fun({
                  url: getDepartmentList + item.id + '/',
                }).then((res) => {
                  message.success('删除成功')
                  doRefresh()
                })
          },
        })
      }

      function filterItems(srcArray: Array<Department>, filterItem: Department) {
        for (let index = 0; index < srcArray.length; index++) {
          const element = srcArray[index]
          if (element.id === filterItem.id) {
            if (!_.isEmpty(element.children)) {
              message.error('当前部门下有子部门，不能删除')
              return
            }
            srcArray.splice(index, 1)
            return
          } else {
            if (!_.isEmpty(element.children)) {
              filterItems(element.children, filterItem)
            }
          }
        }
      }

      onMounted(doRefresh)

      return {
        itemDataFormRef,
        searchDataFormRef,
        onDataFormConfirm,
        tableColumns,
        onUpdateItem,
        ...table,
        onDeleteItem,
        onAddItem,
        itemFormOptions,
        rowKey,
        modalDialog,
      }
    },
  })
</script>
