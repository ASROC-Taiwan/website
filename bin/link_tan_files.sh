#!/usr/bin/env bash

# Define the directory
target_dir="sources/content/tan/tan-bot"

# Move to that directory
cd "$target_dir" || exit 1

# Loop through all .zh-Hant.md files
for file in *.zh-Hant.md; do
  base="${file%.zh-Hant.md}"
  if [ ! -e "${base}.en.md" ]; then
    #ln -s "$file" "${base}.en.md"
    cp "$file" "${base}.en.md"
    echo "Copyed: ${base}.en.md -> $file"
  else
    echo "Skipped: ${base}.en.md already exists"
  fi
done

