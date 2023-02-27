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
      port: 1005,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/api/, '/api'),
        },
        '/ipam': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/ipam/, '/ipam'),
        },
        '/media': {
          target: env.VITE_BASIC_URL,
          ws: true, //代理websockets
          changeOrigin: true, // 虚拟的站点需要更管origin
          rewrite: (path: string) => path.replace(/^\/media/, '/media'),
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
