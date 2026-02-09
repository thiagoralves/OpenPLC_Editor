/**
 * MCP Tool: plc_project
 *
 * Read, create, and manage PLCopen XML project files.
 * This is the bridge between LLM-generated ST code and the
 * PLCopen XML format used by OpenPLC and other editors.
 */

import { z } from 'zod';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { existsSync } from 'node:fs';

export const projectReadToolName = 'plc_project_read';

export const projectReadToolConfig = {
  title: 'Read PLC Project',
  description: `Read a PLCopen XML project file and return its contents in a structured format.

Extracts: POU names, types, languages, variable declarations, and source code.
Supports .xml (PLCopen XML) project files used by OpenPLC Editor.

Use this to understand an existing PLC project before making modifications.`,
  inputSchema: {
    projectPath: z.string().describe('Absolute path to the PLCopen XML project file (.xml)'),
  },
};

export async function projectReadToolHandler({
  projectPath,
}: {
  projectPath: string;
}) {
  const absPath = resolve(projectPath);

  if (!existsSync(absPath)) {
    return {
      content: [{
        type: 'text' as const,
        text: JSON.stringify({ error: `Project file not found: ${absPath}` }),
      }],
    };
  }

  const content = await readFile(absPath, 'utf-8');

  // Return the raw XML with a summary header
  // Full XML parsing is in the parsers module
  const pouCount = (content.match(/<pou\s/gi) ?? []).length;
  const dataTypeCount = (content.match(/<dataType\s/gi) ?? []).length;

  const summary = {
    file: absPath,
    pouCount,
    dataTypeCount,
    format: 'PLCopen XML',
    rawXml: content,
  };

  return {
    content: [{
      type: 'text' as const,
      text: JSON.stringify(summary, null, 2),
    }],
  };
}

// ─── Create Project ─────────────────────────────────────────────────────────

export const projectCreateToolName = 'plc_project_create';

export const projectCreateToolConfig = {
  title: 'Create PLC Project',
  description: `Create a new PLCopen XML project file with the given Structured Text program.

Generates a minimal but valid PLCopen XML file that can be opened in
OpenPLC Editor or any PLCopen XML-compatible tool.

Use this after generating and validating ST code to create a deployable project.`,
  inputSchema: {
    projectPath: z.string().describe('Absolute path for the new project file (.xml)'),
    programName: z.string().optional().default('main').describe('Name of the main program POU'),
    stSource: z.string().describe('Structured Text source code for the main program'),
    variables: z.array(z.object({
      name: z.string(),
      type: z.string(),
      class: z.enum(['input', 'output', 'local']).optional().default('local'),
      initialValue: z.string().optional(),
      address: z.string().optional(),
    })).optional().default([]).describe('Variable declarations for the program'),
  },
};

export async function projectCreateToolHandler({
  projectPath,
  programName,
  stSource,
  variables,
}: {
  projectPath: string;
  programName?: string;
  stSource: string;
  variables?: Array<{
    name: string;
    type: string;
    class?: string;
    initialValue?: string;
    address?: string;
  }>;
}) {
  const name = programName ?? 'main';
  const vars = variables ?? [];
  const now = new Date().toISOString();

  // Build variable XML sections
  const varSections: Record<string, string[]> = {
    localVars: [],
    inputVars: [],
    outputVars: [],
  };

  for (const v of vars) {
    const varXml = `          <variable name="${escapeXml(v.name)}">
            <type><${escapeXml(v.type)} /></type>${v.initialValue ? `
            <initialValue><simpleValue value="${escapeXml(v.initialValue)}" /></initialValue>` : ''}${v.address ? `
            <address>${escapeXml(v.address)}</address>` : ''}
          </variable>`;

    const cls = v.class ?? 'local';
    if (cls === 'input') varSections.inputVars.push(varXml);
    else if (cls === 'output') varSections.outputVars.push(varXml);
    else varSections.localVars.push(varXml);
  }

  const buildVarBlock = (tag: string, items: string[]) =>
    items.length === 0 ? '' : `
        <${tag}>
${items.join('\n')}
        </${tag}>`;

  const xml = `<?xml version='1.0' encoding='utf-8'?>
<project xmlns:ns1="http://www.plcopen.org/xml/tc6_0201"
         xmlns:xhtml="http://www.w3.org/1999/xhtml"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema"
         xmlns="http://www.plcopen.org/xml/tc6_0201">
  <fileHeader companyName="" productName="OpenPLC Toolkit"
              productVersion="1" creationDateTime="${now}" />
  <contentHeader name="${escapeXml(name)}"
                 modificationDateTime="${now}">
    <coordinateInfo>
      <fbd><scaling x="10" y="10" /></fbd>
      <ld><scaling x="10" y="10" /></ld>
      <sfc><scaling x="10" y="10" /></sfc>
    </coordinateInfo>
  </contentHeader>
  <types>
    <dataTypes />
    <pous>
      <pou name="${escapeXml(name)}" pouType="program">
        <interface>${buildVarBlock('localVars', varSections.localVars)}${buildVarBlock('inputVars', varSections.inputVars)}${buildVarBlock('outputVars', varSections.outputVars)}
        </interface>
        <body>
          <ST>
            <xhtml:p><![CDATA[${stSource}]]></xhtml:p>
          </ST>
        </body>
      </pou>
    </pous>
  </types>
  <instances>
    <configurations>
      <configuration name="config">
        <resource name="resource1">
          <task name="task0" interval="T#20ms" priority="0">
            <pouInstance name="${escapeXml(name)}0" typeName="${escapeXml(name)}" />
          </task>
        </resource>
      </configuration>
    </configurations>
  </instances>
</project>
`;

  const absPath = resolve(projectPath);
  await mkdir(dirname(absPath), { recursive: true });
  await writeFile(absPath, xml, 'utf-8');

  return {
    content: [{
      type: 'text' as const,
      text: JSON.stringify({
        success: true,
        projectPath: absPath,
        programName: name,
        variableCount: vars.length,
        format: 'PLCopen XML (IEC 61131-10)',
      }, null, 2),
    }],
  };
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}
