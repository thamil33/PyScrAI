#!/bin/bash

############################################################################
# Run tests for the agno library
# Usage: ./libs/agno/scripts/test.sh
############################################################################

CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGNO_DIR="$(dirname ${CURR_DIR})"
source ${CURR_DIR}/_utils.sh

print_heading "Running tests for agno"

print_heading "Running: pytest ${AGNO_DIR} with coverage"
pytest ${AGNO_DIR}/tests/unit --cov=${AGNO_DIR}/agno --cov-report=term-missing --cov-report=html
