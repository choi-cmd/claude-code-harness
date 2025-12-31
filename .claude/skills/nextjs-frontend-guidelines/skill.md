---
name: nextjs-frontend-guidelines
description: Next.js 15 frontend development guidelines for React 19/TypeScript applications. Modern patterns including App Router, Server/Client Components, MUI v5 styling, Server Actions, performance optimization, and TypeScript best practices. Use when creating components, pages, API routes, fetching data, styling, or working with frontend code.
---

# Next.js 15 Frontend Development Guidelines

## Purpose

Comprehensive guide for modern Next.js 15 development with React 19, emphasizing App Router patterns, Server/Client component separation, MUI v5 styling, and performance optimization.

## When to Use This Skill

- Creating new components or pages
- Building new features with App Router
- Fetching data with Server Components or client-side patterns
- Styling components with MUI v5 and Tailwind CSS 4
- Setting up API routes or Server Actions
- Performance optimization
- Organizing frontend code
- TypeScript best practices

---

## Quick Start

### New Component Checklist

Creating a component? Follow this checklist:

- [ ] Determine if Server or Client Component
- [ ] Use `'use client'` directive only when needed
- [ ] Props type with TypeScript interface
- [ ] Use `@/` import alias for project imports
- [ ] Styles: Inline if <100 lines, separate file if >100 lines
- [ ] Use `useCallback` for event handlers passed to children
- [ ] Named export for components
- [ ] Async Server Components for data fetching when possible
- [ ] Client Components for interactivity (useState, useEffect, event handlers)

### New Feature Checklist

Creating a feature? Set up this structure:

- [ ] Create `src/components/{feature-name}/` directory
- [ ] Separate Server and Client components
- [ ] Create API route if needed: `src/app/api/{feature}/route.ts`
- [ ] Set up TypeScript types in `src/types/`
- [ ] Create route in `src/app/{feature-name}/page.tsx`
- [ ] Use Server Components by default
- [ ] Add Client Components only for interactivity
- [ ] Use Server Actions for mutations when appropriate

---

## Import Patterns Quick Reference

| Pattern | Usage | Example |
|---------|-------|---------|
| `@/` | Project imports (primary) | `import { api } from '@/lib/api'` |
| Relative | Same directory | `import { Component } from './Component'` |

Your project structure (import with `@/` alias):
```
src/                    # Import as '@/'
  app/                  # App Router pages and API routes
  components/           # Reusable components
  lib/                  # Utilities (api.ts, serverAuth.ts, etc.)
  hooks/                # Custom React hooks
  providers/            # Context providers
  types/                # TypeScript types
  utils/                # Utility functions
  const/                # Constants
  interfaces/           # Interfaces
```

---

## Common Imports Cheatsheet

```typescript
// Server Component (no 'use client')
import { Suspense } from 'react';
import { Box, Typography, Button } from '@mui/material';
import type { Metadata } from 'next';

// Client Component
'use client';

import { useState, useCallback, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useRouter } from 'next/navigation';

// MUI Components
import { Box, Paper, Typography, Button, Grid } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';

// Project imports
import { api } from '@/lib/api';
import { getAuth } from '@/lib/serverAuth';

// Types
import type { User } from '@/types/user';
```

---

## Topic Guides

### 🎨 Component Patterns

**Server vs Client Components:**
- **Server Components (default)**: Data fetching, static content, no interactivity
- **Client Components ('use client')**: State, effects, event handlers, browser APIs

**Key Concepts:**
- Server Components are async and fetch data directly
- Client Components need 'use client' directive at the top
- Minimize Client Components for better performance
- Pass data from Server to Client Components via props
- Component structure: Props → Hooks → Handlers → Render → Export

**[📖 Complete Guide: resources/component-patterns.md](resources/component-patterns.md)**

---

### 📊 Data Fetching

**PRIMARY PATTERNS:**

**Server Component Data Fetching (Recommended):**
```typescript
async function Page() {
    const data = await fetch('...', { cache: 'no-store' });
    // Or use your API client
    const users = await api.users.getAll();
    return <div>{/* render */}</div>;
}
```

**Client-Side Data Fetching:**
- Use `@/lib/api` for API calls
- Handle loading/error states manually
- Consider Server Components first

