import { mapTwoLevelRouter } from '@/utils'
import { createRouter, createWebHistory } from 'vue-router'

const Layout = () => import('@/components/Layout.vue')

export const constantRoutes = [
    {
        path: '/',
        redirect: '/index/work-place',
        hidden: true,
    },
    {
        path: '/login',
        name: 'Login',
        hidden: true,
        component: () => import('@/views/login/index.vue'),
    },
    {
        path: '/personal',
        name: 'personal',
        component: Layout,
        hidden: true,
        meta: {
            title: '个人中心',
        },
        children: [
            {
                path: '',
                component: () => import('@/views/personal/index.vue'),
                meta: {
                    title: '个人中心',
                },
            },
        ],
    },
    {
        path: '/index',
        component: Layout,
        name: 'Index',
        meta: {
            title: 'Dashboard',
            iconPrefix: 'iconfont',
            icon: 'dashboard',
        },
        children: [
            {
                path: 'work-place',
                name: 'WorkPlace',
                component: (): any => import('@/views/index/work-place.vue'),
                meta: {
                    title: '工作台',
                    affix: true,
                    iconPrefix: 'iconfont',
                    icon: 'index',
                },
            },
        ],
    },

    // {
    //     path: '/ip_manage',
    //     component: Layout,
    //     name: 'Ip_manage',
    //     meta: {
    //         title: '地址管理',
    //         iconPrefix: 'iconfont',
    //         icon: 'dashboard',
    //     },
    //     children: [
    //         {
    //             path: 'ipam',
    //             name: 'ipam',
    //             component: (): any => import('@/views/ip_manage/ipam.vue'),
    //             meta: {
    //                 title: 'IPAM',
    //                 affix: true,
    //                 iconPrefix: 'iconfont',
    //                 icon: 'infomation',
    //             },
    //         },
    //     ],
    // },


    {
        path: '/redirect',
        component: Layout,
        hidden: true,
        meta: {
            noShowTabbar: true,
        },
        children: [
            {
                path: '/redirect/:path(.*)*',
                component: (): any => import('@/views/redirect/index.vue'),
            },
        ],
    },
    {
        path: '/404',
        name: '404',
        hidden: true,
        component: () => import('@/views/exception/404.vue'),
    },
    {
        path: '/500',
        name: '500',
        hidden: true,
        component: () => import('@/views/exception/500.vue'),
    },
    {
        path: '/403',
        name: '403',
        hidden: true,
        component: () => import('@/views/exception/403.vue'),
    },
    {
        path: '/ssh',
        name: 'ssh',
        component: () => import('../views/ssh.vue'),
        hidden: true,
        meta: {
            requireAuth: true,
            index: '/ssh',
        }
    },
]
const router = createRouter({
    // history: createWebHashHistory(),
    history: createWebHistory(),
    routes: mapTwoLevelRouter(constantRoutes),
})

export default router
