#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Contract Compliance Executive Dashboard - Startup Script     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the dashboard directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Please run this script from the dashboard directory${NC}"
    echo "   cd dashboard && ./start-dashboard.sh"
    exit 1
fi

echo -e "${BLUE}📦 Setting up backend...${NC}"

# Backend setup
cd backend
if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing Python dependencies..."
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install Python dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend setup complete${NC}"
echo ""

echo -e "${BLUE}📦 Setting up frontend...${NC}"

# Frontend setup
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing Node dependencies..."
    npm install

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install Node dependencies${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Frontend setup complete${NC}"
echo ""

# Start servers
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Starting Servers                                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${YELLOW}⚡ Starting backend server (Port 8000)...${NC}"
cd ../backend
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

echo -e "${YELLOW}⚡ Starting frontend server (Port 5173)...${NC}"
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait a bit for frontend to start
sleep 3

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Dashboard is Running! 🚀                                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ Backend API:${NC}      http://localhost:8000"
echo -e "${GREEN}✅ API Docs:${NC}         http://localhost:8000/docs"
echo -e "${GREEN}✅ Frontend Dashboard:${NC} http://localhost:5173"
echo ""
echo -e "${YELLOW}📊 The dashboard will open automatically in your browser...${NC}"
echo ""
echo -e "${BLUE}ℹ️  Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for user interrupt
trap "echo '';echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Goodbye! 👋'; exit 0" INT

# Keep script running
wait
