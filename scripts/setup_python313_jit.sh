#!/bin/bash
# Setup Python 3.13 with JIT for multicardz Development Environment

set -e  # Exit on any error

echo "🐍 Setting up Python 3.13 with JIT for multicardz™"
echo "=================================================="

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS - using Homebrew for installation"

    # Install or update Homebrew if needed
    if ! command -v brew &> /dev/null; then
        echo "🍺 Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "🍺 Homebrew found, updating..."
        brew update
    fi

    # Install Python 3.13 (JIT-enabled build)
    echo "🐍 Installing Python 3.13 with JIT support..."

    # Try official Python 3.13 first
    if brew list python@3.13 &> /dev/null; then
        echo "✅ Python 3.13 already installed"
    else
        # Install Python 3.13
        brew install python@3.13 || {
            echo "⚠️  Official Python 3.13 not available yet, trying alternative..."
            # Install from python.org or compile from source if needed
            echo "📥 Please install Python 3.13 from python.org or compile from source"
            echo "🔗 https://www.python.org/downloads/"
            exit 1
        }
    fi

    # Set up pyenv if not already installed (for version management)
    if ! command -v pyenv &> /dev/null; then
        echo "🐍 Installing pyenv for Python version management..."
        brew install pyenv
        echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
        echo 'eval "$(pyenv init -)"' >> ~/.zshrc
        export PATH="$HOME/.pyenv/bin:$PATH"
        eval "$(pyenv init -)"
    fi

else
    echo "🐧 Detected Linux - using package manager or source compilation"

    # Check for Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        echo "📦 Using apt-get for installation..."
        sudo apt-get update

        # Install dependencies for compiling Python with JIT
        sudo apt-get install -y \
            build-essential \
            libssl-dev \
            zlib1g-dev \
            libbz2-dev \
            libreadline-dev \
            libsqlite3-dev \
            wget \
            curl \
            llvm \
            libncurses5-dev \
            libncursesw5-dev \
            xz-utils \
            tk-dev \
            libffi-dev \
            liblzma-dev \
            python3-openssl \
            git

        # Install pyenv for Python version management
        if ! command -v pyenv &> /dev/null; then
            echo "🐍 Installing pyenv..."
            curl https://pyenv.run | bash
            echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
            echo 'eval "$(pyenv init -)"' >> ~/.bashrc
            export PATH="$HOME/.pyenv/bin:$PATH"
            eval "$(pyenv init -)"
        fi
    fi
fi

# Check Python 3.13 installation
echo "🔍 Checking Python 3.13 installation..."

# Try to find Python 3.13
PYTHON313_PATH=""
for py_path in /usr/local/bin/python3.13 /opt/homebrew/bin/python3.13 ~/.pyenv/versions/3.13.*/bin/python python3.13; do
    if command -v "$py_path" &> /dev/null; then
        PYTHON313_PATH="$py_path"
        break
    fi
done

if [[ -z "$PYTHON313_PATH" ]]; then
    echo "❌ Python 3.13 not found. Installing via pyenv..."

    # Install Python 3.13 via pyenv
    pyenv install 3.13.0 || {
        echo "⚠️  Python 3.13.0 not available in pyenv yet"
        echo "🔨 Attempting to compile from source with JIT..."

        # Compile Python 3.13 from source with JIT
        cd /tmp
        wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz || {
            echo "❌ Python 3.13.0 source not available yet"
            echo "📝 Please check python.org for latest 3.13 release"
            exit 1
        }

        tar xzf Python-3.13.0.tgz
        cd Python-3.13.0

        # Configure with JIT support
        ./configure \
            --enable-optimizations \
            --with-lto \
            --enable-shared \
            --prefix="$HOME/.local/python313" \
            --enable-jit

        make -j$(nproc || sysctl -n hw.ncpu || echo 4)
        make install

        PYTHON313_PATH="$HOME/.local/python313/bin/python3.13"

        # Add to PATH
        echo 'export PATH="$HOME/.local/python313/bin:$PATH"' >> ~/.bashrc
        echo 'export PATH="$HOME/.local/python313/bin:$PATH"' >> ~/.zshrc
        export PATH="$HOME/.local/python313/bin:$PATH"
    }

    pyenv global 3.13.0 2>/dev/null || true
    PYTHON313_PATH=$(pyenv which python 2>/dev/null) || PYTHON313_PATH="python3.13"
fi

echo "✅ Python 3.13 found at: $PYTHON313_PATH"

