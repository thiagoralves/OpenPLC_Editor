#!/usr/bin/env node
/**
 * OpenPLC Toolkit CLI
 *
 * Headless PLC development tool for IEC 61131-3 programming.
 * Designed for CI/CD pipelines, LLM agents, and developers
 * who prefer the terminal.
 *
 * Commands:
 *   plc compile <file.st>     Compile Structured Text
 *   plc validate <file.st>    Validate without compiling
 *   plc create <project.xml>  Create a PLCopen XML project
 *   plc parse <project.xml>   Parse and display project info
 *   plc mcp                   Start the MCP server
 *   plc help                  Show help
 */

import { compile, validate, readSTFile } from '../compiler/index.js';
import { parsePLCopenXML } from '../parsers/plcopen-xml.js';
import { startMCPServer } from '../mcp-server/index.js';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const command = args[0];

async function main() {
  switch (command) {
    case 'compile':
      await handleCompile(args.slice(1));
      break;
    case 'validate':
      await handleValidate(args.slice(1));
      break;
    case 'parse':
      await handleParse(args.slice(1));
      break;
    case 'mcp':
      await startMCPServer();
      break;
    case 'help':
    case '--help':
    case '-h':
    case undefined:
      showHelp();
      break;
    default:
      console.error(`Unknown command: ${command}`);
      showHelp();
      process.exit(1);
  }
}

async function handleCompile(args: string[]) {
  const file = args[0];
  const jsonFlag = args.includes('--json');
  const outputDir = getFlagValue(args, '--output') ?? getFlagValue(args, '-o');

  if (!file) {
    console.error('Usage: plc compile <file.st> [--json] [--output <dir>]');
    process.exit(1);
  }

  const result = await compile({
    source: file,
    ...(outputDir && { outputDir }),
  });

  if (jsonFlag) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    if (result.success) {
      console.log(`Compiled successfully in ${result.duration}ms`);
      if (result.outputPath) {
        console.log(`Output: ${result.outputPath}`);
      }
    } else {
      console.error('Compilation failed:');
    }

    for (const d of result.diagnostics) {
      const loc = d.line ? `${d.file ?? ''}:${d.line}:${d.column ?? 0}` : '';
      const prefix = d.severity === 'error' ? 'ERROR' : d.severity === 'warning' ? 'WARN' : 'INFO';
      console.log(`  ${prefix} ${loc ? `[${loc}] ` : ''}${d.message}`);
      if (d.suggestion) {
        console.log(`        Suggestion: ${d.suggestion}`);
      }
    }
  }

  process.exit(result.success ? 0 : 1);
}

async function handleValidate(args: string[]) {
  const file = args[0];
  const jsonFlag = args.includes('--json');

  if (!file) {
    console.error('Usage: plc validate <file.st> [--json]');
    process.exit(1);
  }

  const result = await validate(file);

  if (jsonFlag) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    if (result.valid) {
      console.log('Valid IEC 61131-3 program');
    } else {
      console.error('Validation failed:');
    }

    for (const d of result.diagnostics) {
      const loc = d.line ? `${d.file ?? ''}:${d.line}:${d.column ?? 0}` : '';
      const prefix = d.severity === 'error' ? 'ERROR' : d.severity === 'warning' ? 'WARN' : 'INFO';
      console.log(`  ${prefix} ${loc ? `[${loc}] ` : ''}${d.message}`);
      if (d.suggestion) {
        console.log(`        Suggestion: ${d.suggestion}`);
      }
    }
  }

  process.exit(result.valid ? 0 : 1);
}

async function handleParse(args: string[]) {
  const file = args[0];
  const jsonFlag = args.includes('--json');

  if (!file) {
    console.error('Usage: plc parse <project.xml> [--json]');
    process.exit(1);
  }

  const xml = await readFile(resolve(file), 'utf-8');
  const project = parsePLCopenXML(xml);

  if (jsonFlag) {
    console.log(JSON.stringify(project, null, 2));
  } else {
    console.log(`Project: ${project.name}`);
    console.log(`POUs (${project.pous.length}):`);
    for (const pou of project.pous) {
      console.log(`  ${pou.type.padEnd(15)} ${pou.name.padEnd(25)} [${pou.language}]`);
      for (const v of pou.variables) {
        console.log(`    ${v.class.padEnd(8)} ${v.name}: ${v.type}${v.address ? ` AT ${v.address}` : ''}`);
      }
    }
    if (project.globalVars.length > 0) {
      console.log(`\nGlobal Variables (${project.globalVars.length}):`);
      for (const v of project.globalVars) {
        console.log(`  ${v.name}: ${v.type}${v.address ? ` AT ${v.address}` : ''}`);
      }
    }
  }
}

function showHelp() {
  console.log(`
OpenPLC Toolkit v0.1.0
Headless PLC development for IEC 61131-3

Usage: plc <command> [options]

Commands:
  compile <file.st>     Compile Structured Text via MatIEC
    --json              Output results as JSON
    --output, -o <dir>  Output directory for compiled files

  validate <file.st>    Validate ST code without generating output
    --json              Output results as JSON

  parse <project.xml>   Parse a PLCopen XML project file
    --json              Output full project structure as JSON

  mcp                   Start MCP server (for LLM agent integration)

  help                  Show this help message

Environment:
  MATIEC_PATH           Path to the iec2c binary (auto-detected)

Examples:
  plc compile program.st --json
  plc validate my_fb.st
  plc parse project.xml --json
  plc mcp
`);
}

function getFlagValue(args: string[], flag: string): string | undefined {
  const idx = args.indexOf(flag);
  if (idx !== -1 && idx + 1 < args.length) {
    return args[idx + 1];
  }
  return undefined;
}

main().catch((err) => {
  console.error('Fatal error:', err.message ?? err);
  process.exit(1);
});
