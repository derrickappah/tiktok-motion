#!/usr/bin/env bash

# Resolve script directory (so the script works when invoked from any location)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Activate virtual environment if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the Python add_account script with any passed arguments
python3 add_account.py "$@"

# Keep the terminal open on macOS when double‑clicked
if [[ "$OSTYPE" == "darwin"* ]]; then
    read -p "Press Enter to exit..."
fi
