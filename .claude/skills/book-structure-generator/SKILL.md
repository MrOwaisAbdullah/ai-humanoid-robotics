---
name: book-structure-generator
description: Generates comprehensive book structures for Docusaurus with proper hierarchy, navigation, and SEO. Creates chapter outlines, sidebar configurations, and ensures consistent structure across the book.
category: content
version: 1.0.0
---

# Book Structure Generator Skill

## Purpose

Rapidly scaffold well-organized book structures for Docusaurus projects with:
- Logical chapter organization (Parts → Chapters → Sections)
- Proper Docusaurus sidebar configuration
- SEO-optimized frontmatter
- Consistent naming conventions
- Progressive learning path

## When to Use This Skill

Use this skill when:
- Starting a new book project
- Restructuring existing documentation
- Creating comprehensive educational content
- Planning chapter dependencies and learning progression

## Core Capabilities

### 1. Chapter Hierarchy Design

**Standard Book Structure:**
```
Part 0: Front Matter
├── Preface/Welcome
└── Table of Contents (auto-generated)

Part 1: Foundation (Chapters 1-3)
├── Chapter 1: Introduction
├── Chapter 2: Core Concepts
└── Chapter 3: Ecosystem

Part 2: Core Knowledge (Chapters 4-7)
├── Chapter 4: [Core Skill 1]
├── Chapter 5: [Core Skill 2]
├── Chapter 6: [Core Skill 3]
└── Chapter 7: Integration & Best Practices

Part 3: Advanced Topics (Chapters 8-10)
├── Chapter 8: Advanced Techniques
├── Chapter 9: Real-World Projects
└── Chapter 10: Future Directions

Part 4: Back Matter
├── Appendix A: Glossary
└── Appendix B: Resources
```

### 2. Sidebar Configuration Generator

**Template for `sidebars.js`:**
```javascript
module.exports = {
  bookSidebar: [
    // Welcome
    {
      type: 'doc',
      id: 'index',
      label: '👋 Welcome',
    },

    // Part 1: Foundation
    {
      type: 'category',
      label: '📚 Part 1: Foundation',
      collapsible: true,
      collapsed: false,
      items: [
        'part-1-foundation/chapter-1-introduction',
        'part-1-foundation/chapter-2-core-concepts',
        'part-1-foundation/chapter-3-ecosystem',
      ],
    },

    // Part 2: Core Knowledge
    {
      type: 'category',
      label: '🎯 Part 2: Core Knowledge',
      collapsible: true,
      collapsed: false,
      items: [
        'part-2-core/chapter-4-skill-1',
        'part-2-core/chapter-5-skill-2',
        'part-2-core/chapter-6-skill-3',
        'part-2-core/chapter-7-integration',
      ],
    },

    // Part 3: Advanced
    {
      type: 'category',
      label: '🚀 Part 3: Advanced Topics',
      collapsible: true,
      collapsed: false,
      items: [
        'part-3-advanced/chapter-8-advanced',
        'part-3-advanced/chapter-9-projects',
        'part-3-advanced/chapter-10-future',
      ],
    },

    // Appendices
    {
      type: 'category',
      label: '📖 Appendices',
      collapsible: true,
      collapsed: true,
      items: [
        'appendices/glossary',
        'appendices/resources',
      ],
    },
  ],
};
```

### 3. Chapter Outline Generation

For each chapter, generate detailed outline:

**Input:** Topic + Target audience + Learning goals
**Output:** Detailed chapter structure with sections

**Example Process:**
```
Topic: "Introduction to RAG Systems"
Audience: Intermediate developers
Goals: Understand RAG architecture, implement basic RAG

Generated Outline:
├── What You'll Learn (3-5 bullets)
├── Why RAG Matters (motivation)
├── RAG Architecture Overview
│   ├── Components breakdown
│   ├── Data flow diagram
│   └── Key concepts
├── Building Your First RAG System
│   ├── Step 1: Document ingestion
│   ├── Step 2: Vector storage
│   ├── Step 3: Retrieval
│   └── Step 4: Generation
├── Best Practices
├── Common Pitfalls
└── Summary & Next Steps
```

