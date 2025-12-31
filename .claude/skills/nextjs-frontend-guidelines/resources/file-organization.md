# File Organization - Next.js 15

## Project Structure

```
src/
  app/                     # Next.js App Router
    page.tsx              # Home page
    layout.tsx            # Root layout
    loading.tsx           # Loading UI
    error.tsx             # Error UI

    {route}/              # Route folder
      page.tsx            # Route page
      loading.tsx         # Route loading
      error.tsx           # Route error
      layout.tsx          # Route layout (optional)

    api/                  # API Routes
      {endpoint}/
        route.ts          # API handler

  components/             # React components
    {feature}/            # Feature-specific components
      Component.tsx
      Component.styles.ts # Styles if > 100 lines
    shared/               # Reusable components
      Button.tsx
      Header.tsx

  lib/                    # Core utilities
    api.ts                # API client
    serverAuth.ts         # Server-side auth
    s3Upload.ts           # S3 upload utilities
    theme.ts              # MUI theme

  hooks/                  # Custom React hooks
    useArtists.ts
    useAuth.ts

  providers/              # Context providers
    ThemeProvider.tsx
    AuthProvider.tsx

  types/                  # TypeScript types
    user.ts
    artist.ts

  utils/                  # Utility functions
    formatDate.ts
    validation.ts

  const/                  # Constants
    routes.ts
    config.ts
```

## Component Organization

### Feature-Based (Recommended)

Group related components by feature:

```
components/
  artist/
    ArtistCard.tsx
    ArtistProfile.tsx
    ArtistList.tsx
  artwork/
    ArtworkCard.tsx
    ArtworkGallery.tsx
  exhibition/
    ExhibitionCard.tsx
    ExhibitionDetail.tsx
```

### Shared/Reusable Components

```
components/
  shared/
    Button.tsx
    Header.tsx
    Footer.tsx
    LoadingSpinner.tsx
```

## Best Practices

1. **Co-locate related files**: Keep components with their styles/tests
2. **Feature grouping**: Group by feature, not by file type
3. **Consistent naming**: Use PascalCase for components
4. **Index exports**: Export from feature folders for clean imports
5. **Separate concerns**: Server Components, Client Components, utilities
