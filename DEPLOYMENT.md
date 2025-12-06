# Deployment Guide for AI Humanoid Robotics Book

## Repository Information

- **Repository Name**: `ai-humanoid-robotics`
- **GitHub Pages URL**: `https://mrowaisabdullah.github.io/ai-humanoid-robotics`
- **Base URL**: `/ai-humanoid-robotics/`

## Configuration Details

### Docusaurus Configuration (`docusaurus.config.ts`)

```typescript
const config: Config = {
  title: "Physical AI & Humanoid Robotics",
  tagline: "A Comprehensive Guide to Embodied Intelligence",

  // URL Configuration
  url: "https://mrowaisabdullah.github.io",
  baseUrl: "/ai-humanoid-robotics/",

  // Repository Information
  organizationName: "mrowaisabdullah",
  projectName: "ai-humanoid-robotics",

  // Edit URL for documentation
  docs: {
    editUrl:
      "https://github.com/mrowaisabdullah/ai-humanoid-robotics/tree/main/",
  },

  // GitHub Links
  themeConfig: {
    navbar: {
      items: [
        {
          href: "https://github.com/mrowaisabdullah/ai-humanoid-robotics",
          label: "GitHub",
        },
      ],
    },
    footer: {
      links: [
        {
          title: "More",
          items: [
            {
              label: "GitHub Repo",
              href: "https://github.com/mrowaisabdullah/ai-humanoid-robotics",
            },
            {
              label: "Report Issue",
              href: "https://github.com/mrowaisabdullah/ai-humanoid-robotics/issues",
            },
          ],
        },
      ],
    },
  },
};
```

### Package Configuration (`package.json`)

```json
{
  "name": "ai-humanoid-robotics",
  "version": "0.0.0",
  "private": true
}
```

## Deployment Process

### 1. GitHub Actions Workflow

The project uses GitHub Actions for automatic deployment to GitHub Pages. The workflow (`.github/workflows/deploy.yml`) automatically:

- Triggers on push to the `main` branch
- Builds the Docusaurus site
- Deploys to GitHub Pages using the repository name

### 2. Manual Deployment (if needed)

```bash
# Build the site
npm run build

# Deploy to GitHub Pages
npm run deploy
```

### 3. Local Development

```bash
# Start development server
npm start

# Site will be available at: http://localhost:3000/ai-humanoid-robotics/
```

## Important Notes

1. **Repository Name Change**: All references to `ai-book` have been updated to `ai-humanoid-robotics`
2. **Base URL**: The site now serves from `/ai-humanoid-robotics/` instead of `/ai-humanoid-robotics/`
3. **GitHub Integration**: All GitHub links point to the new repository name
4. **Search Index**: Search functionality will work correctly with the new URL structure
5. **Asset Paths**: All static assets are properly configured for the new base URL

## Migration Checklist

- [x] Updated `docusaurus.config.ts` with new `baseUrl` and `projectName`
- [x] Updated all GitHub repository links
- [x] Updated edit URL for documentation
- [x] Package name already set to `ai-humanoid-robotics`
- [x] GitHub Actions workflow will auto-detect new repository name
- [x] Updated specifications to reflect new URL structure

## Verification Steps

1. **Local Development**: Run `npm start` and verify the site loads correctly at `http://localhost:3000/ai-humanoid-robotics/`
2. **Build Process**: Run `npm run build` and ensure no errors occur
3. **Link Verification**: Check all GitHub links point to the correct repository
4. **Asset Loading**: Verify all images and static assets load correctly with the new base URL
5. **Search Functionality**: Test search with the new URL structure

## Future Considerations

- When moving to a custom domain, update the `url` and `baseUrl` in `docusaurus.config.ts`
- Ensure any external documentation or links are updated to reference the new URL
- Monitor for any broken links in the initial deployment after the repository name change
