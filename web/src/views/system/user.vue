<template>
  <div>
    <n-grid :x-gap="10">
      <n-grid-item :span="40">
        <div>
          <TableBody>
            <template #header>
              <TableHeader ref="tableHeaderRef" :show-filter="false">
                <template #top-right>
                  <DeleteButton @delete="onDeleteItems" />
                </template>
              </TableHeader>
            </template>
            <template #default>
              <n-data-table
                :loading="tableLoading"
                :data="dataList"
                :row-key="rowKey"
                :columns="tableColumns"
                :scroll-x="1000"
                :style="{ height: `${tableHeight}px` }"
                :flex-height="true"
                @update:checked-row-keys="onRowCheck"
              />
            </template>
            <template #footer>
              <TableFooter ref="tableFooterRef" :pagination="pagination" />
            </template>
          </TableBody>
        </div>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script lang="ts">
  import { get, put, delete_fun } from '@/api/http'
  import { getTableList, getRoleList } from '@/api/url'
  import { renderTag } from '@/hooks/form'
  import {
    TableActionModel,
    usePagination,
    useRenderAction,
    useRowKey,
    useTable,
    useTableColumn,
    useTableHeight,
    } from '@/hooks/table'
  import { transformSelect } from '@/utils'
  import { DataTableColumn, useDialog, useMessage, NSelect } from 'naive-ui'
  import { defineComponent, h, onMounted, ref } from 'vue'
  export default defineComponent({
    name: 'UserList',
    setup() {
      const role = ref([])
      const table = useTable()
      const message = useMessage()
      const rowKey = useRowKey('id')
      const naiveDialog = useDialog()
      const pagination = usePagination(doRefresh)
      const checkedRowKeys = [] as Array<any>
      const tableColumns = useTableColumn(
        [
          table.selectionColumn,
          table.indexColumn,
          {
            title: '用户',
            key: 'username',
            width: 120,
          },
          {
            title: '姓名',
            key: 'nick_name',
            width: 120,
          },
          {
            title: '性别',
            key: 'gender',
            width: 80,
            render: (rowData) => {
              return h('div', rowData.gender === 1 ? '男' : '女')
            },
          },
          {
            title: '角色',
            key: 'role_name',
            width: 120,
            render: (rowData, index) => {
              return h(NSelect, {
                // 数据问题待优化
                value: rowData.role[0],
                options: transformSelect(role.value, 'name', 'id'),
                onUpdateValue: (val: any) => {
                  table.dataList[index].role = val
                  // 用户页面点击更新用户角色
                  put({
                      url: getTableList + rowData.id + "/",
                      data: {"role": [val]},
                    }).then((res) => {
                      message.success('提交成功')
                      doRefresh()
                    }).catch(console.log)
                },
                placeholder: '请选择角色名称',
              })
            },
          },
          {
            title: '上次登录时间',
            key: 'last_login',
            fixed: 'right',
            width: 220,
          },
          {
            title: '状态',
            key: 'is_active',
            fixed: 'right',
            width: 80,
            render: (rowData) =>
              renderTag(!!rowData.is_active ? '正常' : '禁用', {
                type: !!rowData.is_active ? 'success' : 'error',
                size: 'small',
              }),
          },
          {
            title: '操作',
            key: 'actions',
            fixed: 'right',
            width: 80,
            render: (rowData) => {
              return useRenderAction([
                {
                  label: '删除',
                  type: 'error',
                  onClick: onDeleteItem.bind(null, rowData),
                },
              ] as TableActionModel[])
            },
          },
        ],
        {
          align: 'center',
        } as DataTableColumn
      )

      function roleList() {
        get({
          url: getRoleList,
        }).then((res) => {
          role.value = res.results
        })
      }

      function doRefresh() {
        get({
          url: getTableList,
        }).then((res) => {
          table.handleSuccess(res)
          pagination.setTotalSize((res as any).total)
        }).catch(console.log)
      }

      function onRowCheck(rowKeys: Array<any>) {
        checkedRowKeys.length = 0
        checkedRowKeys.push(...rowKeys)
      }

      function onDeleteItem(item: any) {
        naiveDialog.warning({
          title: '提示',
          content: '确定要删除此数据吗？',
          positiveText: '确定',
          onPositiveClick: () => {
            delete_fun({
                  url: getTableList + item.id + '/',
                }).then((res) => {
                  message.success('删除成功')
                  doRefresh()
                })
          },
        })
      }

      function onDeleteItems() {
        naiveDialog.warning({
          title: '提示',
          content: '确定要删除此数据吗？',
          positiveText: '确定',
          onPositiveClick: () => {
            // delete_fun({
            //       url: getTableList + '/' + item.id + '/',
            //     }).then((res) => {
            //       message.success('删除成功')
            //       doRefresh()
            //     })
            message.success('数据模拟删除成功，参数为：' + JSON.stringify(checkedRowKeys))
          },
        })
      }

      onMounted(async () => {
        table.tableHeight.value = await useTableHeight()
        doRefresh()
        roleList()
      })

      return {
        ...table,
        rowKey,
        tableColumns,
        pagination,
        onDeleteItem,
        onDeleteItems,
        onRowCheck
      }
    },
  })
</script>

<style lang="scss" scoped>
  .avatar-container {
    position: relative;
    width: 30px;
    margin: 0 auto;
    vertical-align: middle;
    .avatar {
      width: 100%;
      border-radius: 50%;
    }
    .avatar-vip {
      border: 2px solid #cece1e;
    }
    .vip {
      position: absolute;
      top: 0;
      right: -9px;
      width: 15px;
      transform: rotate(60deg);
    }
  }
  .gender-container {
    .gender-icon {
      width: 20px;
    }
  }
</style>
