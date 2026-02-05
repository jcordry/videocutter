#!/usr/bin/env bash

# Usage check
if [ $# -ne 1 ]; then
    echo "Usage: $0 <base_name>"
    exit 1
fi

BASENAME="$1"
DIR="sections"
COUNT=1

cd "$DIR"

for FILE in *; do
    # Skip directories
    [ -f "$FILE" ] || continue

    EXT="${FILE##*.}"
    printf -v NUM "%02d" "$COUNT"

    # Handle files without extension
    if [[ "$FILE" == "$EXT" ]]; then
        NEWNAME="${BASENAME}_${NUM}"
    else
        NEWNAME="${BASENAME}_${NUM}.${EXT}"
    fi

    mv -n -- "$FILE" "$NEWNAME"
    ((COUNT++))
done
