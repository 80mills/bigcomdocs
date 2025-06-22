/**
 * Utility functions for the BigCommerce MCP Server
 */
/**
 * Safely parse JSON with error handling
 */
export declare function safeJsonParse(text: string): any;
/**
 * Truncate text to a specific length with ellipsis
 */
export declare function truncateText(text: string, maxLength: number): string;
/**
 * Extract file extension from path
 */
export declare function getFileExtension(filePath: string): string;
/**
 * Check if a string contains any of the given keywords
 */
export declare function containsKeywords(text: string, keywords: string[]): boolean;
/**
 * Score text relevance based on keyword matches
 */
export declare function scoreTextRelevance(text: string, keywords: string[]): number;
/**
 * Clean and normalize API names
 */
export declare function normalizeApiName(name: string): string;
/**
 * Format HTTP method for display
 */
export declare function formatHttpMethod(method: string): string;
/**
 * Check if a value is a valid HTTP method
 */
export declare function isValidHttpMethod(method: string): boolean;
/**
 * Generate a unique identifier
 */
export declare function generateId(): string;
/**
 * Deep merge two objects
 */
export declare function deepMerge(target: any, source: any): any;
/**
 * Debounce function execution
 */
export declare function debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void;
/**
 * Format bytes to human readable string
 */
export declare function formatBytes(bytes: number, decimals?: number): string;
