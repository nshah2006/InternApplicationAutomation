# GitHub Repository Setup Guide

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Fill in the repository details:
   - **Repository name**: `InternApplicationAutomation` (or your preferred name)
   - **Description**: "Automated resume parsing and job application system with AI-powered text generation"
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

## Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these commands in your terminal:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/InternApplicationAutomation.git

# Or if you prefer SSH:
# git remote add origin git@github.com:YOUR_USERNAME/InternApplicationAutomation.git

# Rename branch to main (if you prefer main over master)
git branch -M main

# Push your code to GitHub
git push -u origin main
```

## Step 3: Verify

1. Go to your GitHub repository page
2. You should see all your files uploaded
3. The README.md should be displayed on the repository homepage

## Optional: Set Up Branch Protection

For production repositories, consider setting up branch protection:

1. Go to **Settings** → **Branches**
2. Add a branch protection rule for `main`
3. Enable:
   - Require pull request reviews
   - Require status checks to pass
   - Require branches to be up to date

## Environment Variables

Before deploying, make sure to set up these environment variables in your deployment platform:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT tokens
- `OPENAI_API_KEY`: OpenAI API key for AI generation
- `GITHUB_CLIENT_ID`: GitHub OAuth client ID (optional)
- `GITHUB_CLIENT_SECRET`: GitHub OAuth client secret (optional)
- `LOG_LEVEL`: Logging level (default: INFO)

## Next Steps

1. Set up CI/CD pipelines (GitHub Actions)
2. Configure environment variables in your hosting platform
3. Set up database migrations
4. Configure domain and SSL certificates

