/**
 * PLCopen XML Parser
 *
 * Parses PLCopen XML (IEC 61131-10) project files into the toolkit's
 * vendor-neutral intermediate representation.
 *
 * Supports reading projects from:
 *   - OpenPLC Editor (v3 and v4)
 *   - Beremiz
 *   - CODESYS PLCopen XML export
 *   - Beckhoff TwinCAT PLCopen XML export
 *   - Any IEC 61131-10 compliant exporter
 *
 * The parser extracts:
 *   - POU definitions (programs, function blocks, functions)
 *   - Variable declarations with types, addresses, initial values
 *   - ST/IL source code bodies
 *   - Data type definitions
 *   - Task and resource configuration
 */

import { XMLParser } from 'fast-xml-parser';
import type {
  PLCProject,
  POU,
  POUType,
  PLCLanguage,
  Variable,
  VariableClass,
  PLCConfiguration,
  PLCResource,
  PLCTask,
  StructType,
  EnumType,
} from '../types/index.js';

const xmlParser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  textNodeName: '#text',
  isArray: (name) => {
    // These elements can appear multiple times
    return [
      'pou', 'variable', 'dataType', 'configuration',
      'resource', 'task', 'pouInstance', 'member',
      'value', 'dimension',
    ].includes(name);
  },
});

/**
 * Parse a PLCopen XML string into a PLCProject.
 */
export function parsePLCopenXML(xml: string): PLCProject {
  const parsed = xmlParser.parse(xml);
  const project = parsed.project ?? parsed;

  const contentHeader = project.contentHeader ?? {};
  const types = project.types ?? {};
  const instances = project.instances ?? {};

  return {
    name: contentHeader['@_name'] ?? 'Untitled',
    version: contentHeader['@_version'],
    author: contentHeader['@_author'],
    description: extractText(contentHeader.Comment),
    pous: parsePOUs(types.pous),
    globalVars: parseGlobalVars(instances),
    dataTypes: parseDataTypes(types.dataTypes),
    configurations: parseConfigurations(instances),
  };
}

// ─── POU Parsing ────────────────────────────────────────────────────────────

function parsePOUs(pous: any): POU[] {
  if (!pous?.pou) return [];

  const pouList = ensureArray(pous.pou);
  return pouList.map(parsePOU);
}

function parsePOU(pou: any): POU {
  const name = pou['@_name'] ?? 'unnamed';
  const pouType = mapPOUType(pou['@_pouType']);
  const language = detectLanguage(pou.body);
  const body = extractBody(pou.body, language);
  const variables = parseInterface(pou.interface);

  return { name, type: pouType, language, body, variables };
}

function mapPOUType(type: string): POUType {
  switch (type?.toLowerCase()) {
    case 'functionblock': return 'functionBlock';
    case 'function': return 'function';
    default: return 'program';
  }
}

function detectLanguage(body: any): PLCLanguage {
  if (!body) return 'ST';
  if (body.ST) return 'ST';
  if (body.IL) return 'IL';
  if (body.FBD) return 'FBD';
  if (body.LD) return 'LD';
  if (body.SFC) return 'SFC';
  return 'ST';
}

function extractBody(body: any, language: PLCLanguage): string {
  if (!body) return '';

  // For textual languages, extract the source text
  if (language === 'ST' || language === 'IL') {
    const langNode = body[language];
    if (!langNode) return '';

    // PLCopen XML stores ST/IL in <xhtml:p> elements
    const xhtmlP =
      langNode['xhtml:p'] ??
      langNode['p'] ??
      langNode['#text'] ??
      '';

    return typeof xhtmlP === 'string'
      ? xhtmlP.trim()
      : JSON.stringify(xhtmlP);
  }

  // For graphical languages, return the XML subtree as JSON
  // (preserves structure for visualization tools)
  const langNode = body[language];
  return langNode ? JSON.stringify(langNode, null, 2) : '';
}

// ─── Variable Parsing ───────────────────────────────────────────────────────

function parseInterface(iface: any): Variable[] {
  if (!iface) return [];

  const variables: Variable[] = [];

  const varSections: Array<[string, VariableClass]> = [
    ['localVars', 'local'],
    ['inputVars', 'input'],
    ['outputVars', 'output'],
    ['inOutVars', 'inOut'],
    ['externalVars', 'external'],
    ['tempVars', 'temp'],
    ['globalVars', 'global'],
  ];

  for (const [xmlTag, varClass] of varSections) {
    const section = iface[xmlTag];
    if (!section) continue;

    const sectionList = ensureArray(section);
    for (const sec of sectionList) {
      const vars = ensureArray(sec.variable ?? []);
      for (const v of vars) {
        variables.push(parseVariable(v, varClass));
      }
    }
  }

  return variables;
}

