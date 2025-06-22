import { resolve } from 'node:path';

export interface ServerConfig {
  docsPath: string;
  referencePath: string;
  modelsPath: string;
  serverName: string;
  serverVersion: string;
  maxSearchResults: number;
  defaultTimeout: number;
  cacheTimeout: number;
  maxCacheSize: number;
  lazyLoadEnabled: boolean;
  environment: 'development' | 'production';
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class Config {
  private config: ServerConfig;
  private static instance: Config;
  private cache = new Map<string, CacheEntry<any>>();

  constructor(basePath: string = process.cwd()) {
    this.config = {
      docsPath: resolve(basePath, 'docs'),
      referencePath: resolve(basePath, 'reference'),
      modelsPath: resolve(basePath, 'models'),
      serverName: 'bigcommerce-docs-ts',
      serverVersion: '1.0.0',
      maxSearchResults: 50,
      defaultTimeout: 30000,
      cacheTimeout: 300000, // 5 minutes
      maxCacheSize: 100,
      lazyLoadEnabled: true,
      environment: (process.env.NODE_ENV as 'development' | 'production') || 'production',
    };
  }

  static getInstance(basePath?: string): Config {
    if (!Config.instance) {
      Config.instance = new Config(basePath);
    }
    return Config.instance;
  }

  get docsPath(): string {
    return this.config.docsPath;
  }

  get referencePath(): string {
    return this.config.referencePath;
  }

  get modelsPath(): string {
    return this.config.modelsPath;
  }

  get serverName(): string {
    return this.config.serverName;
  }

  get serverVersion(): string {
    return this.config.serverVersion;
  }

  get maxSearchResults(): number {
    return this.config.maxSearchResults;
  }

  get defaultTimeout(): number {
    return this.config.defaultTimeout;
  }

  get cacheTimeout(): number {
    return this.config.cacheTimeout;
  }

  get maxCacheSize(): number {
    return this.config.maxCacheSize;
  }

  get lazyLoadEnabled(): boolean {
    return this.config.lazyLoadEnabled;
  }

  get environment(): 'development' | 'production' {
    return this.config.environment;
  }

  updateConfig(updates: Partial<ServerConfig>): void {
    this.config = { ...this.config, ...updates };
  }

  // Cache management methods
  setCache<T>(key: string, data: T, ttl: number = this.config.cacheTimeout): void {
    // Cleanup old entries if cache is full
    if (this.cache.size >= this.config.maxCacheSize) {
      this.cleanupCache();
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  getCache<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  private cleanupCache(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => this.cache.delete(key));

    // If still at max capacity, remove oldest entries
    if (this.cache.size >= this.config.maxCacheSize) {
      const entries = Array.from(this.cache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      
      const toRemove = entries.slice(0, Math.floor(this.config.maxCacheSize * 0.2));
      toRemove.forEach(([key]) => this.cache.delete(key));
    }
  }

  clearCache(): void {
    this.cache.clear();
  }

  getCacheStats(): { size: number; maxSize: number; hitRate?: number } {
    return {
      size: this.cache.size,
      maxSize: this.config.maxCacheSize,
    };
  }
} 