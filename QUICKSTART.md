# Quick Start Guide

Follow these steps to get the Chess Training App running in minutes.

## Prerequisites Check

Run these commands to verify you have everything:

```bash
python3 --version  # Should be 3.9 or higher
node --version     # Should be 18 or higher
docker --version   # Docker installed
docker-compose --version
```

## Step-by-Step Setup

### 1. Start Database (30 seconds)

```bash
# From chess-app directory
docker-compose up -d

# Wait for database to be ready (about 10 seconds)
sleep 10

# Verify it's running
docker ps | grep chess_postgres
```

### 2. Setup Backend (2 minutes)

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# IMPORTANT: Open .env and change SECRET_KEY to something random
# Example: SECRET_KEY=your-very-secret-key-12345-change-this
```

### 3. Start Backend Server

```bash
# Make sure you're in backend/ with venv activated
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal open!** Open a new terminal for the next steps.

### 4. Setup Frontend (1 minute)

```bash
# In a NEW terminal, from chess-app directory
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
```

### 5. Start Frontend Server

```bash
# Still in frontend/
npm run dev
```

You should see:
```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
```

## Test It Out!

1. Open your browser to [http://localhost:3000](http://localhost:3000)

2. You should be redirected to the login page

3. Click "create a new account"

4. Register with:
   - Email: test@example.com
   - Username: testuser
   - Password: password123

5. After login, you'll see the dashboard

6. Click "Connect Platform" and try connecting:
   - **Lichess**: Enter your Lichess username
   - **Chess.com**: Enter your Chess.com username

7. Games will be imported automatically!

## Verify Everything Works

### Check Backend API:
Visit [http://localhost:8000/docs](http://localhost:8000/docs) to see the interactive API documentation.

### Check Database:
```bash
docker exec -it chess_postgres psql -U postgres -d chess_training -c "\dt"
```

You should see the `users` and `games` tables.

### Check Frontend:
[http://localhost:3000](http://localhost:3000) should show your dashboard.

## Common Issues

### Port Already in Use

**Backend (port 8000):**
```bash
# Find what's using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

**Frontend (port 3000):**
```bash
# Find what's using port 3000
lsof -i :3000
# Kill it
kill -9 <PID>
```

**Database (port 5432):**
```bash
# Stop any local PostgreSQL
brew services stop postgresql  # macOS
sudo service postgresql stop   # Linux
```

### Database Connection Failed

```bash
# Restart the database
docker-compose down
docker-compose up -d

# Wait a bit
sleep 10
```

### Module Not Found (Backend)

```bash
cd backend
source venv/bin/activate  # Make sure venv is activated!
pip install -r requirements.txt --force-reinstall
```

### Cannot Find Module (Frontend)

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

Once everything is running:

1. **Import Some Games**: Connect your Lichess or Chess.com account and import games

2. **Explore the API**: Visit [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Check the Database**:
   ```bash
   # View your games
   docker exec -it chess_postgres psql -U postgres -d chess_training -c "SELECT * FROM games LIMIT 5;"
   ```

4. **Start Building Features**: Check out the main README.md for development guidelines

## Stopping the App

When you're done:

```bash
# Stop backend: Press Ctrl+C in backend terminal
# Stop frontend: Press Ctrl+C in frontend terminal

# Stop database
docker-compose down
```

## Getting Help

- Check the main [README.md](README.md) for detailed documentation
- Visit [http://localhost:8000/docs](http://localhost:8000/docs) for API reference
- Check the Troubleshooting section in README.md

Enjoy building your chess training app!
