<template>
  <div class="main-container">
    <n-space>
      <n-select
        v-model:value="topology_value"
        :options="topology_options"
        style="width: 200px"
        filterable
        placeholder="请选择拓扑"
        @update:value="select_topology"
      />
      <n-button type="info" size="small" @click="addGraph">新建</n-button>
      <n-button type="info" size="small" @click="save_graph">保存</n-button>
      <n-button type="error" size="small" @click="del_graph">删除</n-button>
      <n-button type="info" size="small" @click="Brush">框选</n-button>
      <n-button type="info" size="small" @click="addDevice" v-show="showAddNodeButton"
        >添加设备</n-button
      >
      <n-button type="info" size="small" @click="manageNodes" v-show="showAddNodeButton"
        >节点管理</n-button
      >
      <n-button type="info" size="small" @click="unBrush" v-show="showCancelBrushBtn"
        >取消框选</n-button
      >
      <n-button type="info" size="small" @click="nodeAlignmentbyY" v-show="showNodeAlignmentBtn"
        >横向对齐</n-button
      >
      <n-button type="info" size="small" @click="nodeAlignmentbyX" v-show="showNodeAlignmentBtn"
        >竖向对齐</n-button
      >
    </n-space>
    <n-card size="small" :bordered="false" content-style="padding: 5px;">
      <div id="container">
        <!-- CONTENT HERE -->
        <svg id="primary-svg" :height="height" width="100%" ref="toppolgoy_svg" />
      </div>
      <n-popover
        :show="showNodePopoverRef"
        :x="NodePopoveXRef"
        :y="NodePopoveyRef"
        trigger="manual"
      >
        <div style="width: 300px; height: auto; background-color: white; transform-origin: inherit">
          <n-table
            :bordered="false"
            :single-line="false"
            :bottom-bordered="false"
            :single-column="false"
            size="small"
          >
            <tr>
              <td>设备名</td>
              <td>
                <p>{{ popover_node.name }}</p></td
              >
            </tr>
            <tr>
              <td>设备IP</td>
              <td>
                <p>{{ popover_node.manage_ip }}</p></td
              >
            </tr>
            <tr>
              <td>位置</td
              ><td
                ><p>{{ popover_node.location }}</p></td
              ></tr
            >
            <tr
              ><td>序列号</td
              ><td
                ><p>{{ popover_node.serial_num }}</p></td
              ></tr
            >
            <tr
              ><td>厂商型号</td
              ><td
                ><p>{{ popover_node.vendor_model }}</p></td
              > </tr
            ><tr
              ><td>维保到期</td
              ><td
                ><p>{{ popover_node.expire }}</p></td
              ></tr
            ></n-table
          >
        </div>
      </n-popover>
      <n-popover
        :show="showLinkPopoverRef"
        :x="LinkPopoveXRef"
        :y="LinkPopoveyRef"
        trigger="manual"
      >
        <div style="width: 400px; height: auto; background-color: white; transform-origin: inherit">
          <n-table
            :bordered="false"
            :single-line="false"
            :bottom-bordered="false"
            :single-column="false"
            size="small"
          >
            <tr>
              <td>左设备</td>
              <td>
                <p>{{ popover_link.left_device }}</p></td
              >
            </tr>
            <tr>
              <td>左接口</td>
              <td>
                <p>{{ popover_link.left_int }}</p></td
              >
            </tr>
            <tr>
              <td>左接口IP</td
              ><td
                ><p>{{ popover_link.left_int_ip }}</p></td
              ></tr
            >
            <tr
              ><td>右设备</td
              ><td
                ><p>{{ popover_link.right_device }}</p></td
              ></tr
            >
            <tr
              ><td>右接口</td
              ><td
                ><p>{{ popover_link.right_int }}</p></td
              > </tr
            ><tr
              ><td>右接口IP</td
              ><td
                ><p>{{ popover_link.right_int_ip }}</p></td
              ></tr
            >
            <tr
              ><td>速率</td
              ><td
                ><p>{{ popover_link.speed }}</p></td
              ></tr
            >
          </n-table>
        </div>
      </n-popover>
    </n-card>
    <!--节点抽屉-->
    <n-drawer v-model:show="show_drawer" :width="502" :placement="placement">
      <n-drawer-content :title="dblclick_node_model.name" closable>
        <n-form ref="drawerFormRef" :model="dblclick_node_model">
          <n-form-item path="name" label="节点名">
            <n-input v-model:value="dblclick_node_model.name" :disabled="true" />
          </n-form-item>
          <n-form-item path="image" label="图标">
            <n-select
              :options="drawerImgOptions"
              filterable
              :render-label="renderLabel"
              :render-tag="renderSingleSelectTag"
              v-model:value="dblclick_node_model.image"
            />
          </n-form-item>
          <n-row :gutter="[0, 24]">
            <n-col :span="24">
              <div style="display: flex; justify-content: flex-end">
                <n-button round type="primary" @click="drawerChangeNode"> 保存 </n-button>
              </div>
            </n-col>
          </n-row>
        </n-form>
      </n-drawer-content>
    </n-drawer>
    <!--线路抽屉-->
    <n-drawer v-model:show="show_link_drawer" :width="502" :placement="link_placement">
      <n-drawer-content title="编辑链路" closable>
        <n-form ref="drawerLinkFormRef" :model="dblclick_link_model">
          <n-form-item path="source" label="源节点">
            <n-input v-model:value="dblclick_link_model.source.name" :disabled="true" />
          </n-form-item>
          <n-form-item path="source_manage_ip" label="源节点管理IP">
            <n-input v-model:value="dblclick_link_model.source_manage_ip" :disabled="true" />
          </n-form-item>
          <n-form-item path="source_interfaces" label="源节点接口">
            <n-input v-model:value="dblclick_link_model.source_interfaces" :disabled="true" />
          </n-form-item>
          <n-form-item path="source_interface_ip" label="源节点接口IP">
            <n-input v-model:value="dblclick_link_model.source_interface_ip" :disabled="true" />
          </n-form-item>
          <n-form-item path="target" label="目标节点">
            <n-input v-model:value="dblclick_link_model.target.name" :disabled="true" />
          </n-form-item>
          <n-form-item path="target_manage_ip" label="目标节点管理IP">
            <n-input v-model:value="dblclick_link_model.target_manage_ip" :disabled="true" />
          </n-form-item>
          <n-form-item path="target_interfaces" label="目标节点接口">
            <n-input v-model:value="dblclick_link_model.target_interfaces" :disabled="true" />
          </n-form-item>
          <n-form-item path="target_interface_ip" label="目标节点接口IP">
            <n-input v-model:value="dblclick_link_model.target_interface_ip" :disabled="true" />
          </n-form-item>
          <n-form-item path="speed" label="速率">
            <n-input-number v-model:value="dblclick_link_model.speed" :disabled="true" />
          </n-form-item>
          <n-form-item path="color" label="线路颜色">
            <n-color-picker v-model:value="dblclick_link_model.color" :show-alpha="false" />
          </n-form-item>
          <n-row :gutter="[0, 24]">
            <n-col :span="24">
              <div style="display: flex; justify-content: flex-end">
                <n-button round type="primary" @click="drawerChangeLink"> 保存 </n-button>
              </div>
            </n-col>
          </n-row>
        </n-form>
      </n-drawer-content>
    </n-drawer>
    <!--新建拓扑-->
    <n-modal v-model:show="showAddGraphModal">
      <n-card
        style="width: 600px"
        title="新建拓扑"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <template #header-extra> </template>
        <DataForm
          ref="addGraphDataFormRef"
          :form-config="{ labelWidth: 80 }"
          preset="form-item"
          :options="addGraphFormOptions"
        />
        <template #footer>
          <div style="display: flex; justify-content: flex-end">
            <n-button round type="primary" @click="onAddGraphConfirm"> 新建 </n-button>
          </div>
        </template>
      </n-card>
    </n-modal>
    <!--添加节点-->
    <n-modal v-model:show="showAddNodeModal">
      <n-card
        style="width: 800px"
        title="添加节点"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <template #header-extra> </template>
        <n-form ref="addNodeFormRef1" :model="add_node_query_model" inline>
          <n-form-item path="name" label="节点名">
            <n-input v-model:value="add_node_query_model.name" />
          </n-form-item>
          <n-form-item path="manage_ip" label="管理IP">
            <n-input v-model:value="add_node_query_model.manage_ip" />
          </n-form-item>
          <n-form-item path="idc" label="idc">
            <n-select :options="idcOptions" filterable v-model:value="add_node_query_model.idc" />
          </n-form-item>
        </n-form>
        <n-form ref="addNodeFormRef2" :model="add_node_query_model">
          <n-form-item path="image" label="图标">
            <n-select
              :options="drawerImgOptions"
              filterable
              :render-label="renderLabel"
              :render-tag="renderSingleSelectTag"
              v-model:value="add_node_query_model.image"
            />
          </n-form-item>
        </n-form>

        <div style="display: flex; justify-content: flex-end">
          <n-button round type="primary" @click="doRefresh"> 查询 </n-button>
        </div>
        <TableBody>
          <template #default>
            <n-data-table
              :loading="tableLoading"
              :data="dataList"
              :columns="tableColumns"
              :single-line="bordered"
              :row-key="rowKey"
              @update:checked-row-keys="handleSelectionChange"
            />
          </template>
          <template #footer>
            <TableFooter :pagination="pagination" />
          </template>
        </TableBody>
        <template #footer>
          <div style="display: flex; justify-content: flex-end">
            <n-button round type="primary" @click="onAddNodeConfirm"> 添加 </n-button>
          </div>
        </template>
      </n-card>
    </n-modal>
    <!--节点管理-->
    <n-modal v-model:show="showManageNodeModal">
      <n-card
        style="width: 800px"
        title="节点管理"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <template #header-extra> </template>
        <TableBody>
          <template #default>
            <n-data-table
              :data="graph.nodes"
              :columns="manageNodesTableColumns"
              :row-key="rowKey"
              @update:checked-row-keys="handleSelectionChange"
            />
          </template>
          <template #footer>
            <TableFooter :pagination="manageNodesPagination" />
          </template>
        </TableBody>
        <template #footer> </template>
      </n-card>
    </n-modal>
  </div>
