# Build & Push to Docker Hub via GitHub Actions

Since you can't install Docker locally, use GitHub Actions to automatically build and push your Docker image to Docker Hub.

## Setup Steps

### Step 1: Push Code to GitHub

1. **Create a GitHub repository** (if you haven't already):
   - Go to https://github.com/new
   - Create a new repository (e.g., `llmassesment`)

2. **Push your code to GitHub:**
   ```bash
   cd /Volumes/HashSSD/mywork/LLMAssesment
   
   # Initialize git (if not already done)
   git init
   
   # Add all files
   git add .
   
   # Commit
   git commit -m "Initial commit"
   
   # Add remote (replace YOUR_USERNAME with your GitHub username)
   git remote add origin https://github.com/YOUR_USERNAME/llmassesment.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

### Step 2: Add Docker Hub Secrets to GitHub

1. **Go to your GitHub repository**
2. **Click Settings** → **Secrets and variables** → **Actions**
3. **Click "New repository secret"**
4. **Add these two secrets:**

   **Secret 1:**
   - Name: `DOCKER_USERNAME`
   - Value: `hashdev89`

   **Secret 2:**
   - Name: `DOCKER_PASSWORD`
   - Value: Your Docker Hub password (or access token)

### Step 3: Get Docker Hub Access Token (Recommended)

Instead of using your password, use an access token:

1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Give it a name (e.g., "GitHub Actions")
4. Copy the token
5. Use this token as `DOCKER_PASSWORD` secret in GitHub

### Step 4: Trigger the Build

The workflow will automatically run when you:

- **Push to main/master branch:**
  ```bash
  git push origin main
  ```

- **Create a tag:**
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```

- **Manual trigger:**
  - Go to GitHub → Actions tab
  - Click "Build and Push Docker Image"
  - Click "Run workflow"
  - Enter a tag (e.g., `latest` or `v1.0.0`)
  - Click "Run workflow"

## How It Works

1. GitHub Actions runs on Ubuntu (has Docker pre-installed)
2. Builds your Docker image automatically
3. Pushes to Docker Hub: `hashdev89/llmassesment:latest`
4. You can see progress in the Actions tab

## View Results

After the workflow runs:

1. Go to your GitHub repository → **Actions** tab
2. Click on the workflow run to see logs
3. Check Docker Hub: https://hub.docker.com/r/hashdev89/llmassesment

## Pull and Use the Image

Once pushed, anyone can use:

```bash
docker pull hashdev89/llmassesment:latest
docker run -d -p 8000:8000 -e ANTHROPIC_API_KEY=your-key hashdev89/llmassesment:latest
```

## Alternative: Use GitLab CI/CD

If you prefer GitLab:

1. Create `.gitlab-ci.yml` in your project
2. GitLab also has Docker pre-installed in CI runners
3. Similar setup process

## Alternative: Use Cloud Build Services

- **Google Cloud Build**
- **AWS CodeBuild**
- **Azure Container Registry**

All can build Docker images without local Docker installation.

