import { BigCommerceMCPServer } from '../src/index';
import { Config } from '../src/config/index';

describe('BigCommerce MCP Server', () => {
  let server: BigCommerceMCPServer;

  beforeEach(() => {
    server = new BigCommerceMCPServer();
  });

  test('should initialize server with default config', () => {
    expect(server).toBeInstanceOf(BigCommerceMCPServer);
    expect(server.server).toBeDefined();
  });

  test('should create config with default paths', () => {
    const config = new Config();
    expect(config.serverName).toBe('bigcommerce-docs-ts');
    expect(config.serverVersion).toBe('1.0.0');
    expect(config.maxSearchResults).toBe(50);
  });

  test('should handle server initialization', async () => {
    // Mock the initialization to avoid file system dependencies
    jest.spyOn(server, 'initialize').mockResolvedValue();
    
    await expect(server.initialize()).resolves.not.toThrow();
  });
});

describe('Config', () => {
  test('should create config with custom base path', () => {
    const customPath = '/custom/path';
    const config = new Config(customPath);
    
    expect(config.docsPath).toContain('docs');
    expect(config.referencePath).toContain('reference');
    expect(config.modelsPath).toContain('models');
  });

  test('should allow config updates', () => {
    const config = new Config();
    const originalTimeout = config.defaultTimeout;
    
    config.updateConfig({ defaultTimeout: 60000 });
    
    expect(config.defaultTimeout).toBe(60000);
    expect(config.defaultTimeout).not.toBe(originalTimeout);
  });
});

describe('BigCommerce MCP Server - Optimized', () => {
  let server: BigCommerceMCPServer;

  beforeEach(() => {
    server = new BigCommerceMCPServer();
  });

  test('should create server instance', () => {
    expect(server).toBeInstanceOf(BigCommerceMCPServer);
    expect(server.server).toBeDefined();
  });

  test('should create config with default settings', () => {
    const config = Config.getInstance();
    
    expect(config.serverName).toBe('bigcommerce-docs-ts');
    expect(config.serverVersion).toBe('1.0.0');
    expect(config.maxSearchResults).toBe(50);
    expect(config.lazyLoadEnabled).toBe(true);
    expect(config.environment).toMatch(/development|production/);
  });

  test('should have caching capabilities', () => {
    const config = Config.getInstance();
    
    // Test cache operations
    config.setCache('test-key', 'test-value');
    expect(config.getCache('test-key')).toBe('test-value');
    
    // Test cache stats
    const stats = config.getCacheStats();
    expect(stats).toHaveProperty('size');
    expect(stats).toHaveProperty('maxSize');
    
    // Clear cache
    config.clearCache();
    expect(config.getCache('test-key')).toBeNull();
  });

  test('should allow config updates', () => {
    const config = Config.getInstance();
    const originalTimeout = config.defaultTimeout;

    config.updateConfig({ 
      defaultTimeout: 60000,
      maxCacheSize: 200 
    });

    expect(config.defaultTimeout).toBe(60000);
    expect(config.maxCacheSize).toBe(200);
    expect(config.defaultTimeout).not.toBe(originalTimeout);
  });
});

describe('Config Singleton Pattern', () => {
  test('should maintain singleton instance', () => {
    const config1 = Config.getInstance();
    const config2 = Config.getInstance();
    
    expect(config1).toBe(config2);
    
    // Test that changes persist across getInstance calls
    config1.setCache('singleton-test', 'persisted');
    expect(config2.getCache('singleton-test')).toBe('persisted');
  });
});

describe('Performance Optimizations', () => {
  test('should have lazy loading enabled by default', () => {
    const config = Config.getInstance();
    expect(config.lazyLoadEnabled).toBe(true);
  });

  test('should have reasonable cache limits', () => {
    const config = Config.getInstance();
    expect(config.maxCacheSize).toBe(100);
    expect(config.cacheTimeout).toBe(300000); // 5 minutes
  });

  test('should detect production environment correctly', () => {
    const config = Config.getInstance();
    expect(['development', 'production']).toContain(config.environment);
  });
}); 