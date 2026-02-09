/**
 * MatIEC Compiler Wrapper
 *
 * Wraps the MatIEC iec2c compiler (IEC 61131-3 to C transpiler)
 * and provides structured JSON output suitable for LLM consumption.
 *
 * MatIEC is the standard open-source IEC 61131-3 compiler used by
 * OpenPLC, Beremiz, and other open-source PLC platforms.
 */

import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import { readFile, writeFile, mkdir, readdir } from 'node:fs/promises';
import { join, dirname, resolve, basename } from 'node:path';
import { promisify } from 'node:util';
import type {
  CompileOptions,
  CompileResult,
  Diagnostic,
  Severity,
  ValidateResult,
} from '../types/index.js';

const execFileAsync = promisify(execFile);

// ─── MatIEC binary discovery ────────────────────────────────────────────────

const PLATFORM_MAP: Record<string, string> = {
  linux: 'linux',
  darwin: 'darwin',
  win32: 'win32',
};

/**
 * Locate the iec2c binary. Search order:
 * 1. Explicit path from options
 * 2. OpenPLC v4 bundled binary (../openplc-editor-v4/resources/bin/<platform>/)
 * 3. OpenPLC v3 build output (../editor/arduino/bin/)
 * 4. System PATH
 */
export function findMatIEC(explicitPath?: string): string | null {
  if (explicitPath && existsSync(explicitPath)) {
    return explicitPath;
  }

  const platform = PLATFORM_MAP[process.platform] ?? 'linux';
  const binaryName = process.platform === 'win32' ? 'iec2c.exe' : 'iec2c';

  // Check v4 bundled binaries
  const v4Path = resolve(
    dirname(new URL(import.meta.url).pathname),
    '../../../openplc-editor-v4/resources/bin',
    platform,
    binaryName,
  );
  if (existsSync(v4Path)) return v4Path;

  // Check v3 editor build output
  const v3Path = resolve(
    dirname(new URL(import.meta.url).pathname),
    '../../../editor/arduino/bin',
    binaryName,
  );
  if (existsSync(v3Path)) return v3Path;

  // Fallback: assume it's on PATH
  return binaryName;
}

// ─── Error Parsing ──────────────────────────────────────────────────────────

/**
 * Parse MatIEC compiler output into structured diagnostics.
 *
 * MatIEC error formats:
 *   file.st:12:5-15: error: Undeclared variable 'x'
 *   file.st:12:5..12:15: warning: Unused variable 'y'
 *   error  : some error message
 */
export function parseDiagnostics(output: string): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
  const lines = output.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Pattern: file:line:col-end: severity: message
    const fileMatch = trimmed.match(
      /^(.+?):(\d+):(\d+)(?:[-.]\d+(?::\d+)?)?:\s*(error|warning|info):\s*(.+)$/i,
    );
    if (fileMatch) {
      diagnostics.push({
        file: fileMatch[1],
        line: parseInt(fileMatch[2], 10),
        column: parseInt(fileMatch[3], 10),
        severity: fileMatch[4].toLowerCase() as Severity,
        message: fileMatch[5],
        suggestion: generateSuggestion(fileMatch[5]),
      });
      continue;
    }

    // Pattern: severity : message (no file location)
    const bareMatch = trimmed.match(
      /^(error|warning|info)\s*:\s*(.+)$/i,
    );
    if (bareMatch) {
      diagnostics.push({
        severity: bareMatch[1].toLowerCase() as Severity,
        message: bareMatch[2],
        suggestion: generateSuggestion(bareMatch[2]),
      });
    }
  }

  return diagnostics;
}

/**
 * Generate an LLM-friendly fix suggestion based on common error patterns.
 */
