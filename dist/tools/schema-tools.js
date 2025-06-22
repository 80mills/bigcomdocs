export class SchemaTools {
    schemaParser;
    constructor(schemaParser) {
        this.schemaParser = schemaParser;
    }
    async getSchema(schemaName) {
        try {
            const schema = this.schemaParser.getSchema(schemaName);
            if (!schema) {
                const availableSchemas = Array.from(this.schemaParser.getAllSchemas().keys());
                return `Schema '${schemaName}' not found. Available schemas: ${availableSchemas.slice(0, 10).join(', ')}`;
            }
            const output = [`# Schema: ${schema.name}\n`];
            output.push(`**Path:** ${schema.path}`);
            // Format the schema nicely
            if (typeof schema.schema === 'object') {
                output.push("\n## Schema Definition");
                output.push("```json");
                output.push(JSON.stringify(schema.schema, null, 2));
                output.push("```");
                // Extract useful information from the schema
                if (schema.schema.type) {
                    output.push(`\n**Type:** ${schema.schema.type}`);
                }
                if (schema.schema.description) {
                    output.push(`**Description:** ${schema.schema.description}`);
                }
                if (schema.schema.properties) {
                    output.push("\n## Properties");
                    for (const [propName, propDef] of Object.entries(schema.schema.properties)) {
                        const prop = propDef;
                        const type = prop.type || 'unknown';
                        const desc = prop.description || 'No description';
                        const required = schema.schema.required?.includes(propName) ? ' (required)' : ' (optional)';
                        output.push(`- **${propName}** (${type})${required}: ${desc}`);
                    }
                }
                if (schema.schema.required) {
                    output.push(`\n**Required Fields:** ${schema.schema.required.join(', ')}`);
                }
            }
            else {
                output.push("\n## Raw Schema");
                output.push("```");
                output.push(String(schema.schema));
                output.push("```");
            }
            return output.join('\n');
        }
        catch (error) {
            return `Error getting schema: ${error}`;
        }
    }
    async searchSchemas(query) {
        try {
            const results = this.schemaParser.searchSchemas(query);
            if (results.length === 0) {
                return `No schemas found matching query: '${query}'`;
            }
            const output = [`Found ${results.length} schema(s) matching '${query}':\n`];
            for (const schema of results) {
                output.push(`## ${schema.name}`);
                output.push(`**Path:** ${schema.path}`);
                if (typeof schema.schema === 'object') {
                    if (schema.schema.description) {
                        output.push(`**Description:** ${schema.schema.description}`);
                    }
                    if (schema.schema.type) {
                        output.push(`**Type:** ${schema.schema.type}`);
                    }
                    if (schema.schema.properties) {
                        const propCount = Object.keys(schema.schema.properties).length;
                        output.push(`**Properties:** ${propCount} fields`);
                        // Show first few properties
                        const propNames = Object.keys(schema.schema.properties).slice(0, 5);
                        if (propNames.length > 0) {
                            output.push(`**Sample Properties:** ${propNames.join(', ')}`);
                        }
                    }
                }
                output.push("");
            }
            return output.join('\n');
        }
        catch (error) {
            return `Error searching schemas: ${error}`;
        }
    }
}
