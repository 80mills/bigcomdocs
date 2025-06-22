import { OpenAPIParser } from '../parsers/openapi-parser.js';
export declare class APITools {
    private openApiParser;
    private config;
    private useCasePatterns;
    private dropshippingConfig;
    constructor(openApiParser: OpenAPIParser);
    private initializeUseCasePatterns;
    private initializeDropshippingConfig;
    searchEndpoints(query: string, method?: string, apiCategory?: string): Promise<string>;
    private formatEndpointResults;
    private groupResultsByAPI;
    getApiSpec(apiName: string): Promise<string>;
    private formatApiSpecOutput;
    private groupEndpointsByTag;
    recommendApiForUseCase(useCase: string, operationType?: string, scale?: string): Promise<string>;
    private formatRecommendationOutput;
    buildHttpRequest(apiName: string, endpointPath: string, method: string, parameters?: Record<string, any>, body?: any, authType?: string): Promise<string>;
    private formatHttpRequestOutput;
    listCategories(): Promise<string>;
    private formatCategoriesOutput;
    getEndpointDetails(apiName: string, endpointPath: string, method: string): Promise<string>;
    private formatEndpointDetailsOutput;
    healthCheck(): Promise<{
        status: string;
        parserHealth: any;
        cacheStats: any;
    }>;
}
