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
      mkcert() // 启用mkcert插件
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
      https: true, // 启用HTTPS
      proxy: {
        // 🔥 关键修改：代理目标仍使用HTTP（Flask内部不需要HTTPS）
        '/flask': {
          target: FLASK_BASE_URL,
          ws: true,
          changeOrigin: true,
          secure: false,
        },
        
         // 2.3新增：直接代理/stopCamera
        '/stopCamera': {
         target: FLASK_BASE_URL,
         changeOrigin: true,
         secure: false,
        },

        '/upload': {
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
        
        '/predictCamera': {  // 🔥 新增摄像头流代理
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        
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
        
        '/api/user': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: (path) => {
            const cleanPath = path.replace(/^\/api\/user/, '');
            const idMatch = cleanPath.match(/^\/(\d+)$/);
            if (idMatch) {
              return `/flask/user/${idMatch[1]}`;
            }
            if (cleanPath && cleanPath !== '/') {
              return `/flask/user${cleanPath}`;
            }
            return '/flask/user';
          },
          secure: false,
        },
        
        '/api/imgRecords': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: () => '/flask/img_records',
          secure: false,
        },
        
        '/api/videoRecords': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: () => '/flask/video_records',
          secure: false,
        },
        
        '/api/cameraRecords': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: () => '/flask/camera_records',
          secure: false,
        },
        
        '/api': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: (path) => {
            const cleanPath = path.replace(/^\/api/, '');
            if (cleanPath.match(/^\/(\d+)$/)) {
              return cleanPath;
            }
            if (!cleanPath.startsWith('/flask') && !cleanPath.startsWith('/uploads')) {
              return `/flask${cleanPath}`;
            }
            return cleanPath;
          },
          secure: false,
        },
        
        '/socket.io': {
          target: FLASK_BASE_URL,
          ws: true,
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