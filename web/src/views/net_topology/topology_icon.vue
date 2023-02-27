<template>
  <div class="main-container">
    <n-modal v-model:show="add_dir_modal_show" preset="dialog" title="新建目录">
      <n-form
        ref="formRef"
        :model="add_dir_model"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
        size="small"
        :style="{
          maxWidth: '640px',
        }"
        ><n-form-item label="路径" path="inputPathName">
          <n-input v-model:value="add_dir_model.path" placeholder="Input" :disabled="true" />
        </n-form-item>
        <n-form-item label="目录" path="inputDirName">
          <n-input v-model:value="add_dir_model.name" placeholder="Input" />
        </n-form-item>
      </n-form>

      <template #action>
        <div style="display: flex; justify-content: flex-end">
          <n-button round type="primary" @click="add_dir_modal_btn"> 确认 </n-button>
        </div>
      </template>
    </n-modal>
    <n-card>
      <div
        style="
          width: 20%;
          padding: 10px;
          border-top: 1px solid #000;
          background-color: white;
          float: left;
        "
      >
        <n-space vertical :size="12">
          <n-input v-model:value="pattern" placeholder="搜索" />
          <n-space :size="12">
            <n-switch v-model:value="showIrrelevantNodes">
              <template #checked> 展示搜索无关的节点 </template>
              <template #unchecked> 隐藏搜索无关的节点 </template>
            </n-switch>
            <n-button round type="primary" size="tiny" @click="add_dir"> 新建目录 </n-button>
          </n-space>
          <n-tree
            :show-irrelevant-nodes="showIrrelevantNodes"
            :pattern="pattern"
            :data="tree_data"
            :default-expand-all="false"
            :readonly="true"
            virtual-scroll
            :node-props="nodeProps"
            style="height: 600px"
            block-line
          />
        </n-space>
      </div>
      <div
        style="
          width: 80%;
          height: 100%;
          padding: 0px;
          float: right;
          border-top: 1px solid #000;
          background-color: white;
        "
      >
        <n-grid cols="xs:2 s:3 m:4 l:6 xl:8" class="icon-parent" responsive="screen">
          <n-grid-item v-for="item of image_list" :key="item.id">
            <div class="flex flex-col items-center justify-center icon-wrapper">
              <n-image :src="topology_media_img + item.key" />
              <div class="text-xs">{{ item.label }}</div>
            </div>
          </n-grid-item>
        </n-grid>

        <n-upload
          multiple
          ref="uploadRef"
          list-type="image"
          @before-upload="beforeUpload"
          class="idcard-upload"
          :custom-request="customRequest"
          :max="5"
        >
          <n-upload-dragger>
            <div style="margin-bottom: 12px">
              <n-icon size="48" :depth="3">
                <archive-icon />
              </n-icon>
            </div>
            <n-text style="font-size: 16px"> 点击或者拖动文件到该区域来上传 </n-text>
            <n-p depth="3" style="margin: 8px 0 0 0"> 请不要上传敏感数据 </n-p>
          </n-upload-dragger>
        </n-upload>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
  // import { onBeforeMount } from 'vue'
  // import { useStore } from 'vuex'
  import { ArchiveOutline as ArchiveIcon } from '@vicons/ionicons5'
  import { h, nextTick, onMounted, ref } from 'vue'
  import _ from 'lodash'
  import { topology_icon, topology_media_img } from '@/api/url'
  import { TreeOption } from 'naive-ui'
  import { FormInst, useMessage, UploadCustomRequestOptions } from 'naive-ui'
  import useGet from '@/hooks/useGet'
  import usePost from '@/hooks/usePost'
  import type { UploadFileInfo } from 'naive-ui'
  const get = useGet()
  const post = usePost()
  const switch_source_code = ref(true)
  const tree_data = ref([])
  const content = ref('')
  // 默认搜索内容
  const pattern = ref('')
  const message = useMessage()
  const image_list = ref([])
  const add_dir_model = ref({
    name: '',
    path: '/',
  })
  const add_dir_modal_show = ref(false)
  const image_src = ref('/netops_static/topology/img/load_balancer/load_balancer_mango_medium.png')
  function add_dir() {
    add_dir_modal_show.value = true
  }
  function beforeUpload(data: { file: UploadFileInfo; fileList: UploadFileInfo[] }) {
    if (data.file.file?.type !== 'image/png') {
      message.error('只能上传png格式的图片文件，请重新上传')
      return false
    }
    return true
  }
  function add_dir_modal_btn() {
    console.log(add_dir_model.value)
    post({
      url: topology_icon,
      data: {
        dir_name: add_dir_model.value.name,
        current_path: add_dir_model.value.path,
      },
    }).then((res) => {
      console.log(res)
      if (res.code == 200) {
        message.success(res.msg)
        add_dir_modal_show.value = false
        nextTick(() => {
          get_icon_tree()
        })
      } else {
        message.error(res.msg)
      }
    })
  }
  // tree_data.value.push()
  // 获取配置文件树
  function get_icon_tree() {
    tree_data.value = []
    get({
      url: topology_icon,
      data: () => {
        return {
          get_tree: 1,
        }
      },
    }).then((res) => {
      console.log(res)
      res.data.forEach((item) => {
        //console.log(item)
        nextTick(() => {
          tree_data.value.push(item)
        })
      })
    })
  }
  // 配置文件树 节点点击事件
  function nodeProps({ option }: { option: TreeOption }) {
    return {
      onClick() {
        if (option.children?.length > 0) {
          add_dir_model.value.path = option.key
          image_list.value = []
          option.children.forEach((element) => {
            image_list.value.push(element)
          })
          // message.info('还有子元素不做查询')
          return
        } else {
          add_dir_model.value.path = option.key
          image_list.value = []
          image_list.value.push(option)
          // image_list.value.push({
          //   id: option.id,
          //   key: option.label,
          // })
          // message.info('当前选中最后一层元素做查询' + option.label
          // get({
          //   url: topology_img + option.key,
          //   data: () => {},
          // }).then((res) => {
          //   if (res) {
          //     content.value = res.data
          //     // console.log('详细数据', res)
          //     // nextTick(()=>{
          //     //
          //     // })
          //   }
          // })
        }
      },
    }
  }
  const customRequest = ({
    file,
    data,
    headers,
    withCredentials,
    action,
    onFinish,
    onError,
    onProgress,
  }: UploadCustomRequestOptions) => {
    const formData = new FormData()
    if (data) {
      Object.keys(data).forEach((key) => {
        formData.append(key, data[key as keyof UploadCustomRequestOptions['data']])
      })
    }
    // formData.append(file.name, file.file as File)
    formData.append('icons', file.file as File)
    formData.append('filename', file.name)
    formData.append('upload_path', add_dir_model.value.path)
    post({
      url: topology_icon,
      data: formData,
      // data: {
      //   method: 'upload',
      //   file: file.file,
      // },
    }).then((res) => {
      console.log(res)
      if (res.code == 200) {
        nextTick(() => {
          get_icon_tree()
        })
      }
    })
  }
  onMounted(get_icon_tree)
  // onBeforeMount(() => {
  //   //console.log('2.组件挂载页面之前执行----onBeforeMount')
  //   initSocket()
  // })
  // console.log(createData())
  const size = ref<'small' | 'medium' | 'large'>('medium')
  const showIrrelevantNodes = ref(false)
  const range = ref([118313526e4, Date.now()])
</script>
<style lang="scss" scoped>
  .n-form.n-form--inline {
    width: 100%;
    display: inline-flex;
    align-items: flex-start;
    align-content: space-around;
    height: 5px;
  }
</style>
