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

const viteConfig = defineConfig((mode: ConfigEnv) => {
  const env = loadEnv(mode.mode, process.cwd());
  const flaskBaseUrl = env.VITE_FLASK_BASE_URL || 'http://127.0.0.1:8080';
  return {
    plugins: [
      vue(), 
      vueSetupExtend(),
      mkcert() // 启用mkcert插件（支持HTTPS）
    ],
    root: process.cwd(),
    resolve: { alias },
    base: mode.command === 'serve' ? '/' : env.VITE_PUBLIC_PATH || './', // 修复开发环境base路径（原./可能导致路由404）
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
        '/flask': {
          target: flaskBaseUrl,
          ws: true, // 支持WebSocket（视频进度推送、摄像头流）
          changeOrigin: true, // 跨域必备
          secure: false, // 允许目标为HTTP（Flask未启用HTTPS）
        },
        '/uploads': {
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
        },
        '/results': {
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
        },
        '/runs': {
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
        },
        '/socket.io': {
          target: flaskBaseUrl,
          ws: true,
          changeOrigin: true,
          secure: false,
        },
        '/stopCamera': {
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
        },
        '/upload': { // 兼容前端上传组件的action="/upload"
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
        },
        '/predict': {
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
          ws: true,
        },
        '/predictVideo': {
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
        },
        '/predictCamera': {
          target: flaskBaseUrl,
          changeOrigin: true,
          secure: false,
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