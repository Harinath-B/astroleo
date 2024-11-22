VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
DEMO_SCRIPT="demo.py"

if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Please install it to proceed."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r $REQUIREMENTS_FILE
else
    echo "Error: $REQUIREMENTS_FILE not found. Exiting."
    deactivate
    exit 1
fi

if [ -f "$DEMO_SCRIPT" ]; then
    echo "Running demo script: $DEMO_SCRIPT"
    python $DEMO_SCRIPT
else
    echo "Error: $DEMO_SCRIPT not found. Exiting."
fi

echo "Deactivating virtual environment..."
deactivate
