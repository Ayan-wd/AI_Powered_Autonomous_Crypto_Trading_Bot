/**
 * Frontend WebSocket Streaming Client.
 * Provides auto-reconnecting WebSocket connection and event dispatching.
 */

export type WebSocketEventHandler = (event: string, data: any) => void;

export class TradingWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private listeners: Set<WebSocketEventHandler> = new Set();
  private reconnectInterval = 3000;
  private shouldReconnect = true;
  private pingTimer: any = null;
  public isConnected = false;

  constructor(url?: string) {
    if (url) {
      this.url = url;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host || '127.0.0.1:8000';
      // In dev mode (Vite on port 5173), proxy or direct backend on 8000
      const targetHost = host.includes('5173') ? '127.0.0.1:8000' : host;
      this.url = `${protocol}//${targetHost}/api/v1/ws/stream`;
    }
  }

  public connect(): void {
    this.shouldReconnect = true;
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.notifyListeners('CONNECTION_OPEN', { url: this.url });
        this.startPing();
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type && payload.data !== undefined) {
            this.notifyListeners(payload.type, payload.data);
          }
        } catch (e) {
          console.warn('Failed to parse WebSocket JSON payload:', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.stopPing();
        this.notifyListeners('CONNECTION_CLOSED', {});
        if (this.shouldReconnect) {
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('WebSocket error:', err);
      };
    } catch (err) {
      console.warn('WebSocket init exception:', err);
      if (this.shouldReconnect) {
        setTimeout(() => this.connect(), this.reconnectInterval);
      }
    }
  }

  public disconnect(): void {
    this.shouldReconnect = false;
    this.stopPing();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  public subscribe(handler: WebSocketEventHandler): () => void {
    this.listeners.add(handler);
    return () => this.listeners.delete(handler);
  }

  private notifyListeners(type: string, data: any): void {
    this.listeners.forEach((handler) => {
      try {
        handler(type, data);
      } catch (e) {
        console.error('Error in WebSocket event listener:', e);
      }
    });
  }

  private startPing(): void {
    this.stopPing();
    this.pingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'PING', client_time: Date.now() }));
      }
    }, 10000);
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
}

// Global WebSocket Singleton Instance
export const wsClient = new TradingWebSocketClient();
