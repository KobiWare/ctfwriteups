#!/bin/bash
# Solve script for missing-one-piece

# Create the binary with the correct argv[0]
ln -sf "$(dirname "$0")/../dist/missing_one_piece" ./devilishFruit

# Run with required environment variables
PWD=/tmp/gogear5 ONE_PIECE=IS_REAL ./devilishFruit
