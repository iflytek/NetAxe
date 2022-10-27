<template>
  <div class="main-container">
    <TableBody>
      <template #header>
        <TableHeader :show-filter="false">
          <template #top-right>
            <AddButton @add="onAddItem"/>
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
      <template #footer>
        <TableFooter ref="tableFooterRef" :pagination="pagination" />
      </template>
    </TableBody>
    <ModalDialog ref="modalDialogRef" @confirm="onDataFormConfirm">
      <template #content>
        <DataForm ref="dataFormRef" :options="formItems" />
      </template>
    </ModalDialog>
    <ModalDialog ref="menuModalDialogRef" title="菜单权限" contentHeight="40vh" @confirm="onCheckedKeys">
      <template #content>
        <n-tree
          block-line
          cascade
          checkable
          check-strategy="child"
          default-expand-all
          :data="menuData"
          :checked-keys="checkedKeys"
          @update:checked-keys="updateCheckedKeys"
        />
      </template>
    </ModalDialog>
  </div>
</template>

<script lang="ts">
  import { get, post, put, delete_fun } from '@/api/http'
  import { getMenuList, getRoleList } from '@/api/url'
  import {
    TableActionModel,
    useRenderAction,
    useRowKey,
    useTable,
    useTableColumn,
    usePagination,
  } from '@/hooks/table'
  import { DataFormType, ModalDialogType, FormItem } from '@/types/components'
  import { DataTableColumn, NInput, TreeOption, useDialog, useMessage } from 'naive-ui'
  import { defineComponent, h, nextTick, onMounted, ref, reactive } from 'vue'
  const ROLE_CODE_FLAG = 'ROLE_'
  const formItems = [
    {
      label: '角色名称',
      type: 'input',
      key: 'name',
      value: ref(null),
      validator: (formItem, message) => {
        if (!formItem.value.value) {
          message.error('请输入角色名称')
          return false
        }
        return true
      },
      render: (formItem) => {
        return h(NInput, {
          value: formItem.value.value,
          onUpdateValue: (val: any) => {
            formItem.value.value = val
          },
          placeholder: '请输入角色名称',
        })
      },
    },
    {
      label: '角色编号',
      key: 'key',
      value: ref(null),
      maxLength: 20,
      validator: (formItem, message) => {
        if (!formItem.value.value) {
          message.error('请输入角色编码')
          return false
        }
        return true
      },
      render: (formItem) => {
        return h(
          NInput,
          {
            value: formItem.value.value,
            onUpdateValue: (val: any) => {
              formItem.value.value = val
            },
            placeholder: '请输入角色描述',
          },
          {
            prefix: () => h('div', ROLE_CODE_FLAG),
          }
        )
      },
    },
    {
      label: '角色描述',
      key: 'description',
      value: ref(null),
      maxLength: 50,
      inputType: 'text',
      validator: (formItem, message) => {
        if (!formItem.value.value) {
          message.error('请输入角色名称')
          return false
        }
        return true
      },
      render: (formItem) => {
        return h(NInput, {
          value: formItem.value.value,
          onUpdateValue: (val: any) => {
            formItem.value.value = val
          },
          placeholder: '请输入角色描述',
          type: 'textarea',
          rows: 3,
        })
      },
    },
  ] as FormItem[]

  export default defineComponent({
    name: 'Role',
    setup() {
      let id = 0
      let actionModel = 'add'
      const table = useTable()
      const rowKey = useRowKey('id')
      const naiveDialog = useDialog()
      const message = useMessage()
      const pagination = usePagination(doRefresh)
      const modalDialogRef = ref<ModalDialogType | null>(null)
      const dataFormRef = ref<DataFormType | null>(null)
      const menuModalDialogRef = ref<ModalDialogType | null>(null)
      const menuData = reactive([] as Array<TreeOption>)
      const tableColumns = useTableColumn(
        [
          table.selectionColumn,
          table.indexColumn,
          {
            title: '角色名称',
            key: 'name',
          },
          {
            title: '角色编号',
            key: 'key',
          },
          {
            title: '角色描述',
            key: 'description',
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
                  onClick: onDeleteItem.bind(null, rowData),
                },
                {
                  label: '菜单权限',
                  type: 'success',
                  onClick: onShowMenu.bind(null, rowData),
                },
              ] as TableActionModel[])
            },
          },
        ],
        {
          align: 'center',
        } as DataTableColumn
      )

      function doRefresh() {
        get({
          url: getRoleList,
        }).then((res) => {
            table.handleSuccess(res)
        })
      }

      function onAddItem() {
        actionModel = "add"
        modalDialogRef.value?.toggle()
        nextTick(() => {
          dataFormRef.value?.reset()
        })
      }

      function onUpdateItem(item: any) {
        id = item.id
        actionModel = 'edit'
        modalDialogRef.value?.toggle()
        nextTick(() => {
          formItems.forEach((it) => {
            const key = it.key
            const propName = item[key]
            if (propName) {
              if (it.key === 'key') {
                it.value.value = propName.replace(ROLE_CODE_FLAG, '')
              } else {
                it.value.value = propName
              }
            }
          })
        })
      }

      function onDataFormConfirm() {
        modalDialogRef.value?.toggle()
        if (actionModel === 'add'){
          if (dataFormRef.value?.validator()) {
            post({
              url: getRoleList,
              data: dataFormRef.value.generatorParams(),
            }).then((res) => {
              table.handleSuccess(res)
              message.success('新增成功')
              doRefresh()
            }).catch(console.log)
          }
        }else{
          if (dataFormRef.value?.validator()) {
            put({
                url: getRoleList + id + "/",
                data: dataFormRef.value?.generatorParams(),
              }).then((res) => {
                table.handleSuccess(res)
                message.success('更新成功')
                doRefresh()
              }).catch(console.log)
          }
          dataFormRef.value?.reset()
        }
      }

      function onDeleteItem(data: any) {
        naiveDialog.warning({
          title: '提示',
          content: '是否要删除此菜单？',
          positiveText: '删除',
          onPositiveClick: () => {
            delete_fun({
                  url: getRoleList + data.id + '/',
                }).then((res) => {
                  message.success('删除成功')
                  doRefresh()
                })
          },
        })
      }

      function handleMenuData(
        menuData: Array<any>,
      ) {
        const tempMenus = [] as Array<TreeOption>
        menuData.forEach((it) => {
          const tempMenu = {} as TreeOption
          tempMenu.key = it.id
          tempMenu.label = it.name
          if (it.children) {
            tempMenu.children = handleMenuData(it.children)
          }
          tempMenus.push(tempMenu)
        })
        return tempMenus
      }

      // 打开菜单权限
      const checkedKeys = reactive([] as Array<string>)
      function onShowMenu(item: any) {
        id = item.id
        menuData.length = 0
        checkedKeys.length = 0
        menuModalDialogRef.value?.toggle()

        get({
          url: getMenuList,
          data: {parent__isnull:true}
        }).then((res) => {
          menuData.push(...handleMenuData(res.results))
        }).catch(console.log)
        
        // 嵌套循环待后续优化
        table.dataList.forEach((it) => {
          if (it.id === id){
            checkedKeys.push(...it.menu)
          }
        })
      }
      
      // 更新菜单权限数据
      function updateCheckedKeys(v: string[]) {
        console.log(v)
        checkedKeys.length = 0
        checkedKeys.push(...v)
      }

      // 提交菜单权限数据
      function onCheckedKeys() {
        put({
            url: getRoleList + id + "/",
            data: {"menu": checkedKeys},
          }).then((res) => {
            message.success('提交成功')
            doRefresh()
          }).catch(console.log)
        menuModalDialogRef.value?.toggle()
      }

      onMounted(doRefresh)

      return {
        rowKey,
        ...table,
        pagination,
        modalDialogRef,
        menuModalDialogRef,
        dataFormRef,
        menuData,
        tableColumns,
        formItems,
        onAddItem,
        onDataFormConfirm,
        onCheckedKeys,
        updateCheckedKeys,
        checkedKeys,
      }
    },
  })
</script>
