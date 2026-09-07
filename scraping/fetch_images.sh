#!/bin/zsh
# Download archived swatch images listed in a TSV of: dest<TAB>timestamp<TAB>original-url
# Wayback rate-limits aggressively, so each file gets several attempts with backoff.
jobs="${1:-image_jobs.tsv}"
ok=0; fail=0
while IFS=$'\t' read -r dest ts url; do
  [ -s "$dest" ] && continue
  for attempt in 1 2 3 4 5; do
    curl -sL --max-time 90 "https://web.archive.org/web/${ts}id_/${url}" -o "$dest"
    if [ -s "$dest" ] && [ "$(head -c 2 "$dest" | xxd -p)" = "ffd8" ]; then
      ok=$((ok+1)); break
    fi
    rm -f "$dest"
    sleep $((attempt * 5))
  done
  [ -s "$dest" ] || { fail=$((fail+1)); echo "FAIL $dest"; }
  sleep 1
done < "$jobs"
echo "ok=$ok fail=$fail"
