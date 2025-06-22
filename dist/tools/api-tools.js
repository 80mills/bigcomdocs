import { Config } from '../config/index.js';
export class APITools {
    openApiParser;
    config;
    useCasePatterns = new Map();
    dropshippingConfig;
    constructor(openApiParser) {
        this.openApiParser = openApiParser;
        this.config = Config.getInstance();
        this.initializeUseCasePatterns();
        this.initializeDropshippingConfig();
    }
    initializeUseCasePatterns() {
        const patterns = {
            product_queries: {
                keywords: ['products', 'catalog', 'items', 'goods', 'merchandise'],
                apis: ['catalog', 'products_catalog'],
                endpoints: ['/catalog/products', '/catalog/products/{product_id}'],
                methods: ['GET'],
                description: 'Query and retrieve product information'
            },
            product_updates: {
                keywords: ['update products', 'modify products', 'edit products', 'change products'],
                apis: ['catalog', 'products_catalog'],
                endpoints: ['/catalog/products/{product_id}'],
                methods: ['PUT', 'PATCH'],
                description: 'Update existing product information'
            },
            bulk_inventory_operations: {
                keywords: ['bulk inventory', 'batch inventory', 'mass inventory', 'hundreds inventory'],
                apis: ['inventory'],
                endpoints: ['/inventory/batch'],
                methods: ['POST', 'PUT'],
                description: 'Update inventory for multiple products'
            },
            order_queries: {
                keywords: ['orders', 'purchases', 'transactions'],
                apis: ['orders'],
                endpoints: ['/orders', '/orders/{order_id}'],
                methods: ['GET'],
                description: 'Query order information'
            },
            customer_management: {
                keywords: ['customers', 'users', 'accounts', 'customer data'],
                apis: ['customers'],
                endpoints: ['/customers', '/customers/{customer_id}'],
                methods: ['GET', 'POST', 'PUT'],
                description: 'Manage customer information and accounts'
            }
        };
        for (const [key, pattern] of Object.entries(patterns)) {
            this.useCasePatterns.set(key, pattern);
        }
    }
    initializeDropshippingConfig() {
        this.dropshippingConfig = {
            pricing_strategy: {
                primary: 'MAP',
                fallback: 'MSRP',
                cost_plus_minimum: 0.15,
                map_compliance: true,
                competitive_factor: 0.95,
                margin_requirements: {
                    minimum: 0.10,
                    target: 0.25,
                    maximum_discount: 0.30
                }
            },
            inventory_sync: {
                update_frequency: 300,
                buffer_stock: 2,
                max_quantity_display: 10,
                stockout_threshold: 1,
                sync_tolerance: 0.1
            },
            product_management: {
                auto_enable_disable: true,
                visibility_rules: {
                    min_stock: 1,
                    valid_pricing: true,
                    supplier_active: true
                },
                bulk_operation_size: 100,
                rate_limit_buffer: 0.8
            },
            order_processing: {
                auto_status_updates: true,
                tracking_sync: true,
                inventory_adjustment: true,
                notification_triggers: ['order_created', 'payment_received', 'shipped']
            }
        };
    }
    async searchEndpoints(query, method, apiCategory) {
        try {
            const cacheKey = `search_endpoints_${query}_${method || 'all'}_${apiCategory || 'all'}`;
            let cachedResult = this.config.getCache(cacheKey);
            if (cachedResult) {
                return cachedResult;
            }
            const results = await this.openApiParser.searchEndpoints(query, method, apiCategory);
            if (results.length === 0) {
                const result = `No endpoints found matching query: '${query}'`;
                this.config.setCache(cacheKey, result, 60000); // Cache for 1 minute
                return result;
            }
            const output = this.formatEndpointResults(results, query);
            this.config.setCache(cacheKey, output, 120000); // Cache for 2 minutes
            return output;
        }
        catch (error) {
            const errorMsg = `Error searching endpoints: ${error instanceof Error ? error.message : String(error)}`;
            console.error(errorMsg, error);
            return errorMsg;
        }
    }
    formatEndpointResults(results, query) {
        const output = [`Found ${results.length} endpoint(s) matching '${query}':\n`];
        // Group by API for better organization
        const groupedResults = this.groupResultsByAPI(results);
        for (const [apiName, endpoints] of groupedResults) {
            output.push(`## ${apiName.toUpperCase()} API`);
            for (const result of endpoints.slice(0, 5)) { // Limit per API
                output.push(`**${result.method} ${result.path}**`);
                if (result.summary) {
                    output.push(`Summary: ${result.summary}`);
                }
                if (result.description) {
                    const desc = result.description.length > 200
                        ? result.description.substring(0, 200) + "..."
                        : result.description;
                    output.push(`Description: ${desc}`);
                }
                if (result.tags?.length) {
                    output.push(`Tags: ${result.tags.join(', ')}`);
                }
                output.push("");
            }
            if (endpoints.length > 5) {
                output.push(`... and ${endpoints.length - 5} more endpoints in ${apiName}\n`);
            }
        }
        return output.join('\n');
    }
    groupResultsByAPI(results) {
        const grouped = new Map();
        for (const result of results) {
            const apiName = result.api_name;
            if (!grouped.has(apiName)) {
                grouped.set(apiName, []);
            }
            grouped.get(apiName).push(result);
        }
        return grouped;
    }
    async getApiSpec(apiName) {
        try {
            const cacheKey = `api_spec_${apiName}`;
            let cachedResult = this.config.getCache(cacheKey);
            if (cachedResult) {
                return cachedResult;
            }
            const specData = await this.openApiParser.getSpec(apiName);
            if (!specData) {
                const categories = await this.openApiParser.listAPICategories();
                const availableApis = categories.map(cat => cat.name);
                const result = `API '${apiName}' not found. Available APIs: ${availableApis.join(', ')}`;
                this.config.setCache(cacheKey, result, 60000);
                return result;
            }
            const output = this.formatApiSpecOutput(specData);
            this.config.setCache(cacheKey, output);
            return output;
        }
        catch (error) {
            const errorMsg = `Error getting API spec: ${error instanceof Error ? error.message : String(error)}`;
            console.error(errorMsg, error);
            return errorMsg;
        }
    }
    formatApiSpecOutput(specData) {
        const spec = specData.spec;
        const info = spec.info;
        const output = [`# ${info.title || specData.name} API Specification\n`];
        if (info.version) {
            output.push(`**Version:** ${info.version}`);
        }
        if (info.description) {
            output.push(`**Description:** ${info.description}`);
        }
        if (spec.servers?.length) {
            output.push(`**Base URL:** ${spec.servers[0].url || 'N/A'}`);
        }
        const endpoints = specData.endpoints;
        if (endpoints.length > 0) {
            output.push(`\n## Endpoints (${endpoints.length} total)`);
            const endpointsByTag = this.groupEndpointsByTag(endpoints);
            for (const [tag, tagEndpoints] of Object.entries(endpointsByTag)) {
                output.push(`\n### ${tag}`);
                for (const endpoint of tagEndpoints.slice(0, 5)) {
                    output.push(`- **${endpoint.method} ${endpoint.path}** - ${endpoint.summary || 'No summary'}`);
                }
                if (tagEndpoints.length > 5) {
                    output.push(`  ... and ${tagEndpoints.length - 5} more endpoints`);
                }
            }
        }
        return output.join('\n');
    }
    groupEndpointsByTag(endpoints) {
        const endpointsByTag = {};
        for (const endpoint of endpoints) {
            const tags = endpoint.tags?.length ? endpoint.tags : ['Untagged'];
            for (const tag of tags) {
                if (!endpointsByTag[tag]) {
                    endpointsByTag[tag] = [];
                }
                endpointsByTag[tag].push(endpoint);
            }
        }
        return endpointsByTag;
    }
    async recommendApiForUseCase(useCase, operationType, scale) {
        try {
            const cacheKey = `recommend_${useCase}_${operationType || 'all'}_${scale || 'all'}`;
            let cachedResult = this.config.getCache(cacheKey);
            if (cachedResult) {
                return cachedResult;
            }
            const useCaseLower = useCase.toLowerCase();
            const matches = [];
            for (const [patternName, pattern] of this.useCasePatterns) {
                let score = 0;
                for (const keyword of pattern.keywords) {
                    if (useCaseLower.includes(keyword)) {
                        score += 1;
                    }
                }
                if (score > 0) {
                    matches.push({ pattern: patternName, pattern_data: pattern, score });
                }
            }
            matches.sort((a, b) => b.score - a.score);
            if (matches.length === 0) {
                const result = `No specific API recommendation found for: '${useCase}'. Try searching for specific endpoints or APIs.`;
                this.config.setCache(cacheKey, result, 300000); // Cache for 5 minutes
                return result;
            }
            const output = await this.formatRecommendationOutput(matches[0], useCase, useCaseLower);
            this.config.setCache(cacheKey, output);
            return output;
        }
        catch (error) {
            const errorMsg = `Error recommending API: ${error instanceof Error ? error.message : String(error)}`;
            console.error(errorMsg, error);
            return errorMsg;
        }
    }
    async formatRecommendationOutput(bestMatch, useCase, useCaseLower) {
        const pattern = bestMatch.pattern_data;
        const output = [`# API Recommendation for: ${useCase}\n`];
        output.push(`**Recommended Pattern:** ${bestMatch.pattern}`);
        output.push(`**Description:** ${pattern.description}`);
        const isBulk = ['bulk', 'batch', 'mass', 'hundreds', 'thousands', 'multiple'].some(word => useCaseLower.includes(word));
        if (isBulk) {
            output.push("\n## ⚠️ Bulk Operation Detected");
            output.push("For operations on hundreds or thousands of items, consider:");
            output.push("- Using batch endpoints when available");
            output.push("- Implementing rate limiting");
            output.push("- Using webhooks for status updates");
        }
        output.push("\n## Recommended APIs");
        for (const apiName of pattern.apis) {
            try {
                const apiData = await this.openApiParser.getSpec(apiName);
                if (apiData) {
                    const spec = apiData.spec;
                    const info = spec.info;
                    output.push(`### ${info.title || apiName}`);
                    output.push(`**API Name:** ${apiName}`);
                    if (info.description) {
                        const desc = info.description.length > 200
                            ? info.description.substring(0, 200) + "..."
                            : info.description;
                        output.push(`**Description:** ${desc}`);
                    }
                    const relevantEndpoints = apiData.endpoints.filter(endpoint => pattern.methods.includes(endpoint.method) &&
                        pattern.endpoints.some(patternEndpoint => endpoint.path.includes(patternEndpoint)));
                    if (relevantEndpoints.length > 0) {
                        output.push("**Relevant Endpoints:**");
                        for (const endpoint of relevantEndpoints.slice(0, 3)) {
                            output.push(`- **${endpoint.method} ${endpoint.path}**`);
                            if (endpoint.summary) {
                                output.push(`  ${endpoint.summary}`);
                            }
                        }
                    }
                }
            }
            catch (error) {
                console.warn(`Failed to load API ${apiName} for recommendation:`, error);
            }
        }
        return output.join('\n');
    }
    async buildHttpRequest(apiName, endpointPath, method, parameters, body, authType = "bearer") {
        try {
            const cacheKey = `http_request_${apiName}_${endpointPath}_${method}_${authType}`;
            let cachedResult = this.config.getCache(cacheKey);
            if (cachedResult && !parameters && !body) {
                return cachedResult;
            }
            const endpoint = await this.openApiParser.getEndpointDetails(apiName, endpointPath, method);
            if (!endpoint) {
                return `Endpoint not found: ${method} ${endpointPath} in ${apiName} API`;
            }
            const output = this.formatHttpRequestOutput(endpoint, endpointPath, method, parameters, body, authType);
            // Only cache if no dynamic parameters/body
            if (!parameters && !body) {
                this.config.setCache(cacheKey, output);
            }
            return output;
        }
        catch (error) {
            const errorMsg = `Error building HTTP request: ${error instanceof Error ? error.message : String(error)}`;
            console.error(errorMsg, error);
            return errorMsg;
        }
    }
    formatHttpRequestOutput(endpoint, endpointPath, method, parameters, body, authType = "bearer") {
        const baseUrl = "https://api.bigcommerce.com/stores/{store_hash}";
        const fullUrl = `${baseUrl}${endpointPath}`;
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        if (authType === 'bearer') {
            headers['X-Auth-Token'] = '{your_access_token}';
        }
        const config = {
            url: fullUrl,
            method: method.toUpperCase(),
            headers,
            params: parameters,
            body
        };
        const output = [`# HTTP Request for ${method.toUpperCase()} ${endpointPath}\n`];
        // cURL example
        output.push("## cURL Example");
        output.push("```bash");
        let curlCmd = `curl -X ${config.method} "${config.url}"`;
        for (const [key, value] of Object.entries(config.headers)) {
            curlCmd += ` \\\n  -H "${key}: ${value}"`;
        }
        if (config.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            curlCmd += ` \\\n  -d '${JSON.stringify(config.body, null, 2)}'`;
        }
        output.push(curlCmd);
        output.push("```\n");
        // JavaScript example
        output.push("## JavaScript (fetch) Example");
        output.push("```javascript");
        output.push(`const response = await fetch('${config.url}', {`);
        output.push(`  method: '${config.method}',`);
        output.push(`  headers: ${JSON.stringify(config.headers, null, 4)},`);
        if (config.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            output.push(`  body: JSON.stringify(${JSON.stringify(config.body, null, 4)})`);
        }
        output.push("});");
        output.push("const data = await response.json();");
        output.push("console.log(data);");
        output.push("```\n");
        // Python example
        output.push("## Python (requests) Example");
        output.push("```python");
        output.push("import requests");
        output.push("import json");
        output.push("");
        output.push(`url = "${config.url}"`);
        output.push(`headers = ${JSON.stringify(config.headers, null, 4).replace(/"/g, "'")}`);
        if (config.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            output.push(`data = ${JSON.stringify(config.body, null, 4).replace(/"/g, "'")}`);
            output.push(`response = requests.${config.method.toLowerCase()}(url, headers=headers, json=data)`);
        }
        else {
            output.push(`response = requests.${config.method.toLowerCase()}(url, headers=headers)`);
        }
        output.push("print(response.json())");
        output.push("```\n");
        // Parameters documentation
        if (endpoint.parameters?.length) {
            output.push("## Parameters");
            for (const param of endpoint.parameters) {
                const required = param.required ? " (required)" : " (optional)";
                output.push(`- **${param.name}** (${param.in})${required}: ${param.description || 'No description'}`);
            }
            output.push("");
        }
        return output.join('\n');
    }
    async listCategories() {
        try {
            const cacheKey = 'list_categories';
            let cachedResult = this.config.getCache(cacheKey);
            if (cachedResult) {
                return cachedResult;
            }
            const categories = await this.openApiParser.listAPICategories();
            if (categories.length === 0) {
                const result = "No API categories found";
                this.config.setCache(cacheKey, result, 300000);
                return result;
            }
            const output = this.formatCategoriesOutput(categories);
            this.config.setCache(cacheKey, output);
            return output;
        }
        catch (error) {
            const errorMsg = `Error listing categories: ${error instanceof Error ? error.message : String(error)}`;
            console.error(errorMsg, error);
            return errorMsg;
        }
    }
    formatCategoriesOutput(categories) {
        const output = [`# BigCommerce API Categories (${categories.length} total)\n`];
        for (const category of categories) {
            output.push(`## ${category.title}`);
            output.push(`**Name:** ${category.name}`);
            if (category.version) {
                output.push(`**Version:** ${category.version}`);
            }
            output.push(`**Endpoints:** ${category.endpoint_count}`);
            if (category.description) {
                const desc = category.description.length > 150
                    ? category.description.substring(0, 150) + "..."
                    : category.description;
                output.push(`**Description:** ${desc}`);
            }
            if (category.tags.length > 0) {
                output.push(`**Tags:** ${category.tags.slice(0, 5).join(', ')}`);
            }
            output.push("");
        }
        return output.join('\n');
    }
    async getEndpointDetails(apiName, endpointPath, method) {
        try {
            const cacheKey = `endpoint_details_${apiName}_${endpointPath}_${method}`;
            let cachedResult = this.config.getCache(cacheKey);
            if (cachedResult) {
                return cachedResult;
            }
            const endpoint = await this.openApiParser.getEndpointDetails(apiName, endpointPath, method);
            if (!endpoint) {
                const result = `Endpoint not found: ${method} ${endpointPath} in ${apiName} API`;
                this.config.setCache(cacheKey, result, 300000);
                return result;
            }
            const output = this.formatEndpointDetailsOutput(endpoint);
            this.config.setCache(cacheKey, output);
            return output;
        }
        catch (error) {
            const errorMsg = `Error getting endpoint details: ${error instanceof Error ? error.message : String(error)}`;
            console.error(errorMsg, error);
            return errorMsg;
        }
    }
    formatEndpointDetailsOutput(endpoint) {
        const output = [`# ${endpoint.method.toUpperCase()} ${endpoint.path}\n`];
        output.push(`**API:** ${endpoint.api_name.toUpperCase()}`);
        if (endpoint.summary) {
            output.push(`**Summary:** ${endpoint.summary}`);
        }
        if (endpoint.description) {
            output.push(`**Description:** ${endpoint.description}`);
        }
        if (endpoint.operation_id) {
            output.push(`**Operation ID:** ${endpoint.operation_id}`);
        }
        if (endpoint.tags?.length) {
            output.push(`**Tags:** ${endpoint.tags.join(', ')}`);
        }
        if (endpoint.parameters?.length) {
            output.push("\n## Parameters");
            for (const param of endpoint.parameters) {
                const paramType = param.in || 'unknown';
                const paramName = param.name || 'unnamed';
                const paramDesc = param.description || 'No description';
                const required = param.required ? " (required)" : " (optional)";
                output.push(`- **${paramName}** (${paramType})${required}: ${paramDesc}`);
            }
        }
        if (endpoint.request_body) {
            output.push("\n## Request Body");
            if (endpoint.request_body.description) {
                output.push(endpoint.request_body.description);
            }
            if (endpoint.request_body.content) {
                const contentTypes = Object.keys(endpoint.request_body.content);
                if (contentTypes.length > 0) {
                    output.push(`**Content-Type:** ${contentTypes[0]}`);
                }
            }
        }
        if (endpoint.responses && Object.keys(endpoint.responses).length > 0) {
            output.push("\n## Responses");
            for (const [statusCode, response] of Object.entries(endpoint.responses)) {
                const desc = response?.description || 'No description';
                output.push(`- **${statusCode}:** ${desc}`);
            }
        }
        return output.join('\n');
    }
    // Health check for API tools
    async healthCheck() {
        try {
            const parserHealth = await this.openApiParser.healthCheck();
            const cacheStats = this.config.getCacheStats();
            return {
                status: 'healthy',
                parserHealth,
                cacheStats
            };
        }
        catch (error) {
            return {
                status: 'unhealthy',
                parserHealth: null,
                cacheStats: this.config.getCacheStats()
            };
        }
    }
}
