#!/bin/bash
cd /home/kavia/workspace/code-generation/onlinetictactoe-29019-f25f2e40/tic_tac_toe_frontend_workspace/tic_tac_toe_frontend
npm run lint
ESLINT_EXIT_CODE=$?
npm run build
BUILD_EXIT_CODE=$?
if [ $ESLINT_EXIT_CODE -ne 0 ] || [ $BUILD_EXIT_CODE -ne 0 ]; then
   exit 1
fi

