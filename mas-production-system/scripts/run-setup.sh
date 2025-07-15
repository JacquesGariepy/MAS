#!/bin/bash

# Simple wrapper to run setup_dev.sh from the correct directory

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project root directory
cd "$SCRIPT_DIR/.."

# Run setup_dev.sh
exec ./scripts/setup_dev.sh "$@"