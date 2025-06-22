import { MDXParser } from '../parsers/mdx-parser.js';
export declare class DocumentationTools {
    private mdxParser;
    constructor(mdxParser: MDXParser);
    searchDocumentation(query: string, section?: string, limit?: number): Promise<string>;
    getSection(sectionPath: string): Promise<string>;
    listTopics(): Promise<string>;
    getCodeExamples(topic: string, language?: string): Promise<string>;
}
