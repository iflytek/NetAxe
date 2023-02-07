<template>
  <div class="main-container">
    <div style="width: 25%; padding: 10px; border-top: 1px solid #000; float: left">
      <n-space style="padding-bottom: 20px" justify="start" :inline="true">
        <!--        <n-input v-model:value="subnet_search_keyword" placeholder="搜索" size="small"-->
        <!--                 @keyup.enter.native="tree_filter" style="width: 125px"/>-->
        <n-input v-model:value="pattern" placeholder="搜索"/>
        <n-button size="medium" type="primary" @click="tree_filter">搜索</n-button>
        <n-button size="medium" type="warning" @click="clear_keywords">清除</n-button>
      </n-space>
      <div style="padding-top: 20px; border-top: 1px solid; border-right: 1px solid">
        <!--        <n-space justify="space-between">-->
        <n-button size="medium" type="info" @click="open_export" disabled style="float: left"
        >导出网段
        </n-button
        >
        <n-button size="medium" type="info" style="float: right" @click="create_subnet()"
        >新增网段
        </n-button
        >
        <!--        </n-space>-->
        <!--        左侧树形结构展示网段信息-->
        <n-tree
            :data="tree_data"
            virtual-scroll
            :node-props="nodeProps"
            :default-expand-all="false"
            :show-irrelevant-nodes="false"
            :render-switcher-icon="renderSwitcherIcon"
            style="height: 600px"
            :pattern="pattern"
            block-line
        />

        <!--        <n-card >-->

        <!--        </n-card>-->
      </div>
    </div>
    <!--    详情-饼图-文字-展示图-->
    <div
        v-show="detail_show"
        style="width: 70%; height: 100%; padding: 10px; float: right; border-top: 1px solid #000"
    >
      <n-grid x-gap="2" :cols="2">
        <n-gi>
          <div class="bold-attribute" style="font-size: 20px">详情</div>
          <div v-show="subnet_info.subnet.indexOf(':')!==-1" style="color: red">因ipv6网段地址较多,下图仅展示单次请求结果数据-可滚动查询下一分页
          </div>
          <div style="float: left; width: 100%">
            <div>
              <span class="bold-attribute">网段:</span>
              {{ subnet_info.subnet }}
            </div>
            <div>
              <span class="bold-attribute">已使用:</span>
              {{ subnet_info.used }}%
            </div>
            <div>
              <span class="bold-attribute">未使用:</span>
              {{ subnet_info.freehosts }}%
            </div>
            <div>
              <span class="bold-attribute">使用率:</span>
              Used: {{ subnet_info.Used_percent }}% | Free: {{ subnet_info.freehosts_percent }}% |
              Total:{{ subnet_info.maxhosts }}
            </div>
            <div>
              <span class="bold-attribute">描述:</span>
              {{ subnet_info.desc }}
              <n-button text style="font-size: 20px" @click="change_desc()">
                <n-icon>
                  <cash-icon/>
                </n-icon>
              </n-button>
            </div>
          </div>
        </n-gi>
        <n-gi>
          <div style="float: right; width: 100%">
            <!--        <n-skeleton text v-if="loading" :repeat="4" />-->
            <!--        <template v-else>-->
            <div ref="channelsChart" class="chart-item"></div>
            <!--        </template>-->
            <!--        <EnrollmentChannelsChart ref="enrollmentChannelsChart" />-->
          </div>
        </n-gi>
      </n-grid>
      <n-space style="margin-bottom: 5px">
        <n-button size="small" @click="dispatch_ip" type="primary">分配</n-button>
        <n-button size="small" @click="dispatch_many_func" type="info">批量分配</n-button>
        <n-popconfirm @positive-click="recycle_many_func" @negative-click="">
          <template #trigger>
            <n-button size="small" type="error">回收</n-button>
          </template>
          请确认是否回收该地址
        </n-popconfirm>
        <!--        <n-button size="medium" type="error" @click="back_ip" >回收</n-button>-->
        <n-button size="small" @click="clear_select" type="warning">清除选中</n-button>
        <n-button size="small" @click="select_all" type="success">全选</n-button>
        <n-button size="small" @click="table_type_func">表格形式</n-button>
        <div v-for="item in uniq4(subnet_tag_list)" :key="item">
          <n-tag size="small" type="info" closable @close="handleCloseTag(item)"> {{ item }}</n-tag>
        </div>
      </n-space>
      <n-scrollbar trigger="none" style="max-height: 500px" @scroll="handleScroll">
        <div>
          <n-button
              style="width: 160px;padding:5px 0;margin: 0 10px 10px 0px;"
              :id="ip_info.address"
              v-for="ip_info of subnet_info.result_list"
              :key="ip_info.address"
              @click="subnet_click(ip_info.address)"
              :value="ip_info.address"
              :class="
              port_style(ip_info.tag)
            "
          >
            {{ ip_info.address }}
          </n-button>
        </div>
      </n-scrollbar>


    </div>

    <ModalDialog ref="modalDialog" title="网段信息" :style="{ height: '768px', width: '1000px' }">
      <template #content>
        <n-button type="info" size="small" style="float: right" @click="export_ipam"
        >导出EXCEL
        </n-button
        >
        <n-data-table
            :loading="subnet_loading"
            :data="
              subnet_list.slice((subnet_page - 1) * subnet_pageSize, subnet_page * subnet_pageSize)
            "
            :columns="subnet_tableColumns"
            :row-key="rowKey"
        />
        <div class="flex justify-center">
          <n-pagination
              v-model:page="subnet_page"
              :page-count="subnet_pageCount"
              show-size-picker
              :page-sizes="subnet_pageSizes"
          />
        </div>
      </template>
    </ModalDialog>

    <ModalDialog
        ref="table_modalDialog"
        title="网段详情表格形式"
        :style="{ height: '768px', width: '1000px' }"
    >
      <template #content>
        <n-button type="info" size="small" style="float: right" @click="export_ipam_detail"
        >导出EXCEL
        </n-button
        >
        <n-data-table
            :data="
              detail_list.slice((detail_page - 1) * detail_pageSize, detail_page * detail_pageSize)
            "
            :columns="detail_tableColumns"
            :row-key="detail_rowKey"
        />
        <div class="flex justify-center">
          <n-pagination
              v-model:page="detail_page"
              v-model:page-size="detail_pageSize"
              :page-count="detail_pageCount"
              show-size-picker
              :page-sizes="detail_pageSizes"
          />
        </div>
      </template>
    </ModalDialog>
    <ModalDialog ref="dispatch_modalDialog" title="地址分配" @confirm="dispatch_confirm">
      <template #content>
        <li
        >目前自动化手段采集的数据只能作为辅助决策，现网操作请慎之又慎，注意流程、宣贯、人工复核
        </li
        >
        <li
        >目前网络自动化工作还处于起步阶段，平台稳定性、功能模块逻辑、设备自身BUG都会导致数据偏移，尤其设备自身bug或版本差异导致的结果差异很难在前期功能开发过程中一一发现识别
        </li
        >
        <li><span style="color: red">总之: 网络不能再出事，我们已不能再承受</span></li>
        <!--        <n-button type="info" size="small" style="float: right" @click="export_ipam_detail">导出EXCEL</n-button>-->
        <n-data-table
            :data="
              dispatch_list.slice(
                (dispatch_page - 1) * dispatch_pageSize,
                dispatch_page * dispatch_pageSize
              )
            "
            :columns="dispatch_tableColumns"
            :row-key="dispatch_rowKey"
        />
        <div class="flex justify-center">
          <n-pagination
              v-model:page="dispatch_page"
              :page-count="dispatch_pageCount"
              show-size-picker
              :page-sizes="dispatch_pageSizes"
          />
        </div>
      </template>
    </ModalDialog>
    <ModalDialog
        ref="dispatch_many_modalDialog"
        title="批量地址分配"
        :style="{ height: '650px', width: '800px' }"
        @confirm="DispatchManyConfirm"
    >
      <template #content>
        <li
        >目前自动化手段采集的数据只能作为辅助决策，现网操作请慎之又慎，注意流程、宣贯、人工复核
        </li
        >
        <li
        >目前网络自动化工作还处于起步阶段，平台稳定性、功能模块逻辑、设备自身BUG都会导致数据偏移，尤其设备自身bug或版本差异导致的结果差异很难在前期功能开发过程中一一发现识别
        </li
        >
        <li><span style="color: red">总之: 网络不能再出事，我们已不能再承受</span></li>
        <!--        <n-button type="info" size="small" style="float: right" @click="export_ipam_detail">导出EXCEL</n-button>-->
        <!--        <template #content>-->
        <DataForm
            ref="dispatch_many_DataFormRef"
            :form-config="{
              labelWidth: 60,
            }"
            :rules="rules"
            preset="form-item"
            :options="dispatch_many_FormOptions"
        />
        <!--        </template>-->
      </template>
    </ModalDialog>
    <n-modal v-model:show="add_root_show" preset="dialog" title="新增根网络">
      <div>
        <n-form :model="add_root_form" label-placement="top" label-width="auto">
          <n-form-item label="子网Subnet">
            <n-input
                v-model:value="add_root_form.add_subnet"
                placeholder="8.8.0.0/16严格CIDR格式"
            />
          </n-form-item>
          <n-form-item label="网段描述\nDescription">
            <n-input v-model:value="add_root_form.add_description" placeholder="Description"/>
          </n-form-item>

          <n-form-item label="父节点master">
            <n-input
                v-model:value="add_root_form.master_subnet_id.split('-')[0]"
                disabled
                placeholder="ROOT"
            />
          </n-form-item>
        </n-form>
      </div>
      <template #action>
        <div>
          <n-space>
            <n-button size="tiny" type="warning" @click="CancelRoot()">取消</n-button>
            <n-button size="tiny" type="info" @click="AddRootConfirm()">确认</n-button>
          </n-space>
        </div>
      </template>
    </n-modal>
    <n-modal v-model:show="add_subnet_show" preset="dialog" title="新增子网">
      <div>
        <n-form :model="add_subnet_form" label-placement="top" label-width="auto">
          <n-form-item label="子网Subnet">
            <n-input
                v-model:value="add_subnet_form.add_subnet"
                placeholder="8.8.0.0/16严格CIDR格式"
            />
          </n-form-item>
          <n-form-item label="网段描述\nDescription">
            <n-input v-model:value="add_subnet_form.add_description" placeholder="Description"/>
          </n-form-item>

          <n-form-item label="父节点master">
            <n-input
                v-model:value="add_subnet_form.master_subnet_id.split('-')[0]"
                disabled
                placeholder="ROOT"
            />
          </n-form-item>
        </n-form>
      </div>
      <template #action>
        <div>
          <n-space>
            <n-button size="tiny" type="warning" @click="CancelRoot()">取消</n-button>
            <n-button size="tiny" type="info" @click="AddSubnetConfirm()">确认</n-button>
          </n-space>
        </div>
      </template>
    </n-modal>
    <n-modal v-model:show="change_desc_show" preset="dialog" title="修改网段描述">
      <n-form :model="change_desc_form" label-placement="top" label-width="auto">
        <n-form-item label="子网">
          <n-input
              v-model:value="change_desc_form.subnet"
              placeholder="8.8.0.0/16严格CIDR格式"
              disabled
          />
        </n-form-item>
        <n-form-item label="描述">
          <n-input
              v-model:value="change_desc_form.description"
              placeholder="description"
              @keyup.enter.native="change_desc_submit()"
          />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script lang="ts">