**API Routes:**
- Create in `src/app/api/{route}/route.ts`
- Export GET, POST, PUT, DELETE functions
- Use `NextRequest` and `NextResponse`

**[📖 Complete Guide: resources/data-fetching.md](resources/data-fetching.md)**

---

### 📁 File Organization

**App Router Structure:**
```
src/
  app/
    page.tsx              # Home page (/)
    layout.tsx            # Root layout
    {route}/
      page.tsx            # Route page
      layout.tsx          # Route layout (optional)
    api/
      {route}/
        route.ts          # API route handler
  components/
    {feature}/            # Feature-specific components
      Component.tsx
    shared/               # Truly reusable components
      Button.tsx
```

**Component Organization:**
- Group by feature in `src/components/{feature}/`
- Shared/reusable in `src/components/shared/`
- Keep Server and Client components separate

**[📖 Complete Guide: resources/file-organization.md](resources/file-organization.md)**

---

### 🎨 Styling

**MUI v5 + Tailwind CSS 4:**
- Primary: MUI `sx` prop for component styling
- Secondary: Tailwind classes for utility styling
- Combination: Use both together when appropriate

**MUI v5 Grid (OLD syntax, not v7):**
```typescript
<Grid container spacing={2}>
  <Grid item xs={12} md={6}>  // ✅ MUI v5 syntax
    Content
  </Grid>
</Grid>
```

**Inline vs Separate:**
- <100 lines: Inline `const styles: Record<string, SxProps<Theme>>`
- >100 lines: Separate `.styles.ts` file

**Tailwind CSS 4:**
```typescript
<div className="flex items-center gap-4 p-4">
  <Button className="bg-blue-500 hover:bg-blue-600">
    Click
  </Button>
</div>
```

**[📖 Complete Guide: resources/styling-guide.md](resources/styling-guide.md)**

---

### 🛣️ Routing

**Next.js 15 App Router:**
- File-based routing in `src/app/`
- `page.tsx` for routes
- `layout.tsx` for layouts
- Server Components by default
- Dynamic routes: `[id]/page.tsx`
- Route groups: `(group)/route/page.tsx`

**Navigation:**
```typescript
'use client';
import { useRouter } from 'next/navigation';

const router = useRouter();
router.push('/path');
router.back();
```

**Server-side:**
```typescript
import { redirect } from 'next/navigation';

if (condition) {
  redirect('/login');
}
```

**[📖 Complete Guide: resources/routing-guide.md](resources/routing-guide.md)**

---

### ⏳ Loading & Error States

**App Router Conventions:**

**Loading:**
```typescript
// loading.tsx (route-level)
export default function Loading() {
  return <Skeleton />;
}

// Or use Suspense
<Suspense fallback={<Loading />}>
  <AsyncComponent />
</Suspense>
```

**Error Handling:**
```typescript
// error.tsx (route-level)
'use client';

export default function Error({ error, reset }) {
  return <ErrorUI error={error} onReset={reset} />;
}
```

**Client-Side:**
- Use try/catch for API calls
- Display errors with MUI Snackbar or toast
- Handle loading states with useState

**[📖 Complete Guide: resources/loading-and-error-states.md](resources/loading-and-error-states.md)**

---

### ⚡ Performance

**Next.js 15 Optimizations:**
- Server Components by default (zero JS to client)
- Dynamic imports: `const Heavy = dynamic(() => import('./Heavy'))`
- Image optimization: `next/image` component
- Font optimization: Built-in font loading
- Turbopack: Faster dev builds (already enabled)

**React 19 Patterns:**
- `useMemo`: Expensive computations
- `useCallback`: Event handlers passed to children
- `React.memo`: Prevent unnecessary re-renders

**[📖 Complete Guide: resources/performance.md](resources/performance.md)**

---

### 📘 TypeScript

**Standards:**
- Strict mode enabled
- Explicit return types on functions
- Type imports: `import type { User } from '@/types/user'`
- Component prop interfaces with JSDoc
- No `any` type (use `unknown` if needed)

**Next.js Types:**
```typescript
import type { Metadata } from 'next';
import type { NextRequest } from 'next/server';

export const metadata: Metadata = {
  title: 'Page Title',
};
```

**[📖 Complete Guide: resources/typescript-standards.md](resources/typescript-standards.md)**

---

### 🔧 Common Patterns

