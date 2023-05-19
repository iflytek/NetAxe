import Cookies from 'js-cookie'
import { get } from '@/api/http'
import layoutStore from '@/store'
import { Layout } from '@/components'
import { UserState } from '@/store/types'
import { defineAsyncComponent } from 'vue'
import { RouteRecordRaw } from 'vue-router'
import useUserStore from '@/store/modules/user'
import router, { constantRoutes } from '../router'
import { isExternal, mapTwoLevelRouter, toHump } from '.'
import LoadingComponent from '../components/loading/index.vue'
import { baseAddress, WebRouter, WebPermission } from '@/api/url'
import defaultRouteJson from '../../../default_memu.json'
import { ADMIN_WORK_USER_INFO_KEY, ADMIN_WORK_BUTTON_AUTH, ADMIN_WORK_S_TENANT } from '@/store/keys'

interface OriginRoute {
  key: any
  name: string
  web_path: string
  link_path?: string
  hidden?: boolean
  affix?: boolean
  cacheable?: boolean
  iconPrefix?: string
  icon?: string
  badge?: string | number
  children: Array<OriginRoute>
}

type RouteRecordRawWithHidden = RouteRecordRaw & { hidden: boolean }

function loadComponents() {
  return import.meta.glob('../views/**/*.vue')
}

const asynComponents = loadComponents()
const navigateID = localStorage.getItem(ADMIN_WORK_S_TENANT)

// 获取web权限
function getRoutes() {
  // console.log(layoutStore.state)
  if(navigateID){
     return get({
    url: baseAddress + WebRouter,
    method: 'GET',
    data: { parent__isnull: true, navigate__id: navigateID }
  }).then((res: any) => {
    return generatorRoutes(res.results)
  })
  }else{
     return get({
    url: baseAddress + WebRouter,
    method: 'GET',
    data: { parent__isnull: true, navigate__id: navigateID }
  }).then((res: any) => {
    return generatorRoutes(res.results)
  })
  }

}

// 获取menu权限
function getPermission() {
  return get({
    url: baseAddress + WebPermission,
    method: 'GET',
    data: { navigate__id: navigateID }
  }).then((res: any) => {
    localStorage.setItem(ADMIN_WORK_BUTTON_AUTH, JSON.stringify(res.results))
  })
}

function getComponent(it: OriginRoute) {
  return defineAsyncComponent({
    loader: asynComponents['../views' + it.web_path + '.vue'],
    loadingComponent: LoadingComponent,
  })
}

function getCharCount(str: string, char: string) {
  const regex = new RegExp(char, 'g')
  const result = str.match(regex)
  const count = !result ? 0 : result.length
  return count
}

function isMenu(path: string) {
  return getCharCount(path, '\/') === 1
}

function getNameByUrl(path: string) {
  const temp = path.split('/')
  return toHump(temp[temp.length - 1])
}

function generatorRoutes(res: Array<OriginRoute>) {
  const tempRoutes: Array<RouteRecordRawWithHidden> = []
  res.forEach((it) => {
    if (!it.key) {
      const path = it.link_path && isExternal(it.link_path) ? it.link_path : it.web_path
      const route: RouteRecordRawWithHidden = {
        path: path,
        name: getNameByUrl(path),
        hidden: !!it.hidden,
        component: it.web_path && isMenu(it.web_path) ? Layout : getComponent(it),
        meta: {
          title: it.name,
          affix: !!it.affix,
          cacheable: !!it.cacheable,
          icon: it.icon || 'menu',
          iconPrefix: it.iconPrefix || 'iconfont',
        },
        // children: []
      }
      if (it.children) {
        route.children = generatorRoutes(it.children)
      }
      tempRoutes.push(route)
    }
  })
  return tempRoutes
}

const whiteRoutes: string[] = ['/login', '/404', '/403', '/500']

function isTokenExpired(): boolean {
  const token = Cookies.get('netops-token')
  return !!token
}

router.beforeEach(async (to) => {
  console.log(to.path)
  if (whiteRoutes.includes(to.path)) {
    return true
  } else {
    if (!isTokenExpired()) {
      return {
        path: '/login',
        query: { redirect: to.fullPath },
      }
    } else {
      // 获取租户信息
      const userInfo: UserState = JSON.parse(localStorage.getItem(ADMIN_WORK_USER_INFO_KEY) || '{}')


      const isEmptyRoute = layoutStore.isEmptyPermissionRoute()
      console.log('isEmptyRoute', isEmptyRoute)
      if (isEmptyRoute && to.path!='/ssh') {
        
        // 加载路由和按钮
        let webRoutes: any = []
        if (!import.meta.env.VITE_LOCAL_ROUTER) {
          webRoutes = await getRoutes()
        } else {
          webRoutes = generatorRoutes(defaultRouteJson.menu)
          console.log('webRoutes', webRoutes)
        }
        // console.log(webRoutes)
        // const webPermission = await getPermission()
        const accessRoutes: Array<RouteRecordRaw> = []
        accessRoutes.push(...webRoutes)

        console.log(accessRoutes)
        const mapRoutes = mapTwoLevelRouter(accessRoutes)
        mapRoutes.forEach((it: any) => {
          router.addRoute(it)
        })
        router.addRoute({
          path: '/:pathMatch(.*)*',
          redirect: '/404',
          hidden: true,
        } as RouteRecordRaw)
        layoutStore.initPermissionRoute([...constantRoutes, ...accessRoutes])
        return { ...to, replace: true }
      } else {
        return true
      }
    }
  }
})
