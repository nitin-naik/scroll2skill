#!/bin/bash
if ! npm test >/dev/null 2>&1; then
  echo "Tests are failing, keep fixing" >&2
  exit 2
fi
exit 0
