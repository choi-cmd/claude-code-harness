# Complete Examples - Next.js 15

## Full Server Component Example

```typescript
// app/artists/page.tsx
import { Suspense } from 'react';
import { Box, Typography, Grid } from '@mui/material';
import { api } from '@/lib/api';
import { ArtistCard } from '@/components/artist/ArtistCard';
import type { Artist } from '@/types/artist';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Artists - Qwarty',
  description: 'Browse our collection of talented artists',
};

export const revalidate = 60; // Revalidate every 60 seconds

export default async function ArtistsPage() {
  // Fetch data directly on the server
  const artists: Artist[] = await api.artists.getAll();

  return (
    <Box sx={{ p: { xs: 2, md: 4 } }}>
      <Typography variant="h3" component="h1" sx={{ mb: 4 }}>
        Artists
      </Typography>

      <Grid container spacing={3}>
        {artists.map((artist) => (
          <Grid item xs={12} sm={6} md={4} key={artist.id}>
            <ArtistCard artist={artist} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
```

## Full Client Component Example

```typescript
// components/artist/ArtistFilters.tsx
'use client';

import { useState, useCallback } from 'react';
import { Box, TextField, Select, MenuItem, Button } from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';

interface ArtistFiltersProps {
  onFilterChange: (filters: FilterState) => void;
}

interface FilterState {
  search: string;
  category: string;
  sortBy: string;
}

export function ArtistFilters({ onFilterChange }: ArtistFiltersProps) {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    category: 'all',
    sortBy: 'name',
  });

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newFilters = { ...filters, search: e.target.value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  }, [filters, onFilterChange]);

  const handleCategoryChange = useCallback((e: SelectChangeEvent) => {
    const newFilters = { ...filters, category: e.target.value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  }, [filters, onFilterChange]);

  const handleReset = useCallback(() => {
    const defaultFilters = { search: '', category: 'all', sortBy: 'name' };
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  }, [onFilterChange]);

  return (
    <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
      <TextField
        placeholder="Search artists..."
        value={filters.search}
        onChange={handleSearchChange}
        sx={{ flex: 1, minWidth: 200 }}
      />

      <Select
        value={filters.category}
        onChange={handleCategoryChange}
        sx={{ minWidth: 150 }}
      >
        <MenuItem value="all">All Categories</MenuItem>
        <MenuItem value="painting">Painting</MenuItem>
        <MenuItem value="sculpture">Sculpture</MenuItem>
        <MenuItem value="digital">Digital Art</MenuItem>
      </Select>

      <Button onClick={handleReset} variant="outlined">
        Reset Filters
      </Button>
    </Box>
  );
}
```

## API Route Example

```typescript
// app/api/artists/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { getAuth } from '@/lib/serverAuth';

export async function GET(request: NextRequest) {
  try {
    // Get search params
    const searchParams = request.nextUrl.searchParams;
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');

    // Fetch artists (from database, external API, etc.)
    const artists = await fetchArtistsFromDatabase({ page, limit });

    return NextResponse.json({
      success: true,
      data: artists,
      page,
      limit,
    });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch artists' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const cookieStore = await cookies();
    const auth = await getAuth({ cookies: cookieStore });

    if (!auth.isAuthenticated) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get request body
    const body = await request.json();

    // Validate and create artist
    const newArtist = await createArtist(body);

    return NextResponse.json(
      { success: true, data: newArtist },
      { status: 201 }
    );
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create artist' },
      { status: 500 }
    );
  }
}
```

## Complete Feature Example

```
src/
  components/
    artist/
      ArtistCard.tsx          # Client component for card
      ArtistProfile.tsx       # Server component for profile
      ArtistFilters.tsx       # Client component for filters

  app/
    artists/
      page.tsx                # Server component - list page
      [id]/
        page.tsx              # Server component - detail page
      loading.tsx             # Loading UI
      error.tsx               # Error UI

  types/
    artist.ts                 # TypeScript types

  lib/
    api.ts                    # API client with artist methods
```

This structure provides:
- Server-side data fetching and rendering
- Client-side interactivity where needed
- Type safety throughout
- Proper error and loading states
- Clean separation of concerns
