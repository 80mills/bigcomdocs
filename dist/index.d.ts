import { Server } from '@modelcontextprotocol/sdk/server/index.js';
export declare class BigCommerceMCPServer {
    server: Server;
    private config;
    private openApiParser?;
    private mdxParser?;
    private schemaParser?;
    private apiTools?;
    private documentationTools?;
    private schemaTools?;
    private initialized;
    constructor(basePath?: string);
    private initializeParsers;
    private setupHandlers;
    private getHealthStatus;
    initialize(): Promise<void>;
    run(): Promise<void>;
    shutdown(): Promise<void>;
}
export default function handler(req: any, res: any): Promise<void>;
