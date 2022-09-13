<template>
    <div class="main-container">
        <div style="width: 50%;float: left;padding:10px">
            <n-button type="info" size="small" @click="new_crontab_show=true">新增crontab_schedule</n-button>
            <n-data-table :data="crontab_list.slice(
                      (crontab_page - 1) * crontab_pageSize,
                      crontab_page * crontab_pageSize
                    )" :columns="crontab_tableColumns" :row-key="rowKey" />
            <div class="flex justify-center">
                <n-pagination v-model:page="crontab_page" :page-count="crontab_pageCount" show-size-picker
                    :page-sizes="crontab_pageSizes">
                    <template #prefix="{ itemCount, startIndex }">
                        共 {{ crontab_count }} 项
                    </template>
                </n-pagination>

            </div>
        </div>
        <div style="width: 50%;float: right;padding:10px">
            <n-button type="info" size="small" @click="new_interval_show = true">新增interval_schedule</n-button>
            <n-data-table :data="interval_list.slice(
                      (interval_page - 1) * interval_pageSize,
                      interval_page * interval_pageSize
                    )" :columns="interval_tableColumns" :row-key="rowKey" />
            <div class="flex justify-center">
                <n-pagination v-model:page="interval_page" :page-count="interval_pageCount" show-size-picker
                    :page-sizes="interval_pageSizes">
                    <template #prefix="{ itemCount, startIndex }">
                        共 {{ interval_count }} 项
                    </template>
                </n-pagination>
            </div>
        </div>
        <n-modal v-model:show="new_crontab_show" preset="dialog" title="新增crontab">
            <div>
                <n-form :model="add_crontab_form" label-placement="left" label-width="auto">
                    <n-form-item label="分">
                        <n-input v-model:value="add_crontab_form.minute" placeholder="" />
                    </n-form-item>
                    <n-form-item label="时">
                        <n-input v-model:value="add_crontab_form.hour" placeholder="" />
                    </n-form-item>
                    <n-form-item label="日">
                        <n-input v-model:value="add_crontab_form.day_of_month" placeholder="" />
                    </n-form-item>
                    <n-form-item label="月">
                        <n-input v-model:value="add_crontab_form.month_of_year" placeholder="" />
                    </n-form-item>
                    <n-form-item label="周">
                        <n-input v-model:value="add_crontab_form.day_of_week" placeholder="" />
                    </n-form-item>
                </n-form>
            </div>
            <template #action>
                <div>
                    <n-space>
                        <n-button size="tiny" type="warning" @click="new_crontab_show= false">取消</n-button>
                        <n-button size="tiny" type="info" @click="AddCrontabConfirm()">确认</n-button>
                    </n-space>
                </div>
            </template>
        </n-modal>
        <n-modal v-model:show="new_interval_show" preset="dialog" title="新增interval">
            <div>
                <n-form :model="add_interval_form" label-placement="left" label-width="auto">
                    <n-form-item label="间隔">
                        <n-input v-model:value="add_interval_form.every" placeholder="" />
                    </n-form-item>
                    <n-form-item label="类型">
                        <n-select :options="add_interval_form.period_options" v-model:value="add_interval_form.period">

                        </n-select>

                    </n-form-item>
                </n-form>
            </div>
            <template #action>
                <div>
                    <n-space>
                        <n-button size="tiny" type="warning" @click="new_interval_show=false">取消</n-button>
                        <n-button size="tiny" type="info" @click="AddIntervalConfirm()">确认</n-button>

                    </n-space>
                </div>
            </template>
        </n-modal>
    </div>
</template>

