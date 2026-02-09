# OpenPLC Toolkit — Strategic Plan

## Vision

A **headless-first, LLM-native PLC development platform** for IEC 61131-3 programming.

The industrial automation world is locked into vendor silos — Siemens TIA Portal,
Rockwell Studio 5000, CODESYS — each with proprietary formats and no real
interoperability. Meanwhile, LLMs can already write decent Structured Text but
have no way to compile, validate, or deploy it.

We're building the missing layer: a **universal PLC toolkit** that connects
LLM agents to real PLC hardware, reads any vendor's code, and treats the
terminal as a first-class citizen.

## Principles

1. **Headless-first** — The core engine is a library and CLI, not an app.
   GUIs are consumers, not the product.

2. **LLM-native** — Every interface returns structured data (JSON diagnostics,
   typed errors with fix suggestions). The MCP server makes PLC tools
   callable by any AI agent.

3. **Compiler-in-the-loop** — LLMs generating PLC code go from ~27% compilation
   success to 90%+ when they get structured compiler feedback. This is the
   killer feature.

4. **Vendor-neutral IR** — Parse all formats (PLCopen XML, Rockwell L5X,
   Siemens SimaticML) into one common AST. Convert between them.

5. **Standards-based** — PLCopen XML (IEC 61131-10) as the pivot format.
   OPC-UA for runtime. IEC 61131-3 Edition 4 (2025) as the language baseline.

6. **Incrementally useful** — Each phase delivers standalone value.
   Don't wait for a monolith.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      USER INTERFACES                         │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌───────────┐ │
│  │ Web IDE  │  │   CLI    │  │  VS Code   │  │  LLM      │ │
│  │ (future) │  │ (plc)    │  │  Extension │  │  Agent    │ │
│  │          │  │          │  │  (via LSP) │  │  (via MCP)│ │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └─────┬─────┘ │
│       └──────────────┴──────────────┴───────────────┘       │
│                           │                                  │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │              CORE ENGINE (Headless)                    │   │
│  │                                                        │   │
│  │  ┌──────────────────┐   ┌───────────────────────────┐ │   │
│  │  │ ST Language       │   │   Format Importers        │ │   │
│  │  │ Server (LSP)      │   │                           │ │   │
│  │  │                   │   │  ┌──────────┐ ┌─────────┐ │ │   │
│  │  │ • Parse & AST     │   │  │ PLCopen  │ │Rockwell │ │ │   │
│  │  │ • Autocomplete    │   │  │ XML      │ │L5X      │ │ │   │
│  │  │ • Go-to-def       │   │  ├──────────┤ ├─────────┤ │ │   │
│  │  │ • Hover info      │   │  │ Siemens  │ │CODESYS  │ │ │   │
│  │  │ • Diagnostics     │   │  │ SimatML  │ │Native   │ │ │   │
│  │  └──────────────────┘   │  └──────────┘ └─────────┘ │ │   │
│  │                          └───────────────────────────┘ │   │
│  │                                                        │   │
│  │  ┌──────────────────┐   ┌───────────────────────────┐ │   │
│  │  │  Compiler         │   │  Vendor-Neutral AST / IR  │ │   │
│  │  │                   │   │                           │ │   │
│  │  │  MatIEC (iec2c)   │   │  Common representation   │ │   │
│  │  │  RuSTy (future)   │   │  for all IEC 61131-3     │ │   │
│  │  │                   │   │  languages and formats    │ │   │
│  │  └──────────────────┘   └───────────────────────────┘ │   │
│  │                                                        │   │
│  │  ┌────────────────────────────────────────────────────┐│   │
│  │  │               Target Runtimes                      ││   │
│  │  │  Linux  │  Arduino  │  ESP32  │  Pico  │  OpenPLC  ││   │
│  │  └────────────────────────────────────────────────────┘│   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              LLM AGENT INTERFACE                        │   │
│  │                                                         │   │
│  │  • MCP Server (Model Context Protocol)                  │   │
│  │    - compile_st: compile ST code, get structured errors │   │
│  │    - validate_st: fast validation without build output  │   │
│  │    - plc_project_read: parse PLCopen XML projects       │   │
│  │    - plc_project_create: generate projects from ST      │   │
│  │    - st_reference: IEC 61131-3 language reference       │   │
│  │                                                         │   │
│  │  • Compiler-in-the-loop feedback                        │   │
│  │    LLM generates ST → compiler validates → errors fed   │   │
│  │    back with suggestions → LLM fixes → repeat           │   │
│  │                                                         │   │
│  │  • RAG over IEC 61131-3 standard libraries              │   │
│  │  • PLCopen XML ↔ ST bidirectional conversion            │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## The Interoperability Landscape

