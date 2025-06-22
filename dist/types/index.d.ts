export interface OpenAPISpec {
    openapi?: string;
    swagger?: string;
    info: {
        title: string;
        version: string;
        description?: string;
    };
    servers?: Array<{
        url: string;
        description?: string;
    }>;
    paths: Record<string, any>;
    components?: {
        schemas?: Record<string, any>;
        securitySchemes?: Record<string, any>;
    };
    security?: Array<Record<string, any>>;
    tags?: Array<{
        name: string;
        description?: string;
    }>;
}
export interface ParsedEndpoint {
    api_name: string;
    path: string;
    method: string;
    summary?: string;
    description?: string;
    operation_id?: string;
    tags?: string[];
    parameters?: Array<{
        name: string;
        in: string;
        required?: boolean;
        description?: string;
        schema?: any;
    }>;
    request_body?: {
        description?: string;
        content?: Record<string, any>;
        required?: boolean;
    };
    responses?: Record<string, any>;
    security?: Array<Record<string, any>>;
}
export interface ParsedAPI {
    name: string;
    spec: OpenAPISpec;
    endpoints: ParsedEndpoint[];
    schemas: Record<string, any>;
}
export interface DocumentationFile {
    path: string;
    title: string;
    content: string;
    frontmatter: Record<string, any>;
    sections: Array<{
        title: string;
        content: string;
        level: number;
    }>;
}
export interface SchemaFile {
    path: string;
    name: string;
    schema: any;
}
export interface UseCasePattern {
    keywords: string[];
    apis: string[];
    endpoints: string[];
    methods: string[];
    description: string;
}
export interface DropshippingConfig {
    pricing_strategy: {
        primary: string;
        fallback: string;
        cost_plus_minimum: number;
        map_compliance: boolean;
        competitive_factor: number;
        margin_requirements: {
            minimum: number;
            target: number;
            maximum_discount: number;
        };
    };
    inventory_sync: {
        update_frequency: number;
        buffer_stock: number;
        max_quantity_display: number;
        stockout_threshold: number;
        sync_tolerance: number;
    };
    product_management: {
        auto_enable_disable: boolean;
        visibility_rules: {
            min_stock: number;
            valid_pricing: boolean;
            supplier_active: boolean;
        };
        bulk_operation_size: number;
        rate_limit_buffer: number;
    };
    order_processing: {
        auto_status_updates: boolean;
        tracking_sync: boolean;
        inventory_adjustment: boolean;
        notification_triggers: string[];
    };
}
export interface SearchResult {
    item: any;
    score: number;
    matches: Array<{
        indices: [number, number][];
        value: string;
        key: string;
    }>;
}
export interface APIRecommendation {
    pattern: string;
    pattern_data: UseCasePattern;
    score: number;
}
export interface HTTPRequestConfig {
    url: string;
    method: string;
    headers: Record<string, string>;
    params?: Record<string, any>;
    body?: any;
}
export interface CodeExample {
    language: string;
    code: string;
    description?: string;
}