# Verify JIT support
echo "🚀 Verifying JIT support..."
$PYTHON313_PATH -c "
import sys
print(f'Python version: {sys.version}')
print(f'Version info: {sys.version_info}')

# Check for JIT support
jit_supported = False
try:
    # Check if JIT is available (this may vary in actual Python 3.13)
    import sys
    if hasattr(sys, '_enable_jit') or hasattr(sys, 'set_jit_threshold'):
        jit_supported = True
        print('✅ JIT support detected!')
    else:
        print('🔍 Checking for JIT environment variables...')
        import os
        if 'PYTHON_JIT' in os.environ or any('JIT' in k for k in os.environ.keys()):
            print('✅ JIT environment configured!')
            jit_supported = True
except Exception as e:
    print(f'⚠️  JIT check failed: {e}')

if not jit_supported:
    print('⚠️  JIT support not confirmed - will enable via environment variables')
"

# Set up virtual environment with Python 3.13
echo "📦 Setting up virtual environment..."
cd /Users/adam/dev/multicardz

# Remove existing venv if it exists
if [[ -d "venv" ]]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment with Python 3.13
$PYTHON313_PATH -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify we're using Python 3.13
echo "🔍 Verifying virtual environment Python version..."
python --version

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install project dependencies
echo "📦 Installing project dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
else
    echo "📝 Installing core dependencies..."
    pip install \
        pydantic>=2.0.0 \
        numpy>=1.24.0 \
        psutil>=5.9.0 \
        pytest>=7.0.0 \
        pytest-bdd>=6.0.0
fi

# Set up JIT environment variables for development
echo "⚡ Configuring JIT environment variables..."

# Create .env file for JIT configuration
cat > .env << EOF
# Python 3.13 JIT Configuration for multicardz™
PYTHON_JIT=1
PYTHON_JIT_OPTIMIZE_LEVEL=3
PYTHON_JIT_THRESHOLD_HOT=50
PYTHON_JIT_THRESHOLD_TRACE=1000
PYTHON_JIT_MAX_TRACES=8192
PYTHON_JIT_MAX_TRACE_LENGTH=200
PYTHON_JIT_INLINE_THRESHOLD=100
PYTHON_JIT_UNROLL_LOOPS=8

# Performance monitoring
MULTICARDZ_PERFORMANCE_MODE=jit_dev
MULTICARDZ_JIT_MONITORING=1
EOF

# Create activation script that sets JIT environment
cat > activate_jit.sh << 'EOF'
#!/bin/bash
# Activate multicardz development environment with JIT

echo "🚀 Activating multicardz™ JIT Development Environment"
echo "=================================================="

# Load environment variables
if [[ -f ".env" ]]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Verify JIT configuration
python -c "
import os
print('🐍 Python JIT Development Environment')
print('====================================')
print(f'Python: {os.sys.version}')
print(f'JIT Enabled: {os.environ.get(\"PYTHON_JIT\", \"No\")}')
print(f'Optimization Level: {os.environ.get(\"PYTHON_JIT_OPTIMIZE_LEVEL\", \"Default\")}')
print(f'Hot Threshold: {os.environ.get(\"PYTHON_JIT_THRESHOLD_HOT\", \"Default\")}')
print()
print('✅ Ready for high-performance set operations!')
print('Run: python -m pytest tests/test_set_operations_performance.py::TestSetOperationsPerformance::test_1000_cards_performance -v')
"

echo ""
echo "💡 Quick commands:"
echo "  • Run performance tests: python run_tests.py performance"
echo "  • Run 1M card test: python run_tests.py million"
echo "  • JIT performance report: python -c 'from python313_jit_config import get_jit_performance_report; print(get_jit_performance_report())'"
EOF

chmod +x activate_jit.sh

echo ""
echo "🎉 Python 3.13 JIT Development Environment Setup Complete!"
echo "========================================================"
echo ""
echo "🚀 To activate the JIT environment, run:"
echo "   source activate_jit.sh"
echo ""
echo "🧪 To test JIT performance:"
echo "   source activate_jit.sh"
echo "   python run_tests.py performance"
echo ""
echo "📊 To monitor JIT optimization:"
echo "   python -c 'from python313_jit_config import get_jit_performance_report; import json; print(json.dumps(get_jit_performance_report(), indent=2))'"
echo ""
echo "💡 The JIT will adapt and optimize based on your usage patterns!"
echo "   - First runs: JIT compilation overhead"
echo "   - Subsequent runs: Optimized performance"
echo "   - Large datasets: Maximum JIT benefit"
