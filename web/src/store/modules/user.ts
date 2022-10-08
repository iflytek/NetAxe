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
      token: userInfo.token || '',
      roles: userInfo.roles || null,
      userName: userInfo.userName || '',
      nickName: userInfo.nickName || '',
      image: userInfo.image || defaultAvatar,
    }
  },
  actions: {
    saveUser(userInfo: UserState) {
      return new Promise<void>((res) => {
        // console.log(res)
        this.token = 'Bearer ' + userInfo.token
        this.roles = userInfo.roles
        this.userName = userInfo.userName
        this.nickName = userInfo.nickName
        this.image = userInfo.image || defaultAvatar
        Cookies.set(NETOPS_TOKEN, 'Bearer ' + userInfo.token)
        // Cookies.set('csrftoken', userInfo["csrf_token"])
        localStorage.setItem('is_superuser', userInfo.isSuperuser + '')
        res()
      })
    },
    changeNickName(newNickName: string) {
      this.nickName = newNickName
    },
    logout() {
      return new Promise<void>((resolve) => {
        this.image = ''
        this.token = ''
        this.roles = []
        this.userName = ''
        this.nickName = ''
        localStorage.clear()
        Cookies.remove(NETOPS_TOKEN)
        layoutStore.reset()
        resolve()
      })
    },
  },
})

export default useUserStore
