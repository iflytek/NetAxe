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
          <template #table-config>
            <TableConfig @update-border="onUpdateBorder" @refresh="doRefresh" />
            <SortableTable class="ml-4" :columns="tableColumns" @update="onUpdateTable" />
          </template>

          <template #top-right>
            <n-button type="info" size="small" @click="device_import"> 资产录入</n-button>

            <n-button type="warning" size="small" @click="btnClick"> 数据导入</n-button>
            <n-button type="primary" size="small" @click="export_excel"> 数据导出</n-button>
            <n-button type="primary" size="small" @click="connect_collect"> 关联采集</n-button>
            <!-- <n-button type="warning" size="small" @click="device_data_show = true">
              运营展示
            </n-button> -->
          </template>
        </TableHeader>
      </template>
      <template #default>
        <DataForm
          ref="searchForm"
          :form-config="{ labelWidth: 60 }"
          :options="conditionItems"
          preset="grid-item"
        />
        <n-space style="float: right; padding-bottom: 20px">
          <n-button style="float: right" size="small" type="info" @click="onSearch()"
            >查询
          </n-button>
          <n-button style="float: right" size="small" type="success" @click="onResetSearch()"
            >重置
          </n-button>
        </n-space>

        <n-data-table
          :loading="tableLoading"
          :data="dataList"
          :columns="tableColumns"
          :single-line="!bordered"
          :row-key="rowKey"
          @update:checked-row-keys="handleCheck"
          @update:expanded-row-keys="handleExpand"
          :scroll-x="1800"
        />
      </template>
      <template #footer>
        <TableFooter :pagination="pagination" />
      </template>
    </TableBody>
    <ModalDialog
      ref="modalDialog"
      title="资产数据维护"
      :segmented="segmented"
      display-directive="show"
      @confirm="EditConfirm"
    >
      <template #content>
        <DataForm
          ref="EditDataFormRef"
          :form-config="{ labelWidth: 60 }"
          preset="grid-item"
          :options="EditFormOptions"
        >
        </DataForm>
      </template>

      <!--      <template #footer>-->
      <!--        <div class="flex justify-end">-->
      <!--          <n-space>-->
      <!--            <n-button type="default" size="small" @click="onCancel">取消</n-button>-->
      <!--            <n-button type="primary" size="small" @click="onConfirm">提交修改</n-button>-->
      <!--          </n-space>-->
      <!--        </div>-->
      <!--      </template>-->
    </ModalDialog>

    <ModalDialog
      ref="device_import_modalDialog"
      title="资产数据录入"
      @confirm="importDataFormConfirm"
    >
      <template #content>
        <DataForm
          ref="importDataFormRef"
          :form-config="{
            labelWidth: 60,
          }"
          preset="grid-item"
          :options="importFormOptions"
        />
      </template>
    </ModalDialog>

    <ModalDialog
      ref="ChangeLogmodalDialog"
      title="变更轨迹"
      :style="{ height: '768px', width: '1366px' }"
    >
      <template #content>
        <n-data-table
          :data="
            change_log_list.slice(
              (change_log_page - 1) * change_log_pageSize,
              change_log_page * change_log_pageSize
            )
          "
          size="small"
          :columns="change_log_tableColumns"
          :row-key="rowKey"
          :loading="tableLoading"
        />
        <div class="flex justify-center">
          <n-pagination
            v-model:page="change_log_page"
            :page-count="change_log_pageCount"
            show-size-picker
            :page-sizes="change_log_pageSizes"
          />
        </div>
      </template>
    </ModalDialog>
    <ModalDialog
      ref="show_password_modalDialog"
      title="查看管理账户信息?"
      :style="{ height: '500px', width: '500px' }"
    >
      <template #content>
        <n-space>
          <h3>请输入二级密码</h3>
          <n-input
            type="password"
            show-password-on="mousedown"
            placeholder="密码"
            v-model:value="second_password"
            @keyup.enter.native="second_onConfirm"
          ></n-input>
        </n-space>
      </template>
    </ModalDialog>
    <ModalDialog
      ref="bind_ip_modalDialog"
      title="关联IP"
      :style="{ height: '400px', width: '300px' }"
      @confirm="BindIpConfirm"
    >
      <template #content>
        <n-form
          label-placement="left"
          :size="size"
          label-width="auto"
          require-mark-placement="right-hanging"
          :style="{
            maxWidth: '640px',
          }"
          :model="bind_ip_form"
        >
          <n-form-item label="IP标识名" path="name">
            <n-input v-model:value="bind_ip_form.name" placeholder="IP标识名" />
          </n-form-item>
          <n-form-item label="绑定IP" path="ip">
            <n-input v-model:value="bind_ip_form.ip" placeholder="绑定IP" />
          </n-form-item>
        </n-form>
      </template>
    </ModalDialog>
    <ModalDialog
      ref="connect_account_modalDialog"
      title="关联设备管理账户"
      :style="{ height: '300px', width: '500px' }"
      @confirm="ConnectAccountConfirm"
    >
      <template #content>
        <DataForm
          ref="connect_account_DataFormRef"
          :form-config="{
            labelWidth: 60,
          }"
          :options="connect_account_FormOptions"
        />
      </template>
    </ModalDialog>
    <ModalDialog
      ref="account_modalDialog"
      title="账户信息"
      :style="{ height: '500px', width: '500px' }"
    >
      <template #content>
        <n-data-table
          :data="
            account_list.slice(
              (account_page - 1) * account_pageSize,
              account_page * account_pageSize
            )
          "
          :columns="account_tableColumns"
          :row-key="rowKey"
          :loading="tableLoading"
        />
      </template>
    </ModalDialog>

    <n-modal
      v-model:show="collect_modalDialog"
      class="modal-dialog-wrapper"
      header-style="padding: 10px 20px"
      :mask-closable="false"
      :style="bodyStyle"
    >
      <n-card
        style="width: 600px"
        title="关联采集方案"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-form
          ref="formRef"
          :model="formRef"
          label-placement="left"
          label-align="left"
          :label-width="160"
          :style="{
            maxWidth: '640px',
          }"
        >
          <n-form-item label="当前选中设备条目:">{{ checkedRowKeysRef.length }}</n-form-item>

          <n-form-item label="采集方案">
            <n-select
              v-model:value="selectCollectValues"
              filterable
              placeholder="勾选采集方案"
              :options="collection_options"
            />
          </n-form-item>
        </n-form>
        <template #footer>
          <div class="flex justify-end">
            <n-button type="default" size="small" @click="onCancelCollect">取消</n-button>
            <n-button type="info" size="small" @click="NewConnectCollect">确认</n-button>
            <!--            <n-button type="primary" size="small" @click="AddConnect">追加关联</n-button>-->
          </div>
        </template>
      </n-card>
    </n-modal>

    <n-modal
      v-model:show="import_show"
      preset="dialog"
      header-style="padding: 10px 20px"
      title="设备批量表格导入"
      :style="{ height: '230px', width: '600px' }"
      :mask-closable="false"
    >
      <input
        class="input-file"
        type="file"
        @change="exportData"
        accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
      />
      <n-button @click="download_template">
        下载导入模板
        <!--      <a :href="device_import_template_url">下载导入模板</a>-->
      </n-button>
      <div class="flex justify-end" style="padding-top: 100px">
        <n-space>
          <n-button @click="import_show = false">取消</n-button>
          <!--          <n-button type="success" @click="exportData">导入</n-button>-->
        </n-space>
      </div>
    </n-modal>
  </div>
</template>

<script lang="ts">
import {
  networkDeviceUrl,
  device_import_url,
  getNetworkDeviceList,
  getCmdbIdcList,
  getCmdbRoleList,
  getVendorList,
  getCategoryList,
  get_api_request_log,
  getCmdbModelList,
  getCmdbNetzoneList,
  getCmdbIdcModelList,
  getCmdbRackList,
  getcmdb_accountList,
  getInterfaceUsedList,
  device_import_template,
  deviceWebSshLogin,
  deviceInfoChange,
  getCollection_planList,
} from '@/api/url'
import { useTable, usePagination, useTableColumn } from '@/hooks/table'
import {
  computed,
  defineComponent,
  h,
  nextTick,
  onMounted,
  reactive,
  ref,
  shallowReactive,
} from 'vue'
import _ from 'lodash'
import * as XLSX from 'xlsx'
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
  NDataTable,
} from 'naive-ui'
import { DataFormType, ModalDialogType, FormItem, TablePropsType } from '@/types/components'
import usePost from '@/hooks/usePost'
import { renderTag } from '@/hooks/form'
import useGet from '@/hooks/useGet'
import usePut from '@/hooks/usePut'
import usePatch from '@/hooks/usePatch'
import { sortColumns } from '@/utils'
import { useLayoutStore } from '@/components'
import Cookies from 'js-cookie'
import router from '@/router'

