import vue from '@vitejs/plugin-vue'
import viteSvgIcons from 'vite-plugin-svg-icons'
import path from 'path'
import vitePluginCompression from 'vite-plugin-compression'
import ViteComponents from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import { loadEnv } from 'vite'
import vueJsx from '@vitejs/plugin-vue-jsx'
export default ({ mode }) => {
  const env = loadEnv(mode, './')
  const config = {
    plugins: [
      vue(),
      viteSvgIcons({
        iconDirs: [path.resolve(process.cwd(), 'src/icons')],
        symbolId: 'icon-[dir]-[name]',
      }),
      vitePluginCompression({
        threshold: 1024 * 10,
      }),
      ViteComponents({
        resolvers: [NaiveUiResolver()],
      }),
      vueJsx(),
    ],
    resolve: {
      alias: [
        {
          find: '@/',
          replacement: path.resolve(process.cwd(), 'src') + '/',
        },
      ],
    },
    server: {
      open: true,
      port: 5005,
      proxy: {
        '/api': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/api/, '/api'),
        },
        '/net_backend': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/net_backend/, '/backend'),
        },
        '/int_utilization': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/int_utilization/, '/int_utilization'),
        },
        '/automation': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/automation/, '/automation'),
        },
        '/topology': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/topology/, '/topology'),
        },
        '/config_center': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/config_center/, '/config_center'),
        },
        '/network': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/network/, '/network'),
        },
        '/ws': {
          target: env.VITE_BASIC_URL,
          timeout: 60000,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/ws/, '/ws'),
        },
      },
    },
  }
  if (mode === 'staging') {
    return Object.assign(
      {
        base: '/admin-work/',
      },
      config
    )
  } else {
    return Object.assign(
      {
        base: '/',
      },
      config
    )
  }
}
