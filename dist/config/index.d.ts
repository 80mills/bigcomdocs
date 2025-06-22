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
export declare class Config {
    private config;
    private static instance;
    private cache;
    constructor(basePath?: string);
    static getInstance(basePath?: string): Config;
    get docsPath(): string;
    get referencePath(): string;
    get modelsPath(): string;
    get serverName(): string;
    get serverVersion(): string;
    get maxSearchResults(): number;
    get defaultTimeout(): number;
    get cacheTimeout(): number;
    get maxCacheSize(): number;
    get lazyLoadEnabled(): boolean;
    get environment(): 'development' | 'production';
    updateConfig(updates: Partial<ServerConfig>): void;
    setCache<T>(key: string, data: T, ttl?: number): void;
    getCache<T>(key: string): T | null;
    private cleanupCache;
    clearCache(): void;
    getCacheStats(): {
        size: number;
        maxSize: number;
        hitRate?: number;
    };
}
