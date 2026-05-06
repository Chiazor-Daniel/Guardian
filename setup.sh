# Guardian LPU - Environment Setup Script

echo "🔧 Setting up Guardian LPU..."

# Check Python version
python_version=$(python3 --version 2>/dev/null || python --version 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi
echo "✅ Python found: $python_version"

# Backend setup
echo ""
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo "✅ Backend setup complete"
cd ..

# Frontend setup
echo ""
echo "📦 Setting up frontend..."
cd frontend

# Check for Node.js
node_version=$(node --version 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo "✅ Node.js found: $node_version"

# Install dependencies
echo "Installing Node dependencies..."
npm install

echo "✅ Frontend setup complete"
cd ..

echo ""
echo "🎉 Guardian LPU setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your Groq API key"
echo "2. Run the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Run the frontend: cd frontend && npm run dev"
echo ""
echo "Get your Groq API key at: https://console.groq.com/"
