import { baseURL } from './axios.config'

export const baseAddress = baseURL
// 登录
export const login = '/api/login/'

// 认证和权限URL
export const getTableList = '/api/users/user/'
export const getRoleList = '/api/system/role/'
export const getMenuList = '/api/system/menu/'
export const getDepartmentList = '/api/system/dept/'
export const getMenuListByRole = '/api/system/menu/web_router/'
export const WebRouter = '/rbac/system/menu/web_router/'
export const WebPermission = '/rbac/system/menu/web_permission/'
// 调度管理
export const getdispach = '/api/backend/dispatch_page/'
// 任务列表
export const jobcenterTaskUrl = '/api/backend/jobCenter/'
// 网络设备
export const get_device_expand = '/api/backend/networklist/'
// 采集方案
export const deviceCollect = '/api/backend/deviceCollect/'
// webssh
export const deviceWebSshLogin = '/api/backend/deviceWebSsh/'
export const automation_chart = '/api/backend/automationChart/'
// 未知
export const deviceInfoChange = '/api/backend/deviceInfoChange/'
export const getperiodic_taskList = '/api/backend/periodic_task/'
// 拓扑图
export const get_topology = '/api/topology/index/'
export const topology_show = '/api/topology/show/'
export const topology_media_img = '/media/topology/img/'
export const topology_icon = '/api/topology/topology_icon/'
// 获取业务对应表
export const getBgbuList = '/api/users/bgbu/'
// 获取变更路径(废弃ing)
export const get_api_request_log = '/api/backend/api_request_log/'
export const getinterval_schedule = '/api/backend/interval_schedule/'

export const get_cmdb_rack = '/api/asset/cmdb_rack/'
export const device_import_url = '/api/asset/excel/'
export const getCmdbIdcList = '/api/asset/cmdb_idc/'
export const getCmdbRackList = '/api/asset/cmdb_rack/'
export const getCmdbRoleList = '/api/asset/cmdb_role/'
export const getVendorList = '/api/asset/cmdb_vendor/'
export const getFrameworkList = '/api/asset/framework/'
export const getAttributeList = '/api/asset/attribute/'
export const getCmdbModelList = '/api/asset/cmdb_model/'
export const device_import_template = '/api/asset/excel/'
export const getCategoryList = '/api/asset/cmdb_category/'
export const getCmdbNetzoneList = '/api/asset/cmdb_netzone/'
export const getcmdb_accountList = '/api/asset/cmdb_account/'
export const get_cmdb_idc_model = '/api/asset/cmdb_idc_model'
export const device_account_url = '/api/asset/device_account/'
export const getCmdbIdcModelList = '/api/asset/cmdb_idc_model/'
export const getNetworkDeviceList = '/api/asset/asset_networkdevice/'

export const get_git_config_tree = '/api/config_center/git_config'

export const getCollection_planList = '/api/automation/collection_plan/'

export const getInterfaceUsedList = '/api/int_utilization/interfaceused/'

// 合规性检查结果
export const get_compliance_results = '/api/config_center/compliance_results'
export const ttp_parse = '/api/config_center/ttp_parse'
export const config_compliance = '/api/config_center/api/config_compliance'
export const config_center_api = '/api/config_center/api/'
export const config_template = '/api/config_center/api/config_template'
export const fsm_parse = '/api/config_center/fsm_parse'
export const jinja2_parse = '/api/config_center/jinja2_parse'
export const config_center = '/api/config_center'

// 微服务ipam测试环境
export const getSubnetTree = '/api/open_ipam/subnet_tree/'
export const PostAddressHandel = '/api/open_ipam/address_handel/'
// export const getinterval_schedule = '/api/open_ipam/interval_schedule/'
export const getSubnetAddress = '/api/open_ipam/subnet/'
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $urlPath: Record<string, string>
  }
}
