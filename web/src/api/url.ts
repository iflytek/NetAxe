import { baseURL } from './axios.config'

export const baseAddress = baseURL

export const test = '/test'

export const login = '/net_backend/login'

export const captcha = '/net_backend/captcha'

export const updateUserInfo = '/updateUser'

export const addUserInfo = '/addUser'

export const getMenuListByRoleId = '/net_backend/getMenusByRoleId'

export const getAllMenuByRoleId = '/getAllMenuByRoleId'

export const deleteUserById = '/deleteUserById'

export const dashboard_chart = '/net_backend/dashboardChart'

export const networkDeviceUrl = '/net_backend/networkDevice'
export const deviceCollect = '/net_backend/deviceCollect'
export const automation_chart = '/net_backend/automationChart'
// 调度管理
export const getdispach = '/net_backend/dispatch_page/'
// 任务列表
export const jobcenterTaskUrl = '/net_backend/jobCenter'
export const device_import_url = '/resources_manage/excel/'
export const getperiodic_taskList = '/api/periodic_task/'
export const getinterval_schedule = '/api/interval_schedule'
export const getNetworkDeviceList = '/resources_manage/api/asset_networkdevice/'
export const getCollection_planList = '/automation/api/collection_plan/'
export const BackendApi = '/api/'

export const getCmdbIdcList = '/resources_manage/api/cmdb_idc/'
export const getFrameworkList = '/resources_manage/api/framework/'

export const getCmdbRoleList = '/resources_manage/api/cmdb_role/'

export const getVendorList = '/resources_manage/api/cmdb_vendor/'

export const getCmdbModelList = '/resources_manage/api/cmdb_model/'

export const get_cmdb_rack = '/api/cmdb_rack/'

export const get_cmdb_idc_model = '/api/cmdb_idc_model'

export const getCategoryList = '/resources_manage/api/cmdb_category/'

export const get_api_request_log = '/api/api_request_log'

export const getCmdbNetzoneList = '/api/cmdb_netzone/'

export const getCmdbIdcModelList = '/api/cmdb_idc_model/'

export const getCmdbRackList = '/api/cmdb_rack'

export const getcmdb_accountList = '/resources_manage/api/cmdb_account/'

export const get_device_expand = '/network/networklist/'

export const device_import_template = '/resources_manage/excel/'

export const deviceWebSshLogin = '/net_backend/deviceWebSsh'

export const deviceInfoChange = '/net_backend/deviceInfoChange'

export const get_git_config_tree = '/config_center/git_config'

export const getInterfaceUsedList = '/int_utilization/api/interfaceused/'

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $urlPath: Record<string, string>
  }
}
