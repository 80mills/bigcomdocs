import { SchemaParser } from '../parsers/schema-parser.js';
export declare class SchemaTools {
    private schemaParser;
    constructor(schemaParser: SchemaParser);
    getSchema(schemaName: string): Promise<string>;
    searchSchemas(query: string): Promise<string>;
}
