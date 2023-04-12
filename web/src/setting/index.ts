import { ADMIN_WORK_SETTING_INFO, ADMIN_WORK_S_TENANT } from '@/store/keys'
const settingInfo = JSON.parse(localStorage.getItem(ADMIN_WORK_SETTING_INFO) || '{}')
interface Setting {
  projectName: string
  theme: 'light' | 'dark'
  sideTheme: 'dark' | 'white' | 'blue' | 'image'
  themeColor: string
  layoutMode: 'ltr' | 'ttb' | 'lcr'
  sideWidth: number
  pageAnim: 'fade' | 'opacity' | 'down' | 'scale'
  isFixedNavBar: boolean
  actionBar: {
    isShowSearch: boolean
    isShowMessage: boolean
    isShowRefresh: boolean
    isShowFullScreen: boolean
  }
}
export const projectName = 'NET-AXE'

export default Object.assign(
  {
    theme: 'light',
    sideTheme: 'white',
    themeColor: 'cyan@#18a058',
    layoutMode: 'ttb',
    sideWidth: 210,
    pageAnim: 'opacity',
    isFixedNavBar: true,
    actionBar: {
      isShowSearch: true,
      isShowMessage: true,
      isShowRefresh: true,
      isShowFullScreen: true,
    },
  },
  settingInfo,
) as Setting
// export const projectName = ''
//
// export default Object.assign(
//   {
//     theme: 'light',
//     sideTheme: 'dark',
//     themeColor: 'cyan@#18a058',
//     layoutMode: 'ltr',
//     sideWidth: 210,
//     pageAnim: 'opacity',
//     isFixedNavBar: true,
//     actionBar: {
//       isShowSearch: true,
//       isShowMessage: true,
//       isShowRefresh: true,
//       isShowFullScreen: true,
//     },
//   },
//   settingInfo
// ) as Setting
