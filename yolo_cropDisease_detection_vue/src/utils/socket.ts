import { io, Socket } from 'socket.io-client'; // 显式导入Socket类型，增强TS类型提示

export class SocketService {
  private socket: Socket; // 强类型定义，替代any

  constructor() {
    // 修复问题1：去掉ws://前缀，用http前缀（Flask-SocketIO默认协议）
    const currentHost = window.location.hostname;
    this.socket = io(`http://${currentHost}:5000`, {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      transports: ['polling', 'websocket'], // 显式指定降级策略，适配Flask-SocketIO
    });

    this.setupListeners();
  }

  // 修复问题4：绑定this，避免指向异常
  private setupListeners = () => {
    this.socket.on('connect', () => {
      console.log('Connected to Weed Detection WebSocket server!'); // 与你之前的控制台日志保持一致
    });

    this.socket.on('disconnect', (reason: string) => {
      console.log('Socket disconnected:', reason);
    });

    this.socket.on('connect_error', (error: Error) => {
      console.error('Socket connection error:', error.message);
    });
  }

  // 修复问题3：移除自定义数据解析，直接透传后端原始数据
  on(event: string, callback: (data: any) => void) {
    this.socket.on(event, callback);
  }

  // 修复问题2：直接用socket.connected获取真实连接状态，删除冗余的connected属性
  emit(event: string, data: any) {
    if (this.socket.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('Socket not connected, cannot emit event:', event);
    }
  }

  // 重连指定URL
  connect(url?: string) {
    if (url && url !== this.socket.io.uri) {
      this.socket.disconnect();
      this.socket.io.uri = url;
    }
    if (!this.socket.connected) {
      this.socket.connect();
    }
  }

  // 断开连接
  disconnect() {
    if (this.socket.connected) {
      this.socket.disconnect();
    }
  }

  close() {
    this.disconnect();
  }

  // 对外暴露真实的连接状态（getter）
  get isConnected(): boolean { // 重命名为isConnected，避免歧义
    return this.socket.connected;
  }
}

// 导出单例实例（推荐，全局只需要一个Socket连接）
export const socketService = new SocketService();