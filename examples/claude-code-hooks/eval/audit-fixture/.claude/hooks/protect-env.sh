#!/bin/bash
FILE=$(jq -r '.tool_input.file_path')
TOOL=$(jq -r '.tool_name')
if [[ $FILE == *.env* ]]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"no env edits"}}'
  exit 2
fi
