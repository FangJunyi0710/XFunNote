#!/bin/bash

if [ -d ".venv" ]; then
    echo "Existing .venv found."
    read -p "Do you want to reuse it and install missing/updated packages? (y/n): " choice
    case "$choice" in
        y|Y )
            echo "Reusing existing virtual environment..."
            source .venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
            echo "Environment updated. Activate with: source .venv/bin/activate"
            exit 0
            ;;
        * )
            echo "Removing old .venv..."
            rm -rf .venv
            ;;
    esac
fi

# Create fresh virtual environment
echo "Creating new virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Environment ready. Activate with: source .venv/bin/activate"
