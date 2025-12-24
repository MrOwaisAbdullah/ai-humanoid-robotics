# Neon PostgreSQL Setup Guide

This guide walks you through setting up Neon PostgreSQL for the AI Book authentication system.

## Why Neon PostgreSQL?

- **Serverless**: Auto-scaling based on demand
- **Free Tier**: Generous free tier for development
- **Full PostgreSQL**: Complete PostgreSQL compatibility
- **Branching**: Database branching for development/testing
- **Connection Pooling**: Built-in connection pooling (PgBouncer)

## Step-by-Step Setup

### 1. Create Neon Account

1. Go to https://neon.tech
2. Click "Sign Up"
3. Sign up with:
   - GitHub (recommended)
   - Google
   - Email

### 2. Create a New Project

1. After signing in, you'll be prompted to create a project
2. Enter project details:
   - **Project Name**: `ai-book-auth`
   - **Database Name**: `ai_book` (or default `neondb`)
   - **Region**: Choose closest to your users (recommended: `us-east-1`)
3. Click "Create Project"

### 3. Get Your Connection String

1. Once project is created, you'll see the connection details
2. Copy the **Connection String** (it looks like):
   ```
   postgresql://[user]:[password]@[endpoint]/[database]?sslmode=require
   ```

### 4. Configure for Python/FastAPI

Neon's connection string uses the standard `postgresql://` format, but for Python with asyncpg driver, we need to modify it:

**Original Neon format:**
```
postgresql://username:password@ep-xxx.us-east-1.aws.neon.tech/ai_book?sslmode=require
```

**Required for asyncpg (Python):**
```
postgresql+asyncpg://username:password@ep-xxx.us-east-1.aws.neon.tech/ai_book?sslmode=require
```

Notice the change: `postgresql://` → `postgresql+asyncpg://`

### 5. Update Environment Variables

#### Option A: Development (backend/.env)

Edit `backend/.env` and update:

```bash
DATABASE_URL=postgresql+asyncpg://username:password@ep-xxx.us-east-1.aws.neon.tech/ai_book?sslmode=require
```

Replace:
- `username` with your Neon username
- `password` with your Neon password
- `ep-xxx.us-east-1.aws.neon.tech` with your Neon endpoint
- `ai_book` with your database name

#### Option B: Production (.env.production)

For production, use the same format but ensure:
- SSL is enabled (`sslmode=require`)
- Connection pooling is configured

```bash
# Production format with connection pooling
DATABASE_URL=postgresql+asyncpg://username:password@ep-xxx.us-east-1.aws.neon.tech/ai_book?sslmode=require&pool_size=10&max_overflow=20
```

### 6. Verify Connection

Test your Neon database connection:

```bash
cd backend
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

load_dotenv()

async def test_connection():
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    async with engine.begin() as conn:
        result = await conn.execute('SELECT version()')
        version = result.fetchone()
        print(f'Connected to: {version[0]}')
    await engine.dispose()

asyncio.run(test_connection())
"
```

Expected output:
```
Connected to: PostgreSQL 16.x.x on x86_64-pc-linux-gnu, compiled by ...
```

### 7. Run Database Migrations

After configuring the connection:

```bash
cd backend
python scripts/manage_migrations.py upgrade head
```

This will create all authentication tables in your Neon database.

## Connection Pooling Settings

For production, configure pool settings in `backend/.env`:

```bash
# Database connection pool settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## Neon Dashboard Features

### View Database Tables

1. Go to https://console.neon.tech
2. Select your project
3. Click "SQL Editor" to run queries
4. Click "Table Editor" to browse tables

### Monitoring

- **Metrics**: View connection counts, storage usage
- **Logs**: View query logs and performance
- **Branches**: Create development branches

## Troubleshooting

### Error: "relation does not exist"

**Cause**: Migrations haven't been run on Neon database

**Solution**:
```bash
cd backend
python scripts/manage_migrations.py upgrade head
```

### Error: "authentication failed"

**Cause**: Incorrect username/password in connection string

**Solution**:
1. Go to Neon Console
2. Copy connection string again
3. Ensure you're using the correct format

### Error: "connection timeout"

**Cause**: Firewall blocking Neon connections

**Solution**: Ensure port 5432 is open for outbound connections

### Error: "too many connections"

**Cause**: Exceeded free tier connection limit

**Solution**:
1. Close idle connections in your code
2. Upgrade to paid Neon tier
3. Use connection pooling

## Security Best Practices

### 1. Never Commit .env Files

Ensure `.env` is in `.gitignore`:
```bash
echo ".env" >> .gitignore
```

### 2. Use Environment Variables in Production

Set environment variables in your hosting platform:
- **Vercel**: Environment Variables settings
- **Hugging Face Spaces**: Secrets/Environment Variables
- **AWS Lambda**: Environment Variables in Lambda configuration

### 3. Rotate Passwords Regularly

1. Go to Neon Console
2. Project Settings → Reset Password
3. Update your .env file
4. Restart your application

### 4. Enable SSL Only

Always use `sslmode=require` in production. Never use `sslmode=disable`.

## Migration from SQLite

If you have existing SQLite data:

1. Export SQLite data:
```bash
cd backend
python -c "
import sqlite3
import json

conn = sqlite3.connect('./database/auth.db')
cursor = conn.cursor()

# Export users
cursor.execute('SELECT * FROM users')
users = cursor.fetchall()
with open('users_backup.json', 'w') as f:
    json.dump(users, f)

conn.close()
print('Exported ' + str(len(users)) + ' users')
"
```

2. Import to Neon:
```bash
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os
import json

load_dotenv()

async def import_data():
    engine = create_async_engine(os.getenv('DATABASE_URL'))

    # Read backup
    with open('users_backup.json', 'r') as f:
        users = json.load(f)

    async with engine.begin() as conn:
        for user in users:
            # Adjust INSERT based on your schema
            await conn.execute(
                'INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)',
                user[1], user[2], user[3]
            )

    await engine.dispose()
    print(f'Imported {len(users)} users')

asyncio.run(import_data())
"
```

## Free Tier Limits

Neon Free Tier includes:
- **Storage**: 0.5 GB
- **Compute Time**: 191 hours/month
- **Rows Read**: 20 GB/month
- **Rows Written**: 10 GB/month
- **Connections**: 10 concurrent

For the AI Book authentication system, this should be sufficient for development and small production deployments.

## Next Steps

After setting up Neon:

1. ✅ Update `backend/.env` with your connection string
2. ✅ Run migrations: `python scripts/manage_migrations.py upgrade head`
3. ✅ Test connection using the verification script above
4. ✅ Start your backend: `uvicorn main:app --reload --port 7860`
5. ✅ Test registration and login

## Additional Resources

- Neon Documentation: https://neon.tech/docs
- PostgreSQL asyncpg: https://magicstack.github.io/asyncpg/
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

## Support

If you encounter issues:
1. Check Neon status: https://status.neon.tech
2. Review Neon docs: https://neon.tech/docs
3. Check authentication logs in Neon Console
4. Verify your connection string format
