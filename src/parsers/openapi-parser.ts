import { readFile, readdir, stat } from 'node:fs/promises';
import { join, extname, basename } from 'node:path';
import { parse } from 'yaml';
import { OpenAPISpec, ParsedAPI, ParsedEndpoint } from '../types/index.js';
import { Config } from '../config/index.js';

interface SpecFileInfo {
  path: string;
  name: string;
  lastModified: number;
}

export class OpenAPIParser {
  private specs: Map<string, ParsedAPI> = new Map();
  private specFiles: SpecFileInfo[] = [];
  private referencePath: string;
  private config: Config;
  private initialized = false;

  constructor(referencePath: string) {
    this.referencePath = referencePath;
    this.config = Config.getInstance();
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    const cacheKey = 'openapi_spec_files';
    let cachedFiles = this.config.getCache<SpecFileInfo[]>(cacheKey);

    if (!cachedFiles) {
      cachedFiles = await this.scanSpecFiles();
      this.config.setCache(cacheKey, cachedFiles);
    }

    this.specFiles = cachedFiles;
    this.initialized = true;
  }

  private async scanSpecFiles(): Promise<SpecFileInfo[]> {
    try {
      const files = await readdir(this.referencePath, { recursive: true });
      const specFiles: SpecFileInfo[] = [];

      for (const file of files) {
        const ext = extname(file).toLowerCase();
        if (ext === '.yaml' || ext === '.yml' || ext === '.json') {
          const fullPath = join(this.referencePath, file);
          try {
            const stats = await stat(fullPath);
            const name = this.extractAPINameFromPath(fullPath);
            specFiles.push({
              path: fullPath,
              name,
              lastModified: stats.mtime.getTime()
            });
          } catch (error) {
            console.warn(`Failed to stat file ${fullPath}:`, error);
          }
        }
      }

      return specFiles;
    } catch (error) {
      console.error('Error scanning spec files:', error);
      return [];
    }
  }

  async loadAllSpecs(): Promise<Map<string, ParsedAPI>> {
    await this.initialize();

    if (this.config.lazyLoadEnabled) {
      // In lazy loading mode, just return empty map and load on demand
      console.log(`Discovered ${this.specFiles.length} OpenAPI specifications (lazy loading enabled)`);
      return this.specs;
    }

    // Eagerly load all specs (for development or when explicitly requested)
    const loadPromises = this.specFiles.map(async (fileInfo) => {
      try {
        const spec = await this.loadSpec(fileInfo.path);
        if (spec) {
          this.specs.set(spec.name, spec);
        }
      } catch (error) {
        console.warn(`Failed to load spec ${fileInfo.path}:`, error);
      }
    });

    await Promise.all(loadPromises);
    console.log(`Loaded ${this.specs.size} OpenAPI specifications`);
    return this.specs;
  }

  private async loadSpec(filePath: string): Promise<ParsedAPI | null> {
    const cacheKey = `openapi_spec_${filePath}`;
    let spec = this.config.getCache<ParsedAPI>(cacheKey);

    if (spec) {
      return spec;
    }

    try {
      const content = await readFile(filePath, 'utf-8');
      const ext = extname(filePath).toLowerCase();
      
      let openApiSpec: OpenAPISpec;
      if (ext === '.json') {
        openApiSpec = JSON.parse(content);
      } else {
        openApiSpec = parse(content);
      }

      if (!openApiSpec.openapi && !openApiSpec.swagger) {
        return null; // Not an OpenAPI spec
      }

      const name = this.extractAPINameFromPath(filePath);
      const endpoints = this.parseEndpoints(openApiSpec, name);
      const schemas = openApiSpec.components?.schemas || {};

      spec = {
        name,
        spec: openApiSpec,
        endpoints,
        schemas,
      };

      // Cache the parsed spec
      this.config.setCache(cacheKey, spec);
      return spec;
    } catch (error) {
      console.error(`Error parsing spec ${filePath}:`, error);
      return null;
    }
  }

  private extractAPINameFromPath(filePath: string): string {
    const filename = basename(filePath, extname(filePath));
    
    // Remove common suffixes and clean up
    const cleanName = filename
      .replace(/\.(v\d+|api|spec)$/, '')
      .replace(/_/g, '-')
      .toLowerCase();

    return cleanName;
  }

  private parseEndpoints(spec: OpenAPISpec, apiName: string): ParsedEndpoint[] {
    const endpoints: ParsedEndpoint[] = [];

    for (const [path, pathItem] of Object.entries(spec.paths || {})) {
      for (const [method, operation] of Object.entries(pathItem)) {
        if (['get', 'post', 'put', 'patch', 'delete', 'options', 'head'].includes(method) && typeof operation === 'object' && operation !== null) {
          const op = operation as any;
          endpoints.push({
            api_name: apiName,
            path,
            method: method.toUpperCase(),
            summary: op.summary,
            description: op.description,
            operation_id: op.operationId,
            tags: op.tags || [],
            parameters: op.parameters || [],
            request_body: op.requestBody,
            responses: op.responses || {},
            security: op.security,
          });
        }
      }
    }

    return endpoints;
  }

