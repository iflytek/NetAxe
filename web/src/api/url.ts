import { baseURL } from './axios.config'

export const baseAddress = baseURL

export const test = '/test'

export const login = '/vue3/login'

export const captcha = '/vue3/captcha'

export const updateUserInfo = '/updateUser'

export const addUserInfo = '/addUser'

export const getMenuListByRoleId = '/vue3/getMenusByRoleId'

export const getAllMenuByRoleId = '/getAllMenuByRoleId'

export const deleteUserById = '/deleteUserById'

export const dashboard_chart = '/vue3/dashboardChart'

export const networkDeviceUrl = '/vue3/networkDevice'

export const device_import_url = '/resources/import_assets/'

export const getNetworkDeviceList = '/api/asset_networkdevice/'

export const BackendApi = '/api/'

export const getCmdbIdcList = '/api/cmdb_idc/'

export const getCmdbRoleList = '/api/cmdb_role/'

export const getVendorList = '/api/cmdb_vendor/'

export const getCmdbModelList = '/api/cmdb_model/'

export const get_cmdb_rack = '/api/cmdb_rack/'

export const get_cmdb_idc_model = '/api/cmdb_idc_model'

export const getCategoryList = '/api/cmdb_category/'

export const get_api_request_log = '/api/api_request_log'

export const getCmdbNetzoneList = '/api/cmdb_netzone/'

export const getCmdbIdcModelList = '/api/cmdb_idc_model/'

export const getCmdbRackList = '/api/cmdb_rack'

export const getcmdb_accountList = '/api/cmdb_account/'

export const get_device_expand = '/network/networklist/'

export const device_import_template = '/vue3/importTemplate'

export const deviceWebSshLogin = '/vue3/deviceWebSsh'

export const deviceInfoChange = '/vue3/deviceInfoChange'

export const get_git_config_tree = '/config_center/git_config'

export const getInterfaceUsedList = '/api/interfaceused'

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $urlPath: Record<string, string>
  }
}
