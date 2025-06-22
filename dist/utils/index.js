/**
 * Utility functions for the BigCommerce MCP Server
 */
/**
 * Safely parse JSON with error handling
 */
export function safeJsonParse(text) {
    try {
        return JSON.parse(text);
    }
    catch (error) {
        console.warn('Failed to parse JSON:', error);
        return null;
    }
}
/**
 * Truncate text to a specific length with ellipsis
 */
export function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }
    return text.substring(0, maxLength) + '...';
}
/**
 * Extract file extension from path
 */
export function getFileExtension(filePath) {
    const lastDot = filePath.lastIndexOf('.');
    if (lastDot === -1) {
        return '';
    }
    return filePath.substring(lastDot + 1).toLowerCase();
}
/**
 * Check if a string contains any of the given keywords
 */
export function containsKeywords(text, keywords) {
    const lowerText = text.toLowerCase();
    return keywords.some(keyword => lowerText.includes(keyword.toLowerCase()));
}
/**
 * Score text relevance based on keyword matches
 */
export function scoreTextRelevance(text, keywords) {
    const lowerText = text.toLowerCase();
    let score = 0;
    for (const keyword of keywords) {
        const lowerKeyword = keyword.toLowerCase();
        const matches = (lowerText.match(new RegExp(lowerKeyword, 'g')) || []).length;
        score += matches;
    }
    return score;
}
/**
 * Clean and normalize API names
 */
export function normalizeApiName(name) {
    return name
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');
}
/**
 * Format HTTP method for display
 */
export function formatHttpMethod(method) {
    return method.toUpperCase();
}
/**
 * Check if a value is a valid HTTP method
 */
export function isValidHttpMethod(method) {
    const validMethods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'];
    return validMethods.includes(method.toUpperCase());
}
/**
 * Generate a unique identifier
 */
export function generateId() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}
/**
 * Deep merge two objects
 */
export function deepMerge(target, source) {
    const result = { ...target };
    for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
            result[key] = deepMerge(target[key] || {}, source[key]);
        }
        else {
            result[key] = source[key];
        }
    }
    return result;
}
/**
 * Debounce function execution
 */
export function debounce(func, wait) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}
/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes, decimals = 2) {
    if (bytes === 0)
        return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
