# B-Mad Method Installation

This directory contains a basic installation of the B-Mad Method (v6 Alpha) framework.

## What is B-Mad Method?

The B-Mad Method (Breakthrough Method for Agile AI Driven Development) is a complete AI-driven agile development framework that revolutionizes how you build software.

## What's Installed

### Core Module
- **Location**: `.bmad/core/`
- **Contains**: Base agents, workflows, tasks, and tools
- **Config**: `.bmad/core/config.yaml`

### BMad Method (BMM) Module
- **Location**: `.bmad/bmm/`
- **Contains**: PM, Analyst, Architect, Developer, and other specialized agents
- **Config**: `.bmad/bmm/config.yaml`
- **Workflows**: Planning, implementation, and review workflows
- **Documentation**: `.bmad/bmm/docs/`

## Configuration

### Core Settings (`.bmad/core/config.yaml`)
- User Name: Jeremy
- Communication Language: English
- Artifacts Folder: docs

### BMM Settings (`.bmad/bmm/config.yaml`)
- Project Name: Jeremy Project 1
- Output Folder: docs
- Story Location: docs/sprint-artifacts

## Available Agents

### BMM Agents (`.bmad/bmm/agents/`)
- **PM (Product Manager)**: `pm.agent.yaml` - Product strategy and requirements
- **Analyst**: `analyst.agent.yaml` - Requirements analysis
- **Architect**: `architect.agent.yaml` - System architecture
- **Developer (Dev)**: `dev.agent.yaml` - Implementation
- **Scrum Master (SM)**: `sm.agent.yaml` - Sprint facilitation
- **Test Architect (TEA)**: `tea.agent.yaml` - Test strategy
- **UX Designer**: `ux-designer.agent.yaml` - User experience
- **Tech Writer**: `tech-writer.agent.yaml` - Documentation

### Core Agents (`.bmad/core/agents/`)
- **BMad Master**: `bmad-master.agent.yaml` - Orchestrator

## Next Steps

To complete the installation with full agent compilation and Claude Code integration:

```bash
npx bmad-method@alpha install
```

This will:
1. Compile all agent YAML files to executable formats
2. Set up Claude Code slash commands in `.claude/commands/bmad/`
3. Configure workflow launchers
4. Install subagents if desired

## Resources

- **Main Repository**: https://github.com/bmad-code-org/BMAD-METHOD
- **Documentation**: `.bmad/bmm/docs/`
- **Quick Start**: `.bmad/bmm/docs/quick-start.md`
- **Workflows Guide**: `.bmad/bmm/workflows/README.md`

## Project Information

- **Version**: 6.0.0-alpha.9
- **Installation Date**: 2025-11-16
- **Project**: Jeremy-Project-1-Claude
