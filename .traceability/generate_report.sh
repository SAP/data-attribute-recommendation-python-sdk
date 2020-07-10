#!/bin/bash

CTM_CONFIG=".traceability/ctm_config.json"

if [[ ! -e "$CTM_CONFIG" ]]; then
    echo "Could not locate $CTM_CONFIG. Execute this from repository root."
    exit 1
fi

set -e

export GOPATH="$HOME/go"
go get github.com/SAP/quality-continuous-traceability-monitor
ln -sf "$GOPATH/bin/quality-continuous-traceability-monitor" "$GOPATH/bin/ctm"

LOGFILE=$(mktemp)
ctm -c .traceability/ctm_config.json > "$LOGFILE" 2>&1

echo "**** Printing ctm logs."

cat "$LOGFILE"

echo "**** Logs printed."


if grep "NOT successful tested requirements: 0" "$LOGFILE"; then
  echo "Successfully tested all requirements!"
  exit 0
else
  echo "NOT all requirements tested successfully."
  exit 55
fi

cat traceability_report/*

