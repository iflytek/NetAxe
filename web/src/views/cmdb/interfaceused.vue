<template>
    <div class="main-container">
        <TableBody>
            <template #header>
                <TableHeader :show-filter="false" title="查询条件" @search="onSearch" @reset-search="onResetSearch">
                    <template #search-content>
                        <DataForm ref="searchForm" :form-config="{
                            labelWidth: 60,
                        }" :options="conditionItems" preset="grid-item" />
                    </template>
                    <template #table-config>
                        <TableConfig @update-border="onUpdateBorder" @refresh="doRefresh" />
                        <SortableTable class="ml-4" :columns="tableColumns" @update="onUpdateTable" />
                    </template>
                </TableHeader>
            </template>
            <template #default>
                <DataForm ref="searchForm" :form-config="{
                    labelWidth: 60,
                }" :options="conditionItems" preset="grid-item" />
                <n-space style="float: right; padding-bottom: 20px">
                    <n-button style="float: right" size="small" type="info" @click="onSearch()">查询
                    </n-button>
                    <n-button style="float: right" size="small" type="success" @click="onResetSearch()">重置
                    </n-button>
                    <n-button style="float: right" size="small" type="warning" @click="chart_show = true">运营数据展示
                    </n-button>
                </n-space>
                <n-data-table :loading="tableLoading" :data="dataList" :columns="tableColumns" :single-line="!bordered"
                    :row-key="rowKey" />
            </template>
            <template #footer>
                <TableFooter :pagination="pagination" />
            </template>
        </TableBody>

        <n-modal v-model:show="chart_show" preset="dialog" header-style="padding: 10px 20px" title="接口利用率运营数据"
            :style="{ height: '500px', width: '1300px' }" :mask-closable="false">
        </n-modal>
    </div>
</template>

<script lang="ts">
import {
    getInterfaceUsedList,
    getCmdbIdcList,
    getCmdbRoleList,
    getVendorList,
    getCategoryList,
} from '@/api/url'
import { useTable, useTableColumn, usePagination } from '@/hooks/table'
import { defineComponent, h, nextTick, onMounted, reactive, ref, shallowReactive } from 'vue'
import _ from 'lodash'
import { DataTableColumn, NInput, useDialog, useMessage, NDatePicker } from 'naive-ui'
import { DataFormType, ModalDialogType, FormItem, TablePropsType } from '@/types/components'
import useGet from '@/hooks/useGet'
import { sortColumns } from '@/utils'