</template>
<script setup lang="ts">
  import { h, nextTick, onMounted, ref, reactive, shallowReactive } from 'vue'
  import {
    get_topology,
    topology_show,
    topology_media_img,
    topology_icon,
    getNetworkDeviceList,
    getCmdbIdcList,
  } from '@/api/url'
  import { useTable, useTableColumn, usePagination, useRowKey } from '@/hooks/table'
  import {
    useMessage,
    NInputGroup,
    DataTableColumn,
    NIcon,
    NButton,
    NPopover,
    NAvatar,
    NText,
    NInput,
    SelectOption,
    NSelect,
  } from 'naive-ui'
  import type { DrawerPlacement } from 'naive-ui'
  import { DataFormType, FormItem } from '@/types/components'
  import * as d3 from 'd3'
  import usePost from '@/hooks/usePost'
  import useGet from '@/hooks/useGet'
  import useDelete from '@/hooks/useDelete'
  const show_drawer = ref(false)
  const show_link_drawer = ref(false)
  const placement = ref<DrawerPlacement>('right')
  const link_placement = ref<DrawerPlacement>('right')
  const show_drawer_activate = (place: DrawerPlacement) => {
    show_drawer.value = true
    placement.value = place
  }
  const show_link_drawer_activate = (place: DrawerPlacement) => {
    show_link_drawer.value = true
    link_placement.value = place
  }
  const message = useMessage()
  const svg_edgepaths = ref(null)
  const svg_edgelabels = ref(null)
  const svg_edgelabeltext = ref(null)
  const NodePopoveXRef = ref(0)
  const LinkPopoveXRef = ref(0)
  const NodePopoveyRef = ref(0)
  const LinkPopoveyRef = ref(0)
  const showNodePopoverRef = ref(false)
  const showLinkPopoverRef = ref(false)
  // 添加设备模态框 选中设备
  const selectedRowKeys = ref([])
  // const handleClick = (e: MouseEvent) => {
  //   if (showNodePopoverRef.value) {
  //     showNodePopoverRef.value = false
  //   } else {
  //     showNodePopoverRef.value = true
  //     NodePopoveXRef.value = e.clientX
  //     NodePopoveyRef.value = e.clientY
  //   }
  // }
  const manageNodesPagination = {
    pageSize: 20,
  }
  const table = useTable()
  const tableColumns = reactive(
    useTableColumn(
      [
        table.selectionColumn,
        {
          title: '名称',
          key: 'name',
          width: 100,
        },
        {
          title: 'IDC',
          key: 'idc_name',
          width: 150,
        },

        {
          title: '管理IP',
          key: 'manage_ip',
          width: 100,
        },
      ],
      {
        align: 'center',
      } as DataTableColumn
    )
  )
  // 节点管理表行删除
  function del_row(row) {
    console.log(row)
    console.log('行删除')
  }
  // 节点管理表
  const manageNodesTableColumns = useTableColumn(
    [
      {
        title: '名字',
        key: 'name',
      },
      {
        title: '管理IP',
        key: 'manage_ip',
      },
      {
        title: '位置',
        key: 'location',
      },
      {
        title: '厂家型号',
        key: 'vendor_model',
      },
      {
        title: '删除',
        key: 'id',
        render: (rowData) => {
          const oper_id = [
            h(
              NButton,
              {
                type: 'error',
                size: 'tiny',
                onClick: del_row.bind(null, rowData),
              },
              () => h('span', {}, '删除')
            ),
          ]
          return oper_id
        },
      },
    ],
    {
      align: 'center',
    } as DataTableColumn
  )
  const { tableLoading, dataList, bordered, handleSelectionChange } = { ...table }
  const rowKey = useRowKey('id')
  function doRefresh() {
    get({
      url: getNetworkDeviceList,
      data: () => {
        return {
          start: (pagination.page - 1) * pagination.pageSize,
          // pageSize: pagination.pageSize,
          limit: pagination.pageSize,
          status: 0,
          name: add_node_query_model.value.name,
          manage_ip: add_node_query_model.value.manage_ip,
          idc: add_node_query_model.value.idc,
          _: Date.now(),
        }
      },
    }).then((res) => {
      if (res.code == 200) {
        table.handleSuccess(res)
        pagination.setTotalSize(res.count || 10)
      } else {
        message.error(res.msg)
      }
    })
  }
  const pagination = usePagination(doRefresh)
  pagination.pageSize = 10
  pagination.limit = 10
  pagination.start = 0
  const popover_node = ref({
    name: '',
    manage_ip: '',
    location: '',
    serial_num: '',
    vendor_model: '',
    expire: '',
  })
  const popover_link = ref({
    left_device: '',
    left_int: '',
    left_int_ip: '',
    right_device: '',
    right_int: '',
    right_int_ip: '',
    speed: '',
  })
  const dblclick_node_model = ref({
    id: '',
    name: '',
    manage_ip: '',
    image: '',
    serial_num: '',
    vendor_model: '',
    location: '',
    device_id: '',
  })
  const dblclick_link_model = ref({
    name: '',
    source: {
      id: '',
      name: '',
      manage_ip: '',
      image: '',
      serial_num: '',
      vendor_model: '',
      location: '',
      device_id: '',
    },
    source_manage_ip: '10.254.24.103',
    source_interface_ip: '100.70.15.122/255.255.255.252',
    source_interfaces: 'FortyGigE1/0/1',
    source_interfaces_indes: '',
    speed: 40,
    target: {
      id: '',
      name: '',
      manage_ip: '',
      image: '',
      serial_num: '',
      vendor_model: '',
      location: '',
      device_id: '',
    },
    target_manage_ip: '10.254.24.101',
    target_interfaces: 'FortyGigE1/0/49',
    target_interfaces_indes: '',
    target_interface_ip: '100.70.15.121/255.255.255.252',
    method: 'auto',
    name: '10.254.24.103FortyGigE1/0/1-10.254.24.101FortyGigE1/0/49',
    color: '',
  })
  const tooltip = ref(null)
  const toppolgoy_svg = ref<HTMLElement>()
  const width = Math.max(document.documentElement.clientWidth, window.innerWidth || 0)
  const height = Math.max(document.documentElement.clientHeight, window.innerHeight || 0) - 250
  const color = d3
    .scaleOrdinal()
    .range(['red', 'green', 'blue', '#6b486b', '#a05d56', '#d0743c', '#ff8c00'])
  const svg = ref<SVGGElement | null>(null)
  const zoom = ref(null)
  const group = ref<SVGGElement | null>(null)
  var svg_node = null
  var svg_link = null
  var svg_brush = null
  var simulation = null
  const viewBox = ref('200 300 800 800')
  const get = useGet()
  const post = usePost()
  const n_del = useDelete()
  const graph = ref({
    links: [],
    nodes: [],
    name: '',
    cmdb: '',
    interface: [],
  })
  const topology_value = ref(null)
  const topology_options = shallowReactive([]) as Array<any>
  const showAddNodeButton = ref(false)
  function node_click(node) {
    //console.log('节点点击', node)
  }

  function get_topology_list() {
    get({
      url: get_topology,
      data: () => {
        return {
          limit: 1000,
        }
      },
    }).then((res) => {
      //console.log(res)
      topology_options.length = 0
      res.results.forEach((item) => {
        var dict = {
          value: item['name'],
          label: item['name'],
        }
        topology_options.push(dict)
      })
      nextTick(() => {
        topology_options.splice(0, 0, { value: '', label: '' })
      })
    })
  }

  function select_topology() {
    // dispose(TopologyChart.value as HTMLDivElement)
    //console.log('选中', topology_value.value)
    // useEcharts(TopologyChart.value as HTMLDivElement).setOption(topology_chart_option)
    console.log('svg_brush', svg_brush)
    svg_brush.selectAll('*').remove()
    showCancelBrushBtn.value = false
    last_coordinate_x.value = 0
    last_coordinate_y.value = 0
    current_coordinate_x.value = 0
    current_coordinate_y.value = 0
    brushNode.value = []
    showNodeAlignmentBtn.value = false
    graph.value.name = topology_value.value
    get({
      url: topology_show,
      data: () => {
        return {
          graph: topology_value.value,
        }
      },
    }).then((res) => {
      console.log(res)
      if (res.code == 200) {
        graph.value = res.data
        if (group.value !== null) {
          group.value.selectAll('*').remove()
        }
        message.success(res.msg)
        nextTick(() => {
          init_svg()
          showAddNodeButton.value = true
        })
      } else {
        graph.value = {
          links: [],
          nodes: [],
          name: '',
          cmdb: '',
          interface: [],
        }
        message.error(res.msg)
        group.value.selectAll('*').remove()
        nextTick(() => {
          init_svg()
          showAddNodeButton.value = true
        })
      }
    })
  }

  function speed_color(speed: number) {
    if (speed === 1) {
      return '#ef9e9e'
    } else if (speed === 10) {
      return '#ffff50'
    } else if (speed === 25) {
      return '#e8b976'
    } else if (speed === 40) {
      return '#69bcdc'
    } else if (speed === 100) {
      return '#4aff9c'
    } else {
      return '#00ffff'
    }
  }

  function calcTranslationExact(targetDistance, point0, point1) {
    let x1_x0 = point1.x - point0.x,
      y1_y0 = point1.y - point0.y,
      x2_x0,
      y2_y0
    if (y1_y0 === 0) {
      x2_x0 = 0
      y2_y0 = targetDistance
    } else {
      let angle = Math.atan(x1_x0 / y1_y0)
      x2_x0 = -targetDistance * Math.cos(angle)
      y2_y0 = targetDistance * Math.sin(angle)
    }
    return {
      dx: x2_x0,
      dy: y2_y0,
    }
  }

  // 节点格式化HTML simple
  function node_formatbase(node) {
    //  //console.log('node', node)
    let content =
      '<div>' +
      `设备名<p>${node.name}</p>` +
      `设备IP<p>${node.manage_ip}</p>` +
      `位置<p>${node.location}</p></tr>` +
      `序列号<p>${node.serial_num}</p></tr>` +
      `厂商型号<p>${node.vendor_model}</p>` +
      `维保到期<p>${node.expire}</p></div>`

    //  //console.log('content', content)
    return content
  }

  function linkArc(d) {
    let arc = 0
    // 上下不一样的间隔
    let dis1 = calcTranslationExact(d.sameIndex * 4, d.source, d.target)
    let dis2 = calcTranslationExact(
      -(d.sameIndex - Math.ceil(d.sameTotalHalf)) * 4,
      d.source,
      d.target
    )
    //大于等于所给数字的最小整数
    let dx1 = dis1.dx
    let dy1 = dis1.dy
    let dx2 = dis2.dx
    let dy2 = dis2.dy
    // 表示奇数的时候，中间的那条
    if (Math.ceil(d.sameTotalHalf) === d.sameIndex && d.sameUneven === true) {
      dx1 = 0
      dx2 = 0
      dy1 = 0
      dy2 = 0
    }
    if (d.sameArcDirection === 0) {
      // 上线
      return (
        'M' +
        (d.source.x + dx1) +
        ',' +
        (d.source.y + dy1) +
        'A' +
        arc +
        ',' +
        arc +
        ' 0 0,' +
        0 +
        ' ' +
        (d.target.x + dx1) +
        ',' +
        (d.target.y + dy1)
      )
    } else {
      // 下线
      return (
        'M' +
        (d.source.x + dx2) +
        ',' +
        (d.source.y + dy2) +
        'A' +
        arc +
        ',' +
        arc +
        ' 0 0,' +
        0 +
        ' ' +
        (d.target.x + dx2) +
        ',' +
        (d.target.y + dy2)
      )
    }
  }

  function ticked() {
    svg_link.attr('d', linkArc)
    svg_edgepaths.value.attr('d', linkArc)
    svg_edgelabels.value
      .attr('d', linkArc)
      .attr('x', function (d) {
        //x指定文字最左侧坐标位置，根据连线两端节点的坐标，勾股出连线的长度l，让文字最左侧位于连线的中间，就是让x = l/2;
        let x = d.target.x - d.source.x,
          y = d.target.y - d.source.y
        let l = Math.sqrt(x * x + y * y)
        return l / 2
      })
      .attr('rotate', function (d) {
        return d.source.x < d.target.x ? 0 : 180
        //return 180
      })
    svg_edgelabeltext.value.text(function (d) {
      //为进行旋转的时候，文字方向是正常；当进行旋转之后，文字就反序显示了，需要将文字转换为顺序。
      let linkName = d.source_interfaces + '--' + d.target_interfaces
      if (d.source.x < d.target.x) {
        return linkName
      }
      return (
        d.source_interfaces.split('').reverse().join('') +
        '--' +
        d.target_interfaces.split('').reverse().join('')
      )
    })

    svg_node.attr('transform', function (d) {
      return 'translate(' + d.x + ',' + d.y + ')'
    })
  }

  // 初始化连线
  function init_links() {
    svg_link = group.value
      .append('g')
      .attr('class', 'links')
      .attr('id', 'links-g')
      .selectAll('line')
      .data(graph.value.links)
      .enter()
      .append('path')
      .attr('fill', 'transparent')
      .attr('id', (d) => 'line' + d.source + d.target)
      // 根据链路利用率来绘制链路颜色 COLOR
      .attr('stroke', function (d) {
        let keys = Object.keys(d)
        if (keys.includes('color')) {
          return d.color
        } else {
          return speed_color(d.speed)
        }
      }) // #  WIDTH 粗细
      .attr('stroke-width', function (d) {
        return 2
      })
      .attr('source', function (d) {
        d.source
      })
      .attr('target', function (d) {
        d.target
      })
      // 不透明度
      .style('opacity', 1)
    svg_link.on('mouseout', function (d, event) {
      showLinkPopoverRef.value = false
    })
    svg_link.on('dblclick', function (event, d) {
      console.log(d)
      show_link_drawer_activate('right')
      dblclick_link_model.value = d
    })
    svg_link.on('click', function (event, d) {
      if (d.source.x < d.target.x) {
        popover_link.value.left_device = d.source.id + '(' + d.source.manage_ip + ')'
        popover_link.value.right_device = d.target.id + '(' + d.target.manage_ip + ')'
        popover_link.value.left_int = d.source_interfaces
        popover_link.value.left_int_ip = d.source_interface_ip
        popover_link.value.right_int = d.target_interfaces
        popover_link.value.right_int_ip = d.target_interface_ip
        popover_link.value.speed = d.speed.toString() + 'G'
      } else {
        popover_link.value.left_device = d.target.id + '(' + d.target.manage_ip + ')'
        popover_link.value.right_device = d.source.id + '(' + d.source.manage_ip + ')'
        popover_link.value.left_int = d.target_interfaces
        popover_link.value.left_int_ip = d.target_interface_ip
        popover_link.value.right_int = d.source_interfaces
        popover_link.value.right_int_ip = d.source_interface_ip
        popover_link.value.speed = d.speed.toString() + 'G'
      }
      if (showLinkPopoverRef.value) {
        showLinkPopoverRef.value = false
        return
      } else {
        showLinkPopoverRef.value = true
        LinkPopoveXRef.value = event.clientX
        LinkPopoveyRef.value = event.clientY
      }
    })
  }

  // 初始化连线path
  function init_edgepaths() {
    svg_edgepaths.value = group.value
      .append('g')
      .selectAll('.edgepath')
      .data(graph.value.links)
      .enter()
      .append('path')
      .attr('fill', 'transparent')
      .attr('fill-opacity', 0)
      .attr('stroke-opacity', 0)
      .attr('id', function (d, i) {
        return 'edgepath' + d.name
      })
      .attr('marker-end', function (d) {
        return 'url(#' + 'edgepath' + d.source.id + d.target.id + ')'
      })
      .style('pointer-events', 'none')
    svg_edgelabels.value = group.value
      .append('g')
      .selectAll('.edgelabel')
      .data(graph.value.links)
      .enter()
      .append('text')
      .style('pointer-events', 'none')
      .attr('class', 'edgelabel')
      .attr('id', function (d, i) {
        return 'edgelabel' + i
      })
      .attr('font-size', 5)
      .attr('fill', '#060505')
    svg_edgelabeltext.value = svg_edgelabels.value
      .append('textPath')
      .attr('xlink:href', function (d, i) {
        return '#edgepath' + d.name
      })
      .style('text-anchor', 'middle')
      .style('pointer-events', 'none')
      //.attr("startOffset", "50%")
      .text((d) => d.source_interfaces + '--' + d.target_interfaces)
  }

  // 初始化节点
  function init_nodes() {
    svg_node = group.value
      .append('g')
      .attr('class', 'nodes')
      .attr('id', 'nodes-g')
      .selectAll('a')
      .data(graph.value.nodes)
      .enter()
      .append('a')
      .attr('class', 'node unselected')
    svg_node.call(drag(simulation))
    svg_node
      .append('image')
      .attr('xlink:href', function (d) {
        return topology_media_img + d.image
      })
      .style('opacity', 1)
      .attr('width', 32)
      .attr('height', 32)
      .attr('x', -16)
      .attr('y', -16)
      .attr('fill', function (d) {
        return color(d.group)
      })
    svg_node
      .append('text')
      .attr('font-size', '1em')
      .attr('y', +30)
      .attr('x', -50)
      .text(function (d) {
        return d.id
      })
    svg_node.append('title').text(function (d) {
      return d.id + '(' + d.manage_ip + ')'
    })
    simulation.nodes(graph.value.nodes).on('tick', ticked)
    svg_node.exit().remove()
    svg_node.on('mouseover', function (d) {})
    svg_node.on('mouseout', function (d, event) {
      showNodePopoverRef.value = false
    })
    svg_node.on('dblclick', function (event, d) {
      show_drawer_activate('right')
      dblclick_node_model.value = d
    })
    svg_node.on('click', function (event, d) {
      popover_node.value = d
      if (showNodePopoverRef.value) {
        showNodePopoverRef.value = false
      } else {
        showNodePopoverRef.value = true

        NodePopoveXRef.value = event.clientX
        NodePopoveyRef.value = event.clientY
      }
    })
  }
  // 用来存放视图缩放偏移量，配合框选确定框选的范围
  const transform_v = ref({})
  const last_coordinate_x = ref(0)
  const last_coordinate_y = ref(0)
  const current_coordinate_x = ref(0)
  const current_coordinate_y = ref(0)
  // 当前框选的范围，根据zoom实时计算
  const default_extent = ref([
    [-99999, -99999],
    [99999, 99999],
  ])
  // 初始化画布
  function init_svg() {
    // tooltip.value = d3.select('body').append('div').attr('id', 'tooltip').style('opacity', 0)
    simulation = d3
      .forceSimulation()
      .force(
        'link',
        d3.forceLink().id(function (d) {
          return d.id
        })
        // .distance(0.01)
        // .strength(0.001)
      )
      .force('charge', d3.forceManyBody().strength(0.001).distanceMax(0.001).distanceMin(0.001))
      .force('center', d3.forceCenter(width / 2, height / 2))

    // .force('collision', d3.forceCollide().radius(25))
    svg.value = d3
      .select(toppolgoy_svg.value)
      //   .attr('viewBox', '0 0 3000 3000')
      .classed('svg-content', true)
    group.value = svg.value.append('g')
    group.value = d3.select('svg#primary-svg g')
    zoom.value = d3
      .zoom()
      // .translateExtent(defaultExtent())
      .scaleExtent([0.5, 2])
      .on('zoom', function (event) {
        // default_extent.value = defaultExtent()
        transform_v.value = event.transform
        group.value.attr('transform', event.transform)
      })
    svg.value.call(zoom.value)
    svg.value.on('dblclick.zoom', null)
    svg_brush = group.value.append('g').attr('class', 'brush')
    init_links()
    init_edgepaths()
    init_nodes()
    simulation.force('link').links(graph.value.links)
    svg_link.exit().remove()
    //console.log(node_formatbase(event))
    //resize_svg_on_window_resize()
    //    //console.log(event)
    // tooltip.value.transition().duration(300).style('opacity', 0.8)
    //   tooltip.value
    //     .style('opacity', 0.0)
    //     .html(node_formatbase(event))
    //     //.style("left", (d3.event.pageX) + "px")
    //     .style('top', event.y + 10 + 'px')
    // })
    // init_edgelabels()
    // svg_node.exit().remove()
    // svg_link.exit().remove()
  }

  function drag(simulation) {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.1).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0.1)
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended)
  }

  function node_transform(node) {
    return 'translate(' + node.x + ',' + node.y + ')'
  }

  function format_link_id(link) {
    return 'line' + link.source + link.target
  }
  // 用于存放框选的设备
  const brushNode = ref([])
  // 对齐基线X
  const AlignmentBaseX = ref(0)
  // 对齐基线Y
  const AlignmentBaseY = ref(0)
  // 框选节点对齐 竖向
  function nodeAlignmentbyX() {
    console.log('竖向对齐')
    AlignmentBaseX.value = brushNode.value[0].fx
    AlignmentBaseY.value = brushNode.value[0].fy
    brushNode.value.forEach((_node) => {
      if (_node.fx < AlignmentBaseX.value) {
        AlignmentBaseX.value = _node.fx
      }
      if (_node.fy < AlignmentBaseY.value) {
        AlignmentBaseY.value = _node.fy
      }
    })
    graph.value.nodes.forEach((node) => {
      brushNode.value.forEach((_node) => {
        if (node.device_id == _node.device_id) {
          node.fx = node.fx == AlignmentBaseX.value ? node.fx : AlignmentBaseX.value
        }
      })
    })
    nextTick(() => {
      unBrush()
    })
  }
  function alignY() {
    message.info('横向对齐')
    // AlignmentBaseX.value = brushNode.value[0].fx
    // AlignmentBaseY.value = brushNode.value[0].fy
  }
  // 框选节点对齐 横向仅对齐
  const nodeAlignmentbyY = () => {
    message.info('横向对齐')
    AlignmentBaseX.value = brushNode.value[0].fx
    AlignmentBaseY.value = brushNode.value[0].fy
    brushNode.value.forEach((_node) => {
      if (_node.fx < AlignmentBaseX.value) {
        AlignmentBaseX.value = _node.fx
      }
      if (_node.fy < AlignmentBaseY.value) {
        AlignmentBaseY.value = _node.fy
      }
    })
    graph.value.nodes.forEach((node) => {
      brushNode.value.forEach((_node) => {
        if (node.device_id == _node.device_id) {
          node.fy = node.fy == AlignmentBaseY.value ? node.fy : AlignmentBaseY.value
        }
      })
    })
    nextTick(() => {
      unBrush()
    })
  }
  const showNodeAlignmentBtn = ref(false)
  const showCancelBrushBtn = ref(false)

  function defaultExtent() {
    // console.log('transform_v', transform_v.value)
    // console.log(toppolgoy_svg.value?.clientHeight)
    // console.log('transform_v', Object.keys(transform_v.value).length)
    if (Object.keys(transform_v.value).length != 0) {
      let x = (0 - transform_v.value.x) / transform_v.value.k
      let y = (0 - transform_v.value.y) / transform_v.value.k
      return [
        [x, y],
        [
          (toppolgoy_svg.value?.clientWidth + 100) * (1 / transform_v.value.k),
          (toppolgoy_svg.value?.clientHeight + 100) * (1 / transform_v.value.k),
        ],
      ]
    } else {
      return [
        [-9999, -9999],
        [9999, 9999],
      ]
    }
  }
  // 框选的范围
  const brush_group = ref([])
  // 框选设备去重
  function uniqueDevice(arr) {
    let res = new Map()
    return arr.filter((arr) => !res.has(arr.device_id) && res.set(arr.device_id, 1))
  }
  // 设备框选函数
  function Brush() {
    message.info('开始框选')
    // console.log(default_extent.value)
    zoom.value = d3.zoom().on('zoom', null)
    svg.value.call(zoom.value)
    svg_brush.call(
      d3
        .brush()
        // .extent(default_extent.value)
        .extent(defaultExtent())
        // brush 是画笔移动时的事件，没什么用
        // .on('start', function brushing(event) {
        //   brushNode.value = []
        // })
        .on('brush', function brushing(event) {
          // if (event.mode != 'drag') return
          // console.log('type', event.type)
          // console.log('event', event.sourceEvent)
          let extent = event.selection
          // console.log(extent)
          // console.log('event.selection', event.selection)
          if (extent == null) {
            // console.log('extent, null')
            return
          }
          if (brush_group.value.length != 0 && extent != null) {
            // 计算上一次这当前的x y 方向的移动距离
            last_coordinate_x.value = brush_group.value[0][0]
            last_coordinate_y.value = brush_group.value[0][1]
            // 当前的x y 方向的移动距离
            current_coordinate_x.value = extent[0][0]
            current_coordinate_y.value = extent[0][1]
            // last_coordinate_x.value = event.sourceEvent.offsetX
            // last_coordinate_y.value = event.sourceEvent.offsetY
            // current_coordinate_x.value = extent[0][0]
            // current_coordinate_y.value = extent[0][1]
          }
          brush_group.value = extent
          if (brushNode.value.length != 0) {
            brushNode.value.forEach((node) => {
              // console.log('before', node.fx, node.fy)
              node.fx = node.x - (last_coordinate_x.value - current_coordinate_x.value)
              node.fy = node.y - (last_coordinate_y.value - current_coordinate_y.value)
              // console.log('end', node.fx, node.fy)
              simulation.alphaTarget(0.1).restart()
            })
          }
        })
        .on('end', function brushed(event) {
          // console.log('brushNode.value', brushNode.value)
          showNodeAlignmentBtn.value = true
          showCancelBrushBtn.value = true
          // console.log('type', event)
          // brushNode.value = []
          // console.log('event', event)
          let extent = event.selection
          console.log('extent', extent)
          if (extent == null) {
            unBrush()
            return
          }
          graph.value.nodes.forEach((node) => {
            if (
              extent[0][0] <= node.x &&
              node.x < extent[1][0] &&
              extent[0][1] <= node.y &&
              node.y < extent[1][1]
            ) {
              // console.log(node)
              brushNode.value.push(node)
              brushNode.value = uniqueDevice(brushNode.value)
              // console.log(brushNode.value)
              // 显示取消框选和对齐的按钮
              showNodeAlignmentBtn.value = true
              simulation.alphaTarget(0.1)
              // 开始计算偏移量
              // node.fx = node.x - (last_coordinate_x.value - current_coordinate_x.value)
              // node.fy = node.y - (last_coordinate_y.value - current_coordinate_y.value)
            }
          })
          console.log(brushNode.value)
          // simulation.alphaTarget(0.1)
        })
    )
    //console.log('框选')
    // 框选定义
    // svg_brush = group.value.selectAll('g').attr('class', 'brush')
    //var brush_handler = d3.brush().on("brush", brushed)
    // var brush = d3.brush().on('brush', function brushed(d) {
    // console.log(d)
    // let extent = d.selection
    // console.log('extent', extent)
    // //console.log(d3.event.target.extent())
    // Is the circle in the selection?

    // })

    // nextTick(() => {
    //console.log(brush.extent())
    // })
    //  //console.log(brush)
    //
    // function brushed() {
    //   //  //console.log('d.event',d.event)
    //   let extent = d3.brush().extent([d.x, d.y], [d.x, d.y])
    //    //console.log('extent', extent)
    //   // //console.log(d3.event.target.extent())
    //   // Is the circle in the selection?
    //   d3.selectAll('a').select('image').classed('selected', function(d) {
    //     //  //console.log(d)
    //
    //     let brushed_node = extent[0][0] <= d.x && d.x < extent[1][0]
    //         && extent[0][1] <= d.y && d.y < extent[1][1]
    //      //console.log('brushed_node', brushed_node)
    //     return brushed_node
    //   })
    //   // Circle is green if in the selection, pink otherwise
    //   //node.classed("selected", isBrushed)
    //
    // }
  }
  function unBrush() {
    console.log('取消框选')
    message.info('取消框选')
    showCancelBrushBtn.value = false
    last_coordinate_x.value = 0
    last_coordinate_y.value = 0
    current_coordinate_x.value = 0
    current_coordinate_y.value = 0
    brushNode.value = []
    // group.value.selectAll('.brush').remove()
    // 删除框选手柄
    svg_brush.on('.brush', null)
    svg_brush = svg_brush.call(d3.brush().clear)
    svg_brush.selectAll('*').remove()
    // 开启缩放
    zoom.value = d3
      .zoom()
      .scaleExtent([0.5, 2])
      .on('zoom', function (event) {
        transform_v.value = event.transform
        group.value.attr('transform', event.transform)
      })
    svg.value.call(zoom.value)
    // 关闭按钮显示
    showNodeAlignmentBtn.value = false
    // nextTick(() => {
    // if (group.value !== null) {
    //   group.value.selectAll('*').remove()
    // }
    // init_svg()
    // })
  }
  function save_graph() {
    console.log('当前位置', graph.value)
    post({
      url: topology_show,
      data: { name: graph.value.name, graph: graph.value },
    }).then((res) => {
      if (res.code == 200) {
        message.success(res.msg)
      } else {
        message.error(res.message)
      }
    })
  }
  // 添加节点按钮
  function addDevice() {
    message.info('添加设备')
    showAddNodeModal.value = true
  }
  // 节点管理按钮
  function manageNodes() {
    message.info('管理节点')
    showManageNodeModal.value = true
  }
  const renderSingleSelectTag: SelectRenderTag = ({ option }) => {
    return h(
      'div',
      {
        style: {
          display: 'flex',
          alignItems: 'center',
        },
      },
      [
        h(NAvatar, {
          // src: 'https://07akioni.oss-cn-beijing.aliyuncs.com/07akioni.jpeg',
          src: topology_media_img + option.value,
          round: true,
          size: 24,
          style: {
            marginRight: '12px',
          },
        }),
        option.label as string,
      ]
    )
  }
  const drawerImgOptions = ref([])
  const idcOptions = ref([])
  // 获取图标库
  function get_icon_tree() {
    drawerImgOptions.value = []
    get({
      url: topology_icon,
      data: () => {
        return {
          get_tree: 1,
        }
      },
    }).then((res) => {
      // console.log(res)
      nextTick(() => {
        res.data.forEach((item) => {
          //console.log(item)
          let keys = Object.keys(item)
          if (keys.includes('children')) {
            if (item.children.length > 0) {
              let tmp = {
                type: 'group',
                label: item.label,
                key: item.key,
                children: [],
              }
              item.children.forEach((sub) => {
                tmp['children'].push({
                  label: sub.label,
                  value: sub.key,
                })
              })
              drawerImgOptions.value.push(tmp)
            }
          }
        })
        // console.log(drawerImgOptions.value)
      })
    })
  }
  // 右侧 抽屉 组件
  const renderLabel: SelectRenderLabel = (option) => {
    if (option.type === 'group') return option.label
    return h(
      'div',
      {
        style: {
          display: 'flex',
          alignItems: 'center',
        },
      },
      [
        h(NAvatar, {
          src: topology_media_img + option.value,
          round: true,
          size: 'small',
        }),
        h(
          'div',
          {
            style: {
              marginLeft: '12px',
              padding: '4px 0',
            },
          },
          [
            h('div', null, [option.label as string]),
            h(
              NText,
              { depth: 3, tag: 'div' },
              {
                default: () => 'description',
              }
            ),
          ]
        ),
      ]
    )
  }
  // 双击线路 抽屉
  function drawerChangeLink() {
    console.log(dblclick_link_model.value)
    graph.value.links.forEach((item) => {
      if (item.name == dblclick_link_model.value.name) {
        item.color = dblclick_link_model.value.color
      }
    })
    save_graph()
    nextTick(() => {
      if (group.value !== null) {
        group.value.selectAll('*').remove()
      }
      init_svg()
    })
  }
  // 双击节点 抽屉
  function drawerChangeNode() {
    console.log(dblclick_node_model.value)
    graph.value.nodes.forEach((item) => {
      if (item.id == dblclick_node_model.value.id) {
        item.image = dblclick_node_model.value.image
      }
    })
    save_graph()
    nextTick(() => {
      if (group.value !== null) {
        group.value.selectAll('*').remove()
      }
      init_svg()
    })
  }
  // 新建拓扑模态框
  const showAddGraphModal = ref(false)
  // 添加节点模态框
  const showAddNodeModal = ref(false)
  // 节点管理模态框
  const showManageNodeModal = ref(false)
  const addGraphDataFormRef = ref<DataFormType | null>(null)
  // 新建拓扑表单
  const addGraphFormOptions = [
    {
      key: 'name',
      label: '名称',
      value: ref(''),
      render: (formItem) => {
        return h(NInput, {
          value: formItem.value.value,
          onUpdateValue: (newVal: any) => {
            formItem.value.value = newVal
          },
        })
      },
    },
    {
      key: 'memo',
      label: '备注',
      value: ref(''),
      render: (formItem) => {
        return h(NInput, {
          value: formItem.value.value,
          onUpdateValue: (newVal: any) => {
            formItem.value.value = newVal
          },
        })
      },
    },
  ] as Array<FormItem>
  // 添加节点表单
  const add_node_query_model = ref({
    name: '',
    manage_ip: '',
    idc: '',
    image: 'routers/router_red_small.png',
  })
  // 新建拓扑
  function addGraph() {
    showAddGraphModal.value = true
    // addGraphModalDialog.value?.toggle()
    nextTick(() => {
      addGraphFormOptions.value?.reset()
    })
  }
  // 删除拓扑
  function del_graph() {
    post({
      url: topology_show,
      data: { name: topology_value.value, del_graph: 'delete' },
    }).then((res) => {
      if (res.code == 200) {
        message.success(res.msg)
        nextTick(() => {
          topology_value.value = ''
          get_topology_list()
        })
      } else {
        message.error(res.msg)
      }
    })
  }
  // 新建拓扑
  function onAddGraphConfirm() {
    // if (addGraphDataFormRef.value?.validator()) {
    // console.log('确认数据', addGraphDataFormRef.value.generatorParams())
    // }
    let post_data = addGraphDataFormRef.value.generatorParams()
    post({
      url: get_topology,
      data: {
        name: post_data.name,
        memo: post_data.memo,
      },
    }).then((res) => {
      console.log(res)
      if (res.code == 201) {
        message.success(res.message)
        showAddGraphModal.value = false
        get_topology_list()
      } else {
        message.error(res.message)
      }
    })
  }
  // 添加节点
  function onAddNodeConfirm() {
    console.log('添加节点')
    // console.log(table.selectRows)
    let add_nodes = shallowReactive([]) as Array<any>
    dataList.forEach((node) => {
      table.selectRows.forEach((select) => {
        if (node.id == select) {
          add_nodes.push({
            id: node.name,
            name: node.name + '(' + node.manage_ip + ')',
            manage_ip: node.manage_ip,
            image: add_node_query_model.value.image,
          })
        }
      })
    })
    post({
      url: topology_show,
      data: { name: graph.value.name, add_nodes: add_nodes },
    }).then((res) => {
      if (res.code == 200) {
        message.success(res.msg)
        showAddNodeModal.value = false
        nextTick(() => {
          select_topology()
        })
      } else {
        message.error(res.msg)
      }
    })
    console.log(add_nodes)
  }
  // 获取IDC
  function doIdc() {
    get({
      url: getCmdbIdcList,
      data: () => {
        return {
          limit: 1000,
        }
      },
    }).then((res) => {
      res.results.forEach((item) => {
        idcOptions.value.push({
          label: item.name,
          value: item.id,
        })
      })
    })
  }
  onMounted(init_svg)
  onMounted(get_topology_list)
  onMounted(get_icon_tree)
  onMounted(doIdc)
  onMounted(() => {
    //   console.log(document.documentElement.clientWidth)
    //   console.log(window.innerWidth)
    //   console.log(document.documentElement.clientHeight)
    //   console.log(window.innerHeight)
  })
</script>
<style lang="scss" scoped>
  /* 透明度 */
  .unselected {
    opacity: 1;
  }

  .selected {
    opacity: 0.1;
  }

  #container {
    background: url('../../assets/topology_bkg.jpeg') no-repeat;
    background-size: 100% 100%;
  }
</style>
