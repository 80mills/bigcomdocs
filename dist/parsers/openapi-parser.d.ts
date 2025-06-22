import { ParsedAPI, ParsedEndpoint } from '../types/index.js';
export declare class OpenAPIParser {
    private specs;
    private specFiles;
    private referencePath;
    private config;
    private initialized;
    constructor(referencePath: string);
    initialize(): Promise<void>;
    private scanSpecFiles;
    loadAllSpecs(): Promise<Map<string, ParsedAPI>>;
    private loadSpec;
    private extractAPINameFromPath;
    private parseEndpoints;
    searchEndpoints(query: string, method?: string, apiCategory?: string): Promise<ParsedEndpoint[]>;
    private getRelevantSpecs;
    getSpec(apiName: string): Promise<ParsedAPI | null>;
    private loadSpecByName;
    getEndpointDetails(apiName: string, endpointPath: string, method: string): Promise<ParsedEndpoint | null>;
    listAPICategories(): Promise<Array<{
        name: string;
        title: string;
        version?: string;
        description?: string;
        endpoint_count: number;
        tags: string[];
    }>>;
    getAllSpecs(): Map<string, ParsedAPI>;
    healthCheck(): Promise<{
        initialized: boolean;
        specsLoaded: number;
        filesDiscovered: number;
        cacheStats: any;
    }>;
}
