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
        // 🔥 核心优化：Flask统一接口代理（所有接口通过/flask前缀访问）
        '/flask': {
          target: FLASK_BASE_URL,
          ws: true, // 支持WebSocket
          changeOrigin: true, // 开启跨域代理
          secure: false, // 关闭HTTPS校验，适配本地Flask服务
          // 移除rewrite，保持路径原样转发到Flask（Flask有/flask前缀接口）
        },
        
        // 🔥 核心优化：统一上传接口代理（覆盖所有上传相关路径）
        '/upload': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
          // 直接转发到Flask的/upload接口
        },
        
        // 🔥 核心优化：统一预测接口代理
        '/predict': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
          ws: true, // 预测接口可能需要WebSocket
        },
        
        // 🔥 新增：视频检测流接口代理
        '/predictVideo': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
          // 注意：视频流接口不需要WebSocket，使用HTTP流
        },
        
        // 静态文件代理 - 确保图片/检测结果请求正常
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
        
        // 检测临时图片目录代理
        '/runs': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          secure: false,
        },
        
        // 🔥 优化：用户接口代理（统一到Flask的/user接口）
        '/api/user': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: (path) => {
            // 处理各种用户接口格式：
            // /api/user/login -> /flask/login (已由/flask代理处理)
            // /api/user/test123 -> /flask/user/test123
            const cleanPath = path.replace(/^\/api\/user/, '');
            
            // 如果路径以数字结尾，认为是用户ID操作
            const idMatch = cleanPath.match(/^\/(\d+)$/);
            if (idMatch) {
              return `/flask/user/${idMatch[1]}`;
            }
            
            // 其他情况，如果路径不为空，转发到/flask/user路径
            if (cleanPath && cleanPath !== '/') {
              return `/flask/user${cleanPath}`;
            }
            
            // 默认用户列表
            return '/flask/user';
          },
          secure: false,
        },
        
        // 🔥 优化：业务记录代理（统一到Flask的xxx_records接口）
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
        
        // 🔥 优化：移除/files/upload代理，统一使用/upload
        // （避免路径冲突，Flask现在通过/upload处理所有上传）
        
        // 🔥 优化：兜底代理 - 未匹配的/api请求，统一转发到Flask
        '/api': {
          target: FLASK_BASE_URL,
          changeOrigin: true,
          rewrite: (path) => {
            // 移除/api前缀，转发到Flask对应接口
            const cleanPath = path.replace(/^\/api/, '');
            // 如果路径以数字结尾，保留原样
            if (cleanPath.match(/^\/(\d+)$/)) {
              return cleanPath;
            }
            // 其他情况，如果没有特定前缀，默认加/flask前缀
            if (!cleanPath.startsWith('/flask') && !cleanPath.startsWith('/uploads')) {
              return `/flask${cleanPath}`;
            }
            return cleanPath;
          },
          secure: false,
        },
        
        // 🔥 新增：Socket.IO WebSocket代理（关键：解决Socket连接问题）
        '/socket.io': {
          target: FLASK_BASE_URL,
          ws: true, // 必须开启WebSocket支持
          changeOrigin: true,
          secure: false,
          // Socket.IO需要特殊的headers处理
          headers: {
            'Connection': 'Upgrade',
            'Upgrade': 'websocket'
          }
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