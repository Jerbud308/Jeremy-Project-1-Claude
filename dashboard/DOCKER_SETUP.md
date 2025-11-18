# Running the Dashboard with Docker Desktop

## Quick Start

1. **Open Docker Desktop** on your computer and make sure it's running

2. **Open a terminal** in this directory (`Jeremy-Project-1-Claude/dashboard`)

3. **Run this command:**
   ```bash
   docker-compose up
   ```

4. **Access the dashboard:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Stopping the Dashboard

Press `Ctrl+C` in the terminal, or run:
```bash
docker-compose down
```

## Rebuilding (if you make changes)

```bash
docker-compose up --build
```

## Viewing Logs

```bash
docker-compose logs -f
```

## Troubleshooting

**Port already in use?**
```bash
docker-compose down
# Then start again
docker-compose up
```

**Need to reset everything?**
```bash
docker-compose down -v
docker-compose up --build
```

## What's Running

- **Backend Container**: Python FastAPI server on port 8000
- **Frontend Container**: React + Vite dev server on port 3000
- Both containers are connected via a Docker network
- Data is loaded from test_cases.json
