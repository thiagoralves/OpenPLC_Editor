#!/usr/bin/env node
/**
 * OpenPLC MCP Server
 *
 * Model Context Protocol server that exposes PLC programming tools
 * to LLM agents (Claude, GPT, etc). Enables AI-assisted IEC 61131-3
 * development with compiler-in-the-loop validation.
 *
 * Tools provided:
 *   - compile_st:         Compile Structured Text to C via MatIEC
 *   - validate_st:        Validate ST code without generating output
 *   - plc_project_read:   Read and parse PLCopen XML projects
 *   - plc_project_create: Generate PLCopen XML from ST source
 *   - st_reference:       IEC 61131-3 language reference for LLMs
 *
 * Usage:
 *   npx @openplc/toolkit mcp          # Start MCP server via stdio
 *
 * Claude Desktop config (~/.claude/settings.json):
 *   {
 *     "mcpServers": {
 *       "openplc": {
 *         "command": "node",
 *         "args": ["path/to/plc-toolkit/dist/mcp-server/index.js"]
 *       }
 *     }
 *   }
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

import {
  compileToolName,
  compileToolConfig,
  compileToolHandler,
} from './tools/compile.js';
import {
  validateToolName,
  validateToolConfig,
  validateToolHandler,
} from './tools/validate.js';
import {
  projectReadToolName,
  projectReadToolConfig,
  projectReadToolHandler,
  projectCreateToolName,
  projectCreateToolConfig,
  projectCreateToolHandler,
} from './tools/project.js';
import {
  stReferenceToolName,
  stReferenceToolConfig,
  stReferenceToolHandler,
} from './tools/st-helpers.js';

export async function startMCPServer(): Promise<void> {
  const server = new McpServer({
    name: 'openplc-toolkit',
    version: '0.1.0',
  });

  // Register all tools
  server.registerTool(compileToolName, compileToolConfig, compileToolHandler);
  server.registerTool(validateToolName, validateToolConfig, validateToolHandler);
  server.registerTool(projectReadToolName, projectReadToolConfig, projectReadToolHandler);
  server.registerTool(projectCreateToolName, projectCreateToolConfig, projectCreateToolHandler);
  server.registerTool(stReferenceToolName, stReferenceToolConfig, stReferenceToolHandler);

  // Start the transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    await server.close();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await server.close();
    process.exit(0);
  });
}

// Run directly if invoked as a script
const isDirectRun = process.argv[1]?.includes('mcp-server');
if (isDirectRun) {
  startMCPServer().catch((err) => {
    console.error('Failed to start MCP server:', err);
    process.exit(1);
  });
}