Understanding what we're working with:

```
                      ENGINEERING DATA
                   ┌──────────────────────┐
                   │  AutomationML (AML)  │  Plant topology, I/O, hardware
                   │    IEC 62714         │
                   └──────────┬───────────┘
                              │ contains
                   ┌──────────▼───────────┐
  PROGRAM EXCHANGE │  PLCopen XML         │  POU source, data types, configs
                   │  (IEC 61131-10)      │  ** The only open standard **
                   └──────────┬───────────┘
                              │ represents
                   ┌──────────▼───────────┐
  LANGUAGES        │  IEC 61131-3         │  ST, LD, FBD, SFC
                   │  Edition 4 (2025)    │  (IL deprecated)
                   └──────────┬───────────┘
                              │ exposed via
                   ┌──────────▼───────────┐
  RUNTIME ACCESS   │  OPC-UA              │  Monitoring, data access
                   │  IEC 62541           │
                   └──────────────────────┘

  VENDOR FORMATS   Siemens: SimaticML  |  Rockwell: L5X/L5K  |  CODESYS: Native XML
                   (No cross-vendor conversion exists today)

  LLM SWEET SPOT   Structured Text (ST) → most amenable to LLM processing
                   PLCopen XML → best standardized intermediate representation
```

## Phased Build Plan

### Phase 1: Foundation (Current — In Progress)
**Goal:** A working CLI + MCP server that can compile ST code and manage PLCopen XML projects.

| Component | Status | Description |
|-----------|--------|-------------|
| Type system (`src/types/`) | Done | Full IEC 61131-3 data model as TypeScript types |
| MatIEC wrapper (`src/compiler/`) | Done | Structured JSON errors with LLM suggestions |
| PLCopen XML parser (`src/parsers/`) | Done | Parse any PLCopen XML into vendor-neutral types |
| MCP Server (`src/mcp-server/`) | Done | 5 tools: compile, validate, project read/create, ST reference |
| CLI (`src/cli/`) | Done | `plc compile`, `plc validate`, `plc parse`, `plc mcp` |
| Examples | Done | `blink.st`, `motor_control.st` |
| npm install + build | TODO | Wire up dependencies, verify TypeScript compiles |
| Tests | TODO | Unit tests for compiler wrapper and PLCopen parser |
| CI pipeline | TODO | GitHub Actions: lint, test, build |

### Phase 2: Language Intelligence
**Goal:** A Structured Text Language Server that makes any editor a PLC IDE.

| Component | Description |
|-----------|-------------|
| ST Parser | Full IEC 61131-3 grammar (use `blark` or `iec-checker` as foundation, or write a Lark/tree-sitter grammar) |
| LSP Server | Implements Language Server Protocol for ST |
| Autocomplete | Variable names, standard functions, function blocks |
| Diagnostics | Real-time error checking as you type |
| Hover info | Type info, documentation on hover |
| Go-to-definition | Navigate to variable/POU declarations |
| VS Code extension | Package the LSP as a VS Code extension |

### Phase 3: Multi-Vendor Import
**Goal:** Read and display PLC programs from major manufacturers.

| Format | Library | Priority | Notes |
|--------|---------|----------|-------|
| PLCopen XML | Built-in (Phase 1) | Done | OpenPLC, Beremiz, CODESYS export, Beckhoff export |
| Rockwell L5X | `l5x` Python lib or custom TS parser | High | Fully documented XML, most open proprietary format |
| Siemens SimaticML | Custom TS parser | High | Semi-documented, exported via TIA Openness API |
| CODESYS Native | Custom TS parser | Medium | More complete than PLCopen XML export |
| Beckhoff TwinCAT | Via PLCopen XML | Low | CODESYS-derived, PLCopen XML export covers most cases |

**Import strategy:**
```
Vendor Format → Vendor Parser → Vendor-Neutral AST → PLCopen XML / ST output
                                       ↕
                              LLM can read/modify
```

### Phase 4: LLM Agent Workflows
**Goal:** Production-ready AI-assisted PLC programming.

| Feature | Description |
|---------|-------------|
| Compiler-in-the-loop | Tight generate→compile→fix loop with max 5 iterations |
| RAG pipeline | Embed IEC 61131-3 standard library docs + vendor docs for retrieval |
| Code generation templates | Task-specific prompts: PID control, motor start/stop, conveyor sequencing |
| Formal verification | Integration with SMV or similar model checker for safety-critical code |
| Multi-agent workflow | Planning agent → Coding agent → Verification agent (like Agents4PLC) |