export default defineComponent({
  name: 'networkdevice',
  components: {},
  setup() {
    const formRef = ref({})
    const term = ref(null)
    const socket = ref(null)
    const layoutStore = useLayoutStore()
    const bodyStyle = computed(() => ({
      width: layoutStore.state.device === 'mobile' ? '80%' : '50%',
    }))
    const segmented = {
      content: 'soft',
      footer: 'soft',
    }
    const selectValues = ref(null)
    const selectCollectValues = ref('')
    const EditFormOptions = [
      {
        key: 'manage_ip',
        label: '管理地址',
        value: ref(null),
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
        key: 'framework',
        label: '网络架构',
        value: ref(null),
        optionItems: [
          { value: 0, label: '' },
          { value: 2, label: '二层' },
          { value: 1, label: '三层' },
          { value: 3, label: '大二层' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择架构',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'vendor',
        label: '供应商',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择供应商',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'role',
        label: '设备角色',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'category',
        label: '类型',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'idc_model',
        label: '模块',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },

      {
        label: 'SN号',
        key: 'serial_num',
        value: ref(null),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (val: any) => {
              formItem.value.value = val
            },
            placeholder: '请输入部门编号',
            disabled: true,
          })
        },
      },
      {
        key: 'rack',
        label: '机柜',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'idc',
        label: '所属机房',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'u_location_value',
        label: 'U位置',
        value: ref(''),
        render: (formItem) => {
          return h(NInputGroup, {}, [
            h(NInput, {
              // value: ref(''),
              value: formItem.value.value,
              onUpdateValue: (newVal: any) => {
                // rowData.u_location_start = newVal
                //console.log('formItem.value', newVal)
                formItem.value.value = newVal
              },
              maxlength: 50,
              placeholder: 'U位起始',
            }),
            h(NInput, {
              // value: ref(''),
              value: formItem.value.value,
              onUpdateValue: (newVal: any) => {
                formItem.value.value = newVal
                // rowData.u_location_start = newVal
              },
              maxlength: 50,
              placeholder: 'U位结束',
            }),
          ])
        },
      },
      {
        key: 'netzone',
        label: '网络区域',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择区域',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'memo',
        label: '备注',
        value: ref(null),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (newVal: any) => {
              // rowData.u_location_start = newVal
              //  //console.log('formItem.value', rowData)
              formItem.value.value = newVal
            },
          })
        },
      },
      {
        key: 'attribute',
        label: '网络属性',
        value: ref(''),
        optionItems: [
          { value: '', label: '' },
          { value: 2, label: '生产网络' },
          { value: 4, label: '研发网络' },
          { value: 6, label: '研测网络' },
          { value: 8, label: '骨干网络' },
          { value: 10, label: '公网网络' },
          { value: 12, label: '测试网络' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择属性',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'status',
        label: '设备状态',
        value: ref<number>(0),
        optionItems: [
          { value: '', label: '' },
          { value: 0, label: '在线' },
          { value: 1, label: '下线' },
          { value: 2, label: '挂牌' },
          { value: 3, label: '备用' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'auto_enable',
        label: '数据采集',
        value: ref(null),
        optionItems: [
          { value: '', label: '' },
          { value: true, label: '是' },
          { value: false, label: '否' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        label: 'id',
        key: 'id',
        value: ref(''),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            disabled: true,
            onUpdateValue: (newVal: any) => {
              // rowData.u_location_start = newVal
              //console.log('formItem.value', rowData)
              formItem.value.value = newVal
            },
          })
        },
      },
      // {
      //   key: 'plan',
      //   label: '采集方案',
      //   value: ref(null),
      //   optionItems: shallowReactive([] as Array<SelectOption>),
      //   render: (formItem) => {
      //     return h(NSelect, {
      //       options: formItem.optionItems as Array<SelectOption>,
      //       value: formItem.value.value,
      //       placeholder: '请选择采集方案',
      //       onUpdateValue: (val) => {
      //         formItem.value.value = val
      //       },
      //     })
      //   },
      // },
    ] as Array<FormItem>
    const connect_account_FormOptions = [
      {
        key: 'account',
        label: '管理账号',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem: any) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            multiple:true,
            placeholder: '请选择协议端口',
            onUpdateValue: (val) => {
              formItem.value.value = val
              //console.log(val)
            },
          })
        },
      },
      // {
      //   key: 'protocol_port',
      //   label: '协议端口',
      //   value: ref(''),
      //   optionItems: [],
      //   render: (formItem: any) => {
      //     return h(NSelect, {
      //       options: formItem.optionItems as Array<SelectOption>,
      //       value: formItem.value.value,
      //       placeholder: '请选择协议端口',
      //       onUpdateValue: (val) => {
      //         formItem.value.value = val
      //       },
      //     })
      //   },
      // },
    ]
    const device_import_template_url = ref('')
    const importFormOptions = [
      {
        key: 'manage_ip',
        label: '管理地址',
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
        key: 'framework',
        label: '网络架构',
        value: ref(''),
        optionItems: [
          { value: '2', label: '二层' },
          { value: '4', label: '三层' },
          { value: '6', label: '大二层' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择架构',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'vendor',
        label: '供应商',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择供应商',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'role',
        label: '设备角色',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'category',
        label: '类型',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择设备类型',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'idc',
        label: '所属机房',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            filterable: true,
            placeholder: '请选择机房',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            'on-update:value': get_info_by_idc.bind(formItem.value.value),
          })
        },
      },
      {
        key: 'idc_model',
        label: '模块',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            filterable: true,
            placeholder: '请选择模块',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            'on-update:value': get_info_by_idc_model.bind(formItem.value.value),
          })
        },
      },
      {
        key: 'serial_num',
        label: 'SN号',
        value: ref(''),
        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (val: any) => {
              formItem.value.value = val
            },
            placeholder: '请输入序列号',
          })
        },
      },
      {
        key: 'rack',
        label: '机柜',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择机柜',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'u_location',
        label: 'U位置',
        value: ref(''),
        render: (formItem) => {
          return h(NInputGroup, {}, [
            h(NInput, {
              value: formItem.value.value.split('-')[0],
              onUpdateValue: (newVal: any) => {
                // rowData.u_location_start = newVal
                //console.log('formItem.value', rowData)
                formItem.value.value = newVal
              },
              maxlength: 50,
              placeholder: 'U位起始',
            }),
            h(NInput, {
              value: formItem.value.value.split('-')[1],
              onUpdateValue: (newVal: any) => {
                formItem.value.value = newVal
              },
              maxlength: 50,
              placeholder: 'U位结束',
            }),
          ])
        },
      },
      {
        key: 'netzone',
        label: '网络区域',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            filterable: true,
            // disabled: checkedValueRef.value,
            placeholder: '请选择网络区域',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'memo',
        label: '备注信息',
        value: ref(''),

        render: (formItem) => {
          return h(NInput, {
            value: formItem.value.value,
            onUpdateValue: (val: any) => {
              formItem.value.value = val
            },
            placeholder: '请输入备注信息',
          })
        },
      },
      {
        key: 'attribute',
        label: '网络属性',
        value: ref(''),
        optionItems: [
          { value: '', label: '' },
          { value: 2, label: '生产网络' },
          { value: 4, label: '研发网络' },
          { value: 6, label: '研测网络' },
          { value: 8, label: '骨干网络' },
          { value: 10, label: '公网网络' },
          { value: 12, label: '测试网络' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            filterable: true,
            placeholder: '请选择网络属性',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'status',
        label: '设备状态',
        value: ref<number>(0),
        optionItems: [
          { value: '', label: '' },
          { value: 0, label: '在线' },
          { value: 1, label: '下线' },
          { value: 2, label: '挂牌' },
          { value: 3, label: '备用' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择状态',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'auto_enable',
        label: '数据采集',
        value: ref<number>(1),
        optionItems: [
          { label: '是', value: 1 },
          { label: '否', value: 0 },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择是否',
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
    ] as Array<FormItem>
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
        key: 'vendor',
        label: '供应商',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择供应商',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            'on-update:value': get_info_by_vendor.bind(formItem.value.value),
          })
        },
      },
      {
        key: 'idc',
        label: '机房',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择机房',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            'on-update:value': get_info_by_idc.bind(formItem.value.value),
          })
        },
      },
      {
        key: 'role',
        label: '角色',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择角色',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'manage_ip',
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
        key: 'category',
        label: '类型',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择类型',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'idc_model',
        label: '模块',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择网络属性',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
            'on-update:value': get_info_by_idc_model.bind(formItem.value.value),
          })
        },
      },

      {
        key: 'netzone',
        label: '区域',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择区域',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'serial_num',
        label: '序列号',
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
            placeholder: '请输入序列号',
          })
        },
      },
      {
        key: 'model',
        label: '型号',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择网络属性',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'rack',
        label: '机柜',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择机柜',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },

      {
        key: 'status',
        label: '状态',
        value: ref('0'),
        optionItems: [
          { value: '', label: '' },
          { value: '0', label: '在线' },
          { value: '1', label: '下线' },
          { value: '2', label: '挂牌' },
          { value: '3', label: '备用' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择网络架构',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'framework',
        label: '网络架构',
        value: ref(''),
        optionItems: [
          { value: '', label: '' },
          { value: '2', label: '二层' },
          { value: '4', label: '三层' },
          { value: '6', label: '大二层' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择网络架构',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },
      {
        key: 'attribute',
        label: '网络属性',
        value: ref(''),
        optionItems: [
          { value: '', label: '' },
          { value: 2, label: '生产网络' },
          { value: 4, label: '研发网络' },
          { value: 6, label: '研测网络' },
          { value: 8, label: '骨干网络' },
          { value: 10, label: '公网网络' },
          { value: 12, label: '测试网络' },
        ],
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择网络属性',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
          })
        },
      },

      {
        key: 'u_location_start',
        label: 'U位',
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
            placeholder: '起始U位',
          })
        },
      },
      {
        key: 'plan',
        label: '采集方案',
        value: ref(''),
        optionItems: shallowReactive([] as Array<SelectOption>),
        render: (formItem) => {
          return h(NSelect, {
            options: formItem.optionItems as Array<SelectOption>,
            value: formItem.value.value,
            placeholder: '请选择采集方案',
            filterable: true,
            onUpdateValue: (val) => {
              formItem.value.value = val
            },
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
            onKeyup: (Event) => {
              if (Event.keyCode == 13) {
                onSearch()
              }
            },
            placeholder: '请输入关键字',
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
    const searchDataFormRef = ref<DataFormType | null>(null)
    const rowData = ref<Object | null>(null)
    const message = useMessage()
    const naiveDailog = useDialog()
    const edit_rowData = ref<Object | null>(null)
    const tableColumns = reactive(
      useTableColumn(
        [
          table.selectionColumn,
          // table.indexColumn,row_expand.bind(null,rowData)
          {
            type: 'expand',
            expandable: (rowData) => true,
            renderExpand: (rowData) => {
              return h('DataForm', { preset: 'grid-item' }, [
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '设备名:',
                        style: {
                          height: '0px',
                          width: '32%',
                        },
                      },
                      () => h('span', {}, '' + rowData.name)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '供应商: ',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.vendor_name)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '所属机房:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.idc_name)
                    ),
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '管理IP:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.manage_ip)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '设备类型:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.category_name)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '所属区域:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.netzone_name)
                    ),
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '序列号:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.serial_num)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '硬件型号:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.model_name)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '设备角色:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.role_name)
                    ),
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '设备状态:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.status_name)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '软件版本:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.soft_version)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '机房模块:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.idc_model_name)
                    ),
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: 'HA状态:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.ha_status_name)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '补丁版本:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.patch_version)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '机柜:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.rack_name)
                    ),
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '框式编号:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.slot)
                    ),
                    h(
                      NFormItem,
                      {
                        label: '上线日期:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.uptime)
                    ),
                    h(
                      NFormItem,
                      {
                        label: 'U位:',
                        style: { width: '32%' },
                      },
                      () =>
                        h('span', {}, '' + rowData.u_location_start + '-' + rowData.u_location_end)
                    ),
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '管理账户\n:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, ' ' + rowData.adpp_device)
                    ),

                    h(NFormItem, { label: '监控状态\n:', style: { width: '32%' } }, () =>
                      h(
                        'span',
                        {
                          style: {
                            backgroundColor: status_check.value === '正常' ? '#00a65a' : '#d03050',
                          },
                          // size: 'small',
                        },
                        ' ' + status_check.value
                      )
                    ),
                    h(NFormItem, { label: '变更轨迹\n:', style: { width: '32%' } }, () =>
                      h(
                        NButton,
                        {
                          text: true,
                          color: '#204d74',
                          onclick: change_handleClick.bind(null, rowData),
                        },
                        () => h('span', {}, '变更轨迹')
                      )
                    ),
                    // () => h('span',
                    // //     {
                    // //   type: status_check  ? 'success' : 'error', size: 'small',
                    // // },
                    //     {},
                    // '监控状态: ' + status_check ? '正常' : '异常',)),
                    ,
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '1G端口使用\n:',
                        style: {
                          width: '15%',
                        },
                        hidden: !int_used_obj.value['int_unused_1g'],
                      },
                      () =>
                        h(
                          'span',
                          {},
                          ' ' +
                            int_used_obj.value['int_used_1g'] +
                            '/' +
                            (parseInt(int_used_obj.value['int_used_1g']) +
                              parseInt(int_used_obj.value['int_unused_1g']))
                        )
                    ),
                    h(
                      NFormItem,
                      {
                        label: '10G端口使用\n:',
                        style: {
                          width: '15%',
                        },
                        hidden: !int_used_obj.value['int_unused_10g'],
                      },
                      () =>
                        h(
                          'span',
                          {},
                          '' +
                            int_used_obj.value['int_used_10g'] +
                            '/' +
                            (parseInt(int_used_obj.value['int_used_10g']) +
                              parseInt(int_used_obj.value['int_unused_10g']))
                        )
                    ),
                    h(
                      NFormItem,
                      {
                        label: '40G端口使用\n:',
                        style: {
                          width: '15%',
                        },
                        hidden: !int_used_obj.value['int_used_40g'],
                      },
                      () =>
                        h(
                          'span',
                          {},
                          ' ' +
                            int_used_obj.value['int_used_40g'] +
                            '/' +
                            (parseInt(int_used_obj.value['int_used_40g']) +
                              parseInt(int_used_obj.value['int_unused_40g']))
                        )
                    ),
                    h(
                      NFormItem,
                      {
                        label: '100G端口使用\n:',
                        style: {
                          width: '15%',
                        },
                        hidden: !int_used_obj.value['int_unused_100g'],
                      },
                      () =>
                        h(
                          'span',
                          {},
                          '' +
                            int_used_obj.value['int_used_100g'] +
                            '/' +
                            (parseInt(int_used_obj.value['int_used_100g']) +
                              parseInt(int_used_obj.value['int_unused_100g']))
                        )
                    ),
                    h(
                      NFormItem,
                      {
                        label: '共计使用\n:',
                        style: { width: '15%' },
                        hidden: !int_used_obj.value['int_used'],
                      },
                      () =>
                        h(
                          'span',
                          {},
                          '' +
                            int_used_obj.value['int_used'] +
                            '/' +
                            parseInt(int_used_obj.value['int_total'])
                        )
                    ),
                  ]
                ),
                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px', width: '100%' },
                  },
                  [
                    h(NFormItem, { label: '账户', style: { width: '30%', fontWeight: 'bold' } }, [
                      h(
                        NButton,
                        {
                          text: true,
                          color: '#204d74',
                          onclick: show_account_handleClick.bind(null, rowData),
                        },
                        () => h('span', {}, '查看账户')
                      ),
                      h(
                        NButton,
                        {
                          text: true,
                          color: '#204d74',
                          onclick: connect_account_handleClick.bind(null, rowData),
                        },
                        () => h('span', {}, '关联账户')
                      ),
                      h(
                        NButton,
                        {
                          text: true,
                          color: '#204d74',
                          onclick: BindIP_handleClick.bind(null, rowData),
                        },
                        () => h('span', {}, '绑定IP')
                      ),
                    ]),
                    h(
                      NFormItem,
                      {
                        label: '绑定IP信息',
                        hidden: rowData.bind_ip.length === 0,
                        style: { width: '30%', paddingLeft: '10px' },
                      },
                      () =>
                        h(NDataTable, {
                          data: rowData.bind_ip,
                          size: 'small',
                          hidden: rowData.bind_ip.length === 0,
                          columns: [
                            {
                              title: 'IP标识名',
                              key: 'name',
                              width: 100,
                              render(row, index) {
                                return h('span', row.split('-')[0])
                              },
                            },
                            {
                              title: 'IP地址',
                              key: 'ip',
                              width: 150,
                              render(row, index) {
                                return h('span', row.split('-')[1])
                              },
                            },
                          ],
                        })
                    ),
                  ]
                ),

                h(
                  NForm,
                  {
                    labelWidth: '160px',
                    inline: true,
                    labelPlacement: 'left',
                    style: { height: '5px', fontSize: '12px', width: '100%' },
                  },
                  [
                    h(
                      NFormItem,
                      {
                        label: '采集方案:',
                        style: { width: '32%' },
                      },
                      () => h('span', {}, '' + rowData.plan_name)
                    ),
                  ]
                ),
              ])
            },
          },
          {
            title: '设备名称',
            key: 'name',
            width: 150,
            fixed: 'left',
          },
          {
            title: '管理IP',
            key: 'manage_ip',
            width: 120,
          },
          {
            title: '厂商',
            key: 'vendor_name',
            width: 100,
          },
          {
            title: '型号',
            key: 'model_name',
            width: 100,
          },
          {
            title: '类型',
            key: 'category_name',
            width: 100,
          },
          {
            title: '机房',
            key: 'idc_name',
            width: 100,
          },
          {
            title: '区域',
            key: 'netzone_name',
            width: 100,
          },
          {
            title: '角色',
            key: 'role_name',
            width: 100,
          },
          {
            title: '状态',
            key: 'status_name',
            width: 80,
          },
          {
            title: '自动化',
            key: 'auto_enable',
            width: 60,
            render: (rowData) =>
              renderTag(!!rowData.auto_enable ? '启用' : '禁用', {
                type: !!rowData.auto_enable ? 'success' : 'error',
                size: 'small',
              }),
          },
          {
            title: '机柜',
            key: 'rack_name',
            width: 80,
          },
          {
            title: 'U位',
            key: 'u_location_start',
            width: 120,
            render: (rowData) => {
              return rowData.u_location_start + '-' + rowData.u_location_end
            },
          },
          {
            title: '编辑',
            key: 'edit',
            fixed: 'right',
            width: 80,
            render: (rowData) => {
              return h(
                NButton,
                {
                  type: 'info',
                  size: 'tiny',
                  onClick: EditFunction.bind(null, rowData),
                },
                () => h('span', {}, 'EDIT')
              )
              // return useRenderAction([
              //   {
              //     label: 'Edit',
              //     onClick: EditFunction.bind(null, rowData),
              //   },
              //
              // ] as TableActionModel[])
            },
          },
          {
            title: 'WEBSSH',
            key: 'webssh',
            fixed: 'right',
            width: 80,
            render: (rowData) => {
              return h(
                NButton,
                {
                  type: 'success',
                  size: 'tiny',
                  onClick: onWebssh.bind(null, rowData),
                },
                () => h('span', {}, 'WEBSSH')
              )
              // return useRenderAction([
              //   {
              //     label: 'WEBSSH',
              //     onClick: onWebssh.bind(null, rowData),
              //   },
              //
              // ] as TableActionModel[])
            },
          },
          {
            title: '复制',
            key: 'actions',
            fixed: 'right',
            width: 80,
            render: (rowData) => {
              return h(
                NButton,
                {
                  type: 'warning',
                  size: 'tiny',
                  onClick: Copy.bind(null, rowData),
                },
                () => h('span', {}, '信息复制')
              )
              // return useRenderAction([
              //   {
              //     label: 'WEBSSH',
              //     onClick: onWebssh.bind(null, rowData),
              //   },
              //
              // ] as TableActionModel[])
            },
          },
        ],
        {
          align: 'center',
        } as DataTableColumn
      )
    )
    const account_tableColumns = reactive(
      useTableColumn(
        [
          {
            title: '账户',
            key: 'account__username',
          },
          {
            title: '密码',
            key: 'account__password',
          },
          {
            title: '协议',
            key: 'protocol_port__protocol',
          },
          {
            title: '端口',
            key: 'protocol_port__port',
            width: 100,
          },
        ],
        { align: 'center' } as DataTableColumn
      )
    )
    const itemDataFormRef = ref<DataFormType | null>(null)
    const importDataFormRef = ref<DataFormType | null>(null)
    const connect_account_DataFormRef = ref<DataFormType | null>(null)
    const EditDataFormRef = ref<DataFormType | null>(null)
    // const searchDataFormRef = ref<DataFormType | null>(null)
    const modalDialog = ref<ModalDialogType | null>(null)
    const WebsshmodalDialog = ref<ModalDialogType | null>(null)
    const ChangeLogmodalDialog = ref<ModalDialogType | null>(null)
    const show_password_modalDialog = ref<ModalDialogType | null>(null)
    const connect_account_modalDialog = ref<ModalDialogType | null>(null)
    const account_modalDialog = ref<ModalDialogType | null>(null)
    const device_import_modalDialog = ref<ModalDialogType | null>(null)
    const bind_ip_modalDialog = ref<ModalDialogType | null>(null)
    const device_import_dialog = useDialog()
    const collect_modalDialog = ref(false)
    const report_modalDialog = ref(false)
    const device_data_show = ref(false)
    const int_used_obj = ref({})
    const current_row_data = ref(null)
    const status_check = ref('')
    const change_log_tableColumns = reactive(
      useTableColumn(
        [
          {
            title: '用户名',
            key: 'username',
            width: 100,
          },
          {
            title: '方法',
            key: 'view_method',
            width: 120,
          },
          {
            title: '登录IP',
            key: 'remote_addr',
            width: 150,
          },
          {
            title: '操作数据',
            key: 'data',
          },
          {
            title: '时间',
            key: 'requested_at',
            width: 120,
          },
        ],
        {
          align: 'center',
        } as DataTableColumn
      )
    )
    const change_log_list = shallowReactive([]) as Array<any>
    const account_list = shallowReactive([]) as Array<any>
    const account_page = ref<number>(1)
    const account_pageSize = ref<number>(10)
    const account_pageCount = ref<number>(1)
    const change_log_page = ref<number>(1)
    const change_log_pageSize = ref<number>(10)
    const change_log_pageCount = ref<number>(1)
    const change_log_keyword = ref('')
    const second_password = ref('')
    const bind_ip_form = ref({
      name: '',
      ip: '',
    })
    const change_log_pageSizes = [
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
    const account_pageSizes = [
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
    const get = useGet()
    const post = usePost()
    const put = usePut()
    const patch = usePatch()
    const checkedRowKeysRef = ref([])
    const collection_options = shallowReactive([]) as Array<any>
    const report_options = shallowReactive([]) as Array<any>
    const import_show = ref(false)
    const device_info = ref(0)

    function btnClick() {
      import_show.value = true
      // document.querySelector('.input-file').click()
    }

    function download_template() {
      // window.open(device_import_template)
      // let postdata = 'areaName='+obj.areaName+'&areaCode='+obj.areaCode+'&schoolName='+obj.schoolName+'&studentName='+obj.studentName+'&studentExamNumber='+obj.studentExamNumber+'&state='+obj.state+'&subjectName='+obj.subjectName+'&readTeacher='+obj.readTeacher;
      let xhr = new XMLHttpRequest()
      // xhr.setRequestHeader('Authorization', Cookies.get('netops-token'))
      xhr.responseType = 'arraybuffer'
      xhr.open('get', device_import_template, true)
      // xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
      xhr.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
          let blob = new Blob([xhr.response], {
            type: 'application/vnd.ms-excel',
          })
          let link = document.createElement('a')
          link.href = window.URL.createObjectURL(blob)
          link.download = 'import-demo.xlsx'
          link.click()
          window.URL.revokeObjectURL(link.href)
        }
      }
      xhr.send()
    }

    function exportData(event) {
      //console.log(event)
      // if (!event.currentTarget.files.length) {
      //   return
      // }

      let f = event.currentTarget.files[0]

      const import_data = new FormData()
      let csrf_token = Cookies.get('csrftoken')
      import_data.append('csrfmiddlewaretoken', csrf_token)
      import_data.append('file', f)
      post({
        url: device_import_url,
        data: import_data,
      }).then((res) => {
        //console.log(res)
        if (res.code === 200) {
          message.success(res.msg)
        } else {
          message.error('导入失败:' + res.msg)
        }
      })
      nextTick(() => {
        import_show.value = false
        doRefresh()
      })
      // //这里已经拿到了excel的file文件，若是项目需求，可直接$emit丢出文件
      // // that.$emit('getMyExcelData',f);
      // // 用FileReader来读取
      // let reader = new FileReader()
      // // 重写FileReader上的readAsBinaryString方法
      // // FileReader.prototype.readAsBinaryString = function(f) {
      // //   let binary = "";
      // //   let wb; // 读取完成的数据
      // //   let outdata; // 你需要的数据
      // //   let reader = new FileReader();
      // reader.onload = function(e) {
      //   // 读取成Uint8Array，再转换为Unicode编码（Unicode占两个字节）
      //   // let bytes = new Uint8Array(reader.result);
      //   // let length = bytes.byteLength;
      //   // for (let i = 0; i < length; i++) {
      //   //   binary += String.fromCharCode(bytes[i]);
      //   // }
      //   // var data = e.target.result
      //
      //   // 接下来就是xlsx
      //   // var wb = XLSX.read(data, {
      //   //   type: 'buffer',
      //   // })
      //   // var outdata = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]])
      //   // 导出格式为json，{表数据：[]}
      //   //  //console.log('表格数据', outdata)
      //   // that.excelData = outdata
      //   // that.tableData = outdata.slice(0, 10)
      //   // that.tableData = outdata
      //   // that.total = outdata.length
      //
      //   // 获取数据的key
      //   // var importDataThead = Array.from(Object.keys(outdata[0])).map(
      //   //     (item) => {
      //   //       return item
      //   //     },
      //   // )
      //
      //   // that.columnHeader = importDataThead
      //   // that.checkboxTableColumn = importDataThead.slice(0, 9)
      //   // that.checkboxTableColumn = importDataThead.slice(0, 9)
      //   //  //console.log('表头', importDataThead)
      // }
      // reader.readAsArrayBuffer(f)
      // // };
      // // reader.readAsBinaryString(f);
    }

    function NewConnectCollect() {
      collect_modalDialog.value = false
      checkedRowKeysRef.value.forEach((devid) => {
        let collect_data = new FormData()
        let dev_detail_info = table.dataList.filter((item) => item.id === devid)[0]
        collect_data.append('plan', selectCollectValues.value)
        collect_data.append('serial_num', dev_detail_info['serial_num'])
        patch({
          url: getNetworkDeviceList + devid + '/',
          data: collect_data,
        }).then((res) => {
          message.success('新关联方案成功')
          doRefresh()
          checkedRowKeysRef.value.length = 0
        })
      })
    }

    function NewConnectReport() {
      report_modalDialog.value = false
      checkedRowKeysRef.value.forEach((devid) => {
        let report_data = new FormData()
        let dev_detail_info = table.dataList.filter((item) => item.id === devid)[0]
        report_data.append('report', selectCollectValues.value)
        report_data.append('serial_num', dev_detail_info['serial_num'])
        patch({
          url: getNetworkDeviceList + '/' + devid + '/',
          data: report_data,
        }).then((res) => {
          if (res.code === 200) {
            message.success('新关联告警通知方案成功')
            doRefresh()
            checkedRowKeysRef.value.length = 0
          }
        })
      })
    }

    function onCancelCollect() {
      collect_modalDialog.value = false
      checkedRowKeysRef.value.length = 0
    }

    function row_expand(row: Record<string, unknown>) {
      //console.log('当前行', row)
    }

    function onSearch() {
      let request_url = ''
      // if (item) {
      //   request_url = getNetworkDeviceList + '?search=' + item
      // } else {
      const search_form = searchForm.value?.generatorParams()
      searchDataFormRef.value = search_form
      request_url =
        getNetworkDeviceList +
        '?name=' +
        search_form.name +
        '&manage_ip=' +
        search_form.manage_ip +
        '&vendor=' +
        search_form.vendor +
        '&idc=' +
        search_form.idc +
        '&role=' +
        search_form.role +
        '&category=' +
        search_form.category +
        '&serial_num=' +
        search_form.serial_num +
        '&framework=' +
        search_form.framework +
        '&attribute=' +
        search_form.attribute +
        '&plan=' +
        search_form.plan +
        '&model=' +
        search_form.model +
        '&netzone=' +
        search_form.netzone +
        '&idc_model=' +
        search_form.idc_model +
        '&status=' +
        search_form.status +
        '&search=' +
        search_form.search +
        '&rack=' +
        search_form.rack
      // }

      //  //console.log(searchForm.value?.generatorParams())

      get({
        url: request_url,
        data: () => {
          return {
            start: 0,
            // pageSize: pagination.pageSize,
            limit: pagination.pageSize,
          }
        },
      }).then((res) => {
        //  //console.log(res)
        if (res.code === 200) {
          // message.success('查询成功')
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
      searchForm.value?.reset()
    }

    function onUpdateBorder(isBordered: boolean) {
      table.bordered.value = isBordered
    }

    function onUpdateTable(newColumns: Array<TablePropsType>) {
      sortColumns(tableColumns, newColumns)
    }

    function doRefresh() {
      // device_import_template_url.value = device_import_template
      //console.log(searchDataFormRef.value)
      let request_url = ''
      let search_form = searchDataFormRef.value
      let info_host_list = sessionStorage.getItem('hostlist')
      let last_path = sessionStorage.getItem('last_path')
      if (last_path === '/cmdb/network_device') {
        // return
        sessionStorage.removeItem('last_path')
        window.location.reload()
      }
      if (searchDataFormRef.value === null) {
        request_url = getNetworkDeviceList
      } else {
        request_url =
          getNetworkDeviceList +
          '?name=' +
          search_form.name +
          '&manage_ip=' +
          search_form.manage_ip +
          '&vendor=' +
          search_form.vendor +
          '&idc=' +
          search_form.idc +
          '&role=' +
          search_form.role +
          '&category=' +
          search_form.category +
          '&serial_num=' +
          search_form.serial_num +
          '&framework=' +
          search_form.framework +
          '&attribute=' +
          search_form.attribute +
          '&plan=' +
          search_form.plan +
          '&model=' +
          search_form.model +
          '&netzone=' +
          search_form.netzone +
          '&idc_model=' +
          search_form.idc_model +
          '&status=' +
          search_form.status +
          '&search=' +
          search_form.search
      }
      if (info_host_list) {
        request_url = getNetworkDeviceList + '?search_host_list=' + info_host_list
      }
      if (info_host_list === '') {
        // message.error("检索无数据")
        request_url = getNetworkDeviceList
      }
      get({
        url: request_url,
        data: () => {
          return {
            start: (pagination.page - 1) * pagination.pageSize,
            // pageSize: pagination.pageSize,
            limit: pagination.pageSize,
            status: 0,
          }
        },
      }).then((res) => {
        //  //console.log(res)
        table.handleSuccess(res)
        pagination.setTotalSize(res.count || 10)
      })
    }

    function doIdc() {
      get({
        url: getCmdbIdcList,
        data: () => {
          return {
            limit: 1000,
          }
        },
      }).then((res) => {
        //  //console.log('idc_res', res)
        //  //console.log(conditionItems)
        const idc_list = res.results
        for (var i = 0; i < idc_list.length; i++) {
          const dict = {
            label: idc_list[i]['name'],
            value: idc_list[i]['id'],
          }
          if (conditionItems[2].optionItems != undefined) {
            conditionItems[2].optionItems.push(dict)
          }
          if (importFormOptions[5].optionItems != undefined) {
            importFormOptions[5].optionItems.push(dict)
          }
          if (EditFormOptions[8].optionItems !== undefined) {
            EditFormOptions[8].optionItems.push(dict)
          }
        }
        nextTick(() => {
          conditionItems[2].optionItems.splice(0, 0, { label: '', value: '' })
          EditFormOptions[8].optionItems.splice(0, 0, { label: '', value: '' })
          importFormOptions[5].optionItems.splice(0, 0, { label: '', value: '' })
        })
      })
    }

    function doVendor() {
      get({
        url: getVendorList,
        data: () => {
          return {
            limit: 1000,
          }
        },
      }).then((res) => {
        //  //console.log('vendor_res', res)
        //  //console.log(conditionItems)
        const idc_list = res.results
        for (var i = 0; i < idc_list.length; i++) {
          const dict = {
            label: idc_list[i]['name'],
            value: idc_list[i]['id'],
          }
          if (conditionItems[1].optionItems != undefined) {
            conditionItems[1].optionItems.push(dict)
          }

          if (EditFormOptions[2].optionItems != undefined) {
            EditFormOptions[2].optionItems.push(dict)
          }
          if (importFormOptions[2].optionItems != undefined) {
            importFormOptions[2].optionItems.push(dict)
          }
        }
        nextTick(() => {
          conditionItems[1].optionItems.splice(0, 0, { label: '', value: '' })
          EditFormOptions[2].optionItems.splice(0, 0, { label: '', value: '' })
          importFormOptions[2].optionItems.splice(0, 0, { label: '', value: '' })
        })
      })
    }

    function doRole() {
      get({
        url: getCmdbRoleList,
        data: () => {
          return {
            limit: 1000,
          }
        },
      }).then((res) => {
        //  //console.log('role_res', res)
        //  //console.log(conditionItems)
        const idc_list = res.results
        for (var i = 0; i < idc_list.length; i++) {
          const dict = {
            label: idc_list[i]['name'],
            value: idc_list[i]['id'],
          }
          if (conditionItems[3].optionItems != undefined) {
            conditionItems[3].optionItems.push(dict)
            // conditionItems[3].optionItems.splice(0, 0, {
            //   label: '',
            //   value: ''
            // });
          }
          if (EditFormOptions[3].optionItems != undefined) {
            EditFormOptions[3].optionItems.push(dict)
          }
          if (importFormOptions[3].optionItems != undefined) {
            importFormOptions[3].optionItems.push(dict)
          }
        }
      })
    }

    function doCagetory() {
      get({
        url: getCategoryList,
        data: () => {
          return {
            limit: 1000,
          }
        },
      }).then((res) => {
        //  //console.log('category_res', res)
        //  //console.log(conditionItems)
        const idc_list = res.results
        for (var i = 0; i < idc_list.length; i++) {
          const dict = {
            label: idc_list[i]['name'],
            value: idc_list[i]['id'],
          }
          if (conditionItems[5].optionItems != undefined) {
            conditionItems[5].optionItems.push(dict)
          }
          if (EditFormOptions[4].optionItems != undefined) {
            EditFormOptions[4].optionItems.push(dict)
          }
          if (importFormOptions[4].optionItems != undefined) {
            importFormOptions[4].optionItems.push(dict)
          }
        }
      })
    }

    function device_import() {
      device_import_modalDialog.value?.toggle()
    }

    function importDataFormConfirm() {
      if (importDataFormRef.value?.validator()) {
        let myDate = new Date()
        let year = myDate.getFullYear() //获取当前年
        let endyear = myDate.getFullYear() + 3 //获取当前年
        let mon = myDate.getMonth() + 1 //获取当前月
        let date = myDate.getDate()
        device_import_modalDialog.value?.toggle()
        let import_form = importDataFormRef.value.generatorParams()
        //console.log('设备录入参数', import_form)
        let import_formdata = new FormData()
        import_formdata.append('manage_ip', import_form['manage_ip'])
        import_formdata.append('vendor', import_form['vendor'])
        import_formdata.append('category', import_form['category'])
        import_formdata.append('serial_num', import_form['serial_num'])
        import_formdata.append('idc', import_form['idc'])
        import_formdata.append('netzone', import_form['netzone'])
        import_formdata.append('attribute', import_form['attribute'])
        import_formdata.append('framework', import_form['framework'])
        import_formdata.append('role', import_form['role'])
        import_formdata.append('idc_model', import_form['idc_model'])
        import_formdata.append('rack', import_form['rack'])
        import_formdata.append('u_location_start', import_form['u_location'])
        import_formdata.append('u_location_end', import_form['u_location'])
        import_formdata.append('memo', import_form['memo'])
        import_formdata.append('status', import_form['status'])
        import_formdata.append('auto_enable', import_form['auto_enable'])
        import_formdata.append('expire', '2099-01-01')
        import_formdata.append('uptime', year + '-' + mon + '-' + date)
        import_formdata['uptime'] = year + '-' + mon + '-' + date
        let vendor_id = import_form['vendor']
        if (vendor_id === 2) {
          import_formdata.append('plan', '13')
        }
        post({
          url: getNetworkDeviceList,
          data: import_formdata,
        }).then((res) => {
          console.log('res',res)
          if (res.code === 400) {
            message.error(res.message)
          }
          // if (res.code === 201) {
          var monitor_data = new FormData()
          monitor_data.append('serial_num', import_form['serial_num'])
          // 添加监控
          post({
            url: networkDeviceUrl,
            data: monitor_data,
          }).then((res) => {
            if (res.data === 200) {
              message.success(res.result)
            } else {
            }
          })
          get({
            url: networkDeviceUrl,
            data: () => {
              return {
                bgbu: JSON.stringify(['16', '80']),
                id: res.data['id'],
              }
            },
          }).then((res) => {
            if (res.code === 200) {
              message.success(res.data['msg'])
            }
          })
          nextTick(() => {
            message.success('设备录入成功,SN号:' + JSON.stringify(import_form.serial_num))
            doRefresh()
          })
          // }
        })

        // importDataFormRef.value?.reset()
      }
    }

    function EditConfirm() {
      //  //console.log('编辑确认提交', EditDataFormRef.value.generatorParams())
      modalDialog.value!.toggle()
      let device_info = EditDataFormRef.value.generatorParams()
      let edit_formdata = new FormData()
      edit_formdata.append('manage_ip', device_info['manage_ip'])
      edit_formdata.append('framework', device_info['framework'])
      edit_formdata.append('vendor', device_info['vendor'])
      edit_formdata.append('role', device_info['role'])
      edit_formdata.append('category', device_info['category'])
      edit_formdata.append('idc_model', device_info['idc_model'])
      edit_formdata.append('rack', device_info['rack'])
      edit_formdata.append('idc', device_info['idc'])
      edit_formdata.append('u_location_start', device_info['u_location_value'])
      edit_formdata.append('u_location_end', device_info['u_location_value'])
      edit_formdata.append('memo', device_info['memo'])
      edit_formdata.append('attribute', device_info['attribute'])
      edit_formdata.append('status', device_info['status'])
      edit_formdata.append('auto_enable', device_info['auto_enable'])
      edit_formdata.append('netzone', device_info['netzone'])
      edit_formdata.append('serial_num', device_info['serial_num'])
      edit_formdata.append('auto_enable', device_info['auto_enable'])
      patch({
        url: getNetworkDeviceList + '/' + device_info.id + '/',
        data: edit_formdata,
      }).then((res) => {
        // if (res.code === 200) {
          message.success('编辑设备成功')
          doRefresh()
        // } else {
          // message.error(res.message)
        // }
      })
    }

    function onWebssh(item) {
      localStorage.removeItem('init_cmd')
      get({
        url: deviceWebSshLogin,
        data: () => {
          return {
            pk: item.id,
          }
        },
      }).then((res) => {
        //console.log(res)
        const init_cmd = res.data['init_cmd']
        const remote_ip = res.data['remote_ip']
        const routerUrl = router.resolve({
          path: '/ssh',
          query: {
            id: item.id,
            remote_ip: remote_ip,
            manage_ip: item.manage_ip,
          },
        })
        //console.log(routerUrl)
        window.open(routerUrl.fullPath, '_blank') //打开新的窗口
      })
    }

    function Copy(item) {
      //console.log('item', item)
      var input = document.createElement('input') // 创建input对象
      input.value =
        item.idc_name +
        '/' +
        item['idc_model_name'] +
        '/' +
        item['rack_name'] +
        '/' +
        item['u_location_start'] +
        '-' +
        item['u_location_end'] +
        ' ' +
        '/SN:' +
        item['serial_num'] // 设置复制内容
      document.body.appendChild(input) // 添加临时实例
      input.select() // 选择实例内容
      document.execCommand('Copy') // 执行复制
      document.body.removeChild(input) // 删除临时实例
      message.success('复制成功')
    }

    function EditFunction(item: any) {
      modalDialog.value?.toggle()
      //console.log('编辑当前行', item)
      rowData.value = item
      //console.log(rowData.value)
      // edit_rowData.value['u_location'] = item.u_location_start+"-" +item.u_location_end
      nextTick(() => {
        // 根据机房查询网络区域
        get({
          url: getCmdbNetzoneList,
          // data: () => {
          //   return {
          //     limit: 1000,
          //   }
          // },
        }).then((res) => {
          //console.log('编辑--根据机房获取网络区域', res)
          //console.log(conditionItems)
          // let filter_list = []
          if (EditFormOptions[10].optionItems !== undefined) {
            EditFormOptions[10].optionItems.length = 0
            let netzone_list = []
            res.results.forEach((ele) => {
              let dict = {
                value: ele['id'],
                label: ele['name'],
              }
              netzone_list.push(dict)
            })
            EditFormOptions[10].optionItems.push(...netzone_list)
          }
        })

        // 根据机房查询模块
        get({
          url: getCmdbIdcModelList,
          data: () => {
            return {
              idc: item.idc,
              limit: 1000,
            }
          },
        }).then((res) => {
          //console.log('编辑--机房获取模块', res)
          //  //console.log(conditionItems)
          // let filter_list = []
          if (EditFormOptions[5].optionItems !== undefined) {
            EditFormOptions[5].optionItems.length = 0
            let idc_model_list = []
            res.results.forEach((ele) => {
              let dict = {
                value: ele['id'],
                label: ele['name'],
              }
              idc_model_list.push(dict)
            })
            EditFormOptions[5].optionItems.push(...idc_model_list)
          }
        })

        // 根据模块查询机柜
        get({
          url: getCmdbRackList,
          data: () => {
            return {
              idc_model: item.idc_model,
              limit: 1000,
            }
          },
        }).then((res) => {
          //console.log('编辑模块机柜内容', res)
          //  //console.log(conditionItems)
          // let filter_list = []
          if (EditFormOptions[7].optionItems !== undefined) {
            EditFormOptions[7].optionItems.length = 0
            let model_list = []
            res.results.forEach((ele) => {
              let dict = {
                value: ele['id'],
                label: ele['name'],
              }
              model_list.push(dict)
            })
            EditFormOptions[7].optionItems.push(...model_list)
          }
        })
        // 根据供应商查询型号

        EditFormOptions.forEach((it) => {
          const key = it.key
          const propName = item[key]
          if (key === 'u_location') {
            it.value.value = item['u_location_start'] + '-' + item['u_location_end']
          }
          if (key === 'id') {
            it.value.value = JSON.stringify(propName)
          } else {
            it.value.value = propName
          }
        })
      })
    }

    function get_info_by_idc(item) {
      //console.log('当前选中机房', item)
      get({
        url: getCmdbNetzoneList,
        // data: () => {
        //   return {
        //     limit: 1000,
        //   }
        // },
      }).then((res) => {
        //console.log('选中机房获取网络区域', res)
        //console.log(conditionItems)
        // let filter_list = []
        if (conditionItems[7].optionItems !== undefined) {
          conditionItems[7].optionItems.length = 0
          let netzone_list = []
          res.results.forEach((ele) => {
            let dict = {
              value: ele['id'],
              label: ele['name'],
            }
            netzone_list.push(dict)
          })
          conditionItems[7].optionItems.push(...netzone_list)
          if (importFormOptions[10].optionItems !== undefined) {
            importFormOptions[10].optionItems.length = 0
            importFormOptions[10].optionItems.push(...netzone_list)
          }
        }
      })

      get({
        url: getCmdbIdcModelList,
        data: () => {
          return {
            idc: item,
            limit: 1000,
          }
        },
      }).then((res) => {
        //console.log('选中机房获取模块', res)
        //console.log(conditionItems)
        // let filter_list = []
        if (conditionItems[6].optionItems !== undefined) {
          conditionItems[6].optionItems.length = 0
          let idc_model_list = []
          res.results.forEach((ele) => {
            let dict = {
              value: ele['id'],
              label: ele['floor'].toString() + 'F/' + ele['name'],
            }
            idc_model_list.push(dict)
          })
          conditionItems[6].optionItems.push(...idc_model_list)
          if (importFormOptions[6].optionItems !== undefined) {
            importFormOptions[6].optionItems.length = 0
            importFormOptions[6].optionItems.push(...idc_model_list)
          }
        }
      })
    }

    function get_info_by_vendor(item) {
      //console.log('当前选中供应商', item)
      get({
        url: getCmdbModelList,
        data: () => {
          return {
            vendor: item,
            limit: 1000,
          }
        },
      }).then((res) => {
        //console.log('该供应商型号', res)
        //console.log(conditionItems)
        // let filter_list = []
        if (conditionItems[9].optionItems !== undefined) {
          conditionItems[9].optionItems.length = 0
          let model_list = []
          res.results.forEach((ele) => {
            let dict = {
              value: ele['id'],
              label: ele['name'],
            }
            model_list.push(dict)
          })
          conditionItems[9].optionItems.push(...model_list)
        }
      })
    }

    function get_info_by_idc_model(item) {
      //console.log('当前选中什么模块', item)
      get({
        url: getCmdbRackList,
        data: () => {
          return {
            idc_model: item,
            limit: 1000,
          }
        },
      }).then((res) => {
        //console.log('该模块机柜内容', res)
        //console.log(conditionItems)
        // let filter_list = []
        if (conditionItems[10].optionItems !== undefined) {
          conditionItems[10].optionItems.length = 0
          let model_list = []
          res.results.forEach((ele) => {
            let dict = {
              value: ele['id'],
              label: ele['name'],
            }
            model_list.push(dict)
          })
          conditionItems[10].optionItems.push(...model_list)
          if (importFormOptions[8].optionItems !== undefined) {
            importFormOptions[8].optionItems.push(...model_list)
          }
        }
      })
    }

    function change_handleClick(item) {
      ChangeLogmodalDialog.value?.toggle()
      //console.log(item)
      get({
        url: get_api_request_log,
        data: () => {
          return {
            path: `/api/asset_networkdevice/${item.id}/`,
            limit: 1000,
          }
        },
      }).then((res) => {
        //console.log('变更轨迹', res)
        //  //console.log(conditionItems)
        // let filter_list = []
        change_log_list.length = 0
        change_log_list.push(...res.results)
        change_log_page.value = 1
        change_log_pageSize.value = 10
        change_log_pageCount.value = Math.ceil(res.count / 10)
      })
    }

    function show_account_handleClick(item) {
      show_password_modalDialog.value?.toggle()
      rowData.value = item
    }

    function connect_account_handleClick(item) {
      connect_account_modalDialog.value?.toggle()
      //console.log('设备关联账号')
      // getasset_account_protocolList
      device_info.value = item.id
      // get({
      //   url: getasset_account_protocolList,
      //   data: () => {
      //     return {
      //       asset: item.id,
      //     }
      //   },
      // }).then((res) => {
        //console.log('当前设备账户信息', res)
        // connect_account_FormOptions.forEach((it) => {
        //   const key = it.key
        //   const propName = item[key]
        //   if (key === 'account') {
        //     it.value.value = res.results[0]['account']
        //   }
        //   if (key === 'protocol_port') {
        //     it.value.value = res.results[0]['protocol_port']
        //   }
        // })

        //console.log(connect_account_FormOptions)
      // })
    }

    function BindIP_handleClick(item) {
      bind_ip_modalDialog.value?.toggle()
    }

    function BindIpConfirm() {
      //console.log(bind_ip_form.value)
    }

    function second_onConfirm() {
      //console.log(second_password.value)
      if (second_password.value === 'ccr_network') {
        show_password_modalDialog.value!.toggle()
        let csrf_token = Cookies.get('csrftoken')
        // 打开真实密码account_list/getInterfaceUsedList
        get({
          url: getInterfaceUsedList,
          data: () => {
            return {
              password: second_password.value,
              serial_num: rowData.value['serial_num'],
              csrfmiddlewaretoken: csrf_token,
            }
          },
        }).then((res) => {
          //console.log('account_list', res)
          account_list.length = 0
          account_list.push(...res.results)
          account_page.value = 1
          account_pageSize.value = 10
          account_pageCount.value = Math.ceil(res.results.length / 10)
        })
        account_modalDialog.value?.toggle()
      } else {
        message.warning('请校验二级管理密码')
      }
      // showModal.value = false
      //
    }

    function second_onCancel() {
      //console.log(second_password.value)
    }

    function rowKey(rowData: any) {
      return rowData.id
    }

    function handleCheck(rowKeys) {
      checkedRowKeysRef.value = rowKeys
      //console.log('选中哪几行', rowKeys)
    }

    function handleExpand(rowKeys) {
      // checkedRowKeysRef.value = rowKeys
      //console.log('展开哪一行', rowKeys)
      if (rowKeys.length > 1) {
        rowKeys.splice(0, 1)
      }
      if (rowKeys.length === 0) {
        return
      }
      current_row_data.value = table.dataList.filter((item) => {
        return item['id'] == rowKeys
      })[0]
      //  //console.log(current_row_data.value)
      if (current_row_data.value) {
        nextTick(() => {
          get({
            url: getInterfaceUsedList,
            data: () => {
              return {
                host_id: current_row_data.value.id,
                interface_used: 1,
              }
            },
          }).then((res) => {
            if (res.code === 200) {
              //console.log('获取展开行设备intused', res.results[0])
              const int_used_item = res.results[0]
              int_used_obj.value = int_used_item
              //console.log(int_used_obj.value)
            } else {
              //  //console.log('获取展开行设备intused', res.results[0])
              const int_used_item = {}
              int_used_obj.value = int_used_item
              //  //console.log(int_used_obj.value)
            }
          })
        })
        // nextTick(()=>{
        //   console
        // })

        // nextTick(() => {
        //   get({
        //     url: getInterfaceUsedList,
        //     data: () => {
        //       return {
        //         stauts_check: current_row_data.value.manage_ip,
        //       }
        //     },
        //   }).then((res) => {
        //     //console.log('获取展开行设备监控状态', res)
        //     if (res.code === 200) {
        //       const status_check_res = res.result[0]
        //       // status_check.value = status_check
        //       if (status_check_res['snmp_available'] == '1') {
        //         status_check.value = '正常'
        //       } else {
        //         status_check.value = '异常'
        //       }
        //     } else {
        //       status_check.value = '异常'
        //     }
        //   })
        // })
      }
    }

    function connect_collect() {
      if (checkedRowKeysRef.value.length > 0) {
        //console.log('执行设备关联采集方案')
        //console.log(table.dataList)
        let check_list = []
        table.dataList.forEach((ele) => {
          if (checkedRowKeysRef.value.indexOf(ele.id) !== -1) {
            check_list.push(ele)
          }
        })
        //console.log('选择关联采集方案的行', check_list)
        collect_modalDialog.value = true
      } else {
        message.error('请先勾选需要关联采集方案的设备')
      }
    }

    function connect_report() {
      if (checkedRowKeysRef.value.length > 0) {
        //console.log('执行设备关联通知方案')
        //console.log(table.dataList)
        let check_list = []
        table.dataList.forEach((ele) => {
          if (checkedRowKeysRef.value.indexOf(ele.id) !== -1) {
            check_list.push(ele)
          }
        })
        //console.log('选择关联通知方案的行', check_list)
        report_modalDialog.value = true
      } else {
        message.error('请先勾选需要关联通知方案的设备')
      }
    }

    function export_excel() {
      //  //console.log('选中哪几行', checkedRowKeysRef.value)
      if (checkedRowKeysRef.value.length > 0) {
        //console.log('执行数据导出')
        //console.log(table.dataList)
        let check_list = []
        table.dataList.forEach((ele) => {
          if (checkedRowKeysRef.value.indexOf(ele.id) !== -1) {
            check_list.push(ele)
          }
        })
        //console.log('选择导出的行', check_list)
        let export_str =
          '设备名称,管理IP,序列号,厂商,型号,类型,机房位置,机房模块,区域,角色,状态,机柜,U位\n'
        for (let i = 0; i < check_list.length; i++) {
          export_str =
            export_str +
            check_list[i].name +
            ',' +
            check_list[i].manage_ip +
            ',' +
            '`' +
            check_list[i].serial_num +
            ',' +
            check_list[i].vendor_name +
            ',' +
            check_list[i].model_name +
            ',' +
            check_list[i].category_name +
            ',' +
            check_list[i].idc_name +
            ',' +
            check_list[i].idc_model_name +
            ',' +
            check_list[i].netzone_name +
            ',' +
            check_list[i].role_name +
            ',' +
            check_list[i].status_name +
            ',' +
            check_list[i].rack_name +
            ',' +
            check_list[i].u_location_start +
            '--' +
            check_list[i].u_location_end +
            '\n'
        }
        export_str = encodeURIComponent(export_str)
        const link = document.createElement('a')
        link.href = 'data:text/csv;charset=utf-8,\ufeff' + export_str
        // link.style = 'visibility:hidden'
        link.download = '网络设备信息表.csv'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } else {
        message.error('请先勾选需要导出的设备')
      }
    }

    function get_cmdb_account() {
      get({
        url: getcmdb_accountList,
        data: () => {
          return {
            limit: 1000,
          }
        },
      }).then((res) => {
        if (connect_account_FormOptions[0].optionItems !== undefined) {
          res.results.forEach((ele) => {
            var dict = {
              label: ele['name'] + '(' + ele['username'] + ')',
              value: ele['id'],
            }
            connect_account_FormOptions[0].optionItems.push(dict)
          })
        }
      })
      //console.log('connect_account_FormOptions', connect_account_FormOptions)
    }

    function ConnectAccountConfirm() {
      console.log(connect_account_DataFormRef.value?.generatorParams())
      console.log('device_info.value',device_info.value)
      var connect_account_info = connect_account_DataFormRef.value?.generatorParams()
      var account_data = new FormData()
      account_data.append('asset',device_info.value)
      account_data.append('account',connect_account_info['account'])
      patch({
        url: getNetworkDeviceList +'/' +device_info.value+'/',
        data: account_data
      }).then((res) => {
        if (res.code === 200) {
          message.success('修改设备信息成功')
          connect_account_modalDialog.value!.toggle()
          doRefresh()
        }
      })
    }

    function doCollection() {
      get({
        url: getCollection_planList,
        data: () => {
          return {
            limit: 1000,
          }
        },
      }).then((res) => {
        const collection_list = res.results
        for (var i = 0; i < collection_list.length; i++) {
          const dict = {
            label: collection_list[i]['name'],
            value: collection_list[i]['id'],
          }
          collection_options.push(dict)
          if (conditionItems[15].optionItems != undefined) {
            conditionItems[15].optionItems.push(dict)
          }
          if (EditFormOptions[15].optionItems != undefined) {
            EditFormOptions[15].optionItems.push(dict)
          }
        }
        nextTick(() => {
          conditionItems[15].optionItems.splice(0, 0, { label: '', value: '' })
        })
      })
    }
    onMounted(get_cmdb_account)
    onMounted(doRefresh)
    onMounted(doIdc)
    onMounted(doVendor)
    onMounted(doRole)
    onMounted(doCagetory)
    onMounted(doCollection)

    return {
      // doReport,
      ConnectAccountConfirm,
      Copy,
      device_info,
      term,
      socket,

      BindIP_handleClick,
      BindIpConfirm,
      bind_ip_modalDialog,
      btnClick,
      exportData,
      download_template,
      handleCheck,
      handleExpand,
      int_used_obj,
      status_check,
      export_excel,
      device_import,
      checkedRowKeysRef,
      collection_options,
      report_options,
      connect_collect,
      connect_report,
      second_password,
      bind_ip_form,
      second_onConfirm,
      second_onCancel,
      itemDataFormRef,
      EditDataFormRef,
      importDataFormRef,
      device_import_dialog,
      searchDataFormRef,
      importDataFormConfirm,
      EditConfirm,
      tableColumns,
      account_tableColumns,
      EditFunction,
      change_handleClick,
      pagination,
      searchForm,
      onResetSearch,
      onSearch,
      ...table,
      rowData,
      change_log_list,
      account_list,
      change_log_page,
      change_log_pageSize,
      change_log_pageSizes,
      account_page,
      account_pageSize,
      account_pageSizes,

      change_log_keyword,
      change_log_pageCount,
      change_log_tableColumns,
      EditFormOptions,
      importFormOptions,
      connect_account_FormOptions,
      connect_account_DataFormRef,
      rowKey,
      modalDialog,
      WebsshmodalDialog,
      ChangeLogmodalDialog,
      show_password_modalDialog,
      connect_account_modalDialog,
      account_modalDialog,
      device_import_modalDialog,
      collect_modalDialog,
      report_modalDialog,
      show_account_handleClick,
      conditionItems,
      onUpdateTable,
      onUpdateBorder,
      doRefresh,
      get_info_by_idc,
      get_info_by_vendor,
      get_info_by_idc_model,
      row_expand,
      selectValues,
      selectCollectValues,
      bodyStyle,
      // onConfirm,
      NewConnectCollect,
      NewConnectReport,
      onCancelCollect,
      edit_rowData,
      segmented,
      connect_account_handleClick,
      device_data_show,
      import_show,
      device_import_template_url,
      formRef,
    }
  },
})
</script>

<style lang="scss">
.n-form.n-form--inline {
  width: 100%;
  display: inline-flex;
  align-items: flex-start;
  align-content: space-around;
  height: 5px;
}

.n-form-item.n-form-item--left-labelled .n-form-item-label {
  font-weight: bold;
}

.light-green {
  height: 220px;
  background-color: rgba(0, 128, 0, 0.12);
}

.green {
  height: 220px;
  background-color: rgba(0, 128, 0, 0.24);
}

.terminal {
  width: 100%;
  height: 100%;
}
</style>
