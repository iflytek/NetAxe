<template>
  <n-card
      :content-style="{ padding: '10px' }"
      :header-style="{ padding: '10px' }"
      :segmented="true"
  >
    <template #header>
      <!--      <n-skeleton text style="width: 50%" v-if="loading" />-->
      <!--      <template v-else>-->
      <div class="text-sm">厂商维度，展示采集方案数量</div>
      <!--      </template>-->
    </template>
    <div class="chart-item-container">
      <!--      <n-skeleton text v-if="loading" :repeat="4" />-->
      <!--      <template v-else>-->
      <div ref="collectionPlanChart" class="chart-item"> </div>
      <!--      </template>-->
    </div>
  </n-card>
</template>

<script lang="ts">
import useEcharts from '@/hooks/useEcharts'
import { defineComponent, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { dispose } from 'echarts'
import { automation_chart } from '@/api/url'
import useGet from '@/hooks/useGet'
export default defineComponent({
  name: 'CollectionPlanChart',
  setup() {
    const get = useGet()
    const collection_plan_option =  {
      // title: {
      //   text: 'Referer of a Website',
      //   subtext: 'Fake Data',
      //   left: 'center'
      // },
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '采集方案数量',
          type: 'pie',
          radius: '50%',
          data: [
            // { value: 1048, name: 'Search Engine' },
            // { value: 735, name: 'Direct' },
            // { value: 580, name: 'Email' },
            // { value: 484, name: 'Union Ads' },
            // { value: 300, name: 'Video Ads' }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
    const loading = ref(true)
    const collectionPlanChart = ref<HTMLDivElement | null>(null)
    const init = () => {

      setTimeout(() => {
        loading.value = false
        nextTick(() => {
          useEcharts(collectionPlanChart.value as HTMLDivElement).setOption(collection_plan_option)
        })
      }, 1000)
    }
    const updateChart = () => {
      useEcharts(collectionPlanChart.value as HTMLDivElement).resize()
    }
    function echarts_init() {
      // nextTick(() => {
      useEcharts(collectionPlanChart.value as HTMLDivElement).setOption(collection_plan_option)
      // })
      nextTick(() => {
        get({
          url: automation_chart,
          data: () => {
            return {
              collection_plan: 1,
            }
          },
        }).then((res) => {
           //console.log('collection_plan_res', res)
          // const item = res.data
          res.data.forEach((item)=>{
            // collection_plan_option.xAxis.data.push(item.log_time)
            collection_plan_option.series[0].data.push(
                { value:item.sum_count,name:item.vendor },
                // { value:item.not_work_time,name:'非工作时间' },
            )
            useEcharts(collectionPlanChart.value as HTMLDivElement).setOption(collection_plan_option)
          })
        })
      })
    }

    // onMounted(init)
    onMounted(echarts_init)
    onBeforeUnmount(() => {
      dispose(collectionPlanChart.value as HTMLDivElement)
    })
    return {
      collection_plan_option,
      echarts_init,
      loading,
      collectionPlanChart,
      updateChart,
    }
  },
})
</script>

<style lang="scss" scoped>
.chart-item-container {
  width: 100%;
  .chart-item {
    height: 180px;
  }
}
</style>
