import { SchemaFile } from '../types/index.js';
export declare class SchemaParser {
    private schemas;
    private modelsPath;
    constructor(modelsPath: string);
    loadAllSchemas(): Promise<Map<string, SchemaFile>>;
    private getSchemaFiles;
    private loadSchema;
    getSchema(schemaName: string): SchemaFile | null;
    searchSchemas(query: string): SchemaFile[];
    getAllSchemas(): Map<string, SchemaFile>;
}
