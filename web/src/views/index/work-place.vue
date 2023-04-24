<template>
  <div class="main-container">
    <n-card title="工作台" :content-style="{ padding: '10px' }" :header-style="{ padding: '10px' }">
      <n-grid :cols="4" :y-gap="15" item-responsive responsive="screen">
        <n-grid-item class="flex" span="4 s:2 m:2 l:2 xl:2 2xl:2">
          <div class="avatar-wrapper">
            <img :src="avatar" />
          </div>
          <div class="flex flex-col justify-around ml-3.5 flex-1">
            <div class="text-lg">CMDB工作台</div>
            <div class="text-sm text-gray-500">今日有小雨，出门别忘记带伞哦~ </div>
          </div>
        </n-grid-item>
        <n-grid-item class="flex justify-end" span="4 s:2 m:2 l:2 xl:2 2xl:2">
          <div class="flex flex-col justify-around align-end item-action">
            <div class="text-gray">应用资源</div>
            <div class="text-xl">12</div>
          </div>
          <div class="flex flex-col justify-around align-end item-action">
            <div class="text-gray">基础设施</div>
            <div class="text-xl">2250</div>
          </div>
          <div class="flex flex-col justify-around align-end item-action">
            <div class="text-gray">当前日期</div>
            <div class="text-xl">{{ currentDate }}</div>
          </div>
        </n-grid-item>
      </n-grid>
    </n-card>
    <n-grid class="mt-4 mb-4" :y-gap="15" :x-gap="15" cols="2 s:2 m:3 l:6 xl:6 2xl:6" responsive="screen">
      <n-grid-item v-for="(item, index) of fastActions" :key="index">
        <n-card @click="fastActionClick(item)">
          <div class="flex flex-col items-center justify-center">
            <span :class="[item.icon, 'iconfont']" :style="{ color: item.color, fontSize: '30px' }"></span>
            <span class="mt-1">{{ item.title }}</span>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>


  </div>
</template>

<script lang="ts">
import ProjectItem from './components/ProjectItem.vue'
import TodoItem from './components/TodoItem.vue'
import { computed, defineComponent } from 'vue'
import { useRouter } from 'vue-router'
import { random } from 'lodash'
import { useLayoutStore } from '@/components'
import useUserStore from '@/store/modules/user'
const COLORS = ['#67C23A', '#E6A23C', '#F56C6C', '#409EFF']
const date = new Date()
export default defineComponent({
  name: 'WorkPlace',
  components: {
    ProjectItem,
    TodoItem,
  },
  setup() {
   
    const layoutStore = useLayoutStore()
    const isMobileScreen = computed(() => {
      return layoutStore.state.device === 'mobile'
    })
    const userStore = useUserStore()
    const avatar = computed(() => userStore.image)
    const router = useRouter()
    const fastActionClick = ({ path = '/' }) => {
      router.push(path)
    }
    return {
      isMobileScreen,
      avatar,
      currentDate: date.getFullYear() + '/' + (date.getMonth() + 1) + '/' + date.getDate(),
      fastActions: [
        {
          title: '首页',
          icon: 'icon-dashboard-fill',
          path: '/',
          color: COLORS[random(0, COLORS.length)],
        },
        {
          title: '网络设备',
          path: '/cmdb/network_device',
          icon: 'icon-windows-fill',
          color: COLORS[random(0, COLORS.length)],
        },
        {
          title: '接口清单',
          path: '/cmdb/interfaceused',
          icon: 'icon-detail-fill',
          color: COLORS[random(0, COLORS.length)],
        },
        // {
        //   title: '采集方案',
        //   path: '/automated/collect',
        //   icon: 'icon-file-text-fill',
        //   color: COLORS[random(0, COLORS.length)],
        // },
        // {
        //   title: '任务列表',
        //   path: '/task_center/task_list',
        //   icon: 'icon-golden-fill',
        //   color: COLORS[random(0, COLORS.length)],
        // },
        {
          title: '更多功能',
          path: '/other/qrcode',
          icon: 'icon-appstore-fill',
          color: COLORS[random(0, COLORS.length)],
        },
      ],
      fastActionClick,
    }
  },
})
</script>

<style lang="scss" scoped>
.avatar-wrapper {
  width: 3rem;
  height: 3rem;
  max-width: 3rem;
  max-height: 3rem;
  min-width: 3rem;
  min-height: 3rem;

  &>img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid var(--primary-color);
  }
}

.item-action {
  position: relative;
  padding: 0 30px;
}

.item-action::after {
  position: absolute;
  top: 20%;
  right: 0;
  height: 60%;
  content: '';
  display: block;
  width: 1px;
  background-color: #e0e0e0;
}

div.item-action:last-child::after {
  width: 0;
}

.fast-item-wrapper {
  border-right: 1px solid #f7f7f7;
  border-bottom: 1px solid #f7f7f7;
  height: 80px;
}

.fast-item-wrapper:hover {
  cursor: pointer;
  box-shadow: 0px 0px 10px #ddd;
}

.el-link+.el-link {
  margin-bottom: 10px;
}
</style>
