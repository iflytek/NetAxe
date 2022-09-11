import { AxiosResponse } from 'axios'
import { App } from '@vue/runtime-core'
import service from './axios.config'
import router from '@/router'

export interface HttpOption {
  url: string
  data?: any
  method?: string
  headers?: any
  beforeRequest?: () => void
  afterRequest?: () => void
}

export interface Response {
  totalSize: number | 0
  count: number | 0
  code: number
  msg: string
  message: string
  data: any
  results: any
  result: any
  length: number | 0
  now: any
  path: any
  sub_net: any
  ip_used: any
  subnet_used: any
  crontab_data: any
  interval_data: any
}

function http({ url, data, method, headers, beforeRequest, afterRequest }: HttpOption) {
  const successHandler = (res: AxiosResponse<Response>) => {
    // console.log(res)
    if (res.data.code === 200) {
      return res.data
    }
    if (res.data.code === 204) {
      return res.data
    }
    if (res.data.code === 401) {
      router.push('/login')
      throw new Error('认证失败请重新登录一下')
      // throw new Error('认证失败请重新登录一下')

    }
    if (res.data.code === 404) {
      // throw new Error(res.data.msg + '请求失败，未知异常')
      return res.data
    }
    if (res.data.code === undefined) {
      return res.data
    }
    if (res.data.code === 400) {
      return res.data
    }
    if (res.data.code === 500) {
      return res.data
    }
    if (res.data.code === 201) {
      return res.data
    }
    throw new Error(res.data.message + '请求失败，未知异常')
    // return res.data
  }
  const failHandler = (error: Response) => {
    afterRequest && afterRequest()
    // console.log(error)
    // throw new Error(error.msg || '请求失败，未知异常')
  }
  beforeRequest && beforeRequest()
  method = method || 'GET'
  const params = Object.assign(typeof data === 'function' ? data() : data || {}, {})
  return method === 'GET'
    ? service.get(url, { params }).then(successHandler, failHandler)
    : method === 'POST'
    ? service.post(url, params, { headers: headers }).then(successHandler, failHandler)
    : method === 'PUT'
    ? service.put(url, params, { headers: headers }).then(successHandler, failHandler)
    : method === 'PATCH'
    ? service.patch(url, params, { headers: headers }).then(successHandler, failHandler)
    : service.delete(url, params).then(successHandler, failHandler)
}

export function get({
  url,
  data,
  method = 'GET',
  beforeRequest,
  afterRequest,
}: HttpOption): Promise<Response> {
  return http({
    url,
    method,
    data,
    beforeRequest,
    afterRequest,
  })
}

export function post({
  url,
  data,
  method = 'POST',
  headers,
  beforeRequest,
  afterRequest,
}: HttpOption): Promise<Response> {
  return http({
    url,
    method,
    data,
    headers,
    beforeRequest,
    afterRequest,
  })
}

export function put({
  url,
  data,
  method = 'PUT',
  headers,
  beforeRequest,
  afterRequest,
}: HttpOption): Promise<Response> {
  return http({
    url,
    method,
    data,
    headers,
    beforeRequest,
    afterRequest,
  })
}

export function patch({
  url,
  data,
  method = 'PATCH',
  headers,
  beforeRequest,
  afterRequest,
}: HttpOption): Promise<Response> {
  return http({
    url,
    method,
    data,
    headers,
    beforeRequest,
    afterRequest,
  })
}

export function delete_fun({
  url,
  data,
  method = 'DELETE',
  headers,
  beforeRequest,
  afterRequest,
}: HttpOption): Promise<Response> {
  return http({
    url,
    method,
    data,
    headers,
    beforeRequest,
    afterRequest,
  })
}
function install(app: App): void {
  app.config.globalProperties.$http = http

  app.config.globalProperties.$get = get

  app.config.globalProperties.$post = post
}

export default {
  install,
  get,
  post,
  put,
  patch,
  delete_fun,
}

declare module '@vue/runtime-core' {
  // 为 `this.$` 提供类型声明
  interface ComponentCustomProperties {
    $get: (options: HttpOption) => Promise<Response>
    $post: (options: HttpOption) => Promise<Response>
    $put: (options: HttpOption) => Promise<Response>
    $patch: (options: HttpOption) => Promise<Response>
    $delete_fun: (options: HttpOption) => Promise<Response>
  }
}
