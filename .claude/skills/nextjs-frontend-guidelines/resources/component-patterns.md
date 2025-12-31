# Component Patterns - Next.js 15

## Server Components vs Client Components

### Server Components (Default)

**When to use:**
- Static content that doesn't change
- Data fetching from APIs or databases
- No interactivity needed
- SEO-critical content

**Characteristics:**
- No `'use client'` directive
- Can be async functions
- Fetch data directly
- Zero JavaScript sent to client
- Cannot use hooks (useState, useEffect, etc.)
- Cannot use browser APIs
- Cannot use event handlers

```typescript
// Server Component (no 'use client')
import { Box, Typography } from '@mui/material';
import { api } from '@/lib/api';
import type { Artist } from '@/types/artist';

interface ArtistProfileProps {
  artistId: string;
}

export default async function ArtistProfile({ artistId }: ArtistProfileProps) {
  // Fetch data directly - this runs on the server
  const artist: Artist = await api.artists.getById(artistId);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4">{artist.name}</Typography>
      <Typography variant="body1">{artist.bio}</Typography>
    </Box>
  );
}
```

### Client Components

**When to use:**
- State management (useState)
- Effects (useEffect)
- Event handlers (onClick, onChange, etc.)
- Browser APIs (localStorage, window, etc.)
- Custom hooks
- Context providers

**Characteristics:**
- Must have `'use client'` at the top of the file
- Can use all React hooks
- Can use browser APIs
- Sends JavaScript to the client
- Interactive elements

```typescript
'use client';

import { useState, useCallback } from 'react';
import { Box, Button, TextField } from '@mui/material';
import { api } from '@/lib/api';

interface CommentFormProps {
  artworkId: string;
  onSubmit?: () => void;
}

export function CommentForm({ artworkId, onSubmit }: CommentFormProps) {
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(async () => {
    setLoading(true);
    try {
      await api.comments.create({ artworkId, text: comment });
      setComment('');
      onSubmit?.();
    } catch (error) {
      console.error('Failed to submit comment:', error);
    } finally {
      setLoading(false);
    }
  }, [artworkId, comment, onSubmit]);

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <TextField
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Add a comment..."
        fullWidth
      />
      <Button onClick={handleSubmit} disabled={loading}>
        Submit
      </Button>
    </Box>
  );
}
```

## Component Structure Pattern

### Recommended Order

```typescript
'use client'; // Only if needed

// 1. Imports
import { useState, useCallback } from 'react';
import { Box, Button } from '@mui/material';
import { api } from '@/lib/api';
import type { User } from '@/types/user';

// 2. Types/Interfaces
interface MyComponentProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

// 3. Component Function
export function MyComponent({ userId, onUpdate }: MyComponentProps) {
  // 4. State
  const [data, setData] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  // 5. Hooks (useCallback, useMemo, useEffect, custom hooks)
  const fetchUser = useCallback(async () => {
    setLoading(true);
    try {
      const user = await api.users.getById(userId);
      setData(user);
      onUpdate?.(user);
    } finally {
      setLoading(false);
    }
  }, [userId, onUpdate]);

  // 6. Render
  return (
    <Box sx={{ p: 2 }}>
      <Button onClick={fetchUser} disabled={loading}>
        Fetch User
      </Button>
      {data && <div>{data.name}</div>}
    </Box>
  );
}
```

## Mixing Server and Client Components

### Pattern: Server Component with Client Child

```typescript
// app/artists/page.tsx (Server Component)
import { ArtistList } from '@/components/artist/ArtistList'; // Server
import { ArtistFilters } from '@/components/artist/ArtistFilters'; // Client
import { api } from '@/lib/api';

export default async function ArtistsPage() {
  // Fetch data on server
  const artists = await api.artists.getAll();

  return (
    <div>
      {/* Client Component for interactive filters */}
      <ArtistFilters />

      {/* Server Component for static list */}
      <ArtistList artists={artists} />
    </div>
  );
}
```

### Pattern: Passing Data from Server to Client

```typescript
// Server Component
import { ClientComponent } from './ClientComponent';

export default async function ServerPage() {
  const data = await fetch('...');

  // Pass data as props to Client Component
  return <ClientComponent initialData={data} />;
}

// ClientComponent.tsx
'use client';

interface ClientComponentProps {
  initialData: DataType;
}

export function ClientComponent({ initialData }: ClientComponentProps) {
  const [data, setData] = useState(initialData);
  // ... client-side logic
}
```

## Performance Patterns

### Dynamic Imports

For heavy Client Components, use dynamic imports:

```typescript
import dynamic from 'next/dynamic';

// Lazy load with loading state
const HeavyChart = dynamic(
  () => import('@/components/charts/HeavyChart'),
  {
    loading: () => <div>Loading chart...</div>,
    ssr: false, // Disable SSR if component uses browser APIs
  }
);

export function Dashboard() {
  return (
    <div>
      <HeavyChart data={...} />
    </div>
  );
}
```

### React.memo for Expensive Components

```typescript
'use client';

import { memo } from 'react';

interface ExpensiveListProps {
  items: Item[];
}

export const ExpensiveList = memo(function ExpensiveList({ items }: ExpensiveListProps) {
  // Expensive rendering logic
  return (
    <ul>
      {items.map(item => <li key={item.id}>{item.name}</li>)}
    </ul>
  );
});
```

## Common Patterns

### useCallback for Event Handlers

Always use `useCallback` for event handlers passed to child components:

```typescript
'use client';

import { useCallback } from 'react';

export function Parent() {
  const [count, setCount] = useState(0);

  // ✅ Wrapped in useCallback
  const handleClick = useCallback(() => {
    setCount(prev => prev + 1);
  }, []);

  return <Child onClick={handleClick} />;
}
```

### Form Handling

```typescript
'use client';

import { useState, useCallback, FormEvent } from 'react';
import { Box, TextField, Button } from '@mui/material';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    // Handle submission
  }, [email, password]);

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        label="Email"
      />
      <TextField
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        label="Password"
      />
      <Button type="submit">Login</Button>
    </Box>
  );
}
```

## TypeScript Patterns

### Component Props with JSDoc

```typescript
interface ButtonProps {
  /** The text to display on the button */
  label: string;
  /** Optional click handler */
  onClick?: () => void;
  /** Whether the button is in a loading state */
  loading?: boolean;
}

export function Button({ label, onClick, loading = false }: ButtonProps) {
  return <button onClick={onClick} disabled={loading}>{label}</button>;
}
```

### Extracting Types

```typescript
// types/artist.ts
export interface Artist {
  id: string;
  name: string;
  bio: string;
  artworks: Artwork[];
}

// Component
import type { Artist } from '@/types/artist';

interface ArtistCardProps {
  artist: Artist;
}
```

## Best Practices

1. **Default to Server Components**: Only use Client Components when you need interactivity
2. **Keep Client Components Small**: Extract non-interactive parts to Server Components
3. **Pass Data Down**: Fetch in Server Components, pass to Client Components via props
4. **Use Callbacks**: Wrap event handlers in `useCallback` to prevent re-renders
5. **Type Everything**: Explicit types for props, state, and return values
6. **Named Exports**: Use named exports for components (easier to search and refactor)
7. **Async Server Components**: Take advantage of async/await in Server Components
8. **Error Boundaries**: Wrap Client Components with error.tsx for graceful failures