  async searchEndpoints(query: string, method?: string, apiCategory?: string): Promise<ParsedEndpoint[]> {
    await this.initialize();

    const cacheKey = `search_${query}_${method || 'all'}_${apiCategory || 'all'}`;
    let results = this.config.getCache<ParsedEndpoint[]>(cacheKey);

    if (results) {
      return results;
    }

    results = [];
    const queryLower = query.toLowerCase();

    // Load specs on demand if using lazy loading
    const specsToSearch = await this.getRelevantSpecs(apiCategory);

    for (const api of specsToSearch) {
      for (const endpoint of api.endpoints) {
        if (method && endpoint.method !== method.toUpperCase()) {
          continue;
        }

        const matches = [
          endpoint.path.toLowerCase().includes(queryLower),
          endpoint.summary?.toLowerCase().includes(queryLower),
          endpoint.description?.toLowerCase().includes(queryLower),
          endpoint.tags?.some(tag => tag.toLowerCase().includes(queryLower)),
        ].some(Boolean);

        if (matches) {
          results.push(endpoint);
        }
      }
    }

    results = results.slice(0, this.config.maxSearchResults);
    
    // Cache results for 2 minutes (shorter than spec cache)
    this.config.setCache(cacheKey, results, 120000);
    
    return results;
  }

  private async getRelevantSpecs(apiCategory?: string): Promise<ParsedAPI[]> {
    const specs: ParsedAPI[] = [];

    if (apiCategory) {
      // Load only relevant specs
      const relevantFiles = this.specFiles.filter(file => 
        file.name.includes(apiCategory.toLowerCase())
      );

      for (const fileInfo of relevantFiles) {
        const spec = await this.loadSpecByName(fileInfo.name);
        if (spec) specs.push(spec);
      }
    } else {
      // Load all specs (but intelligently)
      for (const fileInfo of this.specFiles) {
        const spec = await this.loadSpecByName(fileInfo.name);
        if (spec) specs.push(spec);
      }
    }

    return specs;
  }

  async getSpec(apiName: string): Promise<ParsedAPI | null> {
    await this.initialize();
    return await this.loadSpecByName(apiName);
  }

  private async loadSpecByName(apiName: string): Promise<ParsedAPI | null> {
    // Check if already loaded
    if (this.specs.has(apiName)) {
      return this.specs.get(apiName)!;
    }

    // Find the spec file
    const fileInfo = this.specFiles.find(f => f.name === apiName);
    if (!fileInfo) {
      return null;
    }

    const spec = await this.loadSpec(fileInfo.path);
    if (spec) {
      this.specs.set(apiName, spec);
    }

    return spec;
  }

  async getEndpointDetails(apiName: string, endpointPath: string, method: string): Promise<ParsedEndpoint | null> {
    const api = await this.getSpec(apiName);
    if (!api) return null;

    return api.endpoints.find(
      endpoint => 
        endpoint.path === endpointPath && 
        endpoint.method === method.toUpperCase()
    ) || null;
  }

  async listAPICategories(): Promise<Array<{
    name: string;
    title: string;
    version?: string;
    description?: string;
    endpoint_count: number;
    tags: string[];
  }>> {
    await this.initialize();

    const cacheKey = 'api_categories';
    let categories = this.config.getCache<Array<any>>(cacheKey);

    if (categories) {
      return categories;
    }

    // Load minimal spec info for categories (don't load full endpoints)
    categories = [];
    
    for (const fileInfo of this.specFiles) {
      try {
        const spec = await this.loadSpec(fileInfo.path);
        if (spec) {
          categories.push({
            name: spec.name,
            title: spec.spec.info.title || spec.name,
            version: spec.spec.info.version,
            description: spec.spec.info.description,
            endpoint_count: spec.endpoints.length,
            tags: [...new Set(spec.endpoints.flatMap(e => e.tags || []))],
          });
        }
      } catch (error) {
        console.warn(`Failed to load spec for category listing: ${fileInfo.path}`, error);
      }
    }

    this.config.setCache(cacheKey, categories);
    return categories;
  }

  getAllSpecs(): Map<string, ParsedAPI> {
    return this.specs;
  }

  // Health check method
  async healthCheck(): Promise<{ 
    initialized: boolean; 
    specsLoaded: number; 
    filesDiscovered: number;
    cacheStats: any;
  }> {
    await this.initialize();
    
    return {
      initialized: this.initialized,
      specsLoaded: this.specs.size,
      filesDiscovered: this.specFiles.length,
      cacheStats: this.config.getCacheStats(),
    };
  }
} 