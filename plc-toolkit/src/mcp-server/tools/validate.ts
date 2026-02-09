/**
 * MCP Tool: validate_st
 *
 * Validates IEC 61131-3 Structured Text without generating compiled output.
 * Lighter-weight than full compilation - good for iterative LLM code generation.
 */

import { z } from 'zod';
import { validate, writeSTFile } from '../../compiler/index.js';
import { join } from 'node:path';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';

export const validateToolName = 'validate_st';

export const validateToolConfig = {
  title: 'Validate Structured Text',
  description: `Validate IEC 61131-3 Structured Text (ST) code for correctness without
generating compiled output. Faster than full compilation.

Returns diagnostics with error locations and fix suggestions.
Use this in a generate-validate-fix loop for iterative PLC code generation.

Checks: syntax, type correctness, variable declarations, standard library usage.`,
  inputSchema: {
    source: z.string().describe(
      'Structured Text source code (inline) or absolute file path to a .st file',
    ),
    isFilePath: z.boolean().optional().default(false).describe(
      'Set to true if source is a file path rather than inline code',
    ),
  },
};

export async function validateToolHandler({
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
    const tempDir = await mkdtemp(join(tmpdir(), 'plc-'));
    sourcePath = join(tempDir, 'program.st');
    await writeSTFile(sourcePath, source);
  }

  const result = await validate(sourcePath);

  const output = {
    valid: result.valid,
    diagnostics: result.diagnostics.map((d) => ({
      severity: d.severity,
      message: d.message,
      ...(d.line && { location: `${d.file ?? 'program.st'}:${d.line}:${d.column ?? 0}` }),
      ...(d.suggestion && { suggestion: d.suggestion }),
    })),
    ...(result.pous && { pous: result.pous }),
  };

  return {
    content: [{
      type: 'text' as const,
      text: JSON.stringify(output, null, 2),
    }],
  };
}