### 4. Frontmatter Template Generation

**Template:** (see `templates/frontmatter-template.yaml`)
```yaml
---
title: "Chapter [X]: [Title] - [Book Name]"
description: "[SEO-optimized 150-160 character description that captures the chapter's value and includes primary keyword]"
keywords:
  - [primary-keyword]
  - [secondary-keyword-1]
  - [secondary-keyword-2]
  - [long-tail-keyword-1]
  - [long-tail-keyword-2]
sidebar_label: "[Short Title for Sidebar]"
sidebar_position: [X]
slug: /part-[X]/chapter-[X]-[slug]
tags:
  - [category-tag]
  - [difficulty-tag]
image: /img/chapters/chapter-[X]-cover.png
---
```

## Usage Instructions

### Basic Usage
```
Use the book-structure-generator skill to create a complete book structure for:

Topic: [Book Topic]
Target Audience: [Description]
Estimated Chapters: [Number]
Focus Areas: [List key topics]

Generate:
1. Complete chapter hierarchy (with titles)
2. Sidebar configuration (sidebars.js)
3. Individual chapter outlines
4. File/folder structure
```

### Advanced Usage with Customization
```
Use book-structure-generator skill with these customizations:

Structure Type: Tutorial-heavy (more hands-on chapters)
Chapter Count: 12 chapters
Special Requirements:
- Each chapter must have a "Try It Yourself" section
- Include 2 appendices (glossary + CLI reference)
- Add a "Quick Start" chapter before Part 1
```

## File Naming Conventions

**Chapters:**
```
docs/
├── index.md                                    # Welcome page
├── part-1-foundation/
│   ├── chapter-1-introduction.md
│   ├── chapter-2-core-concepts.md
│   └── chapter-3-ecosystem.md
├── part-2-core/
│   ├── chapter-4-[topic-slug].md
│   └── ...
└── appendices/
    ├── glossary.md
    └── resources.md
```

**Rules:**
- Use kebab-case (lowercase with hyphens)
- Start with chapter number for clarity
- Keep slugs concise (3-4 words max)
- Be descriptive (avoid generic names like "chapter-4.md")

## Quality Checklist

Every generated structure must ensure:
- [ ] Logical progression (simple → complex)
- [ ] Clear learning path (each chapter builds on previous)
- [ ] Balanced chapter lengths (2000-4000 words each)
- [ ] Consistent naming conventions
- [ ] SEO-optimized titles and descriptions
- [ ] Proper sidebar hierarchy
- [ ] Mobile-friendly navigation
- [ ] Cross-references planned

## Examples

See `examples/sample-chapter.md` for a complete chapter example following this structure.

## Integration with Subagents

**Use with:**
- **content-writer** subagent: After generating structure, use content-writer to fill chapters
- **docusaurus-architect** subagent: For implementing the sidebar configuration

## Customization Options

The skill supports these variations:

**Structure Types:**
- `academic`: Heavy on theory, formal tone
- `tutorial`: Hands-on, project-based
- `reference`: Comprehensive API/command documentation
- `hybrid`: Mix of conceptual and practical (default)

**Chapter Lengths:**
- `short`: 1500-2500 words (quick reads)
- `medium`: 2000-4000 words (standard)
- `long`: 4000-6000 words (deep dives)

**Learning Styles:**
- `beginner`: More explanation, simpler examples
- `intermediate`: Balanced theory and practice
- `advanced`: Assumes knowledge, focuses on nuance

## Output Format

When this skill is invoked, provide:
1. **Complete Chapter List** (with tentative titles)
2. **Sidebar Configuration** (ready-to-use sidebars.js)
3. **File Structure** (directory tree)
4. **Chapter Outlines** (detailed structure for each chapter)
5. **Frontmatter Templates** (for each chapter)
6. **Cross-Reference Map** (which chapters reference each other)

## Time Savings

**Without this skill:** 3-4 hours to manually plan structure
**With this skill:** 10-15 minutes to generate complete structure

Efficiency gain: **~90% time reduction**