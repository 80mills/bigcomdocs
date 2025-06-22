import { DocumentationFile } from '../types/index.js';
export declare class MDXParser {
    private docs;
    private docsPath;
    constructor(docsPath: string);
    loadAllDocs(): Promise<Map<string, DocumentationFile>>;
    private getDocFiles;
    private loadDoc;
    private parseSections;
    private extractTitleFromContent;
    searchDocs(query: string, section?: string, limit?: number): DocumentationFile[];
    getSection(sectionPath: string): DocumentationFile | null;
    listTopics(): Array<{
        path: string;
        title: string;
        description?: string;
    }>;
    getCodeExamples(topic: string, language?: string): Array<{
        code: string;
        language: string;
        description?: string;
    }>;
    getAllDocs(): Map<string, DocumentationFile>;
}
