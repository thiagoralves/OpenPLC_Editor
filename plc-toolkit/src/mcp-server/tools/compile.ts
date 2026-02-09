/**
 * MCP Tool: compile_st
 *
 * Compiles IEC 61131-3 Structured Text source code using MatIEC.
 * Returns structured diagnostics with LLM-friendly suggestions.
 */

import { z } from 'zod';
import { compile, writeSTFile } from '../../compiler/index.js';
import { join } from 'node:path';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';

export const compileToolName = 'compile_st';

export const compileToolConfig = {
  title: 'Compile Structured Text',
  description: `Compile IEC 61131-3 Structured Text (ST) code using the MatIEC compiler.

Accepts either a file path or inline ST source code. Returns structured
diagnostics with error locations and fix suggestions.

Use this to verify PLC code before deployment. The compiler checks syntax,
type correctness, variable declarations, and standard library usage.

Example ST input:
  PROGRAM main
  VAR
    counter : INT := 0;
    running : BOOL := TRUE;
  END_VAR
    IF running THEN
      counter := counter + 1;
    END_IF;
  END_PROGRAM`,
  inputSchema: {
    source: z.string().describe(
      'Structured Text source code (inline) or absolute file path to a .st file',
    ),
    isFilePath: z.boolean().optional().default(false).describe(
      'Set to true if source is a file path rather than inline code',
    ),
  },
};

export async function compileToolHandler({
  source,
  isFilePath,
}: {
  source: string;
  isFilePath?: boolean;
}) {
  let sourcePath: string;

  if (isFilePath) {
    sourcePath = source;
  } else {
    // Write inline source to a temp file
    const tempDir = await mkdtemp(join(tmpdir(), 'plc-'));
    sourcePath = join(tempDir, 'program.st');
    await writeSTFile(sourcePath, source);
  }

  const result = await compile({ source: sourcePath });

  const output = {
    success: result.success,
    diagnostics: result.diagnostics.map((d) => ({
      severity: d.severity,
      message: d.message,
      ...(d.line && { location: `${d.file ?? 'program.st'}:${d.line}:${d.column ?? 0}` }),
      ...(d.suggestion && { suggestion: d.suggestion }),
    })),
    ...(result.outputPath && { outputPath: result.outputPath }),
    durationMs: result.duration,
  };

  return {
    content: [{
      type: 'text' as const,
      text: JSON.stringify(output, null, 2),
    }],
  };
}
