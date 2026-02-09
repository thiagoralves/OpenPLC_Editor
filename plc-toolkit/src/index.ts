/**
 * @openplc/toolkit
 *
 * Headless PLC development toolkit for IEC 61131-3 programming.
 * Designed for LLM agent integration, CI/CD pipelines, and
 * developers who prefer programmatic access to PLC tooling.
 *
 * @example
 * ```typescript
 * import { compile, validate } from '@openplc/toolkit/compiler';
 * import { parsePLCopenXML } from '@openplc/toolkit/parsers';
 * import { startMCPServer } from '@openplc/toolkit/mcp';
 *
 * // Compile ST code
 * const result = await compile({ source: 'program.st' });
 * console.log(result.diagnostics);
 *
 * // Parse a PLCopen XML project
 * const project = parsePLCopenXML(xmlString);
 * console.log(project.pous);
 *
 * // Start MCP server for LLM integration
 * await startMCPServer();
 * ```
 */

export { compile, validate, findMatIEC, readSTFile, writeSTFile } from './compiler/index.js';
export { parsePLCopenXML } from './parsers/index.js';
export { startMCPServer } from './mcp-server/index.js';
export type * from './types/index.js';
