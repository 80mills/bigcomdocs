export class DocumentationTools {
    mdxParser;
    constructor(mdxParser) {
        this.mdxParser = mdxParser;
    }
    async searchDocumentation(query, section, limit = 10) {
        try {
            const results = this.mdxParser.searchDocs(query, section, limit);
            if (results.length === 0) {
                return `No documentation found matching query: '${query}'`;
            }
            const output = [`Found ${results.length} documentation result(s) for '${query}':\n`];
            for (const doc of results) {
                output.push(`## ${doc.title}`);
                output.push(`**Path:** ${doc.path}`);
                if (doc.frontmatter.description) {
                    output.push(`**Description:** ${doc.frontmatter.description}`);
                }
                // Show first section content as preview
                if (doc.sections.length > 0) {
                    const firstSection = doc.sections[0];
                    const preview = firstSection.content.substring(0, 200);
                    output.push(`**Preview:** ${preview}${firstSection.content.length > 200 ? '...' : ''}`);
                }
                if (doc.frontmatter.tags) {
                    const tags = Array.isArray(doc.frontmatter.tags)
                        ? doc.frontmatter.tags.join(', ')
                        : doc.frontmatter.tags;
                    output.push(`**Tags:** ${tags}`);
                }
                output.push("");
            }
            return output.join('\n');
        }
        catch (error) {
            return `Error searching documentation: ${error}`;
        }
    }
    async getSection(sectionPath) {
        try {
            const doc = this.mdxParser.getSection(sectionPath);
            if (!doc) {
                const availableDocs = this.mdxParser.listTopics();
                const paths = availableDocs.slice(0, 10).map(d => d.path).join(', ');
                return `Documentation section '${sectionPath}' not found. Available sections include: ${paths}`;
            }
            const output = [`# ${doc.title}\n`];
            if (doc.frontmatter.description) {
                output.push(`**Description:** ${doc.frontmatter.description}\n`);
            }
            if (doc.frontmatter.tags) {
                const tags = Array.isArray(doc.frontmatter.tags)
                    ? doc.frontmatter.tags.join(', ')
                    : doc.frontmatter.tags;
                output.push(`**Tags:** ${tags}\n`);
            }
            // Add table of contents if there are sections
            if (doc.sections.length > 1) {
                output.push("## Table of Contents");
                for (const section of doc.sections) {
                    const indent = '  '.repeat(section.level - 1);
                    output.push(`${indent}- ${section.title}`);
                }
                output.push("");
            }
            // Add the content
            output.push("## Content");
            output.push(doc.content);
            return output.join('\n');
        }
        catch (error) {
            return `Error getting documentation section: ${error}`;
        }
    }
    async listTopics() {
        try {
            const topics = this.mdxParser.listTopics();
            if (topics.length === 0) {
                return "No documentation topics found";
            }
            const output = [`# Available Documentation Topics (${topics.length} total)\n`];
            // Group by top-level directory
            const grouped = {};
            for (const topic of topics) {
                const topLevel = topic.path.split('/')[0] || 'root';
                if (!grouped[topLevel]) {
                    grouped[topLevel] = [];
                }
                grouped[topLevel].push(topic);
            }
            for (const [category, categoryTopics] of Object.entries(grouped)) {
                output.push(`## ${category.charAt(0).toUpperCase() + category.slice(1)}`);
                for (const topic of categoryTopics.slice(0, 10)) {
                    output.push(`### ${topic.title}`);
                    output.push(`**Path:** ${topic.path}`);
                    if (topic.description) {
                        const desc = topic.description.length > 150
                            ? topic.description.substring(0, 150) + "..."
                            : topic.description;
                        output.push(`**Description:** ${desc}`);
                    }
                    output.push("");
                }
                if (categoryTopics.length > 10) {
                    output.push(`... and ${categoryTopics.length - 10} more topics in this category\n`);
                }
            }
            return output.join('\n');
        }
        catch (error) {
            return `Error listing topics: ${error}`;
        }
    }
    async getCodeExamples(topic, language) {
        try {
            const examples = this.mdxParser.getCodeExamples(topic, language);
            if (examples.length === 0) {
                return `No code examples found for topic: '${topic}'${language ? ` in language: ${language}` : ''}`;
            }
            const output = [`# Code Examples for: ${topic}\n`];
            if (language) {
                output.push(`**Filtered by language:** ${language}\n`);
            }
            for (let i = 0; i < examples.length; i++) {
                const example = examples[i];
                output.push(`## Example ${i + 1}: ${example.description || 'Code Sample'}`);
                output.push(`**Language:** ${example.language}`);
                output.push("");
                output.push("```" + example.language);
                output.push(example.code);
                output.push("```");
                output.push("");
            }
            return output.join('\n');
        }
        catch (error) {
            return `Error getting code examples: ${error}`;
        }
    }
}
