# Common Patterns - Next.js 15

## Authentication

### Server-Side Auth Check

```typescript
import { cookies } from 'next/headers';
import { getAuth } from '@/lib/serverAuth';
import { redirect } from 'next/navigation';

export default async function ProtectedPage() {
  const cookieStore = await cookies();
  const auth = await getAuth({ cookies: cookieStore });

  if (!auth.isAuthenticated) {
    redirect('/login');
  }

  return <div>Protected Content</div>;
}
```

### Client-Side Auth Hook

```typescript
'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.auth.getUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return { user, loading, isAuthenticated: !!user };
}
```

## File Upload to S3

```typescript
'use client';

import { useState, useCallback } from 'react';
import { uploadToS3 } from '@/lib/s3Upload';

export function FileUploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    try {
      const url = await uploadToS3(file);
      console.log('Uploaded to:', url);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  }, [file]);

  return (
    <div>
      <input
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  );
}
```

## Form Handling

### With Server Actions

```typescript
// app/actions.ts
'use server';

export async function submitForm(formData: FormData) {
  const name = formData.get('name') as string;
  const email = formData.get('email') as string;

  // Process form data
  await api.users.create({ name, email });

  return { success: true };
}

// Component
'use client';

import { useState } from 'react';
import { submitForm } from './actions';

export function Form() {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const result = await submitForm(formData);

    if (result.success) {
      e.currentTarget.reset();
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" required />
      <input name="email" type="email" required />
      <button type="submit" disabled={loading}>
        Submit
      </button>
    </form>
  );
}
```

## Pagination

```typescript
'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export function PaginatedList() {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.items.getPage(page)
      .then(setItems)
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div>
      {loading ? <div>Loading...</div> : <List items={items} />}
      <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>
        Previous
      </button>
      <span>Page {page}</span>
      <button onClick={() => setPage(p => p + 1)}>
        Next
      </button>
    </div>
  );
}
```

## MUI Theme Customization

```typescript
// lib/theme.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: 'IBM Plex Sans, sans-serif',
  },
});

// Usage in layout
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '@/lib/theme';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <ThemeProvider theme={theme}>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```
