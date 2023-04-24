<template>
  <n-el>
    <div class="flex login-container" v-if="!isMobileScreen">
      <div class="left">
        <img :src="ImageBg2" />
        <div class="content-wrapper">
          <div class="logo-wrapper">
            <img src="../../assets/logo.png" />
          </div>
          <!-- <div class="title">NetAxe</div> -->
          <div class="sub-title">网络自动化平台CMDB</div>
          <div class="flex-1 flex justify-center items-center ttppii"> 生活，应该还有诗和远方</div>
          <div class="version">NetAxe {{ version }} </div>
        </div>
      </div>
      <div class="right">
        <div class="form-wrapper">
          <div class="form-title">账号登录</div>
          <div class="item-wrapper">
            <n-input
              v-model:value="username"
              placeholder="请输入用户名"
              prefix-icon="el-icon-user"
              clearable
            />
          </div>
          <div class="mt-4 item-wrapper">
            <n-input
              v-model:value="password"
              placeholder="请输入密码"
              type="password"
              clearable
              prefix-icon="el-icon-lock"
            />
          </div>
          <div class="mt-6">
            <n-button type="primary" class="login" :loading="loading" @click="onLogin">
              登录
            </n-button>
          </div>
          <div class="mt-6 my-width flex-sub">
            <div class="flex justify-between">
              <n-checkbox v-model:checked="autoLogin">自动登录</n-checkbox>
              <a :underline="false" type="primary">忘记密码？</a>
            </div>
          </div>
        </div>

      </div>
    </div>
    <div v-else class="m-login-container">
      <div class="header">
        <div class="the-p"> P</div>
        <div class="mt-4 text-lg font-bold text-white"> NetAxe</div>
      </div>
      <div class="content">
        <n-input round placeholder="请输入用户名/手机号" size="large" v-model:value="username">
          <template #prefix>
            <n-icon>
              <PhoneIcon />
            </n-icon>
          </template>
        </n-input>
        <n-input
          class="mt-10"
          round
          placeholder="请输入密码"
          size="large"
          v-model:value="password"
          type="password"
          show-password-toggle
          :maxlength="8"
        >
          <template #prefix>
            <n-icon>
              <PasswordIcon />
            </n-icon>
          </template>
        </n-input>
        <n-button class="mt-20" round type="primary" block :loading="loading" @click="onLogin">
          登录
        </n-button>
        <div class="flex justify-between mt-4">
          <n-checkbox v-model:checked="autoLogin" color="#fff">自动登录</n-checkbox>
          <a class="text-white" type="primary">忘记密码？</a>
        </div>
      </div>
    </div>
  </n-el>
</template>

<script lang="ts">
  import { PUBLIC_KEY } from '@/store/keys'
  import { computed, defineComponent, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import ImageBg1 from '@/assets/img_login_bg.png'
  import ImageBg2 from '@/assets/img_login_fg.9c0e0a4c.jpeg'
  import { post, Response } from '@/api/http'
  import { login } from '@/api/url'
  import { UserState } from '@/store/types'
  import { useMessage } from 'naive-ui'
  import { useLayoutStore } from '@/components'
  import { DeviceType } from '@/types/store'
  import {
    PhonePortraitOutline as PhoneIcon,
    LockClosedOutline as PasswordIcon,
    // LogoGithub,
    // LogoAlipay,
    // LogoWechat,
  } from '@vicons/ionicons5'
  import useAppInfo from '@/hooks/useAppInfo'
  import useUserStore from '@/store/modules/user'
  import JsEncrypt from 'jsencrypt'

  export default defineComponent({
    name: 'Login',
    components: { PhoneIcon, PasswordIcon },
    setup() {
      const { version } = useAppInfo()
      const username = ref('')
      const password = ref('')
      const autoLogin = ref(true)
      const loading = ref(false)
      const router = useRouter()
      const route = useRoute()
      const userStore = useUserStore()
      const message = useMessage()
      const layoutStore = useLayoutStore()
      const encryptStr = new JsEncrypt()
      const isMobileScreen = computed(() => {
        return layoutStore.state.device === DeviceType.MOBILE
      })
      const onLogin = () => {
        loading.value = true
        const formdata = new FormData()
        //加密
        encryptStr.setKey(PUBLIC_KEY)
        formdata.append('username', username.value)
        formdata.append('password', encryptStr.encrypt(password.value).toString())
        post({
          url: login,
          data: formdata,
        })
          .then(({ data }: Response) => {
            userStore.saveUser(data as UserState).then(() => {
              router
                .replace({
                  path: route.query.redirect ? (route.query.redirect as string) : '/',
                })
                .then(() => {
                  loading.value = false
                })
            })
          })
          .catch((error) => {
            loading.value = false
            message.error(error.message)
          })
      }
      return {
        isMobileScreen,
        username,
        password,
        autoLogin,
        loading,
        onLogin,
        ImageBg1,
        ImageBg2,
        version,
      }
    },
  })
</script>

<style lang="scss" scoped>
  @keyframes left-to-right {
    from {
      transform: translateX(-100%);
    }
    to {
      transform: translateX(0);
    }
  }

  .login-container {
    position: relative;
    overflow: hidden;
    height: 100vh;
    width: 100%;
    @media screen and (max-width: 960px) {
      .left {
        display: none !important;
      }
    }

    .left {
      display: block;
      position: relative;
      min-width: 450px;
      /*width: 450px;*/

      & > img {
        width: 100%;
        height: 100%;
      }

      &::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.6);
        z-index: 2;
      }

      .content-wrapper {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9;
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        align-items: center;

        .logo-wrapper {
          width: 80px;
          margin-top: 30%;
        }

        .title {
          margin-top: 10px;
          color: #ffffff;
          font-weight: bold;
          font-size: 24px;
        }

        .sub-title {
          margin-top: 10px;
          color: #f5f5f5;
          font-size: 16px;
        }

        .ttppii {
          color: #ffffff;
          font-weight: 500;
          font-size: 30px;
          // text-shadow: 1px 1px 2px #f5f5f5;
          /*animation: left-to-right 1s cubic-bezier(0.175, 0.885, 0.32, 1.275);*/
          /*text-shadow: 0 0 5px var(--primary-color), 0 0 15px var(--primary-color),*/
          /*  0 0 50px var(--primary-color), 0 0 150px var(--primary-color);*/
        }

        .version {
          margin-bottom: 5%;
          color: #c0c0c0;
          font-size: 16px;
        }
      }
    }

    .right {
      flex: 1;
      display: flex;
      justify-content: center;
      flex-direction: column;
      align-items: center;
      width: 45%;
      /*background: linear-gradient(to bottom, var(--primary-color));*/

      .form-wrapper {
        width: 35%;
        border-radius: 5px;
        border: 1px solid #f0f0f0;
        padding: 20px;
        /*box-shadow: 0px 0px 7px #dddddd;*/

        .form-title {
          font-size: 26px;
          margin-bottom: 20px;
          font-weight: bold;
        }

        .item-wrapper {
          width: 100%;
        }

        .login {
          width: 100%;
        }
      }

      .third-login {
        width: 50%;
      }
    }
  }
</style>
