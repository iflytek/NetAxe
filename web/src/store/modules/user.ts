import { defineStore } from 'pinia'
import { UserState } from '../types'
import layoutStore from '../index'
import { ADMIN_WORK_USER_INFO_KEY, ADMIN_WORK_TOkEN_KEY, NETOPS_TOKEN } from '../keys'

import Avatar from '@/assets/img_avatar.gif'
import Cookies from 'js-cookie'

const defaultAvatar = Avatar

const userInfo: UserState = JSON.parse(localStorage.getItem(ADMIN_WORK_USER_INFO_KEY) || '{}')

const useUserStore = defineStore('user', {
  state: () => {
    return {
      userId: userInfo.userId || 0,
      roleId: userInfo.roleId || 0,
      roles: userInfo.roles || null,
      token: userInfo.token || '',
      userName: userInfo.userName || '',
      nickName: userInfo.nickName || '',
      avatar: userInfo.avatar || defaultAvatar,
    }
  },
  actions: {
    saveUser(userInfo: UserState) {
      return new Promise<void>((res) => {
        // console.log(res)
        this.userId = userInfo.userId
        this.userId = userInfo.userId
        this.token = 'Bearer ' + userInfo.token
        this.roleId = userInfo.roleId
        this.roles = userInfo.roles
        this.userName = userInfo.userName
        this.nickName = userInfo.nickName
        this.avatar = userInfo.avatar || defaultAvatar
        // console.log(userInfo)
        // Cookies.set(ADMIN_WORK_TOkEN_KEY, 'Bearer ' + userInfo.token)
        Cookies.set(NETOPS_TOKEN, 'Bearer ' + userInfo.token)
        Cookies.set('csrftoken', userInfo['csrf_token'])
        // localStorage.setItem(ADMIN_WORK_USER_INFO_KEY, JSON.stringify(userInfo))
        localStorage.setItem('userId', userInfo.userId + '')
        localStorage.setItem('roleId', userInfo.roleId + '')
        // localStorage.setItem(ADMIN_WORK_USER_INFO_KEY, JSON.stringify(userInfo))
        res()
      })
    },
    changeNickName(newNickName: string) {
      this.nickName = newNickName
    },
    logout() {
      return new Promise<void>((resolve) => {
        this.userId = 0
        this.avatar = ''
        this.roleId = 0
        this.roles = []
        this.userName = ''
        this.nickName = ''
        this.token = ''
        // Cookies.remove(ADMIN_WORK_TOkEN_KEY)
        Cookies.remove(NETOPS_TOKEN)
        localStorage.clear()
        layoutStore.reset()
        resolve()
      })
    },
  },
})

export default useUserStore