<script lang="ts">
    import {
        getdispach,
    } from '@/api/url'
    import { TableActionModel, useTable, useRenderAction, useTableColumn, usePagination } from '@/hooks/table'
    import { defineComponent, h, nextTick, onMounted, reactive, ref, shallowReactive } from 'vue'
    import _ from 'lodash'
    import { DataTableColumn, NInput, NSelect, SelectOption, useDialog, useMessage, NButton } from 'naive-ui'
    import { DataFormType, ModalDialogType, FormItem, TablePropsType } from '@/types/components'
    import usePost from '@/hooks/usePost'
    import { renderTag } from '@/hooks/form'
    import useGet from '@/hooks/useGet'
    import { sortColumns } from '@/utils'

    // import { windowOpen } from 'echarts/types/src/util/format'
    import Cookies from 'js-cookie'

    export default defineComponent({
        name: 'dispatch_manage',
        setup() {
            const new_crontab_show = ref(false)
            const new_interval_show = ref(false)
            const add_crontab_form = ref({
                minute: ref('*'),
                hour: ref('*'),
                day_of_month: ref('*'),
                month_of_year: ref("*"),
                day_of_week: ref('*'),
                timezone: ref('Asia/Shanghai')

            })
            const add_interval_form = ref({
                every: ref('0'),
                period_options: ref([
                    { value: 'days', label: '天' },
                    { value: 'hours', label: '小时' },
                    { value: 'minutes', label: '分钟' },
                    { value: 'seconds', label: '秒' },
                    { value: 'microseconds', label: '毫秒' },
                ]),
                period: ref('')
            })
            const crontab_count = ref(0)
            const interval_count = ref(0)
            const table = useTable()
            const pagination = usePagination(doRefresh)
            pagination.pageSize = 10
            pagination.limit = 10
            pagination.start = 0
            const searchForm = ref < DataFormType | null > (null)
            const message = useMessage()
            const naiveDailog = useDialog()
            const config_detail = ref('')
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
                                    return h(NButton, { type: 'error' }, '禁用')
                                } else {
                                    return h(NButton, { type: 'primary' }, '启用')
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
                                return useRenderAction([
                                    {
                                        label: '详细/修改',
                                        // onClick: show_config.bind(null, rowData),
                                    },

                                ] as TableActionModel[])
                            },
                        },
                        {
                            title: '停止',
                            key: 'config_file',
                            // render:(rowData)=>{
                            //  return  h('a', {
                            //    href:rowData.config_file,
                            //   }, '下载配置')
                            render: (rowData) => {
                                return h(NButton, { type: 'warning' }, '停止')
                            },
                        },
                        {
                            title: '删除',
                            key: 'config_file',
                            // render:(rowData)=>{
                            //  return  h('a', {
                            //    href:rowData.config_file,
                            //   }, '下载配置')
                            render: (rowData) => {
                                return h(NButton, { type: 'error' }, '删除')
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
                                return h(NButton, { type: 'info' }, '运行')
                            },
                        },
                    ],
                    {
                        align: 'center',
                    } as DataTableColumn),
            )
            const itemDataFormRef = ref < DataFormType | null > (null)
            const searchDataFormRef = ref < DataFormType | null > (null)
            const modalDialog = ref < ModalDialogType | null > (null)
            const WebsshmodalDialog = ref < ModalDialogType | null > (null)
            const get = useGet()
            const post = usePost()


            const crontab_tableColumns = reactive(
                useTableColumn(
                    [
                        {
                            title: '分',
                            key: 'minute',
                            // width: '100px',
                        },
                        {
                            title: '时',
                            key: 'hour',
                            // width: '100px',
                        },
                        {
                            title: '日',
                            key: 'day_of_week',
                            // width: '100px',
                        },
                        {
                            title: '月',
                            key: 'day_of_month',
                            // width: '100px',
                        },
                        {
                            title: '周',
                            key: 'month_of_year',
                            // width: '100px',
                        },
                        {
                            title: '操作',
                            key: 'actions',
                            render: (rowData) => {
                                return h(NButton, {
                                    type: 'error',
                                    size: 'tiny',
                                    onClick: delete_crontab.bind(null, rowData),
                                }, () => h('span', {}, '删除'))
                                // return useRenderAction([
                                //   {
                                //     label: 'Edit',
                                //     onClick: EditFunction.bind(null, rowData),
                                //   },
                                //
                                // ] as TableActionModel[])
                            },
                        },

                    ],
                    {
                        align: 'center',
                    } as DataTableColumn),
            )

            const interval_tableColumns = reactive(
                useTableColumn(
                    [
                        {
                            title: '间隔',
                            key: 'every',
                            // width: '100px',
                        },
                        {
                            title: '类型',
                            key: 'period',
                            // width: '100px',
                            render: (rowData) => {
                                if (rowData.period === 'days') {
                                    return '天'
                                }
                                if (rowData.period === 'hours') {
                                    return '小时'
                                }
                                if (rowData.period === 'minutes') {
                                    return '分钟'
                                }
                                if (rowData.period === 'seconds') {
                                    return '秒'
                                }
                            },
                        },
                        {
                            title: '操作',
                            key: 'actions',
                            render: (rowData) => {
                                return h(NButton, {
                                    type: 'error',
                                    size: 'tiny',
                                    onClick: delete_interval.bind(null, rowData),
                                }, () => h('span', {}, '删除'))
                                // return useRenderAction([
                                //   {
                                //     label: 'Edit',
                                //     onClick: EditFunction.bind(null, rowData),
                                //   },
                                //
                                // ] as TableActionModel[])
                            },
                        },

                    ],
                    {
                        align: 'center',
                    } as DataTableColumn),
            )
            const crontab_list = shallowReactive([]) as Array<any>
            const crontab_tag_list = shallowReactive([]) as Array<any>
            const crontab_page = ref < number > (1)
            const crontab_pageSize = ref < number > (10)
            const crontab_pageCount = ref < number > (1)
            const crontab_keyword = ref('')
            // const second_password = ref('')
            const crontab_pageSizes = [
                {
                    label: '10 每页',
                    value: 10,
                },
                {
                    label: '50 每页',
                    value: 50,
                },
                {
                    label: '100 每页',
                    value: 100,
                },
                {
                    label: '200 每页',
                    value: 200,
                },
            ]


            const interval_list = shallowReactive([]) as Array<any>
            const interval_tag_list = shallowReactive([]) as Array<any>
            const interval_page = ref < number > (1)
            const interval_pageSize = ref < number > (10)
            const interval_pageCount = ref < number > (1)
            const interval_keyword = ref('')
            // const second_password = ref('')
            const interval_pageSizes = [
                {
                    label: '10 每页',
                    value: 10,
                },
                {
                    label: '50 每页',
                    value: 50,
                },
                {
                    label: '100 每页',
                    value: 100,
                },
                {
                    label: '200 每页',
                    value: 200,
                },
            ]


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
                    url: getdispach,
                }).then((res) => {
                    if (res.code === 200) {
                        crontab_list.length = 0
                        crontab_list.push(...res.crontab_data)
                        crontab_page.value = 1
                        crontab_pageSize.value = 10
                        crontab_pageCount.value = Math.ceil(crontab_list.length / 10)
                        crontab_count.value = crontab_list.length


                        interval_list.length = 0
                        interval_list.push(...res.interval_data)
                        interval_page.value = 1
                        interval_pageSize.value = 10
                        interval_pageCount.value = Math.ceil(interval_list.length / 10)
                        interval_count.value = interval_list.length
                    }
                })
            }


            function onDataFormConfirm() {
                if (itemDataFormRef.value?.validator()) {
                    modalDialog.value?.toggle()
                    naiveDailog.success({
                        title: '提示',
                        positiveText: '确定',
                        content:
                            '模拟部门添加/编辑成功，数据为：' +
                            JSON.stringify(itemDataFormRef.value.generatorParams()),
                    })
                }
            }





            function rowKey(rowData: any) {
                return rowData.id
            }

            function delete_crontab(item) {
                //console.log('删除crontab', item)
                let delete_formdata = new FormData()
                delete_formdata.append('csrfmiddlewaretoken', Cookies.get('csrftoken'))
                delete_formdata.append('schedule_type', 'crontab_schedule')
                delete_formdata.append('id', item.id)
                delete_formdata.append('delete', '1')
                post({
                    url: getdispach,
                    data: delete_formdata,
                }).then((res) => {
                    if (res.code === 200) {
                        message.success(res.msg)
                        doRefresh()
                    }
                })
            }

            function delete_interval(item) {
                //console.log('删除crontab', item)
                let delete_formdata = new FormData()
                delete_formdata.append('csrfmiddlewaretoken', Cookies.get('csrftoken'))
                delete_formdata.append('schedule_type', 'interval_schedule')
                delete_formdata.append('id', item.id)
                delete_formdata.append('delete', '1')
                post({
                    url: getdispach,
                    data: delete_formdata,
                }).then((res) => {
                    if (res.code === 200) {
                        message.success(res.msg)
                        doRefresh()
                    }
                })
            }
            function AddCrontabConfirm() {
                console.log(add_crontab_form.value)
                var post_params = add_crontab_form.value
                var new_crontab_formdata = new FormData()
                new_crontab_formdata.append("add_crontab_schedule", '1')
                new_crontab_formdata.append("minute", post_params['minute'])
                new_crontab_formdata.append("hour", post_params['hour'])
                new_crontab_formdata.append("timezone", post_params['timezone'])
                new_crontab_formdata.append("day_of_month", post_params['day_of_month'])
                new_crontab_formdata.append("month_of_year", post_params['month_of_year'])
                new_crontab_formdata.append("day_of_week", post_params['day_of_week'])


                post({
                    url: getdispach,
                    data: new_crontab_formdata,
                }).then((res) => {
                    if (res.code === 200) {
                        new_crontab_show.value = false
                        message.success(res.msg)
                        doRefresh()
                    } else {
                        message.error(res.msg)
                    }
                })
            }
            function AddIntervalConfirm() {
                console.log(add_interval_form.value)
                var post_params = add_interval_form.value
                var new_crontab_formdata = new FormData()
                new_crontab_formdata.append("add_interval_schedule", '1')
                new_crontab_formdata.append("period", post_params['period'])
                new_crontab_formdata.append("every", post_params['every'])


                post({
                    url: getdispach,
                    data: new_crontab_formdata,
                }).then((res) => {
                    if (res.code === 200) {
                        new_interval_show.value = false
                        message.success(res.msg)
                        doRefresh()
                    } else {
                        message.error(res.msg)
                    }
                })
            }
            onMounted(doRefresh)
            return {
                AddCrontabConfirm, 
                AddIntervalConfirm,
                crontab_count,
                interval_count,
                new_crontab_show,
                add_crontab_form,
                add_interval_form,
                new_interval_show,
                delete_crontab,
                delete_interval,
                itemDataFormRef,
                searchDataFormRef,
                onDataFormConfirm,
                tableColumns,
                config_detail,
                pagination,
                searchForm,
                onResetSearch,
                ...table,

                rowKey,
                modalDialog,
                WebsshmodalDialog,

                onUpdateTable,
                onUpdateBorder,
                doRefresh,

                crontab_list,
                crontab_page,
                crontab_pageSize,
                crontab_pageSizes,
                crontab_keyword,
                crontab_pageCount,
                crontab_tableColumns,


                interval_list,
                interval_page,
                interval_pageSize,
                interval_pageSizes,
                interval_keyword,
                interval_pageCount,
                interval_tableColumns,
            }
        },
    })
</script>