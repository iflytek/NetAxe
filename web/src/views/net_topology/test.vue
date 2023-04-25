<template>
  <div class="main-container">
    <n-grid x-gap="12" :cols="2" class="rack-main">
      <n-gi>
        <div class="rectangle">
          <svg viewBox="0 0 100 100" preserveAspectRatio="none">
            <rect
              x="0"
              :y="100 - utilization"
              width="100"
              :height="utilization + '%'"
              :fill="fillColor"
            />
          </svg>
          <div class="utilization">{{ utilization }}%</div>
          <div class="rackName">{{ rackName }}</div>
        </div>
      </n-gi>
      <n-gi>
        <div class="rack">
          <div
            class="u"
            v-for="u in 32"
            :key="u"
            :class="{ occupied: (u >= 1 && u <= 2) || (u >= 5 && u <= 6) }"
          >
            <div class="u-number">{{ u }}</div>
            <div class="u-content">123145</div>
          </div>
        </div>
      </n-gi>
    </n-grid>
  </div>
</template>

<script lang="ts" setup>
  import { ref } from 'vue'

  const utilization = ref(70)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const fillColor = utilization.value >= 80 ? 'red' : 'green'
  // eslint-disable-next-line @typescript-eslint/no-unused-vars, no-unused-vars
  const rackName = ref('E03')
</script>

<style lang="scss" scoped>
  .rack-main {
    background: url('../../assets/rack_bkg.jpeg') no-repeat;
    background-size: 100% 100%;
  }
  .rectangle {
    position: relative;
    left: 50%;
    top: 50%;
    width: 200px;
    height: 200px;
    border: 1px solid #ffffff;
  }

  svg {
    display: block;
    width: 100%;
    height: 100%;
  }
  .rackName {
    position: absolute;
    top: 70%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 16px;
    color: white;
  }
  .utilization {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 20px;
    color: white;
  }
  .rack {
    width: 40%;
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    border: 1px solid;
    color: white;
  }

  .u {
    width: 100%;
    height: calc(100% / 32);
    border-bottom: 1px solid;
    display: flex;
    align-items: center;
    // background-color: #71dc81;
  }

  .u-number {
    width: 15%;
    text-align: center;
    font-size: 14px;
  }

  .u-content {
    width: 85%;
    height: 90%;
    margin-left: 5%;
    // background-color: #71dc81;
  }

  .u.occupied {
    background-color: #73da5e;
  }
</style>
