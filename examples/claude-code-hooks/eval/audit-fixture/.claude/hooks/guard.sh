#!/bin/bash
CMD=$(jq -r '.tool_input.command')
if echo "$CMD" | grep -qE 'rm -rf /'; then
  echo "Blocked dangerous rm"
  exit 1
fi
if echo "$CMD" | grep -qE 'git push.*--force[^-]'; then
  echo "Blocked force push" >&2
  exit 2
fi
exit 0
