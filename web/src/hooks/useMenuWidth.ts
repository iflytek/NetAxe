import Setting from '../setting'
import { ADMIN_WORK_SETTING_INFO, ADMIN_WORK_S_TENANT } from '@/store/keys'
export function useMenuWidth() {
  // const r = document.querySelector(':root') as HTMLElement
  // const styles = getComputedStyle(r)
  // const menuWith = styles.getPropertyValue('--menu-width')
  //   console.log(menuWith)
  const menuWith = '210px'
  return parseInt(menuWith)
}

export function useChangeMenuWidth(width: Number) {
  // const r = document.querySelector(':root') as HTMLElement
  // r.style.setProperty('--menu-width', width + 'px')
  localStorage.setItem(
    ADMIN_WORK_SETTING_INFO,
    JSON.stringify(
      Object.assign(Setting, {
        sideWidth: width,
      })
    )
  )
}