### Phase 5: Web IDE + Deployment
**Goal:** Full browser-based PLC development environment.

| Feature | Description |
|---------|-------------|
| Monaco-based web editor | ST editing with LSP support in the browser |
| Visual FBD/LD viewer | Read-only visualization of graphical programs (imported from XML) |
| Hardware manager | Discover and connect to OpenPLC runtimes |
| OPC-UA client | Monitor running PLC variables in real-time |
| One-click deploy | Compile → upload → run on target hardware |

## Key Technical Decisions

### Why Headless-First?
The v4 OpenPLC Editor is a beautiful Electron app, but it's a closed box.
You can't CI/CD your PLC code, you can't have an LLM agent compile code,
and you can't integrate it into existing automation workflows. By building
the core as a library + CLI, every interface (GUI, agent, pipeline) gets
equal access.

### Why MCP (Model Context Protocol)?
MCP is the emerging standard for connecting LLM agents to external tools.
By exposing PLC compilation as MCP tools, any MCP-compatible agent (Claude,
GPT, open-source agents) can write and validate PLC code. This is how we
get compiler-in-the-loop for free.

### Why PLCopen XML as the Pivot?
It's the only vendor-neutral standard. Every format we import gets converted
to our AST, which can be serialized as PLCopen XML. This means:
- Import Rockwell L5X → view in our tool → export as PLCopen XML → open in CODESYS
- LLM generates ST → we wrap it in PLCopen XML → open in OpenPLC Editor

### Why Structured Text First?
1. LLMs are good at text, bad at spatial reasoning (LD/FBD)
2. ST is the most expressive IEC 61131-3 language
3. ST can represent anything LD/FBD can (the reverse is not true)
4. ST is plain text — works with git, diff, grep, and LLMs natively
5. The industry is shifting toward ST anyway

### Why Not Fork the v4 Editor?
The v4 editor (Autonomy-Logic) is React/Electron with a deeply coupled
architecture. Extracting the headless core would be harder than building
from scratch. We can use their bundled MatIEC binaries and reference
their code, but our architecture is fundamentally different: we're
building a toolkit, not an IDE.

## Competitive Landscape

| Project | What it is | Gap we fill |
|---------|-----------|-------------|
| OpenPLC Editor v4 | GUI-only IDE | No CLI, no LLM integration, no vendor import |
| Beremiz | GUI-only IDE | Same gaps as OpenPLC |
| CODESYS | Commercial IDE | Proprietary, expensive, no LLM integration |
| Eclipse 4diac | IEC 61499 IDE | Different standard (event-driven), not 61131-3 |
| AutoPLC (research) | LLM pipeline for ST | Academic prototype, not a reusable tool |
| Agents4PLC (research) | LLM benchmark | Dataset only, no production tooling |
| RuSTy | Rust ST compiler | Compiler only, no tooling ecosystem |

**Nobody is building a headless, LLM-native PLC toolkit.** This is greenfield.

## File Structure

```
plc-toolkit/
├── package.json              # npm package
├── tsconfig.json             # TypeScript config
├── PLAN.md                   # This file
├── examples/
│   ├── blink.st              # Hello world for PLCs
│   └── motor_control.st      # Industrial control example
└── src/
    ├── index.ts              # Package entry point
    ├── types/
    │   └── index.ts          # IEC 61131-3 type system
    ├── compiler/
    │   ├── index.ts          # Compiler exports
    │   └── matiec.ts         # MatIEC wrapper
    ├── parsers/
    │   ├── index.ts          # Parser exports
    │   └── plcopen-xml.ts    # PLCopen XML parser
    ├── mcp-server/
    │   ├── index.ts          # MCP server entry point
    │   └── tools/
    │       ├── compile.ts    # compile_st tool
    │       ├── validate.ts   # validate_st tool
    │       ├── project.ts    # plc_project_read/create tools
    │       └── st-helpers.ts # st_reference tool
    └── cli/
        └── index.ts          # CLI entry point

Future additions:
    ├── lsp/                  # Language Server Protocol (Phase 2)
    ├── parsers/
    │   ├── rockwell-l5x.ts   # Rockwell L5X parser (Phase 3)
    │   └── siemens-simatml.ts # Siemens SimaticML parser (Phase 3)
    └── agents/               # LLM agent workflows (Phase 4)
```

## Next Steps (Immediate)

1. `npm install` and verify the TypeScript compiles
2. Write unit tests for `parseDiagnostics()` and `parsePLCopenXML()`
3. Test the MCP server with Claude Desktop
4. Set up GitHub Actions CI
5. Start Phase 2: ST parser research (evaluate `blark`, `iec-checker`, tree-sitter)
