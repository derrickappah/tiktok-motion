#!/usr/bin/env bash

# Resolve script directory (Finder opens .command files in $HOME by default)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Activate venv if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python3 add_account.py "$@"

echo ""
read -p "Press Enter to exit..."
