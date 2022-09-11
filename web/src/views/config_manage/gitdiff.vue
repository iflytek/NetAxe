<template>
  <div class="main-container">
    <n-card>
      <n-tabs
        class="card-tabs"
        default-value="config_file_tab"
        @update:value="tab_change"
        size="large"
        animated
        style="margin: 0 -4px"
        pane-style="padding-left: 4px; padding-right: 4px; box-sizing: border-box;"
      >
        <n-tab-pane name="config_file_tab" tab="配置查看">
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
              <n-switch v-model:value="showIrrelevantNodes">
                <template #checked> 展示搜索无关的节点 </template>
                <template #unchecked> 隐藏搜索无关的节点 </template>
              </n-switch>
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
            v-show="detail_show"
            style="
              width: 80%;
              height: 100%;
              padding: 0px;
              float: right;
              border-top: 1px solid #000;
              background-color: white;
            "
          >
            <n-space vertical :size="12">
              <n-form ref="formRef" :label-width="80" :size="size">
                <n-grid :cols="24" :x-gap="24">
                  <n-form-item-gi :span="8" label="开始commit">
                    <n-select v-model:value="from_commit" filterable :options="commit_option" />
                  </n-form-item-gi>
                  <n-form-item-gi :span="8" label="结束commit">
                    <n-select v-model:value="to_commit" filterable :options="commit_option" />
                  </n-form-item-gi>
                  <n-form-item-gi :span="4">
                    <n-button type="primary" @click="getCommitData"> 查询 </n-button>
                  </n-form-item-gi>
                  <n-form-item-gi :span="4" label="显示当前内容">
                    <n-switch @update:value="switch_ace_show" v-model:value="switch_source_code" />
                  </n-form-item-gi>
                </n-grid>
              </n-form>
              <div class="green" v-show="ace_editor_show">
                <v-ace-editor
                  v-model:value="content"
                  lang="yaml"
                  theme="chrome"
                  style="height: 620px"
                />
              </div>
              <code-diff
                :old-string="diff_old_string"
                :new-string="diff_new_string"
                :file-name="diff_file_name"
                :trim="true"
                :noDiffLineFeed="true"
                :isShowNoChange="false"
                :syncScroll="true"
                output-format="side-by-side"
              />
            </n-space>
          </div>
        </n-tab-pane>

        <n-tab-pane name="commit_trace" tab="commit轨迹">
          <n-space vertical :size="12">
            <n-form ref="form_commit_trace" :label-width="80" :size="size">
              <n-grid :cols="24" :x-gap="24">
                <n-form-item-gi :span="12" label="指定commit">
                  <n-select v-model:value="commit_value" :options="commit_option" />
                </n-form-item-gi>
                <n-form-item-gi :span="4">
                  <n-button type="primary" @click="getCommitHistory"> 查询 </n-button>
                </n-form-item-gi>
              </n-grid>
              <n-grid :cols="24" :x-gap="24">
                <n-form-item-gi :span="12" label="变更文件">
                  <n-select
                    v-model:value="change_file"
                    filterable
                    :options="change_file_option"
                    @update:value="show_code_diff(change_file)"
                  />
                </n-form-item-gi>
              </n-grid>
            </n-form>
            <code-diff
              :old-string="diff_old_string"
              :new-string="diff_new_string"
              :file-name="diff_file_name"
              :trim="true"
              :noDiffLineFeed="true"
              :isShowNoChange="false"
              :renderNothingWhenEmpty="true"
              :syncScroll="true"
              output-format="side-by-side"
            />
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script lang="ts">
  // import { onBeforeMount } from 'vue'
  // import { useStore } from 'vuex'
  import { defineComponent, h, nextTick, onMounted, ref } from 'vue'
  import _ from 'lodash'
  import { get_git_config_tree } from '@/api/url'
  import { TreeOption } from 'naive-ui'
  import { CodeDiff } from 'v-code-diff'
  import { FormInst, useMessage } from 'naive-ui'
  import useGet from '@/hooks/useGet'
  // import usePut from '@/hooks/usePut'
  import { VAceEditor } from 'vue3-ace-editor'
  import 'ace-builds/src-noconflict/mode-yaml'
  import 'ace-builds/src-noconflict/mode-html'
  import 'ace-builds/src-noconflict/theme-chrome'
  // 语法检查 暂时用不上
  // import ace from 'ace-builds'
  // import workerJsonUrl from 'ace-builds/src-noconflict/worker-json?url'
  // ace.config.setModuleUrl('ace/mode/json_worker', workerJsonUrl)
  export default defineComponent({
    name: 'Diff',
    components: {
      CodeDiff,
      VAceEditor,
    },
    setup() {
      // const store = useStore()
      // //websocket初始化
      // const initSocket = () => {
      //   store.commit('initWebsocket')
      // }
      const formRef = ref<FormInst | null>(null)
      const form_commit_trace = ref<FormInst | null>(null)
      const get = useGet()
      const diff_old_string = ref('')
      const ace_editor_show = ref(true)
      const diff_new_string = ref('')
      const diff_file_name = ref('')
      const switch_source_code = ref(true)
      const diff_type_select = ref('by_range')
      const from_commit = ref(null)
      const to_commit = ref(null)
      const commit_value = ref(null)
      const change_file = ref(null)
      const change_file_option = ref([])
      const commit_option = ref([])
      const select_config_file = ref(null)
      const tree_data = ref([])
      const detail_show = ref(false)
      const content = ref('')
      // 默认搜索内容
      const pattern = ref('')
      const showRangeRadio = ref(false)
      const showCommitRadio = ref(false)
      const message = useMessage()
      // tree_data.value.push()
      // 获取配置文件树
      function get_config_tree() {
        get({
          url: get_git_config_tree,
          data: () => {
            return {
              get_tree: 1,
            }
          },
        }).then((res) => {
          res.data.forEach((item) => {
            //console.log(item)
            nextTick(() => {
              tree_data.value.push(item)
            })
            // tree_data.value.push(item)
            // console.log(item)
          })
          // console.log(tree_data)
        })
      }
      // 配置文件树 节点点击事件
      function nodeProps({ option }: { option: TreeOption }) {
        return {
          onClick() {
            if (option.children) {
              message.info('还有子元素不做查询')
              detail_show.value = false
              return
            } else {
              select_config_file.value = option.key
              // message.info('当前选中最后一层元素做查询' + option.label)
              get({
                url: get_git_config_tree,
                data: () => {
                  return {
                    filename: option.key,
                  }
                },
              }).then((res) => {
                if (res) {
                  detail_show.value = true
                  content.value = res.data
                  // console.log('详细数据', res)
                  // nextTick(()=>{
                  //
                  // })
                }
              })
            }
          },
          // onContextmenu (e: MouseEvent): void {
          //   optionsRef.value = [option]
          //   showDropdownRef.value = true
          //   xRef.value = e.clientX
          //   yRef.value = e.clientY
          //   console.log(e.clientX, e.clientY)
          //   e.preventDefault()
          // }
        }
      }
      // 获取所有的提交
      function allCommits() {
        get({
          url: get_git_config_tree,
          data: () => {
            return {
              get_commit: '1',
            }
          },
        }).then((res) => {
          if (res) {
            res.data.forEach((item) => {
              nextTick(() => {
                commit_option.value.push(item)
                // commit_value.value = item.value
              })
            })
            from_commit.value = res.data.slice(-1).value
            to_commit.value = res.data.slice(-1).value
            commit_value.value = res.data.slice(0).value
            // console.log('详细数据', res)
            // nextTick(()=>{
            //
            // })
          }
        })
      }
      // 获取指定的文件两个commit之间的差异
      function getCommitData() {
        message.info('正在查询')
        get({
          url: get_git_config_tree,
          data: () => {
            return {
              file: select_config_file.value,
              from_commit: from_commit.value,
              to_commit: to_commit.value,
            }
          },
        }).then((res) => {
          message.success('查询成功')
          if (res) {
            console.log('差异详情1', res)
            nextTick(() => {
              diff_new_string.value = res.data[0].new_str
              diff_old_string.value = res.data[0].old_str
              diff_file_name.value = select_config_file.value
            })
          }
        })
      }
      // 获取单个commit的变更轨迹
      function getCommitHistory() {
        change_file_option.value.length = 0
        change_file.value = ''
        console.log(commit_value.value)
        if (commit_value.value !== undefined) {
          message.info('正在查询')
          get({
            url: get_git_config_tree,
            data: () => {
              return {
                commit_detail: commit_value.value,
              }
            },
          }).then((res) => {
            message.success('查询成功')
            if (res) {
              //console.log('单个commit的变更轨迹', res)
              if (res.data.length == 0) {
                message.warning('无变更')
                change_file_option.value.length = 0
                change_file.value = ''
              } else {
                change_file_option.value.length = 0
                change_file.value = ''
                res.data.forEach((item) => {
                  nextTick(() => {
                    change_file_option.value.push(item)
                    // commit_value.value = item.value
                  })
                })
                change_file.value = res.data.slice(0).value
              }
            }
          })
        }
      }
      // 获取指定文件变化
      function show_code_diff(change_file) {
        console.log(change_file)
        get({
          url: get_git_config_tree,
          data: () => {
            return {
              file: change_file,
              single_commit: commit_value.value,
            }
          },
        }).then((res) => {
          if (res) {
            nextTick(() => {
              diff_new_string.value = res.data[0].new_str
              diff_old_string.value = res.data[0].old_str
              diff_file_name.value = select_config_file.value
            })
          }
        })
      }
      // 控制ace代码块的显示
      function switch_ace_show(switch_source_code) {
        ace_editor_show.value = switch_source_code
      }
      // 标签页切换清空diff内容
      function tab_change(value) {
        //console.log(value)
        diff_new_string.value = ''
        diff_old_string.value = ''
        diff_file_name.value = ''
      }
      onMounted(get_config_tree)
      onMounted(allCommits)
      // onBeforeMount(() => {
      //   //console.log('2.组件挂载页面之前执行----onBeforeMount')
      //   initSocket()
      // })
      // console.log(createData())
      return {
        // tree_data,
        diff_new_string,
        diff_old_string,
        diff_file_name,
        formRef,
        form_commit_trace,
        size: ref<'small' | 'medium' | 'large'>('medium'),
        get_config_tree,
        tree_data,
        showIrrelevantNodes: ref(false),
        nodeProps,
        content,
        detail_show,
        pattern,
        range: ref([118313526e4, Date.now()]),
        from_commit,
        to_commit,
        commit_value,
        commit_option,
        diff_type_select,
        showRangeRadio,
        showCommitRadio,
        allCommits,
        getCommitData,
        getCommitHistory,
        ace_editor_show,
        switch_source_code,
        switch_ace_show,
        change_file,
        change_file_option,
        show_code_diff,
        tab_change,
      }
    },
  })
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
