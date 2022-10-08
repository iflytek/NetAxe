export interface UserState {
  token: string
  image: string
  userName: string
  nickName: string
  isSuperuser: boolean
  roles: string[] | null
}
