import router, { constantRoutes } from '../router'
import Cookies from 'js-cookie'
import { get } from '@/api/http'
import { baseAddress, getMenuListByRole } from '@/api/url'
import { RouteRecordRaw } from 'vue-router'
import { isExternal, mapTwoLevelRouter, toHump } from '.'
import { Layout } from '@/components'
import layoutStore from '@/store'
import { defineAsyncComponent } from 'vue'
import LoadingComponent from '../components/loading/index.vue'

interface OriginRoute {
  // menuUrl: string
  // menuName?: string
  name: string
  web_path: string
  hidden?: boolean
  outLink?: string
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
  return get({
    url: baseAddress + getMenuListByRole,
    method: 'GET',
    data: { parent__isnull: true },
  }).then((res: any) => {
    return generatorRoutes(res.results)
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
  return getCharCount(path, '/') === 1
}

function getNameByUrl(web_path: string) {
  const temp = web_path.split('/')
  return toHump(temp[temp.length - 1])
}

function generatorRoutes(res: Array<OriginRoute>) {
  const tempRoutes: Array<RouteRecordRawWithHidden> = []
  res.forEach((it) => {
    const route: RouteRecordRawWithHidden = {
      path: it.outLink && isExternal(it.outLink) ? it.outLink : it.web_path,
      name: getNameByUrl(it.web_path),
      hidden: !!it.hidden,
      component: isMenu(it.web_path) ? Layout : getComponent(it),
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
      const isEmptyRoute = layoutStore.isEmptyPermissionRoute()
      if (isEmptyRoute) {
        try {
          // 加载路由
          const accessRoutes: Array<RouteRecordRaw> = []
          const tempRoutes = await getRoutes()
          accessRoutes.push(...tempRoutes)
          if (localStorage.getItem('is_superuser') === 'true') {
            const system_data = {
              path: '/system',
              name: 'System',
              component: Layout,
              meta: {
                title: '系统配置',
                iconPrefix: 'iconfont',
                icon: 'setting',
              },
              children: [
                {
                  path: 'user',
                  name: 'User',
                  component: () => import('@/views/system/user.vue'),
                  meta: {
                    title: '用户配置',
                    iconPrefix: 'iconfont',
                    icon: 'user',
                  },
                },
                {
                  path: 'department',
                  name: 'Department',
                  component: () => import('@/views/system/department.vue'),
                  meta: {
                    title: '部门配置',
                    iconPrefix: 'iconfont',
                    icon: 'apartment',
                  },
                },
                {
                  path: 'role',
                  name: 'Role',
                  component: () => import('@/views/system/role.vue'),
                  meta: {
                    title: '角色配置',
                    iconPrefix: 'iconfont',
                    icon: 'control',
                  },
                },
                {
                  path: 'menu',
                  name: 'Menu',
                  component: () => import('@/views/system/menu.vue'),
                  meta: {
                    title: '菜单配置',
                    iconPrefix: 'iconfont',
                    icon: 'menu',
                  },
                },
              ],
            }
            accessRoutes.push(system_data)
          }
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
        } catch {
          return {
            path: '/login',
            query: { redirect: to.fullPath },
          }
        }
      } else {
        return true
      }
    }
  }
})
