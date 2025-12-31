# Next.js Frontend Guidelines Skill

## Overview

This skill provides comprehensive frontend development guidelines adapted specifically for your qwarty project's tech stack:

- **Next.js 15** with App Router
- **React 19**
- **TypeScript**
- **MUI v5** (NOT v7)
- **Tailwind CSS 4**

## What Was Adapted

This skill was created by adapting the showcase repository's `frontend-dev-guidelines` (which was designed for React + MUI v7 + TanStack) to match your actual stack.

### Key Differences from Original

| Original Skill | Your Adapted Skill |
|----------------|-------------------|
| MUI v7 (Grid with `size={{}}`) | MUI v5 (Grid with `xs/sm/md` props) |
| TanStack Query (`useSuspenseQuery`) | Native fetch + Server Components |
| TanStack Router | Next.js 15 App Router |
| Vite | Next.js with Turbopack |
| Generic React patterns | Next.js Server/Client Component patterns |

## What This Skill Covers

1. **Component Patterns** - Server Components vs Client Components, when to use each
2. **Data Fetching** - Server Component async fetching, client-side patterns, API routes
3. **Styling** - MUI v5 `sx` prop + Tailwind CSS 4 combination
4. **Routing** - App Router file-based routing, dynamic routes, navigation
5. **Loading & Error States** - loading.tsx, error.tsx, Suspense boundaries
6. **Performance** - Server Components optimization, dynamic imports, image optimization
7. **TypeScript** - Strict typing, Next.js types, component props
8. **Common Patterns** - Authentication, file upload to S3, forms, pagination
9. **Complete Examples** - Full working examples for Server/Client components

## Skill Activation

The skill is configured to activate when:

### File Triggers
- Working in `frontend/src/**/*.tsx` or `frontend/src/**/*.ts`
- Files containing MUI imports, Grid components, 'use client', Next.js patterns

### Prompt Triggers
- Keywords: "component", "React", "UI", "page", "Next.js", "server component", "MUI", "styling"
- Intent patterns: Creating/editing components, styling questions, Next.js patterns

### Enforcement
- **Type**: Guardrail (blocks execution)
- **Priority**: High
- You must use the skill before working on frontend files to ensure best practices

## Quick Start

### Test the Skill

Try editing a frontend component file:

```bash
# Open a frontend file
code frontend/src/components/artist/ArtistCard.tsx
```

The skill should automatically suggest when you:
1. Ask about creating a component
2. Edit a .tsx file in the frontend
3. Ask about styling or MUI patterns

### Skip Validation (if needed)

Add this comment to any file to skip validation:

```typescript
// @skip-validation
```

## Project Structure Match

The skill references YOUR actual project structure:

```
frontend/
  src/
    app/              # Next.js App Router (referenced in skill)
    components/       # Your components (referenced in skill)
    lib/
      api.ts          # Your API client (used in examples)
      serverAuth.ts   # Your auth (used in examples)
      s3Upload.ts     # Your S3 upload (used in examples)
    types/            # Your types (referenced in skill)
```

## Integration Status

✅ Skill directory created: `.claude/skills/nextjs-frontend-guidelines/`
✅ Main skill.md adapted for Next.js 15 + MUI v5
✅ 10 resource files created with Next.js patterns
✅ skill-rules.json updated with new skill configuration
✅ Old frontend-dev-guidelines deprecated but kept for reference
✅ Skill activation hooks already set up and working

## Next Steps

1. **Test the skill**: Edit a frontend component and the skill should suggest
2. **Review the patterns**: Read through skill.md for quick reference
3. **Expand resources**: Add more examples as your project patterns evolve
4. **Update triggers**: Modify skill-rules.json if you need different activation patterns

## Maintenance

As your project evolves, you can:

1. **Add new patterns**: Create new .md files in `resources/`
2. **Update examples**: Edit resource files with project-specific examples
3. **Adjust triggers**: Modify `skill-rules.json` to change when skill activates
4. **Add skip markers**: Use `// @skip-validation` in files that don't need checking

## Files Created

```
.claude/skills/nextjs-frontend-guidelines/
  ├── skill.md                              # Main skill overview
  ├── README.md                             # This file
  └── resources/
      ├── component-patterns.md             # Server vs Client components
      ├── data-fetching.md                  # Async fetching, API routes
      ├── styling-guide.md                  # MUI v5 + Tailwind CSS 4
      ├── file-organization.md              # Project structure
      ├── routing-guide.md                  # App Router patterns
      ├── loading-and-error-states.md       # Loading and error handling
      ├── performance.md                    # Optimization patterns
      ├── typescript-standards.md           # Type safety
      ├── common-patterns.md                # Auth, forms, uploads
      └── complete-examples.md              # Full working examples
```

## Tech Stack Compatibility

✅ **Next.js 15**: All patterns use App Router
✅ **React 19**: Server/Client component patterns
✅ **MUI v5**: Grid uses `xs/sm/md` props (NOT `size={{}}`)
✅ **TypeScript**: Strict typing throughout
✅ **Tailwind CSS 4**: Combined with MUI patterns
✅ **Your API client**: Examples use `src/lib/api.ts`
✅ **Your auth**: Examples use `src/lib/serverAuth.ts`
✅ **Your S3 upload**: Examples use `src/lib/s3Upload.ts`

---

**Status**: ✅ Fully integrated and ready to use
**Created**: 2025-11-02
**Adapted from**: claude-code-infrastructure-showcase/frontend-dev-guidelines
