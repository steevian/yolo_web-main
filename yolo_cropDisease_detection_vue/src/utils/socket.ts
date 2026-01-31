import { io } from 'socket.io-client';

export class SocketService {
  private socket: any;
  private connected = false;

  constructor() {
    // 使用当前页面host，而不是固定localhost
    const currentHost = window.location.hostname;
    this.socket = io(`ws://${currentHost}:5000`, {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });
    
    this.setupListeners();
  }

  private setupListeners() {
    this.socket.on('connect', () => {
      console.log('Socket connected');
      this.connected = true;
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
      this.connected = false;
    });

    this.socket.on('connect_error', (error: any) => {
      console.error('Socket connection error:', error);
      this.connected = false;
    });
  }

  on(event: string, callback: Function) {
    this.socket.on(event, (data: any) => {
      // 处理不同的数据格式
      if (typeof data === 'object' && data.data !== undefined) {
        callback(data.data);
      } else {
        callback(data);
      }
    });
  }

  emit(event: string, data: any) {
    if (this.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('Socket not connected, cannot emit:', event);
    }
  }

  connect(url?: string) {
    if (url) {
      this.socket.disconnect();
      this.socket.io.uri = url;
    }
    this.socket.connect();
  }

  disconnect() {
    this.socket.disconnect();
    this.connected = false;
  }

  close() {
    this.disconnect();
  }

  get connected(): boolean {
    return this.socket && this.socket.connected;
  }
}