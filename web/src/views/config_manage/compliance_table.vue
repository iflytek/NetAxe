<template>
  <TableBody>
    <template #header>
      <TableHeader
        :show-filter="true"
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
      </TableHeader>
    </template>
    <template #default>
      <n-data-table
        :columns="ComplianceTableColumns"
        :data="compliance_res_table_data"
        :pagination="pagination"
        :row-key="rowKey"
        :style="{ height: `${tableHeight}px` }"
        default-expand-all
      />
    </template>
  </TableBody>
</template>

<script setup lang="ts">
  import { ref, onMounted, h, nextTick } from 'vue'
  import { NTag, useMessage, DataTableColumn, NSelect, NInput, SelectOption } from 'naive-ui'
  import { useTableColumn, useTable, useTableHeight } from '@/hooks/table'
  import { get_compliance_results } from '@/api/url'
  import { DataFormType, FormItem } from '@/types/components'
  import useGet from '@/hooks/useGet'
  const table = useTable()
  const get = useGet()
  const message = useMessage()
  const tableHeight = ref(500)
  // 查询参数
  const query_params = ref({
    get_results: 1,
  })
  const compliance_res_table_data = ref([])
  const conditionItems: Array<FormItem> = [
    {
      key: 'rule',
      label: '规则名',
      value: ref(null),
      render: (formItem) => {
        return h(NInput, {
          value: formItem.value.value,
          onUpdateValue: (val) => {
            formItem.value.value = val
          },
          placeholder: '请输入规则名',
        })
      },
    },
    {
      key: 'compliance',
      label: '是否合规',
      value: ref(null),
      optionItems: [
        {
          label: '合规',
          value: '合规',
        },
        {
          label: '不合规',
          value: '不合规',
        },
      ],
      render: (formItem) => {
        return h(NSelect, {
          options: formItem.optionItems as Array<SelectOption>,
          value: formItem.value.value,
          placeholder: '请选择用户姓别',
          onUpdateValue: (val) => {
            formItem.value.value = val
          },
        })
      },
    },
  ]
  const ComplianceTableColumns = useTableColumn(
    [
      {
        title: '规则名称',
        key: 'rule',
      },
      {
        title: '厂家',
        key: 'vendor',
      },
      {
        title: '设备',
        key: 'hostip',
      },
      {
        title: '更新时间',
        key: 'log_time',
      },
      {
        title: '是否合规',
        key: 'compliance',
        render(row) {
          let _type = row.compliance == '合规' ? 'success' : 'error'
          return h(
            NTag,
            {
              style: {
                marginRight: '6px',
              },
              type: _type,
              bordered: false,
            },
            {
              default: () => row.compliance,
            }
          )
        },
      },
    ],
    {
      align: 'center',
    } as DataTableColumn
  )
  const pagination = {
    pageSize: 20,
  }
  const searchForm = ref<DataFormType | null>(null)
  function rowKey(rowData: any) {
    return rowData.id
  }
  function get_compliance_result() {
    get({
      url: get_compliance_results,
      data: () => {
        return query_params.value
      },
    }).then((res) => {
      if (res.code == 404) {
        message.warning('没有合规检查数据')
        compliance_res_table_data.value = []
      } else {
        compliance_res_table_data.value = res.data
      }
    })
  }
  function onSearch() {
    query_params.value = searchForm.value?.generatorParams()
    get_compliance_result()
    // message.success('模拟查询成功，参数为：' + JSON.stringify(searchForm.value?.generatorParams()))
  }
  function onResetSearch() {
    searchForm.value?.reset()
  }
  onMounted(async () => {
    tableHeight.value = await useTableHeight()
    get_compliance_result()
  })
</script>

<style lang="scss" scoped></style>
