# 🚨 Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. **Git LFS Authentication Error**

**Symptoms:**
- `Error: Process completed with exit code 1`
- Git LFS authentication failures
- Large files not being pushed

**Solutions:**
```bash
# 1. Verify HF_TOKEN has correct permissions
# Go to HuggingFace Settings > Access Tokens
# Ensure token has "Write" permissions

# 2. Check Git LFS setup locally
git lfs install
git lfs track "*.pkl" "*.pth"
git add .gitattributes
git commit -m "Add Git LFS tracking"

# 3. Manual push to test
cd farming-assistant/backend
git init
git lfs install
git lfs track "*.pkl" "*.pth"
git add .
git commit -m "Test deployment"
git push -f https://YOUR_USERNAME:YOUR_HF_TOKEN@huggingface.co/spaces/abhijeetraj/farming-assistant-backend main
```

### 2. **Directory Structure Issues**

**Symptoms:**
- `cd: backend: No such file or directory`
- Workflow can't find files

**Solutions:**
- Ensure you're in the correct repository structure
- The workflow expects: `farming-assistant/backend/` not just `backend/`
- Check GitHub Actions logs for actual directory structure

### 3. **Model Loading Failures**

**Symptoms:**
- Models not loading in HF Spaces
- Memory errors
- Import errors

**Solutions:**
```bash
# Check model files exist and are tracked by LFS
git lfs ls-files

# Verify requirements.txt includes all dependencies
# Check HF Spaces logs for specific error messages
```

### 4. **Environment Variables Missing**

**Symptoms:**
- API calls failing
- Authentication errors
- Service unavailable errors

**Solutions:**
1. **Check HF Spaces Settings**:
   - Go to your HF Space settings
   - Verify all environment variables are set:
     - `DATABASE_URL`
     - `SUPABASE_URL`
     - `SUPABASE_KEY`
     - `GOOGLE_API_KEY`
     - `OPENWEATHER_API_KEY`

2. **Test locally first**:
```bash
cd farming-assistant/backend
cp .env.example .env
# Fill in your actual API keys
python -m uvicorn app.main:app --reload
```

### 5. **Docker Build Failures**

**Symptoms:**
- Docker build timeouts
- Package installation failures
- Memory issues during build

**Solutions:**
```bash
# Test Docker build locally
cd farming-assistant/backend
docker build -t farming-assistant .
docker run -p 7860:7860 farming-assistant

# Check for common issues:
# - Large model files (use .dockerignore)
# - Missing system dependencies
# - Python version compatibility
```

## 🔧 **Quick Fixes**

### Fix 1: Reset and Redeploy
```bash
# 1. Delete the HF Space and recreate it
# 2. Ensure Git LFS is properly set up
cd farming-assistant
git lfs install
git lfs track "*.pkl" "*.pth" "*.h5" "*.bin"
git add .gitattributes
git commit -m "Fix Git LFS setup"
git push origin main
```

### Fix 2: Manual Deployment
```bash
# If GitHub Actions keeps failing, deploy manually
cd farming-assistant/backend
git init
git lfs install
git lfs track "*.pkl" "*.pth"
git add .
git commit -m "Manual deployment"
git remote add hf https://huggingface.co/spaces/abhijeetraj/farming-assistant-backend
git push -f hf main
```

### Fix 3: Verify HF Space Configuration
1. **Go to HF Spaces**: https://huggingface.co/spaces/abhijeetraj/farming-assistant-backend
2. **Check Settings**:
   - SDK: Docker
   - Port: 7860
   - All environment variables set
3. **Check Build Logs** for specific errors

## 🧪 **Testing Deployment**

After fixing issues, test the deployment:

```bash
# 1. Wait for HF Spaces to finish building (check logs)
# 2. Test basic endpoints
curl https://abhijeetraj-farming-assistant-backend.hf.space/ping

# 3. Run full verification
cd farming-assistant/backend
python verify_deployment.py

# 4. Test specific endpoints
curl -X POST "https://abhijeetraj-farming-assistant-backend.hf.space/api/v1/crop/recommend" \
  -H "Content-Type: application/json" \
  -d '{"nitrogen": 90, "phosphorus": 42, "potassium": 43, "temperature": 28.5, "humidity": 78, "ph": 6.5, "rainfall": 45}'
```

## 📞 **Getting Help**

If issues persist:

1. **Check HF Spaces Community**: https://huggingface.co/spaces
2. **GitHub Actions Logs**: Look for specific error messages
3. **HF Spaces Logs**: Check the build and runtime logs
4. **Local Testing**: Always test locally first

## 🎯 **Prevention**

To avoid future issues:

1. **Always test locally** before pushing
2. **Use Git LFS** for files >10MB
3. **Keep environment variables** in sync
4. **Monitor HF Spaces** build logs
5. **Use the verification script** after each deployment