# Styling Guide - MUI v5 + Tailwind CSS 4

## Overview

Your project uses two styling systems:
- **MUI v5**: Component library with `sx` prop
- **Tailwind CSS 4**: Utility-first CSS framework

Use both together appropriately based on context.

---

## MUI v5 Styling

### sx Prop (Primary Method)

```typescript
import { Box, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';

export function Component() {
  return (
    <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
      <Typography sx={{ color: 'primary.main', fontWeight: 'bold' }}>
        Title
      </Typography>
    </Box>
  );
}
```

### Theme Access

```typescript
<Box
  sx={(theme) => ({
    p: 2,
    bgcolor: theme.palette.background.default,
    color: theme.palette.text.primary,
    [theme.breakpoints.down('md')]: {
      p: 1,
    },
  })}
>
  Content
</Box>
```

### Inline Styles (< 100 lines)

```typescript
import type { SxProps, Theme } from '@mui/material';

export function Component() {
  const styles: Record<string, SxProps<Theme>> = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      p: 3,
    },
    title: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: 'primary.main',
    },
  };

  return (
    <Box sx={styles.container}>
      <Typography sx={styles.title}>Title</Typography>
    </Box>
  );
}
```

### Separate Styles File (> 100 lines)

```typescript
// Component.styles.ts
import type { SxProps, Theme } from '@mui/material';

export const styles: Record<string, SxProps<Theme>> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    p: 3,
    bgcolor: 'background.paper',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  // ... many more styles
};

// Component.tsx
import { styles } from './Component.styles';

export function Component() {
  return (
    <Box sx={styles.container}>
      <Box sx={styles.header}>...</Box>
    </Box>
  );
}
```

---

## ⚠️ MUI v5 Grid (CRITICAL WARNING!)

**⚠️ YOUR PROJECT USES MUI v5, NOT v7!**

**DO NOT USE MUI v7 Grid syntax. It will break your application!**

```typescript
import { Grid } from '@mui/material';

// ✅ MUI v5 Syntax (CORRECT - USE THIS)
<Grid container spacing={2}>
  <Grid item xs={12} md={6}>
    Content
  </Grid>
  <Grid item xs={12} md={6}>
    Content
  </Grid>
</Grid>

// ❌ MUI v7 Syntax (WRONG - DO NOT USE!)
// This will cause errors in your MUI v5 project!
<Grid size={{ xs: 12, md: 6 }}>
  Content
</Grid>
```

**Key Differences:**
- **MUI v5**: Uses `<Grid item xs={12}>` with separate `item` prop
- **MUI v7**: Uses `<Grid size={{xs: 12}}>` with `size` prop object
- **Your Project**: MUI v5 (version ^5.9.2) - ALWAYS use `item` + `xs/sm/md/lg/xl` props

### Responsive Grid

```typescript
<Grid container spacing={2}>
  {/* Full width on mobile, half on tablet, third on desktop */}
  <Grid item xs={12} sm={6} md={4}>
    Card 1
  </Grid>
  <Grid item xs={12} sm={6} md={4}>
    Card 2
  </Grid>
  <Grid item xs={12} sm={6} md={4}>
    Card 3
  </Grid>
</Grid>
```

---

## Tailwind CSS 4

### Utility Classes

```typescript
export function Component() {
  return (
    <div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow-md">
      <img
        src="..."
        alt="..."
        className="w-16 h-16 rounded-full object-cover"
      />
      <div className="flex-1">
        <h3 className="text-lg font-bold text-gray-900">Title</h3>
        <p className="text-sm text-gray-600">Description</p>
      </div>
    </div>
  );
}
```

### Responsive Classes

```typescript
<div className="
  flex flex-col       /* Mobile: column layout */
  md:flex-row         /* Tablet+: row layout */
  gap-4 md:gap-6      /* Different gaps */
  p-4 md:p-8          /* Different padding */
">
  Content
</div>
```

### Combining with MUI

```typescript
import { Button } from '@mui/material';

export function Component() {
  return (
    <div className="flex items-center gap-4">
      {/* Tailwind for layout */}
      <Button
        sx={{ px: 3, py: 1 }}
        /* MUI for component styling */
      >
        Click Me
      </Button>
    </div>
  );
}
```

---

## When to Use What

### Use MUI sx when:
- Styling MUI components
- Need theme access (colors, breakpoints)
- Complex component-specific styles
- Hover/active states for MUI components

### Use Tailwind when:
- Layout (flex, grid, positioning)
- Spacing (padding, margin, gap)
- Quick utility styling
- Non-MUI elements (div, img, etc.)

### Combine Both:
```typescript
import { Box, Typography } from '@mui/material';

export function Card() {
  return (
    {/* Tailwind for layout */}
    <div className="flex flex-col gap-4 p-6">
      {/* MUI for themed components */}
      <Box sx={{ bgcolor: 'primary.light', p: 2, borderRadius: 1 }}>
        <Typography sx={{ color: 'primary.contrastText' }}>
          Title
        </Typography>
      </Box>
    </div>
  );
}
```

---

## Common Patterns

### Card Component

```typescript
import { Paper, Typography } from '@mui/material';

export function Card({ title, children }) {
  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        borderRadius: 2,
        '&:hover': {
          elevation: 4,
          transform: 'translateY(-2px)',
          transition: 'all 0.2s',
        },
      }}
    >
      <Typography variant="h6" sx={{ mb: 2 }}>
        {title}
      </Typography>
      {children}
    </Paper>
  );
}
```

### Form Layout

```typescript
import { Box, TextField, Button } from '@mui/material';

export function Form() {
  return (
    <Box
      component="form"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        maxWidth: 500,
        mx: 'auto',
      }}
    >
      <TextField label="Name" fullWidth />
      <TextField label="Email" type="email" fullWidth />
      <Button variant="contained" type="submit">
        Submit
      </Button>
    </Box>
  );
}
```

### Responsive Layout

```typescript
import { Box } from '@mui/material';

export function ResponsiveLayout() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        gap: { xs: 2, md: 4 },
        p: { xs: 2, sm: 3, md: 4 },
      }}
    >
      <Box sx={{ flex: { xs: 1, md: 2 } }}>Main Content</Box>
      <Box sx={{ flex: 1 }}>Sidebar</Box>
    </Box>
  );
}
```

---

## Best Practices

1. **<100 lines inline, >100 separate**: Keep styles organized
2. **Type your styles**: Use `SxProps<Theme>` for type safety
3. **Use theme**: Access theme colors, spacing, breakpoints
4. **⚠️ MUI v5 Grid ONLY**: ALWAYS use `<Grid item xs={12}>` syntax, NEVER use `<Grid size={{xs: 12}}>` (v7 syntax)
5. **Combine systems**: Use Tailwind for layout, MUI for components
6. **Responsive design**: Use theme breakpoints or Tailwind responsive classes
7. **Hover states**: Define in sx prop for MUI components
8. **Semantic names**: Name style objects descriptively
9. **Version awareness**: Check package.json before using MUI features (you're on v5, not v7)
