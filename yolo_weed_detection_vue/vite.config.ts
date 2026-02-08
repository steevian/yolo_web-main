import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { defineConfig, loadEnv, ConfigEnv } from 'vite';
import vueSetupExtend from 'vite-plugin-vue-setup-extend';
import mkcert from 'vite-plugin-mkcert'; // 引入mkcert

// 路径解析方法
const pathResolve = (dir: string) => {
  return resolve(__dirname, '.', dir);
};

// 别名配置
const alias: Record<string, string> = {
  '/@': pathResolve('./src/'),
  'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',
};

// 全局统一Flask局域网地址（保持HTTP）
const FLASK_BASE_URL = 'http://192.168.0.101:5000';

const viteConfig = defineConfig((mode: ConfigEnv) => {
  const env = loadEnv(mode.mode, process.cwd());
  return {
    plugins: [
      vue(), 
      vueSetupExtend(),
      mkcert() // 启用mkcert插件（支持HTTPS）
    ],
    root: process.cwd(),
    resolve: { alias },
    base: mode.command === 'serve' ? './' : env.VITE_PUBLIC_PATH || './',
    optimizeDeps: {
      include: [
        'element-plus/lib/locale/lang/zh-cn',
        'element-plus/lib/locale/lang/en',
        'element-plus/lib/locale/lang/zh-tw'
      ],
    },
    server: {
      host: '0.0.0.0',
      port: (env.VITE_PORT as unknown as number) || 5173,
      open: env.VITE_OPEN === 'true' || false,
      hmr: true,
      https: true, // 启用HTTPS（前端）
      proxy: {
        // 🔥 1. 核心：所有后端接口（/flask前缀）统一转发（优先级最高）
        '/flask': {
          target: FLASK_BASE_URL,
          ws: true, // 支持WebSocket（视频进度推送、摄像头流）
          changeOrigin: true, // 跨域必备
          secure: false, // 允许目标为HTTP（Flask未启用HTTPS）
        },

        // 🔥 2. 静态资源路径直接转发（后端已配置路由，无需rewrite）
        '/uploads': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/results': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/runs': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },

        // 🔥 3. WebSocket专用代理（视频处理进度、摄像头流）
        '/socket.io': {
          target: FLASK_BASE_URL,
          ws: true,
          changeOrigin: true,
          secure: false,
        },

        // 🔥 4. 独立接口代理（兼容可能遗留的直接请求）
        '/stopCamera': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/upload': { // 兼容前端上传组件的action="/upload"
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/predict': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
          ws: true,
        },
        '/predictVideo': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        '/predictCamera': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },

        // 🔥 5. 简化/api代理（仅处理未迁移的旧请求，可选保留）
        '/api': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, '/flask'), // 旧/api请求自动转为/flask前缀
        },
      },
    },
    build: {
      outDir: 'dist',
      chunkSizeWarningLimit: 1500,
      rollupOptions: {
        output: {
          entryFileNames: `assets/[name].[hash].js`,
          chunkFileNames: `assets/[name].[hash].js`,
          assetFileNames: `assets/[name].[hash].[ext]`,
          compact: true,
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            echarts: ['echarts'],
            elementPlus: ['element-plus'],
          },
        },
      },
    },
    css: {
      preprocessorOptions: {
        css: { charset: false },
      },
    },
    define: {
      __VUE_I18N_LEGACY_API__: JSON.stringify(false),
      __VUE_I18N_FULL_INSTALL__: JSON.stringify(false),
      __INTLIFY_PROD_DEVTOOLS__: JSON.stringify(false),
      __VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
    },
  };
});

export default viteConfig;