function parseVariable(v: any, varClass: VariableClass): Variable {
  return {
    name: v['@_name'] ?? 'unnamed',
    type: extractType(v.type),
    class: varClass,
    initialValue: extractInitialValue(v.initialValue),
    address: v['@_address'] ?? v.address ?? undefined,
    comment: extractText(v.documentation),
  };
}

function extractType(typeNode: any): string {
  if (!typeNode) return 'BOOL';

  // Simple types: <BOOL />, <INT />, etc.
  const simpleTypes = [
    'BOOL', 'BYTE', 'WORD', 'DWORD', 'LWORD',
    'SINT', 'INT', 'DINT', 'LINT',
    'USINT', 'UINT', 'UDINT', 'ULINT',
    'REAL', 'LREAL',
    'TIME', 'DATE', 'TOD', 'DT',
    'STRING', 'WSTRING',
  ];

  for (const t of simpleTypes) {
    if (typeNode[t] !== undefined) return t;
  }

  // Derived type reference: <derived name="MyType" />
  if (typeNode.derived) {
    return typeNode.derived['@_name'] ?? 'UNKNOWN';
  }

  // Array type
  if (typeNode.array) {
    const baseType = extractType(typeNode.array.baseType);
    return `ARRAY OF ${baseType}`;
  }

  // String with size: <string length="80" />
  if (typeNode.string) {
    const len = typeNode.string['@_length'];
    return len ? `STRING[${len}]` : 'STRING';
  }

  return 'UNKNOWN';
}

function extractInitialValue(initNode: any): string | undefined {
  if (!initNode) return undefined;

  if (initNode.simpleValue) {
    return initNode.simpleValue['@_value'];
  }
  if (typeof initNode === 'string') {
    return initNode;
  }
  return undefined;
}

// ─── Data Type Parsing ──────────────────────────────────────────────────────

function parseDataTypes(dataTypes: any): Array<StructType | EnumType> {
  if (!dataTypes?.dataType) return [];

  const dtList = ensureArray(dataTypes.dataType);
  const result: Array<StructType | EnumType> = [];

  for (const dt of dtList) {
    const name = dt['@_name'] ?? 'Unnamed';

    if (dt.baseType?.struct) {
      const members = ensureArray(dt.baseType.struct.variable ?? []);
      result.push({
        kind: 'struct',
        name,
        members: members.map((m: any) => parseVariable(m, 'local')),
      });
    }

    if (dt.baseType?.enum) {
      const values = ensureArray(dt.baseType.enum.values?.value ?? []);
      result.push({
        kind: 'enum',
        name,
        values: values.map((v: any) => v['@_name'] ?? String(v)),
      });
    }
  }

  return result;
}

// ─── Configuration Parsing ──────────────────────────────────────────────────

function parseConfigurations(instances: any): PLCConfiguration[] {
  const configs = instances?.configurations?.configuration;
  if (!configs) return [];

  return ensureArray(configs).map((config: any) => ({
    name: config['@_name'] ?? 'config',
    resources: parseResources(config),
  }));
}

function parseResources(config: any): PLCResource[] {
  const resources = config?.resource;
  if (!resources) return [];

  return ensureArray(resources).map((res: any) => ({
    name: res['@_name'] ?? 'resource',
    tasks: parseTasks(res),
    globalVars: [],
  }));
}

function parseTasks(resource: any): PLCTask[] {
  const tasks = resource?.task;
  if (!tasks) return [];

  return ensureArray(tasks).map((task: any) => ({
    name: task['@_name'] ?? 'task',
    interval: task['@_interval'],
    priority: task['@_priority'] ? parseInt(task['@_priority'], 10) : undefined,
    programInstances: ensureArray(task.pouInstance ?? []).map((pi: any) => ({
      name: pi['@_name'] ?? '',
      typeName: pi['@_typeName'] ?? '',
    })),
  }));
}

// ─── Utilities ──────────────────────────────────────────────────────────────

function ensureArray<T>(value: T | T[]): T[] {
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null) return [];
  return [value];
}

function extractText(node: any): string | undefined {
  if (!node) return undefined;
  if (typeof node === 'string') return node;
  if (node['#text']) return String(node['#text']);
  if (node['xhtml:p']) return String(node['xhtml:p']);
  return undefined;
}
