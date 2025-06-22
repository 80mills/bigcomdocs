import { resolve } from 'node:path';
export class Config {
    config;
    static instance;
    cache = new Map();
    constructor(basePath = process.cwd()) {
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
            environment: process.env.NODE_ENV || 'production',
        };
    }
    static getInstance(basePath) {
        if (!Config.instance) {
            Config.instance = new Config(basePath);
        }
        return Config.instance;
    }
    get docsPath() {
        return this.config.docsPath;
    }
    get referencePath() {
        return this.config.referencePath;
    }
    get modelsPath() {
        return this.config.modelsPath;
    }
    get serverName() {
        return this.config.serverName;
    }
    get serverVersion() {
        return this.config.serverVersion;
    }
    get maxSearchResults() {
        return this.config.maxSearchResults;
    }
    get defaultTimeout() {
        return this.config.defaultTimeout;
    }
    get cacheTimeout() {
        return this.config.cacheTimeout;
    }
    get maxCacheSize() {
        return this.config.maxCacheSize;
    }
    get lazyLoadEnabled() {
        return this.config.lazyLoadEnabled;
    }
    get environment() {
        return this.config.environment;
    }
    updateConfig(updates) {
        this.config = { ...this.config, ...updates };
    }
    // Cache management methods
    setCache(key, data, ttl = this.config.cacheTimeout) {
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
    getCache(key) {
        const entry = this.cache.get(key);
        if (!entry)
            return null;
        const now = Date.now();
        if (now - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return null;
        }
        return entry.data;
    }
    cleanupCache() {
        const now = Date.now();
        const expiredKeys = [];
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
    clearCache() {
        this.cache.clear();
    }
    getCacheStats() {
        return {
            size: this.cache.size,
            maxSize: this.config.maxCacheSize,
        };
    }
}
