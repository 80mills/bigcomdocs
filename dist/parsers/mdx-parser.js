import { readFile, readdir, stat } from 'node:fs/promises';
import { join, extname, relative } from 'node:path';
import matter from 'gray-matter';
export class MDXParser {
    docs = new Map();
    docsPath;
    constructor(docsPath) {
        this.docsPath = docsPath;
    }
    async loadAllDocs() {
        try {
            const files = await this.getDocFiles();
            for (const file of files) {
                try {
                    const doc = await this.loadDoc(file);
                    if (doc) {
                        const relativePath = relative(this.docsPath, file);
                        this.docs.set(relativePath, doc);
                    }
                }
                catch (error) {
                    console.warn(`Failed to load doc ${file}:`, error);
                }
            }
            console.log(`Loaded ${this.docs.size} documentation files`);
            return this.docs;
        }
        catch (error) {
            console.error('Error loading documentation:', error);
            return new Map();
        }
    }
    async getDocFiles() {
        const files = [];
        const scanDirectory = async (dir) => {
            try {
                const items = await readdir(dir);
                for (const item of items) {
                    const fullPath = join(dir, item);
                    const stats = await stat(fullPath);
                    if (stats.isDirectory()) {
                        await scanDirectory(fullPath);
                    }
                    else if (stats.isFile()) {
                        const ext = extname(item).toLowerCase();
                        if (ext === '.mdx' || ext === '.md') {
                            files.push(fullPath);
                        }
                    }
                }
            }
            catch (error) {
                console.warn(`Error scanning directory ${dir}:`, error);
            }
        };
        await scanDirectory(this.docsPath);
        return files;
    }
    async loadDoc(filePath) {
        try {
            const content = await readFile(filePath, 'utf-8');
            const { data: frontmatter, content: markdown } = matter(content);
            const sections = this.parseSections(markdown);
            const title = frontmatter.title || this.extractTitleFromContent(markdown) || 'Untitled';
            return {
                path: filePath,
                title,
                content: markdown,
                frontmatter,
                sections,
            };
        }
        catch (error) {
            console.error(`Error parsing doc ${filePath}:`, error);
            return null;
        }
    }
    parseSections(content) {
        const sections = [];
        const lines = content.split('\n');
        let currentSection = null;
        for (const line of lines) {
            const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
            if (headerMatch) {
                // Save previous section
                if (currentSection) {
                    sections.push(currentSection);
                }
                // Start new section
                currentSection = {
                    title: headerMatch[2].trim(),
                    content: '',
                    level: headerMatch[1].length,
                };
            }
            else if (currentSection) {
                currentSection.content += line + '\n';
            }
        }
        // Add the last section
        if (currentSection) {
            sections.push(currentSection);
        }
        return sections;
    }
    extractTitleFromContent(content) {
        const titleMatch = content.match(/^#\s+(.+)$/m);
        return titleMatch ? titleMatch[1].trim() : null;
    }
    searchDocs(query, section, limit = 10) {
        const results = [];
        const queryLower = query.toLowerCase();
        for (const [path, doc] of this.docs) {
            if (section && !path.includes(section)) {
                continue;
            }
            let score = 0;
            // Title match (highest weight)
            if (doc.title.toLowerCase().includes(queryLower)) {
                score += 10;
            }
            // Content match
            const contentMatches = (doc.content.toLowerCase().match(new RegExp(queryLower, 'g')) || []).length;
            score += contentMatches;
            // Section title matches
            for (const docSection of doc.sections) {
                if (docSection.title.toLowerCase().includes(queryLower)) {
                    score += 5;
                }
            }
            // Frontmatter matches
            const frontmatterText = JSON.stringify(doc.frontmatter).toLowerCase();
            if (frontmatterText.includes(queryLower)) {
                score += 2;
            }
            if (score > 0) {
                results.push({ doc, score });
            }
        }
        return results
            .sort((a, b) => b.score - a.score)
            .slice(0, limit)
            .map(r => r.doc);
    }
    getSection(sectionPath) {
        return this.docs.get(sectionPath) || null;
    }
    listTopics() {
        return Array.from(this.docs.entries()).map(([path, doc]) => ({
            path,
            title: doc.title,
            description: doc.frontmatter.description || doc.sections[0]?.content?.substring(0, 150),
        }));
    }
    getCodeExamples(topic, language) {
        const examples = [];
        const topicLower = topic.toLowerCase();
        for (const doc of this.docs.values()) {
            if (!doc.title.toLowerCase().includes(topicLower) &&
                !doc.content.toLowerCase().includes(topicLower)) {
                continue;
            }
            // Extract code blocks
            const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
            let match;
            while ((match = codeBlockRegex.exec(doc.content)) !== null) {
                const blockLanguage = match[1] || 'text';
                const code = match[2].trim();
                if (!language || blockLanguage.toLowerCase().includes(language.toLowerCase())) {
                    examples.push({
                        code,
                        language: blockLanguage,
                        description: `From ${doc.title}`,
                    });
                }
            }
        }
        return examples.slice(0, 20); // Limit results
    }
    getAllDocs() {
        return this.docs;
    }
}
