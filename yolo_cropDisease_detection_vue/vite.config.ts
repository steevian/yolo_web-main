import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { defineConfig, loadEnv, ConfigEnv } from 'vite';
import vueSetupExtend from 'vite-plugin-vue-setup-extend';

// 路径解析方法
const pathResolve = (dir: string) => {
  return resolve(__dirname, '.', dir);
};

// 别名配置
const alias: Record<string, string> = {
  '/@': pathResolve('./src/'),
  'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',
};

// 全局统一Flask局域网地址（唯一配置点，后续改IP只动这里）
const FLASK_BASE_URL = 'http://192.168.0.101:5000';

const viteConfig = defineConfig((mode: ConfigEnv) => {
  const env = loadEnv(mode.mode, process.cwd());
  return {
    plugins: [vue(), vueSetupExtend()],
    root: process.cwd(),
    resolve: { alias },
    // 开发环境相对路径，生产环境读取环境变量
    base: mode.command === 'serve' ? './' : env.VITE_PUBLIC_PATH || './',
    // 依赖预构建优化
    optimizeDeps: {
      include: [
        'element-plus/lib/locale/lang/zh-cn',
        'element-plus/lib/locale/lang/en',
        'element-plus/lib/locale/lang/zh-tw'
      ],
    },
    server: {
      host: '0.0.0.0', // 强制绑定本机所有IP，确保192.168.0.101:5173可访问
      port: (env.VITE_PORT as unknown as number) || 5173, // 端口默认5173，兼容环境变量
      open: env.VITE_OPEN === 'true' || false, // 修复布尔值解析
      hmr: true, // 热更新开启
      proxy: {
        // 🔥 核心修复：/flask代理（匹配后端/flask/login）- 移除rewrite，直接转发完整路径
        '/flask': {
          target: FLASK_BASE_URL,
          ws: true, // 支持WebSocket
          changeOrigin: true, // 开启跨域代理（核心）
          secure: false, // 关闭HTTPS校验，适配本地Flask服务
        },
        // 静态文件代理 - 保留原有配置，确保图片/检测结果请求正常
        '/uploads': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          ws: false, // 静态文件无需WebSocket，强制关闭避免冲突
          secure: false,
        },
        '/results': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          ws: false,
          secure: false,
        },
        // 添加预测接口代理 - 保留WebSocket支持
        '/predict': {
          target: FLASK_BASE_URL,
          ws: true, // 支持WebSocket  
          secure: false
        },
        // 后端检测临时图片目录代理
        '/runs': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          ws: false,
          secure: false,
        },
        // 🔴 删除了无效的/api/user/login映射（原映射到后端/login，无此接口）
        // 通用用户接口：更新/删除/查询，统一映射到Flask/user
        '/api/user': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: (path) => {
            // 提取ID并重构路径：/api/user/update/123 → /user/123
            const idMatch = path.match(/\/api\/user\/(update|delete)\/(\d+)/);
            if (idMatch) {
              return `/user/${idMatch[2]}`;
            }
            // 其他用户接口：/api/user/info → /user/info
            return path.replace(/^\/api\/user/, '/user');
          },
          secure: false,
        },
        // 业务记录代理：/api/xxxRecords 映射到Flask/xxx_records（下划线标准化）
        '/api/imgRecords': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: () => '/img_records',
          secure: false,
        },
        '/api/videoRecords': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: () => '/video_records',
          secure: false,
        },
        '/api/cameraRecords': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: () => '/camera_records',
          secure: false,
        },
        // 文件上传代理：/files/upload 映射到Flask/upload
        '/files/upload': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: () => '/upload',
          secure: false,
        },
        // 兜底代理：未匹配的/api请求，统一转发到Flask（兼容旧代码）
        '/api': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          secure: false,
        },
      },
    },
    // 构建配置
    build: {
      outDir: 'dist', // 输出目录
      chunkSizeWarningLimit: 1500, // 代码分割大小警告阈值
      rollupOptions: {
        output: {
          // 构建产物命名规则
          entryFileNames: `assets/[name].[hash].js`,
          chunkFileNames: `assets/[name].[hash].js`,
          assetFileNames: `assets/[name].[hash].[ext]`,
          compact: true, // 压缩代码
          // 手动代码分割：第三方库单独打包，提升加载速度
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            echarts: ['echarts'],
            elementPlus: ['element-plus'],
          },
        },
      },
    },
    // CSS配置：关闭charset警告
    css: {
      preprocessorOptions: {
        css: { charset: false },
      },
    },
    // 全局常量定义
    define: {
      __VUE_I18N_LEGACY_API__: JSON.stringify(false),
      __VUE_I18N_FULL_INSTALL__: JSON.stringify(false),
      __INTLIFY_PROD_DEVTOOLS__: JSON.stringify(false),
      __VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
    },
  };
});

export default viteConfig;