**Covered Topics:**
- Server Actions for mutations
- API Route handlers
- Authentication with JWT (serverAuth.ts)
- File uploads to S3 (s3Upload.ts)
- Form handling patterns
- MUI theme customization

**[📖 Complete Guide: resources/common-patterns.md](resources/common-patterns.md)**

---

### 📚 Complete Examples

**Full working examples:**
- Server Component with data fetching
- Client Component with state/effects
- API Route handler
- Server Action for mutations
- Page with Suspense boundaries
- Form with validation

**[📖 Complete Guide: resources/complete-examples.md](resources/complete-examples.md)**

---

## Navigation Guide

| Need to... | Read this resource |
|------------|-------------------|
| Create a component | [component-patterns.md](resources/component-patterns.md) |
| Fetch data | [data-fetching.md](resources/data-fetching.md) |
| Organize files/folders | [file-organization.md](resources/file-organization.md) |
| Style components | [styling-guide.md](resources/styling-guide.md) |
| Set up routing | [routing-guide.md](resources/routing-guide.md) |
| Handle loading/errors | [loading-and-error-states.md](resources/loading-and-error-states.md) |
| Optimize performance | [performance.md](resources/performance.md) |
| TypeScript types | [typescript-standards.md](resources/typescript-standards.md) |
| Forms/Auth/API Routes | [common-patterns.md](resources/common-patterns.md) |
| See full examples | [complete-examples.md](resources/complete-examples.md) |

---

## Core Principles

1. **Server Components First**: Use Server Components by default, Client Components only for interactivity
2. **Async Data Fetching**: Fetch data directly in Server Components
3. **Minimize Client JS**: Less JavaScript sent to the browser = better performance
4. **App Router Conventions**: Use loading.tsx, error.tsx, layout.tsx appropriately
5. **Styles Based on Size**: <100 inline, >100 separate file
6. **Import with @/ alias**: Consistent import paths across the project
7. **MUI v5 + Tailwind**: Combine both styling systems appropriately
8. **Type Safety**: Strict TypeScript with explicit types

---

## Quick Reference: File Structure

```
src/
  app/
    page.tsx                    # Home page
    layout.tsx                  # Root layout
    loading.tsx                 # Root loading UI
    error.tsx                   # Root error UI

    login/
      page.tsx                  # Login page

    artists/
      page.tsx                  # Artists list
      [id]/
        page.tsx                # Artist detail

    api/
      upload/
        route.ts                # Upload API endpoint

  components/
    artist/
      ArtistCard.tsx            # Artist-specific component
      ArtistProfile.tsx
    shared/
      Button.tsx                # Reusable component
      Header.tsx

  lib/
    api.ts                      # API client
    serverAuth.ts               # Server-side auth
    s3Upload.ts                 # S3 upload utilities

  types/
    user.ts                     # User types
    artist.ts                   # Artist types
```

---

## Server Component Template (Quick Copy)

```typescript
import { Box, Typography } from '@mui/material';
import { api } from '@/lib/api';
import type { User } from '@/types/user';

interface PageProps {
  params: { id: string };
  searchParams: { [key: string]: string | string[] | undefined };
}

export default async function Page({ params }: PageProps) {
  // Fetch data directly
  const user: User = await api.users.getById(params.id);

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4">{user.name}</Typography>
      {/* Content */}
    </Box>
  );
}
```

## Client Component Template (Quick Copy)

```typescript
'use client';

import { useState, useCallback } from 'react';
import { Box, Button, Typography } from '@mui/material';
import { api } from '@/lib/api';

interface MyComponentProps {
  userId: string;
}

export function MyComponent({ userId }: MyComponentProps) {
  const [data, setData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFetch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.users.getById(userId);
      setData(result.name);
    } catch (error) {
      console.error('Fetch failed:', error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  return (
    <Box sx={{ p: 2 }}>
      <Button onClick={handleFetch} disabled={loading}>
        Fetch Data
      </Button>
      {data && <Typography>{data}</Typography>}
    </Box>
  );
}
```

For complete examples, see [resources/complete-examples.md](resources/complete-examples.md)

---

## Related Skills

- **error-tracking**: Error tracking with Sentry (applies to frontend too)
- **backend-dev-guidelines**: Backend API patterns that frontend consumes

---

**Skill Status**: Modular structure with progressive loading for optimal context management