function generateSuggestion(message: string): string | undefined {
  const lower = message.toLowerCase();

  if (lower.includes('undeclared') || lower.includes('undefined')) {
    return 'Declare the variable in the appropriate VAR..END_VAR block before using it.';
  }
  if (lower.includes('type mismatch') || lower.includes('incompatible')) {
    return 'Check that the variable types on both sides of the assignment are compatible. Use type conversion functions (e.g. INT_TO_REAL) if needed.';
  }
  if (lower.includes('syntax error') || lower.includes('unexpected token')) {
    return 'Check for missing semicolons, unmatched BEGIN/END blocks, or incorrect keyword usage.';
  }
  if (lower.includes('duplicate')) {
    return 'A symbol with this name already exists. Rename one of the declarations.';
  }
  return undefined;
}

// ─── Compile ────────────────────────────────────────────────────────────────

/**
 * Compile an IEC 61131-3 source file using MatIEC.
 *
 * This wraps the iec2c binary and returns structured results
 * with diagnostics suitable for LLM processing.
 */
export async function compile(options: CompileOptions): Promise<CompileResult> {
  const startTime = Date.now();
  const iec2c = findMatIEC(options.matiecPath);

  if (!iec2c) {
    return {
      success: false,
      diagnostics: [{
        severity: 'error',
        message: 'MatIEC (iec2c) compiler not found. Install it or provide the path via matiecPath option.',
        suggestion: 'Run the OpenPLC Editor installer, or build MatIEC from source: https://github.com/thiagoralves/matiec',
      }],
      duration: Date.now() - startTime,
      rawOutput: '',
    };
  }

  const sourcePath = resolve(options.source);
  if (!existsSync(sourcePath)) {
    return {
      success: false,
      diagnostics: [{
        severity: 'error',
        message: `Source file not found: ${sourcePath}`,
      }],
      duration: Date.now() - startTime,
      rawOutput: '',
    };
  }

  const outputDir = options.outputDir ?? join(dirname(sourcePath), 'build');
  await mkdir(outputDir, { recursive: true });

  const args = [
    '-I', join(dirname(iec2c), '..', 'lib'),  // standard library path
    '-T', outputDir,                             // output directory
    sourcePath,
  ];

  try {
    const { stdout, stderr } = await execFileAsync(iec2c, args, {
      timeout: 30_000,
      maxBuffer: 10 * 1024 * 1024,
    });

    const allOutput = `${stdout}\n${stderr}`;
    const diagnostics = parseDiagnostics(allOutput);
    const hasErrors = diagnostics.some(d => d.severity === 'error');

    return {
      success: !hasErrors,
      diagnostics,
      outputPath: hasErrors ? undefined : outputDir,
      duration: Date.now() - startTime,
      rawOutput: allOutput.trim(),
    };
  } catch (err: unknown) {
    const error = err as { stdout?: string; stderr?: string; message?: string; code?: string };
    const allOutput = `${error.stdout ?? ''}\n${error.stderr ?? ''}`;
    const diagnostics = parseDiagnostics(allOutput);

    // If we couldn't parse any diagnostics, add the raw error
    if (diagnostics.length === 0) {
      diagnostics.push({
        severity: 'error',
        message: error.message ?? 'Unknown compiler error',
        code: error.code,
      });
    }

    return {
      success: false,
      diagnostics,
      duration: Date.now() - startTime,
      rawOutput: allOutput.trim(),
    };
  }
}

// ─── Validate ───────────────────────────────────────────────────────────────

/**
 * Validate an IEC 61131-3 source file without generating output.
 * Uses iec2c in a dry-run fashion and parses diagnostics.
 */
export async function validate(sourcePath: string, matiecPath?: string): Promise<ValidateResult> {
  const result = await compile({
    source: sourcePath,
    matiecPath,
    cOnly: true,
  });

  return {
    valid: result.success,
    diagnostics: result.diagnostics,
  };
}

// ─── Utility ────────────────────────────────────────────────────────────────

/**
 * Read a Structured Text file and return its content.
 */
export async function readSTFile(filePath: string): Promise<string> {
  return readFile(resolve(filePath), 'utf-8');
}

/**
 * Write Structured Text content to a file (for LLM-generated code).
 */
export async function writeSTFile(filePath: string, content: string): Promise<void> {
  const dir = dirname(resolve(filePath));
  await mkdir(dir, { recursive: true });
  await writeFile(resolve(filePath), content, 'utf-8');
}