import { TreeOption } from 'naive-ui'
import { getSubnetTree, getSubnetAddress, PostAddressHandel } from '@/api/url'
import usePost from '@/hooks/usePost'
import useGet from '@/hooks/useGet'
import {
  computed,
  defineComponent,
  h,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  shallowReactive,
} from 'vue'
import { Pencil as CashIcon } from '@vicons/ionicons5'
import {
  DataTableColumn,
  NInput,
  NSelect,
  NButton,
  NForm,
  NFormItem,
  SelectOption,
  useDialog,
  useMessage,
  NInputGroup,
  NIcon,
} from 'naive-ui'
import { ChevronForward } from '@vicons/ionicons5'

import { DataFormType, ModalDialogType } from '@/types/components'
import { useTableColumn } from '@/hooks/table'
import Cookies from 'js-cookie'
import useEcharts from '@/hooks/useEcharts'


export default defineComponent({
  components: {
    CashIcon,
  },

  setup() {
    const roll = ref(null)
    const used_port = []
    const channelsChart = ref<HTMLDivElement | null>(null)
    const button_roll = ref<HTMLDivElement | null>(null)
    const utilization_option = {
      tooltip: {
        trigger: 'item',
        formatter: '分布<br/>{b}<br/>{c}',
      },
      legend: {
        // top: '5%',
        // orient: 'vertical',
        left: 'center',
      },
      series: [
        {
          name: '子网使用情况',
          type: 'pie',
          // radius: ['50%', '70%'],
          radius: '50%',
          // center:['60%', '40%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            // show: false,
            // position: 'center',
            show: true, //由于默认是外部，所以这里没有写position:'outside'
            color: '#dbba97',
            fontSize: '10',
            formatter: '{b}\n\n{c}%',
            padding: [0, 0, 0, 0],
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '10',
              // fontWeight: 'bold'
            },
          },
          labelLine: {
            show: false,
          },
          data: [],
        },
      ],
    }
    const request_next_status = ref(false)
    const subnet_info = ref({
      desc: ref(''),
      table_type: ref([]),
      subnet_id: ref(0),
      subnet: ref(''),
      next_page_url: ref(''),
      result_list: shallowReactive([]) as Array<any>,
      count: ref(0),
      maxhosts: ref(0),
    })
    const refresh_subnet_id = ref(0)
    const change_desc_form = ref({})
    let webSocket = null
    let socketOpen = false
    const detail_show = ref(false)
    const subnet_loading = ref(true)
    const change_desc_show = ref(false)
    const dispatch_many_DataFormRef = ref<DataFormType | null>(null)
    const dispatch_many_FormOptions = [
      {
        key: 'start_ip',
        label: '起始地址',
        path: 'start_ip',
        required: true,
        value: ref(''),
        // optionItems: shallowReactive([] as Array<SelectOption>),
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
        key: 'end_ip',
        label: '结束地址',
        value: ref(''),
        required: true,
        // optionItems: shallowReactive([] as Array<SelectOption>),
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
        key: 'dispatch_status',
        label: '分配状态',
        value: ref('6'),
        optionItems: [
          { value: '1', label: '空闲' },
          { value: '2', label: '已分配已使用' },
          { value: '3', label: '保留' },
          { value: '4', label: '未分配已使用' },
          { value: '6', label: '已分配未使用' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择分配状态',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'description',
        label: '描述信息',
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
        key: 'bgbu',
        label: 'BGBU',
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
    ]
    const get = useGet()
    const post = usePost()
    const message = useMessage()
    const modalDialog = ref<ModalDialogType | null>(null)
    const table_modalDialog = ref<ModalDialogType | null>(null)
    const dispatch_modalDialog = ref<ModalDialogType | null>(null)
    const dispatch_many_modalDialog = ref<ModalDialogType | null>(null)

    const subnet_tableColumns = reactive(
        useTableColumn(
            [
              {
                title: '网段',
                key: 'subnet',
                // width: '100px',
              },
              {
                title: '掩码',
                key: 'mask',
                // width: '120px',
              },
              {
                title: '描述信息',
                key: 'description',
                // width: '150px',
              },
            ],
            {
              align: 'center',
            } as DataTableColumn,
        ),
    )
    const detail_tableColumns = reactive(
        useTableColumn(
            [
              {
                title: '地址',
                key: 'address',
                // width: '100px',
              },
              {
                title: '标签',
                key: 'tag',
                // width: '120px',
                render: (rowData) => {
                  if (rowData.tag === 1) {
                    return '空闲可分配'
                  }
                  if (rowData.tag === 3) {
                    return '保留'
                  }
                  if (rowData.tag === 4) {
                    return '未分配已使用'
                  }
                  if (rowData.tag === 7) {
                    return '空闲可分配'
                  }
                  if (rowData.tag === 2) {
                    return '已分配已使用'
                  }
                  if (rowData.tag === 6) {
                    return '已分配未使用'
                  }
                },
              },
              {
                title: '描述信息',
                key: 'description',
                // width: '150px',
              },
              {
                title: '最近在线',
                key: 'lastOnlineTime',
                // width: '150px',
                render: (rowData) => {
                  return rowData['lastOnlineTime']
                },
              },
              {
                title: 'BGBU',
                key: 'bgbu',
                // width: '150px',
                render: (rowData) => {
                  return rowData['bgbu']
                },
              },
            ],
            {
              align: 'center',
            } as DataTableColumn,
        ),
    )
    const dispatch_tableColumns = reactive(
        useTableColumn(
            [
              {
                title: 'IP地址',
                key: 'ip',
                // width: '100px',
              },
              {
                title: '分配状态',
                key: 'dispatch_status',
                // width: '120px',
                render: (rowData) => {
                  return h(NSelect, {
                    options: [
                      { value: '1', label: '空闲' },
                      { value: '2', label: '已分配已使用' },
                      { value: '3', label: '保留' },
                      { value: '4', label: '未分配已使用' },
                      { value: '6', label: '已分配未使用' },
                    ],
                    value: rowData.dispatch_status,
                    'default-value': '6',
                    placeholder: '请选择分配状态',
                    filterable: true,
                    onUpdateValue: (val) => {
                      rowData.dispatch_status = val
                    },
                  })
                },
              },
              {
                title: '描述信息',
                key: 'description',
                // width: '150px',
                // renderInput
                // render:(rowData)=>{
                //   renderInput(rowData.description, { placeholder: '请输入会议名称', clearable: true })
                // }
                render: (rowData) => {
                  return h(NInput, {
                    value: rowData.description,
                    onUpdateValue: (newVal: any) => {
                      // rowData.u_location_start = newVal
                      //console.log('rowData.value', rowData)
                      rowData.description = newVal
                    },
                  })
                },
              },

              {
                title: 'BGBU',
                key: 'bgbu',
                // width: '150px',
                render: (rowData) => {
                  return h(NInput, {
                    value: rowData.bgbu,
                    onUpdateValue: (newVal: any) => {
                      // rowData.u_location_start = newVal
                      //console.log('rowData.value', rowData)
                      rowData.bgbu = newVal
                    },
                  })
                },
              },
            ],
            {
              align: 'center',
            } as DataTableColumn,
        ),
    )
    const account_list = shallowReactive([]) as Array<any>
    const tags_list = shallowReactive([]) as Array<any>

    const subnet_list = shallowReactive([]) as Array<any>
    const subnet_tag_list = shallowReactive([]) as Array<any>
    const subnet_page = ref<number>(1)
    const subnet_pageSize = ref<number>(10)
    const subnet_pageCount = ref<number>(1)
    const subnet_keyword = ref('')
    // const second_password = ref('')
    const subnet_pageSizes = [
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

    const dispatch_list = shallowReactive([]) as Array<any>
    const dispatch_page = ref<number>(1)
    const dispatch_pageSize = ref<number>(10)
    const dispatch_pageCount = ref<number>(1)

    const dispatch_keyword = ref('')
    const add_root_form = ref({
      add_subnet: '',
      add_description: '',
      master_subnet_id: '',
    })
    const add_subnet_form = ref({
      add_subnet: '',
      add_description: '',
      master_subnet_id: '',
    })
    const add_root_show = ref(false)
    const add_subnet_show = ref(false)
    // const second_password = ref('')
    const dispatch_pageSizes = [
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

    const detail_list = shallowReactive([]) as Array<any>
    // const account_list = shallowReactive([]) as Array<any>
    // const detail_tag_list = shallowReactive([]) as Array<any>
    const detail_page = ref<number>(1)
    const detail_pageSize = ref<number>(10)
    const detail_pageCount = ref<number>(1)
    const detail_keyword = ref('')
    // const second_password = ref('')
    const detail_pageSizes = [
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
    const data: TreeOption[] = [
      {
        label: '0',
        key: '0',
        children: [
          {
            label: '0-0',
            key: '0-0',
            children: [
              { label: '0-0-0', key: '0-0-0' },
              { label: '0-0-1', key: '0-0-1' },
            ],
          },
          {
            label: '0-1',
            key: '0-1',
            children: [
              { label: '0-0-0', key: '0-0-0' },
              { label: '0-0-1', key: '0-0-1' },
            ],
          },
        ],
      },
      {
        label: '1',
        // prefix: () => h('text', 'prefix'),
        key: '1',
        children: [
          {
            label: '1-0',
            key: '1-0',
            children: [
              { label: '1-0-0', key: '1-0-0' },
              { label: '1-0-1', key: '1-0-1' },
            ],
          },
          {
            label: '1-1',
            key: '1-1',
            children: [
              { label: '1-1-0', key: '1-1-0' },
              { label: '1-1-1', key: '1-1-1' },
            ],
          },
        ],
      },
    ]
    // const tree_data = ref<TreeOption | []>([])
    const tree_data = ref([])
    const checkRef = ref('')
    const pattern = ref('')
    const subnet_search_keyword = ref('')
    const room_group_name = ref('')
    const update_data = ref('')
    const start_num = ref(0)

    function doSend(message) {
      if (socketOpen) {
        // sys_log_list.length = 0
        webSocket.send(message)
      }
    }

    function contactSocket() {
      if ('WebSocket' in window) {
        const ws_scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
        const ws_url = ws_scheme + '://' + window.location.host + '/ws/ipam/'
        webSocket = new WebSocket(ws_url)
        webSocket.onopen = function() {
          //console.log('连接成功！')
          socketOpen = true
          let ipam_dict = {
            method: 'get_room_name',
          }
          //console.log(ipam_dict)
          doSend(
              JSON.stringify({
                message: ipam_dict,
              }),
          )
        }

        webSocket.onmessage = function(evt) {
          var received_msg = evt.data
          //console.log('接受消息：', JSON.parse(received_msg)['message'])
          if (JSON.parse(received_msg)['message']['room_name'] !== undefined) {
            room_group_name.value = JSON.parse(received_msg)['message']['room_name']
          }
        }

        webSocket.onclose = function() {
          //console.log('连接关闭！')
        }
        webSocket.onerror = function() {
          //console.log('连接异常！')
        }
      }
    }

    function get_tree_data() {
      // contactSocket()
      get({
        url: getSubnetTree + '?subnet=1',
      }).then((res) => {
        //  //console.log('res', res)
        //  //console.log('tree_data', tree_data.value)

        tree_data.value.length = 0
        // let tree_list = []
        res.data.forEach((ele) => {
          ele['key'] = ele['id']
          // tree_list.push(ele)
          ele['suffix'] = () => {
            // console.log(ele['children'])
            if (ele['children']) {
              return h(
                  NButton,
                  { text: false, round: true, type: 'primary', size: 'tiny', style: { float: 'right' } },
                  { default: () => ele['children'].length },
              )
            } else {
              return h(
                  NButton,
                  { text: false, round: true, type: 'primary', size: 'tiny', style: { float: 'right' } },
                  { default: () => 0 },
              )
            }

          }
          if (ele.children) {
            if (ele.children.length === 0) {
              // console.log('第一层级下面children为空')
              delete ele.children
            } else {
              ele.children.forEach((item) => {
                item['key'] = item['id']

                if (item.children.length === 0) {
                  delete item.children
                }
                if (item.children) {
                  item.children.forEach((child) => {
                    child['key'] = child['id']
                    if (child.children.length === 0) {
                      delete child.children
                    }
                  })
                }
              })
            }

          }
          nextTick(() => {
            tree_data.value.push(ele)
          })
        })
        nextTick(() => {
          //console.log('tree_data', tree_data)
        })
      })
    }

    function get_new() {

      if (subnet_info.value['next_page_url']) {
        console.log('到底了，请二次请求滚动加载最新')
        console.log(subnet_info.value['next_page_url'])
        var start_ipaddress = subnet_info.value['next_page_url'].split('?start=')[1]
        request_next_status.value = true
        get({
          url: getSubnetAddress + subnet_info.value['subnet_id'] + '/ip_address/',
          data: () => {
            return {
              start: decodeURIComponent(start_ipaddress), // # 取消冒号转义
            }
          },
        }).then((next_res) => {
          request_next_status.value = false
          // console.log(next_res)
          subnet_info.value.result_list = subnet_info.value.result_list.concat(next_res['results'])
          subnet_info.value.next_page_url = next_res['next']
          subnet_info.value.maxhosts = Number(subnet_info.value.maxhosts) + Number(next_res['results'].length)
          console.log(subnet_info.value.result_list.length)
        })
      }


    }

    function handleScroll(event) {
      // console.log(event)
      // console.log(button_roll.value.scrollTop)
      //
      // //如果数据有在加载中则这次请求退出
      if (request_next_status.value) return
      // //已经滚动的距离加页面的高度等于整个内容区高度时,视为接触到底部
      // //scrollTop 获取到顶部的滚动距离
      // // clientHeight 表示页面视口高度
      // // scrollHeight 页面内容的高度
      if (event.srcElement.scrollTop + document.body.clientHeight >= event.srcElement.scrollHeight) {
        get_new()
      }
    }

    function nodeProps({ option }
                           :
                           {
                             option: TreeOption
                           },
    ) {
      return {
        onClick() {
          add_subnet_form.value.master_subnet_id = ''
          subnet_tag_list.length = 0

          if (option.label.indexOf((':')) !== -1) {
            // console.log('v6网段')
            add_subnet_form.value.master_subnet_id = option.label + '-' + option.id
            get({
              url: getSubnetAddress + option.id + '/ip_address/',
              data: () => {
                return {
                  // subnet_used: option.label,
                }
              },
            }).then((resp) => {
              if (resp) {
                detail_show.value = true
                var res = resp['data']
                var res_results = resp['results']
                var next_page_url = resp['next']
                //console.log('详细网段数据', res)
                nextTick(() => {
                  utilization_option.series[0].data.length = 0
                  utilization_option.series[0].data.push({
                    value: res.subnet_used['已分配已使用_percent'],
                    name: '已分配已使用',
                    itemStyle: { color: '#e6b600' },
                  })
                  utilization_option.series[0].data.push({
                    value: res.subnet_used['未分配已使用_percent'],
                    name: '未分配已使用',
                    itemStyle: { color: '#1595c4' },
                  })
                  utilization_option.series[0].data.push({
                    value: res.subnet_used['自定义空闲_percent'] + res.subnet_used['empty_percent'],
                    name: '空闲IP',
                    itemStyle: { color: '#e9e9eb' },
                  })
                  utilization_option.series[0].data.push({
                    value: res.subnet_used['已分配未使用_percent'],
                    name: '已分配未使用',
                    itemStyle: { color: '#11eec2' },
                  })
                  utilization_option.series[0].data.push({
                    value: res.subnet_used['保留_percent'],
                    name: '保留',
                    itemStyle: { color: '#22dd22' },
                  })
                  useEcharts(channelsChart.value as HTMLDivElement).setOption(utilization_option)
                })
                var ip_used_list = []
                if (res.ip_used) {
                  ip_used_list = res.ip_used
                } else {
                  ip_used_list = []
                }
                // console.log('ip_used_list', ip_used_list)
                subnet_info.value = {
                  subnet: option.label,
                  desc: res.sub_net[0]['description'],
                  used: res.subnet_used.used.toString(),
                  freehosts: res.subnet_used.freehosts.toString(),
                  Used_percent: res.subnet_used['Used_percent'],
                  freehosts_percent: res.subnet_used.freehosts_percent.toString(),
                  maxhosts: res.subnet_used.maxhosts.toString(),
                  count: parseInt(res.subnet_used.maxhosts),
                  table_type: ip_used_list,
                  subnet_id: option.id,
                  result_list: res_results,
                  next_page_url: next_page_url,
                }
              }
            })
          } else {
            // message.info('当前选中最后一层元素做查询' + option.label)
            if (option.children) {
              //console.log('还有子元素不做查询', option)
              detail_show.value = false
              add_subnet_form.value.master_subnet_id = option.label + '-' + option.id
              return
            } else {
              add_subnet_form.value.master_subnet_id = option.label + '-' + option.id
              get({
                url: getSubnetAddress + option.id + '/ip_address/',
                data: () => {
                  return {
                    // subnet_used: option.label,
                  }
                },
              }).then((resp) => {
                if (resp) {
                  detail_show.value = true
                  var res = resp['data']
                  var res_results = resp['results']
                  var next_page_url = resp['next']
                  //console.log('详细网段数据', res)
                  nextTick(() => {
                    utilization_option.series[0].data.length = 0
                    utilization_option.series[0].data.push({
                      value: res.subnet_used['已分配已使用_percent'],
                      name: '已分配已使用',
                      itemStyle: { color: '#e6b600' },
                    })
                    utilization_option.series[0].data.push({
                      value: res.subnet_used['未分配已使用_percent'],
                      name: '未分配已使用',
                      itemStyle: { color: '#1595c4' },
                    })
                    utilization_option.series[0].data.push({
                      value: res.subnet_used['自定义空闲_percent'] + res.subnet_used['empty_percent'],
                      name: '空闲IP',
                      itemStyle: { color: '#e9e9eb' },
                    })
                    utilization_option.series[0].data.push({
                      value: res.subnet_used['已分配未使用_percent'],
                      name: '已分配未使用',
                      itemStyle: { color: '#11eec2' },
                    })
                    utilization_option.series[0].data.push({
                      value: res.subnet_used['保留_percent'],
                      name: '保留',
                      itemStyle: { color: '#22dd22' },
                    })
                    useEcharts(channelsChart.value as HTMLDivElement).setOption(utilization_option)
                  })
                  var ip_used_list = []
                  if (res.ip_used) {
                    ip_used_list = res.ip_used
                  } else {
                    ip_used_list = []
                  }
                  // console.log('ip_used_list', ip_used_list)
                  subnet_info.value = {
                    subnet: option.label,
                    desc: res.sub_net[0]['description'],
                    used: res.subnet_used.used.toString(),
                    freehosts: res.subnet_used.freehosts.toString(),
                    Used_percent: res.subnet_used['Used_percent'],
                    freehosts_percent: res.subnet_used.freehosts_percent.toString(),
                    maxhosts: res.subnet_used.maxhosts.toString(),
                    count: parseInt(res.subnet_used.maxhosts),
                    table_type: ip_used_list,
                    subnet_id: option.id,
                    result_list: res_results,
                    next_page_url: next_page_url,
                  }
                }
              })
            }
          }
        },
      }
    }

    function echarts_init() {
      nextTick(() => {
        useEcharts(channelsChart.value as HTMLDivElement).setOption(utilization_option)
      })
    }

    onMounted(echarts_init)

    function clear_keywords() {
      //console.log('清除搜索关键字', subnet_search_keyword.value)
      // subnet_search_keyword.value = ''
      pattern.value = ''
      get_tree_data()
    }

    function open_export() {
      //console.log('导出网段对话框打开')
      modalDialog.value?.toggle()
      let csrf_token = Cookies.get('csrftoken')
      let sessionid = Cookies.get('sessionid')
      // subnet_loading.value = true
      //  //console.log({"Cookie":`csrftoken=${csrf_token};sessionid=${sessionid}`})
      // new_static_formdata.append('csrfmiddlewaretoken', csrf_token)
      get({
        url: getSubnetTree,
        // headers:{"Cookie":`csrftoken=${csrf_token};sessionid=${sessionid}`},
        // headers:{"Cookie":'csrftoken=HXeYFfBzHjqkdIgNWzFs4ibmV0M7riy2Z2AWeosEx1mcpMpYqtfGv5DkAo7qcJyd;sessionid=2qbfl3p0q0umylf4qrwfz3x0r6d4d5wp'},
        data: () => {
          return {
            download: 1,

            // csrfmiddlewaretoken:csrf_token
          }
        },
      }).then((res) => {
        subnet_loading.value = false
        subnet_list.length = 0
        subnet_list.push(...res.data)
        subnet_page.value = 1
        subnet_pageSize.value = 10
        subnet_pageCount.value = Math.ceil(subnet_list.length / 10)
      })
    }

    function rowKey(rowData: any) {
      return rowData.id
    }

    function detail_rowKey(rowData: any) {
      return rowData.ip
    }

    function dispatch_rowKey(rowData: any) {
      return rowData.ip
    }

    function export_ipam() {
      let export_str = '网段,掩码,描述信息\n'
      for (let i = 0; i < subnet_list.length; i++) {
        export_str =
            export_str +
            subnet_list[i].subnet +
            ',' +
            subnet_list[i]['mask'] +
            ',' +
            subnet_list[i].description +
            '\n'
      }
      export_str = encodeURIComponent(export_str)
      const link = document.createElement('a')
      link.href = 'data:text/csv;charset=utf-8,\ufeff' + export_str
      // link.style = 'visibility:hidden'
      link.download = '网段详情信息.csv'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    function export_ipam_detail() {
      let export_str = '地址,标签,描述信息,最近在线,BGBU\n'
      // console.log(detail_list)
      for (let i = 0; i < detail_list.length; i++) {
        export_str =
            export_str +
            detail_list[i].address +
            ',' +
            detail_list[i]['tag'] +
            ',' +
            detail_list[i].description +
            ',' +
            detail_list[i]['lastOnlineTime'] +
            ',' +
            detail_list[i]['bgbu'] +
            ',' +
            '\n'
      }
      export_str = encodeURIComponent(export_str)
      const link = document.createElement('a')
      link.href = 'data:text/csv;charset=utf-8,\ufeff' + export_str
      // link.style = 'visibility:hidden'
      link.download = '地址详情表格.csv'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    function AddRootConfirm() {
      //console.log(add_root_form.value)
      add_root_show.value = false
      const post_data = new FormData()
      var master_subnet_id = add_root_form.value['master_subnet_id'].split('-')[1]
      // if (master_subnet_id === 'ROOT') {
      //   master_subnet_id = '0'
      // }
      post_data.append('add_subnet', add_root_form.value['add_subnet'])
      post_data.append('add_description', add_root_form.value['add_description'])
      post_data.append('add_master_id', '0')
      post_data.append('room_group_name', room_group_name.value)
      let csrf_token = Cookies.get('csrftoken')
      post_data.append('csrfmiddlewaretoken', csrf_token)
      post({
        url: PostAddressHandel,
        data: post_data,
      }).then((res) => {
        //console.log(res)
        add_root_show.value = false
        message.success('新增根网段成功')
        get_tree_data()
      })
    }

    function AddSubnetConfirm() {
      //console.log(add_root_form.value)
      add_root_show.value = false
      const post_data = new FormData()
      var master_subnet_id = add_subnet_form.value['master_subnet_id'].split('-')[1]
      // if (master_subnet_id === 'ROOT') {
      //   master_subnet_id = '0'
      // }
      post_data.append('add_subnet', add_subnet_form.value['add_subnet'])
      post_data.append('add_description', add_subnet_form.value['add_description'])
      post_data.append('add_master_id', master_subnet_id)
      post_data.append('room_group_name', room_group_name.value)
      let csrf_token = Cookies.get('csrftoken')
      post_data.append('csrfmiddlewaretoken', csrf_token)
      post({
        url: PostAddressHandel,
        data: post_data,
      }).then((res) => {
        //console.log(res)
        add_subnet_show.value = false
        message.success('新增子网网段成功')
        get_tree_data()
      })
    }

    function CancelRoot() {
      add_root_show.value = false
    }

    function subnet_click(ip_address) {
      let current_select = document.getElementById(ip_address).getAttribute('value').toString()
      subnet_tag_list.push(current_select)
      // if (start_num.value === 0) {
      // let prefix = subnet_info.value['subnet'].split('.')
      // prefix.pop()

      // } else {
      //   let prefix = subnet_info.value['subnet'].split('.')
      //   prefix.pop()
      //   let current_select = prefix.join('.') + '.' + (start_num.value + index).toString()
      //   subnet_tag_list.push(current_select)
      // }

      // var button_ele = document.getElementById((index-1).toString())
      // button_ele.setAttribute('class','button_border')
    }

    function handleCloseTag(item) {
      //console.log('closeitem', item)
      // colors = colors.filter(function(item) {    return item != "red"});
      subnet_tag_list.forEach(function(ele, index, arr) {
        if (ele === item) {
          subnet_tag_list.splice(index, 1)
        }
      })
    }

    function table_type_func() {
      refresh_subnet_id.value = subnet_info.value['subnet_id']
      console.log(subnet_info.value)
      refresh_subnet(refresh_subnet_id.value)
      nextTick(() => {
        table_modalDialog.value?.toggle()
        detail_list.length = 0
        //  //console.log(subnet_info.value['table_type'][0]['note'])
        //  //console.log(typeof subnet_info.value['table_type'][0]['note'])
        //  //console.log(typeof eval('(' + subnet_info.value['table_type'][0]['note'] + ')'))
        //  //console.log(typeof JSON.parse(subnet_info.value['table_type'][0]['note']))
        let detail_eval_list = []
        subnet_info.value['table_type'].forEach((ele) => {
          // if (ele['note']) {
          //   ele.note = JSON.parse(ele['note'])
          //   ele['last_online_time'] = ele['note']['Last Online Time']
          //   ele['bgbu'] = ele['bgbu']
          // } else {
          //   ele['last_online_time'] = ''
          //   ele['bgbu'] = ''
          // }

          detail_eval_list.push(ele)
        })
        //  //console.log(detail_eval_list[0]['note']['Last Online Time'])
        detail_list.push(...detail_eval_list)
        detail_page.value = 1
        detail_pageSize.value = 10
        detail_pageCount.value = Math.ceil(detail_list.length / 10)
      })
    }

    function clear_select() {
      subnet_tag_list.length = 0
    }

    function select_all() {
      //console.log(subnet_info.value['table_type'])
      let tag_array = []
      subnet_info.value['table_type'].forEach((item) => {
        tag_array.push(item.ip)
      })
      subnet_tag_list.length = 0
      subnet_tag_list.push(...tag_array)
    }

    function dispatch_ip() {
      if (subnet_tag_list.length > 0) {
        dispatch_modalDialog.value?.toggle()
        //console.log(subnet_info.value['table_type'])
        //console.log(subnet_tag_list)
        let dispatch_array = []
        // dispatch_array = subnet_info.value['table_type'].filter((item) => {
        //   return subnet_tag_list.includes(item.ip)
        // })
        uniq4(subnet_tag_list).forEach((item) => {
          const dict = {
            ip: item,
          }
          dispatch_array.push(dict)
        })
        dispatch_list.length = 0
        dispatch_list.push(...dispatch_array)
        dispatch_page.value = 1
        dispatch_pageSize.value = 10
        dispatch_pageCount.value = Math.ceil(dispatch_list.length / 10)
      } else {
        message.error('暂未选中任何地址')
      }
    }

//批量回收地址
    function recycle_many_func() {
      let delete_result = []
      if (subnet_tag_list.length > 0) {
        let csrf_token = Cookies.get('csrftoken')
        // let put_data = {}
        subnet_tag_list.forEach((item) => {
          //console.log(item)
          let sub = {
            ipaddr: item,
          }
          delete_result.push(sub)
        })
        var formdata = new FormData()
        formdata.append('room_group_name', room_group_name.value)
        formdata.append('csrfmiddlewaretoken', csrf_token)
        formdata.append('delete', JSON.stringify(delete_result))
        post({
          url: PostAddressHandel,
          data: formdata,
        }).then((res) => {
          message.success('回收成功')

          nextTick(() => {
            // dispatch_many_modalDialog.value!.toggle()
            refresh_subnet(refresh_subnet_id.value)
          })
        })
      } else {
        message.error('暂未选中任何地址')
      }
    }

    function dispatch_many_func() {
      //console.log('dispatch_many_FormOptions', dispatch_many_FormOptions)
      let prefix = subnet_info.value['subnet'].split('.')
      prefix.pop()
      //console.log('前缀', prefix.join('.'))
      if (dispatch_many_FormOptions[0].value.value !== undefined) {
        dispatch_many_FormOptions[0].value.value = prefix.join('.')
      }
      if (dispatch_many_FormOptions[1].value.value !== undefined) {
        dispatch_many_FormOptions[1].value.value = prefix.join('.')
      }
      nextTick(() => {
        dispatch_many_modalDialog.value?.toggle()
      })
    }

    function DispatchManyConfirm() {
      if (dispatch_many_DataFormRef.value?.validator()) {
        let dispatch_many_form = dispatch_many_DataFormRef.value.generatorParams()
        //console.log('dispatch_many_form', dispatch_many_form)

        let csrf_token = Cookies.get('csrftoken')

        let put_data = {}
        put_data['subnet_id'] = subnet_info.value['subnet_id']
        put_data['start_ip'] = dispatch_many_form['start_ip']
        put_data['end_ip'] = dispatch_many_form['end_ip']
        put_data['tag'] = parseInt(dispatch_many_form['dispatch_status'])
        put_data['description'] = dispatch_many_form['description']
            ? dispatch_many_form['description']
            : '批量地址分配'
        // put_data['csrfmiddlewaretoken'] = csrf_token
        var formdata = new FormData()
        formdata.append('range_update', JSON.stringify(put_data))
        formdata.append('room_group_name', room_group_name.value)
        formdata.append('csrfmiddlewaretoken', csrf_token)
        post({
          url: PostAddressHandel,
          data: formdata,
        }).then((res) => {
          message.success('执行批量分配成功')
          nextTick(() => {
            dispatch_many_modalDialog.value!.toggle()
            refresh_subnet(refresh_subnet_id.value)
            refresh_subnet(refresh_subnet_id.value)
          })
        })
      }
    }

    function dispatch_confirm() {
      console.log('执行分配地址', dispatch_list)
      const update_list = []
      dispatch_list.forEach((item) => {
        const dict = {
          ipaddr: item.ip,
          subnet_id: subnet_info.value['subnet_id'],
          tag: 6,
          description: item.description ? item.description : item.ip,
        }
        // update_data.value += (JSON.stringify(dict)) + ','
        update_list.push(dict)
      })

      const dispatch_data = new FormData()
      dispatch_data.append('update', JSON.stringify(update_list))
      dispatch_data.append('room_group_name', room_group_name.value)
      let csrf_token = Cookies.get('csrftoken')
      dispatch_data.append('csrfmiddlewaretoken', csrf_token)
      post({
        url: PostAddressHandel, // TODO
        data: dispatch_data,
      }).then((res) => {
        dispatch_modalDialog.value!.toggle()
        message.success('分配成功')
        nextTick(() => {
          detail_show.value = false
          refresh_subnet(refresh_subnet_id.value)
        })
        // TODO
      })
    }

    function refresh_subnet(subnet_id) {
      subnet_id = subnet_info.value['subnet_id']
      get({
        url: getSubnetAddress + subnet_id + '/ip_address/',
        data: () => {
          return {
            // subnet_used: subnet_info.value['subnet'],
          }
        },
      }).then((resp) => {
        if (resp) {
          var res = resp['data']
          var res_results = resp['results']
          var next_page_url = resp['next']
          detail_show.value = true
          //console.log('详细网段数据', res)
          nextTick(() => {
            subnet_tag_list.length = 0
            utilization_option.series[0].data.length = 0
            // console.log(res.subnet_used)
            utilization_option.series[0].data.push({
              value: res.subnet_used['已分配已使用_percent'],
              name: '已分配已使用',
              itemStyle: { color: '#e6b600' },
            })
            utilization_option.series[0].data.push({
              value: res.subnet_used['未分配已使用_percent'],
              name: '未分配已使用',
              itemStyle: { color: '#1595c4' },
            })
            utilization_option.series[0].data.push({
              value: res.subnet_used['自定义空闲_percent'] + res.subnet_used['empty_percent'],
              name: '空闲IP',
              itemStyle: { color: '#e9e9eb' },
            })
            utilization_option.series[0].data.push({
              value: res.subnet_used['已分配未使用_percent'],
              name: '已分配未使用',
              itemStyle: { color: '#11eec2' },
            })
            utilization_option.series[0].data.push({
              value: res.subnet_used['保留_percent'],
              name: '保留',
              itemStyle: { color: '#22dd22' },
            })
            useEcharts(channelsChart.value as HTMLDivElement).setOption(utilization_option)
          })
          subnet_info.value = {
            subnet: subnet_info.value['subnet'],
            desc: res.sub_net[0]['description'],
            used: res.subnet_used.used.toString(),
            freehosts: res.subnet_used.freehosts.toString(),
            Used_percent: res.subnet_used['已分配已使用_percent'] + res.subnet_used['未分配已使用_percent'],
            freehosts_percent: res.subnet_used.freehosts_percent.toString(),
            maxhosts: res.subnet_used.maxhosts.toString(),
            count: parseInt(res.subnet_used.maxhosts),
            table_type: res.ip_used,
            subnet_id: res.sub_net[0].id,
            result_list: res_results,
            next_page_url: next_page_url,
          }
          // nextTick(()=>{
          //
          // })
        }
      })
    }

    function port_style(status) {
      // console.log(status)
      let tag_value = parseInt(status)
      if (tag_value === 1) {
        // 空闲
        return 'empty'
      } else if (tag_value === 2) {
        // 已分配已使用
        return 'dist_and_used'
      } else if (tag_value === 3) {
        // 保留
        return 'reserved'
      } else if (tag_value === 4) {
        // 未分配已使用
        return 'not_dist_and_used'
      } else if (tag_value === 6) {
        // 已分配未使用
        return 'dist_and_not_used'
      } else if (tag_value === 7) {
        return 'custom_empty'
      }
    }

    function uniq4(arry) {
      var result = []
      for (var i = 0; i < arry.length; i++) {
        if (!result.includes(arry[i])) {
          //如 result 中没有 arry[i],则添加到数组中
          result.push(arry[i])
        }
      }
      return result
    }

    function set_tree_data(array) {
      var result = []
      var subnet_name_list = []
      for (var i = 0; i < array.length; i++) {
        if (!subnet_name_list.includes(array[i]['label'])) {
          //如 result 中没有 array[i],则添加到数组中
          result.push(array[i])
          subnet_name_list.push(array[i]['label'])
        }
      }
      //console.log(set_tree_data)
      return result
    }

    function tree_filter() {
      //console.log('搜索关键字', subnet_search_keyword.value)
      detail_show.value = false
      const filter_list = []
      filter_list.push(...tree_data.value)
      const show_list = []
      if (subnet_search_keyword.value) {
        tree_data.value.length = 0
        show_list.length = 0
        filter_list.forEach((item) => {
          //  //console.log(item)
          if (item.label.indexOf(subnet_search_keyword.value) !== -1) {
            show_list.push(item)
          }
          if (item.label.indexOf(subnet_search_keyword.value) === -1) {
            item.children.forEach((ele) => {
              if (ele.label.indexOf(subnet_search_keyword.value) !== -1) {
                show_list.push(item)
              }
              // else{
              //
              // }
            })
          }
        })
        // set_tree_data(show_list)
        tree_data.value.push(...show_list)
      } else {
        get_tree_data()
      }
    }

    function create_subnet() {
      console.log('master_subnet_id', add_root_form.value['master_subnet_id'])
      if (add_subnet_form.value['master_subnet_id']) {
        console.log('新增子网')
        add_subnet_show.value = true
      } else {
        console.log('新增根网络')
        add_root_show.value = true
      }
    }

    function get_tags() {
      get({
        url: getSubnetTree,
        data: () => {
          return {
            tags: 1,
          }
        },
      }).then((res) => {
        // tags_color_options
        console.log('tags', res)
        tags_list.length = 0
        tags_list.push(...res['data'])
        nextTick(() => {
          console.log('tags_list', tags_list)
        })
      })
    }

    function change_desc() {
      console.log('subnet_info', subnet_info.value)
      change_desc_show.value = true
      change_desc_form.value['subnet'] = subnet_info.value['subnet']
      change_desc_form.value['subnet_id'] = subnet_info.value['subnet_id']
      change_desc_form.value['description'] = subnet_info.value['desc']
    }

    function change_desc_submit() {
      console.log(change_desc_form.value)
      const post_data = new FormData()
      // var master_subnet_id = add_subnet_form.value['master_subnet_id'].split('-')[1]
      // if (master_subnet_id === 'ROOT') {
      //   master_subnet_id = '0'
      // }

      post_data.append('subnet_id', change_desc_form.value['subnet_id'])
      post_data.append('description', change_desc_form.value['description'])
      post_data.append('room_group_name', room_group_name.value)
      let csrf_token = Cookies.get('csrftoken')
      post_data.append('csrfmiddlewaretoken', csrf_token)
      //TODO
      post({
        url: PostAddressHandel,
        data: post_data,
      }).then((res) => {
        console.log('change_desc', res)
        message.info("更新网段描述成功")
        // change_desc_form.value['subnet_id'] = ''
        // change_desc_form.value['description'] = ''
        change_desc_show.value = false
        nextTick(() => {
          refresh_subnet(refresh_subnet_id.value)
        })
      })
    }

    onMounted(get_tree_data)
    onMounted(get_tags)
    return {
      change_desc_submit,
      change_desc,
      get_tags,
      create_subnet,
      set_tree_data,
      uniq4,
      refresh_subnet,
      port_style,
      detail_rowKey,
      echarts_init,
      start_num,
      subnet_info,
      change_desc_form,
      detail_show,
      contactSocket,
      doSend,
      modalDialog,
      table_modalDialog,
      dispatch_modalDialog,
      dispatch_many_modalDialog,
      dispatch_many_func,
      recycle_many_func,
      open_export,
      DispatchManyConfirm,
      dispatch_confirm,
      account_list,
      tags_list,
      subnet_tag_list,

      subnet_list,
      subnet_page,
      subnet_pageSize,
      subnet_pageSizes,
      subnet_search_keyword,
      subnet_pageCount,
      subnet_tableColumns,

      detail_list,
      detail_page,
      detail_pageSize,
      detail_pageSizes,
      detail_keyword,
      detail_pageCount,
      detail_tableColumns,

      dispatch_list,
      dispatch_page,
      dispatch_pageSize,
      dispatch_pageSizes,
      dispatch_keyword,
      dispatch_pageCount,
      dispatch_tableColumns,

      add_root_show,
      add_subnet_show,
      change_desc_show,
      add_root_form,
      add_subnet_form,
      tree_filter,
      handleCloseTag,
      dispatch_ip,
      // back_ip,
      export_ipam,
      export_ipam_detail,
      rowKey,
      table_type_func,
      clear_select,
      select_all,
      checkRef,
      handleScroll,
      get_new,
      nodeProps,
      get_tree_data,
      data,
      tree_data,
      clear_keywords,
      utilization_option,
      channelsChart,
      pattern,
      subnet_keyword,
      subnet_loading,
      dispatch_many_FormOptions,
      rules: {
        start_ip: {
          required: true,
          message: '起始地址',
          trigger: ['input'],
        },
      },
      refresh_subnet_id,
      dispatch_many_DataFormRef,
      subnet_click,
      AddRootConfirm,
      AddSubnetConfirm,
      CancelRoot,
      used_port,
      button_roll,
      request_next_status,
      dispatch_rowKey,
      renderSwitcherIcon: () => h(NIcon, null, { default: () => h(ChevronForward) }),
    }
  },
})
</script>

<style lang="scss" scoped>
.roll_div {
  height: calc(100% - 191px);
  padding: 10px 24px;
  position: relative;
  background-color: #fbfcfe;
  overflow-y: auto;
}

.bold-attribute {
  font-weight: bold;
  padding-right: 5px;
}

.used {
  background-color: #409eff;
}

.reserved {
  background: #22dd22;
}

.dist_and_used {
  /*已分配已使用*/
  background: #e6b600;
}

.not_dist_and_used {
  /*未分配已使用*/
  background: #1695c4;
}

.free {
  background-color: #67c23a;
}

.empty {
  background-color: #f4f4f4;
}

.dist_and_not_used {
  background-color: #11eec2;
}

.custom_empty {
  background: #f4f4f4;
}

.chart-item {
  //height: 500px;
  width: 400px;
  //padding-left:300px;
  //padding-top: 30px;
  height: 300px;
}

.button_border {
  border: 1px solid black;
}
</style>