export default defineComponent({
    name: 'interfaceused',
    components: {},
    setup() {
        const chart_show = ref(false)
        const conditionItems: Array<FormItem> = [
            {
                key: 'name',
                label: '设备名',
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
                        placeholder: '请输入设备名',
                    })
                },
            },
            {
                key: 'host_ip',
                label: '管理IP',
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
                        placeholder: '请输入管理IP',
                    })
                },
            },
            {
                key: 'log_time',
                label: '日期',
                value: ref(Date.now()),
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
                key: 'search',
                label: '搜索',
                value: ref(''),
                render: (formItem) => {
                    return h(NInput, {
                        value: formItem.value.value,
                        onUpdateValue: (val) => {
                            formItem.value.value = val
                        },
                        placeholder: '全局搜索关键字',
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
        const tableColumns = reactive(
            useTableColumn(
                [
                    table.selectionColumn,
                    // table.indexColumn,
                    {
                        title: '主机',
                        key: 'host',
                    },
                    {
                        title: '管理IP',
                        key: 'host_ip',
                    },
                    {
                        title: '记录日期',
                        key: 'log_time',
                    },
                    {
                        title: '接口总数',
                        key: 'int_total',
                    },
                    {
                        title: '1g',
                        key: 'int_used_1g_status',
                        render(rowData) {
                            return (rowData.int_used_1g ? rowData.int_used_1g : 0) + '/' + (rowData.int_used_1g + rowData.int_unused_1g)
                        },
                    },
                    {
                        title: '10g',
                        key: 'int_used_10g_status',
                        render(rowData) {
                            return (rowData.int_used_10g ? rowData.int_used_10g : 0) + '/' + (rowData.int_used_10g + rowData.int_unused_10g)
                        },
                    },
                    {
                        title: '20g',
                        key: 'int_used_20g_status',
                        render(rowData) {
                            return (rowData.int_used_20g ? rowData.int_used_20g : 0) + '/' + (rowData.int_used_20g + rowData.int_unused_20g)
                        },
                    },
                    {
                        title: '25g',
                        key: 'int_used_25g',
                        render(rowData) {
                            return (rowData.int_used_25g ? rowData.int_used_25g : 0) + '/' + (rowData.int_used_25g + rowData.int_unused_25g)
                        },
                    },

                    {
                        title: '40g',
                        key: 'int_used_40g_count',
                        render(rowData) {
                            return (rowData.int_used_40g ? rowData.int_used_40g : 0) + '/' + (rowData.int_used_40g + rowData.int_unused_40g)
                        },
                    },
                    {
                        title: '100g',
                        key: 'int_used_100g',
                        render(rowData) {
                            return (
                                (rowData.int_used_100g ? rowData.int_used_100g : 0) + '/' + (rowData.int_used_100g + rowData.int_unused_100g)
                            )
                        },
                    },
                    {
                        title: '10M',
                        key: 'int_used_10m',
                        render(rowData) {
                            return (rowData.int_used_10m ? rowData.int_used_10m : 0) + '/' + (rowData.int_used_10m + rowData.int_unused_10m)
                        },
                    },
                    {
                        title: '100M',
                        key: 'int_used_100m',
                        render(rowData) {
                            return (
                                (rowData.int_used_100m ? rowData.int_used_100m : 0) + '/' + (rowData.int_used_100m + rowData.int_unused_100m)
                            )
                        },
                    },
                    {
                        title: '已使用',
                        key: 'int_used',
                    },
                    {
                        title: '未使用',
                        key: 'int_unused',
                    },
                    {
                        title: '使用率',
                        key: 'utilization',
                        render(rowData) {
                            return rowData.utilization + '%'
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
        const WebsshmodalDialog = ref<ModalDialogType | null>(null)
        const get = useGet()

        function getFormtTime(dateTime) {
            if (dateTime != null) {
                //若传入的dateTime为字符串类型，需要进行转换成数值，若不是无需下面注释代码
                //var time = parseInt(dateTime)
                var date = new Date(dateTime)
                //获取年份
                var YY = date.getFullYear()
                //获取月份
                var MM = date.getMonth() + 1 < 10 ? '0' + (date.getMonth() + 1) : date.getMonth() + 1
                //获取日期
                var DD = date.getDate() < 10 ? '0' + date.getDate() : date.getDate()
                //返回时间格式： 2020-11-09
                return YY + '-' + MM + '-' + DD
            } else {
                return ''
            }
        }

        function onSearch() {
            // console.log(searchForm.value?.generatorParams())
            const search_form = searchForm.value?.generatorParams()
            get({
                url:
                    getInterfaceUsedList +
                    '?host=' +
                    search_form.name +
                    '&host_ip=' +
                    search_form.host_ip +
                    '&log_time=' +
                    getFormtTime(search_form.log_time) +
                    '&search=' +
                    search_form.search,
                data: () => {
                    return {
                        start: 0,
                        // pageSize: pagination.pageSize,
                        limit: pagination.pageSize,
                    }
                },
            }).then((res) => {
                // console.log(res)
                if (res.code === 200) {
                    message.success('查询成功')
                    table.handleSuccess(res)
                    pagination.setTotalSize(res.count || 10)
                } else {
                    message.success('查询失败:' + res.msg)
                    table.handleSuccess(res)
                    pagination.setTotalSize(res.count || 10)
                }
            })
        }

        function onResetSearch() {
            // searchForm.value?.reset()
            doRefresh()
        }

        function onUpdateBorder(isBordered: boolean) {
            table.bordered.value = isBordered
        }

        function onUpdateTable(newColumns: Array<TablePropsType>) {
            sortColumns(tableColumns, newColumns)
        }

        function doRefresh() {
            get({
                url: getInterfaceUsedList,
                data: () => {
                    return {
                        start: (pagination.page - 1) * pagination.pageSize,
                        // pageSize: pagination.pageSize,
                        limit: pagination.pageSize,
                        status: 0,
                    }
                },
            }).then((res) => {
                // console.log(res)
                table.handleSuccess(res)
                pagination.setTotalSize(res.count || 10)
            })
        }

        function rowKey(rowData: any) {
            return rowData.id
        }

        onMounted(doRefresh)
        return {
            itemDataFormRef,
            searchDataFormRef,

            tableColumns,

            pagination,
            searchForm,
            onResetSearch,
            onSearch,
            ...table,

            rowKey,
            modalDialog,
            WebsshmodalDialog,
            conditionItems,
            onUpdateTable,
            onUpdateBorder,
            doRefresh,

            getFormtTime,
            chart_show,
        }
    },
})
</script>
