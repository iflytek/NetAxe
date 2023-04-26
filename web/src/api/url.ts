import { baseURL } from './axios.config'

export const baseAddress = baseURL
// 登录
export const login = '/base_plateform/login/'

// 认证和权限URL
export const getTableList = '/base_plateform/users/user/'
export const getRoleList = '/base_plateform/system/role/'
export const getMenuList = '/base_plateform/system/menu/'
export const getDepartmentList = '/base_plateform/system/dept/'
// export const getMenuListByRole = '/base_plateform/system/menu/web_router/'
export const WebRouter = '/rbac/system/menu/web_router/'
export const WebPermission = '/rbac/system/menu/web_permission/'
// 调度管理
export const getdispach = '/base_plateform/backend/dispatch_page/'
// 任务列表
export const jobcenterTaskUrl = '/base_plateform/backend/jobCenter/'
// 网络设备
export const get_device_expand = '/base_plateform/backend/networklist/'
// 采集方案
export const deviceCollect = '/base_plateform/backend/deviceCollect/'
// webssh
export const deviceWebSshLogin = '/base_plateform/backend/deviceWebSsh/'
export const automation_chart = '/base_plateform/backend/automationChart/'
// 未知
export const deviceInfoChange = '/base_plateform/backend/deviceInfoChange/'
export const getperiodic_taskList = '/base_plateform/backend/periodic_task/'
// 拓扑图
export const get_topology = '/base_plateform/topology/index/'
export const topology_show = '/base_plateform/topology/show/'
export const topology_media_img = '/media/topology/img/'
export const topology_icon = '/base_plateform/topology/topology_icon/'
// 获取业务对应表
export const getBgbuList = '/base_plateform/users/bgbu/'
// 获取变更路径(废弃ing)
export const get_api_request_log = '/base_plateform/backend/api_request_log/'
export const getinterval_schedule = '/base_plateform/backend/interval_schedule/'

export const get_cmdb_rack = '/base_plateform/asset/cmdb_rack/'
export const device_import_url = '/base_plateform/asset/excel/'
export const getCmdbIdcList = '/base_plateform/asset/cmdb_idc/'
export const getCmdbRackList = '/base_plateform/asset/cmdb_rack/'
export const getCmdbRoleList = '/base_plateform/asset/cmdb_role/'
export const getVendorList = '/base_plateform/asset/cmdb_vendor/'
export const getFrameworkList = '/base_plateform/asset/framework/'
export const getAttributeList = '/base_plateform/asset/attribute/'
export const getCmdbModelList = '/base_plateform/asset/cmdb_model/'
export const device_import_template = '/base_plateform/asset/excel/'
export const getCategoryList = '/base_plateform/asset/cmdb_category/'
export const getCmdbNetzoneList = '/base_plateform/asset/cmdb_netzone/'
export const getcmdb_accountList = '/base_plateform/asset/cmdb_account/'
export const get_cmdb_idc_model = '/base_plateform/asset/cmdb_idc_model'
export const device_account_url = '/base_plateform/asset/device_account/'
export const getCmdbIdcModelList = '/base_plateform/asset/cmdb_idc_model/'
export const getNetworkDeviceList = '/base_plateform/asset/asset_networkdevice/'

export const get_git_config_tree = '/base_plateform/config_center/git_config'

export const getCollection_planList = '/base_plateform/automation/collection_plan/'

export const getInterfaceUsedList = '/base_plateform/int_utilization/interfaceused/'

// 合规性检查结果
export const get_compliance_results = '/base_plateform/config_center/compliance_results'
export const ttp_parse = '/base_plateform/config_center/ttp_parse'
export const config_compliance = '/base_plateform/config_center/api/config_compliance/'
export const config_center_api = '/base_plateform/config_center/api/'
export const config_template = '/base_plateform/config_center/api/config_template/'
export const fsm_parse = '/base_plateform/config_center/fsm_parse'
export const jinja2_parse = '/base_plateform/config_center/jinja2_parse'
export const config_center = '/base_plateform/config_center'

// 微服务ipam测试环境
export const getSubnetTree = '/base_plateform/open_ipam/subnet_tree/'
export const PostAddressHandel = '/base_plateform/open_ipam/address_handel/'
// export const getinterval_schedule = '/base_plateform/open_ipam/interval_schedule/'
export const getSubnetAddress = '/base_plateform/open_ipam/subnet/'
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $urlPath: Record<string, string>
  }
}
