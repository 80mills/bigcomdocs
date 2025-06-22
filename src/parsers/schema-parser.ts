import { readFile, readdir, stat } from 'node:fs/promises';
import { join, extname, relative, basename } from 'node:path';
import { parse } from 'yaml';
import { SchemaFile } from '../types/index.js';

export class SchemaParser {
  private schemas: Map<string, SchemaFile> = new Map();
  private modelsPath: string;

  constructor(modelsPath: string) {
    this.modelsPath = modelsPath;
  }

  async loadAllSchemas(): Promise<Map<string, SchemaFile>> {
    try {
      const files = await this.getSchemaFiles();
      
      for (const file of files) {
        try {
          const schema = await this.loadSchema(file);
          if (schema) {
            this.schemas.set(schema.name, schema);
          }
        } catch (error) {
          console.warn(`Failed to load schema ${file}:`, error);
        }
      }

      console.log(`Loaded ${this.schemas.size} schema files`);
      return this.schemas;
    } catch (error) {
      console.error('Error loading schemas:', error);
      return new Map();
    }
  }

  private async getSchemaFiles(): Promise<string[]> {
    const files: string[] = [];
    
    const scanDirectory = async (dir: string): Promise<void> => {
      try {
        const items = await readdir(dir);
        
        for (const item of items) {
          const fullPath = join(dir, item);
          const stats = await stat(fullPath);
          
          if (stats.isDirectory()) {
            await scanDirectory(fullPath);
          } else if (stats.isFile()) {
            const ext = extname(item).toLowerCase();
            if (ext === '.yaml' || ext === '.yml' || ext === '.json') {
              files.push(fullPath);
            }
          }
        }
      } catch (error) {
        console.warn(`Error scanning directory ${dir}:`, error);
      }
    };

    await scanDirectory(this.modelsPath);
    return files;
  }

  private async loadSchema(filePath: string): Promise<SchemaFile | null> {
    try {
      const content = await readFile(filePath, 'utf-8');
      const ext = extname(filePath).toLowerCase();
      
      let schema: any;
      if (ext === '.json') {
        schema = JSON.parse(content);
      } else {
        schema = parse(content);
      }

      const name = basename(filePath, extname(filePath));

      return {
        path: relative(this.modelsPath, filePath),
        name,
        schema,
      };
    } catch (error) {
      console.error(`Error parsing schema ${filePath}:`, error);
      return null;
    }
  }

  getSchema(schemaName: string): SchemaFile | null {
    return this.schemas.get(schemaName) || null;
  }

  searchSchemas(query: string): SchemaFile[] {
    const results: Array<{ schema: SchemaFile; score: number }> = [];
    const queryLower = query.toLowerCase();

    for (const schema of this.schemas.values()) {
      let score = 0;

      // Name match
      if (schema.name.toLowerCase().includes(queryLower)) {
        score += 10;
      }

      // Schema content match
      const schemaText = JSON.stringify(schema.schema).toLowerCase();
      const matches = (schemaText.match(new RegExp(queryLower, 'g')) || []).length;
      score += matches;

      if (score > 0) {
        results.push({ schema, score });
      }
    }

    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, 20)
      .map(r => r.schema);
  }

  getAllSchemas(): Map<string, SchemaFile> {
    return this.schemas;
  }
} 