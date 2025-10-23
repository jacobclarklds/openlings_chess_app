#!/bin/bash

# Chess App - Test Runner Script

echo "=================================="
echo "Chess Training App - Test Suite"
echo "=================================="
echo ""

# Set PYTHONPATH
export PYTHONPATH=/Users/jacobclark/CHESS/chess-app/backend

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running Lichess Import Tests...${NC}"
echo ""
python3 -m pytest tests/test_lichess_import.py -v -s
LICHESS_EXIT=$?

echo ""
echo "=================================="
echo ""

echo -e "${YELLOW}Running Chess.com Import Tests...${NC}"
echo ""
python3 -m pytest tests/test_chesscom_import.py -v -s
CHESSCOM_EXIT=$?

echo ""
echo "=================================="
echo ""

# Summary
if [ $LICHESS_EXIT -eq 0 ] && [ $CHESSCOM_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Your game import functionality is working correctly."
    echo "You can now use the app to import games from:"
    echo "  - Lichess (jclark982)"
    echo "  - Chess.com (jakebyu97)"
    exit 0
else
    echo "⚠ Some tests failed. Please check the output above."
    exit 1
fi
