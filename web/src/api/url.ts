import { baseURL } from './axios.config'

export const baseAddress = baseURL
// 登录
export const login = '/base_platform/login/'

// 认证和权限URL
export const getTableList = '/base_platform/users/user/'
export const getRoleList = '/base_platform/system/role/'
export const getMenuList = '/base_platform/system/menu/'
export const getDepartmentList = '/base_platform/system/dept/'
// export const getMenuListByRole = '/base_platform/system/menu/web_router/'
export const WebRouter = '/rbac/system/menu/web_router/'
export const WebPermission = '/rbac/system/menu/web_permission/'
// 调度管理
export const getdispach = '/base_platform/backend/dispatch_page/'
// 任务列表
export const jobcenterTaskUrl = '/base_platform/backend/jobCenter/'
// 网络设备
export const get_device_expand = '/base_platform/backend/networklist/'
// 采集方案
export const deviceCollect = '/base_platform/backend/deviceCollect/'
// webssh
export const deviceWebSshLogin = '/base_platform/backend/deviceWebSsh/'
export const automation_chart = '/base_platform/backend/automationChart/'
// 未知
export const deviceInfoChange = '/base_platform/backend/deviceInfoChange/'
export const getperiodic_taskList = '/base_platform/backend/periodic_task/'
// 拓扑图
export const get_topology = '/base_platform/topology/index/'
export const topology_show = '/base_platform/topology/show/'
export const topology_media_img = '/media/topology/img/'
export const topology_icon = '/base_platform/topology/topology_icon/'
// 获取业务对应表
export const getBgbuList = '/base_platform/users/bgbu/'
// 获取变更路径(废弃ing)
export const get_api_request_log = '/base_platform/backend/api_request_log/'
export const getinterval_schedule = '/base_platform/backend/interval_schedule/'

export const get_cmdb_rack = '/base_platform/asset/cmdb_rack/'
export const device_import_url = '/base_platform/asset/excel/'
export const getCmdbIdcList = '/base_platform/asset/cmdb_idc/'
export const getCmdbRackList = '/base_platform/asset/cmdb_rack/'
export const getCmdbRoleList = '/base_platform/asset/cmdb_role/'
export const getVendorList = '/base_platform/asset/cmdb_vendor/'
export const getFrameworkList = '/base_platform/asset/framework/'
export const getAttributeList = '/base_platform/asset/attribute/'
export const getCmdbModelList = '/base_platform/asset/cmdb_model/'
export const device_import_template = '/base_platform/asset/excel/'
export const getCategoryList = '/base_platform/asset/cmdb_category/'
export const getCmdbNetzoneList = '/base_platform/asset/cmdb_netzone/'
export const getcmdb_accountList = '/base_platform/asset/cmdb_account/'
export const get_cmdb_idc_model = '/base_platform/asset/cmdb_idc_model'
export const device_account_url = '/base_platform/asset/device_account/'
export const getCmdbIdcModelList = '/base_platform/asset/cmdb_idc_model/'
export const getNetworkDeviceList = '/base_platform/asset/asset_networkdevice/'

export const get_git_config_tree = '/base_platform/config_center/git_config'

export const getCollection_planList = '/base_platform/automation/collection_plan/'

export const getInterfaceUsedList = '/base_platform/int_utilization/interfaceused/'

// 合规性检查结果
export const get_compliance_results = '/base_platform/config_center/compliance_results'
export const ttp_parse = '/base_platform/config_center/ttp_parse'
export const config_compliance = '/base_platform/config_center/api/config_compliance/'
export const config_center_api = '/base_platform/config_center/api/'
export const config_template = '/base_platform/config_center/api/config_template/'
export const fsm_parse = '/base_platform/config_center/fsm_parse'
export const jinja2_parse = '/base_platform/config_center/jinja2_parse'
export const config_center = '/base_platform/config_center'

// 微服务ipam测试环境
export const getSubnetTree = '/base_platform/open_ipam/subnet_tree/'
export const PostAddressHandel = '/base_platform/open_ipam/address_handel/'
// export const getinterval_schedule = '/base_platform/open_ipam/interval_schedule/'
export const getSubnetAddress = '/base_platform/open_ipam/subnet/'
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $urlPath: Record<string, string>
  }
}
