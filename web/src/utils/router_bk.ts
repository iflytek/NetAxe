import Cookies from 'js-cookie'
import {get} from '@/api/http'
import layoutStore from '@/store'
import {Layout} from '@/components'
import {UserState} from '@/store/types'
import {defineAsyncComponent} from 'vue'
import {RouteRecordRaw} from 'vue-router'
import router, {constantRoutes} from '../router'
import {isExternal, mapTwoLevelRouter, toHump} from '.'
import LoadingComponent from '../components/loading/index.vue'
import {baseAddress, WebPermission, WebRouter} from '@/api/url'
import {ADMIN_WORK_BUTTON_AUTH, ADMIN_WORK_S_TENANT, ADMIN_WORK_USER_INFO_KEY} from '@/store/keys'

const navigateID = localStorage.getItem(ADMIN_WORK_S_TENANT)

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

// 获取路由
function getRoutes() {
  console.log(layoutStore.state)
  return get({
    url: baseAddress + WebRouter,
    method: 'GET',
    data: { parent__isnull: true, navigate__id: navigateID }
  }).then((res: any) => {
    console.log(res)
    return generatorRoutes(res.results)
  })
}

// 获取路由
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function getPermission() {
  return get({
    url: baseAddress + WebPermission,
    method: 'GET',
    data: { navigate__id: layoutStore.state.navigateID }
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
  return !result ? 0 : result.length
}

function isMenu(path: string) {
  return getCharCount(path, '/') === 1
}

function getNameByUrl(path: string) {
  const temp = path.split('/')
  return toHump(temp[temp.length - 1])
}

function generatorRoutes(res: Array<OriginRoute>) {
  const tempRoutes: Array<RouteRecordRawWithHidden> = []
  res.forEach((it) => {
    if (!it.key){
      const path = it.link_path && isExternal(it.link_path) ? it.link_path : it.web_path
      const route: RouteRecordRawWithHidden = {
        path: path,
        name: getNameByUrl(path),
        hidden: !!it.hidden,
        component: it.web_path && isMenu(it.web_path) ? Layout:getComponent(it),
        meta: {
          title: it.name,
          affix: !!it.affix,
          cacheable: !!it.cacheable,
          icon: it.icon || 'menu',
          iconPrefix: it.iconPrefix || 'iconfont',
        },
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
      // layoutStore.changeNavigateID(userInfo.tenantUser[0] as any)

      // 配置租户是否显示
      // layoutStore.changeIsNavigate(false)
      // if (to.matched[0]?.name === "Permissions"){
      //   layoutStore.changeIsNavigate(true)
      // }

      const isEmptyRoute = layoutStore.isEmptyPermissionRoute()
      if (isEmptyRoute) {
        // 加载路由和按钮
        const webRoutes = await getRoutes()
        // const webPermission = await getPermission()
        const accessRoutes: Array<RouteRecordRaw> = []
        accessRoutes.push(...webRoutes)

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
