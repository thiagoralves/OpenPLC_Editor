/**
 * Core types for the OpenPLC Toolkit.
 *
 * These types define the vendor-neutral intermediate representation
 * for PLC programs, enabling interoperability between formats and
 * providing structured data for LLM agents.
 */

// ─── IEC 61131-3 Language Types ─────────────────────────────────────────────

export type PLCLanguage = 'ST' | 'LD' | 'FBD' | 'SFC' | 'IL';

export type POUType = 'program' | 'functionBlock' | 'function';

export interface POU {
  name: string;
  type: POUType;
  language: PLCLanguage;
  /** Raw source text for textual languages (ST, IL) */
  body: string;
  variables: Variable[];
  returnType?: DataType;
}

export interface Variable {
  name: string;
  type: DataType;
  class: VariableClass;
  initialValue?: string;
  address?: string; // e.g. %IX0.0, %QW1, %MD0
  comment?: string;
}

export type VariableClass =
  | 'input'
  | 'output'
  | 'inOut'
  | 'local'
  | 'global'
  | 'external'
  | 'temp';

export type DataType =
  | PrimitiveType
  | ArrayType
  | StructType
  | EnumType
  | string; // named/derived type reference

export type PrimitiveType =
  | 'BOOL'
  | 'BYTE' | 'WORD' | 'DWORD' | 'LWORD'
  | 'SINT' | 'INT' | 'DINT' | 'LINT'
  | 'USINT' | 'UINT' | 'UDINT' | 'ULINT'
  | 'REAL' | 'LREAL'
  | 'TIME' | 'DATE' | 'TOD' | 'DT'
  | 'STRING' | 'WSTRING';

export interface ArrayType {
  kind: 'array';
  elementType: DataType;
  dimensions: Array<{ lower: number; upper: number }>;
}

export interface StructType {
  kind: 'struct';
  name: string;
  members: Variable[];
}

export interface EnumType {
  kind: 'enum';
  name: string;
  values: string[];
}

// ─── Project / Configuration ────────────────────────────────────────────────

export interface PLCProject {
  name: string;
  version?: string;
  author?: string;
  description?: string;
  pous: POU[];
  globalVars: Variable[];
  dataTypes: Array<StructType | EnumType>;
  configurations: PLCConfiguration[];
}

export interface PLCConfiguration {
  name: string;
  resources: PLCResource[];
}

export interface PLCResource {
  name: string;
  tasks: PLCTask[];
  globalVars: Variable[];
}

export interface PLCTask {
  name: string;
  interval?: string; // e.g. 'T#20ms'
  priority?: number;
  programInstances: Array<{ name: string; typeName: string }>;
}

// ─── Compiler Types ─────────────────────────────────────────────────────────

export type Severity = 'error' | 'warning' | 'info';

export interface Diagnostic {
  severity: Severity;
  message: string;
  file?: string;
  line?: number;
  column?: number;
  code?: string;
  /** LLM-friendly suggestion for fixing */
  suggestion?: string;
}

export interface CompileResult {
  success: boolean;
  diagnostics: Diagnostic[];
  outputPath?: string;
  /** Time taken in milliseconds */
  duration: number;
  /** Raw compiler output for debugging */
  rawOutput: string;
}

export interface ValidateResult {
  valid: boolean;
  diagnostics: Diagnostic[];
  /** Parsed POU metadata when valid */
  pous?: Array<{ name: string; type: POUType; language: PLCLanguage }>;
}

// ─── Target / Runtime ───────────────────────────────────────────────────────

export type TargetPlatform =
  | 'linux'
  | 'arduino'
  | 'esp32'
  | 'raspberry-pi'
  | 'raspberry-pico';

export interface CompileOptions {
  /** Source file or directory */
  source: string;
  /** Output directory */
  outputDir?: string;
  /** Target platform */
  target?: TargetPlatform;
  /** Path to MatIEC binary (auto-detected if not set) */
  matiecPath?: string;
  /** Generate intermediate C code only */
  cOnly?: boolean;
}
