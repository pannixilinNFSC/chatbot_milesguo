# GitHub Pages Deployment

## Prerequisites

- Repository pushed to GitHub
- Frontend files in `frontend/` directory

## Deployment Steps

### 1. Create GitHub Actions Workflow

Create `.github/workflows/deploy-pages.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches:
      - main
    paths:
      - 'frontend/**'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './frontend'
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 2. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**
3. Save

### 3. Deploy

```bash
git add .github/workflows/deploy-pages.yml
git commit -m "Add GitHub Pages deployment"
git push
```

Deployment triggers automatically on pushes to `frontend/`. Site available at:
```
https://<username>.github.io/<repository-name>/
```

## Configuration

### API Endpoints

Update API URLs in `index.html` to point to your production backend.

### CORS

Add GitHub Pages URL to backend `CORS_ALLOW_ORIGINS` environment variable.

## Custom Domain

1. Create `frontend/CNAME` with your domain:
   ```
   example.com
   ```
2. Configure DNS: CNAME to `<username>.github.io` or A records to GitHub IPs
3. In **Settings** → **Pages**, enter domain and enable **Enforce HTTPS**
