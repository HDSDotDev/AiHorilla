# 🚀 Railway Deployment - Quick Start

## ⚡ Fast Deploy (3 Steps)

### 1️⃣ Create Railway Project
```bash
# Push code to GitHub first
git add .
git commit -m "Ready for Railway"
git push

# Then on Railway:
# 1. New Project → Deploy from GitHub
# 2. Select your repository
# 3. Add PostgreSQL database
```

### 2️⃣ Set Environment Variables
```bash
SECRET_KEY=<run command below to generate>
ALLOWED_HOSTS=*.railway.app
DEBUG=False
```

**Generate SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3️⃣ Deploy!
Railway will automatically:
- ✅ Build Docker image
- ✅ Initialize database
- ✅ Run migrations
- ✅ Collect static files
- ✅ Create admin user (username: admin, password: admin)
- ✅ Start server

**Done!** Access your app at: `https://yourapp.railway.app`

---

## 🔧 Troubleshooting

### App keeps restarting?
```bash
# Check Railway logs
# Go to: Dashboard → Your Service → Deployments → Logs
```

### Database errors?
```bash
# Use Railway Shell to run:
python manage.py init_railway_db
```

### Need diagnostics?
```bash
# Use Railway Shell to run:
python railway_diagnostics.py
```

---

## 📚 Full Documentation

- **Complete Guide**: `RAILWAY_DEPLOYMENT.md`
- **Fix Details**: `RAILWAY_FIX_SUMMARY.md`

---

## 🆘 Support

- **Railway Issues**: Check logs in Railway Dashboard
- **App Issues**: Review `RAILWAY_FIX_SUMMARY.md`
- **Migration Issues**: Run `python manage.py init_railway_db` in Railway Shell

---

## ⚠️ Important Security Notes

1. **Change admin password immediately** after first login!
2. **Update ALLOWED_HOSTS** with your actual domain
3. **Keep SECRET_KEY secret** (never commit to Git)
4. **Set DEBUG=False** in production

---

## ✅ Post-Deployment Checklist

- [ ] App accessible via Railway URL
- [ ] Admin panel works (`/admin`)
- [ ] Change admin password
- [ ] Static files loading
- [ ] Database operations working
- [ ] Set up regular backups

---

**Need help?** Check `RAILWAY_DEPLOYMENT.md` for detailed instructions.
