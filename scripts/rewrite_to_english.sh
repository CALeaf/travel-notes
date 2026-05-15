#!/usr/bin/env bash
# Rewrite each scraped Chinese note (src/content/_raw/*.zh.md) into a polished
# English blog post in src/content/posts/. Uses the local `claude` CLI so all
# LLM calls go through the user's Claude Code subscription — no API key, no
# Anthropic API charges.
#
# Usage:
#   bash scripts/rewrite_to_english.sh           # process all unprocessed notes
#   bash scripts/rewrite_to_english.sh --force   # re-process even if output exists
#   bash scripts/rewrite_to_english.sh path/to/one.zh.md   # process a single file
#
# Tunables:
#   FIELD_NOTES_MODEL=opus       # override default sonnet
#   FIELD_NOTES_DRY_RUN=1        # print what would run without calling claude

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW_DIR="$ROOT/src/content/_raw"
OUT_DIR="$ROOT/src/content/posts"
PROMPT="$ROOT/scripts/prompts/rewrite_blog.md"

if ! command -v claude >/dev/null 2>&1; then
  echo "error: 'claude' CLI not found in PATH. Install Claude Code first."
  exit 1
fi
if [[ ! -f "$PROMPT" ]]; then
  echo "error: prompt template missing at $PROMPT"
  exit 1
fi

mkdir -p "$OUT_DIR"

FORCE=0
FILES=()
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help)
      sed -n '2,15p' "$0"
      exit 0
      ;;
    *) FILES+=("$arg") ;;
  esac
done

# If no specific files passed, process every *.zh.md in _raw/
if [[ ${#FILES[@]} -eq 0 ]]; then
  if [[ -d "$RAW_DIR" ]]; then
    while IFS= read -r -d '' f; do
      FILES+=("$f")
    done < <(find "$RAW_DIR" -name '*.zh.md' -print0 2>/dev/null)
  fi
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No .zh.md files found in $RAW_DIR. Run scrape_xhs.py first."
  exit 0
fi

MODEL="${FIELD_NOTES_MODEL:-sonnet}"
DRY="${FIELD_NOTES_DRY_RUN:-0}"

processed=0
skipped=0
failed=0

for raw in "${FILES[@]}"; do
  base="$(basename "$raw" .zh.md)"
  out="$OUT_DIR/${base}.md"

  if [[ -f "$out" && "$FORCE" -eq 0 ]]; then
    echo "skip  $base (already in posts/)"
    skipped=$((skipped+1))
    continue
  fi

  echo ">> rewriting $base"

  if [[ "$DRY" -eq 1 ]]; then
    echo "   (dry run — would call claude with model=$MODEL)"
    continue
  fi

  # Build the message: system prompt + the Chinese note wrapped in tags.
  tmp_in="$(mktemp)"
  tmp_out="$(mktemp)"
  trap 'rm -f "$tmp_in" "$tmp_out"' EXIT

  {
    cat "$PROMPT"
    printf '\n<note>\n'
    cat "$raw"
    printf '\n</note>\n'
  } > "$tmp_in"

  if claude -p --model "$MODEL" --output-format text < "$tmp_in" > "$tmp_out" 2>&1; then
    if [[ -s "$tmp_out" ]]; then
      mv "$tmp_out" "$out"
      processed=$((processed+1))
      echo "   -> $out"
    else
      echo "   ! empty output — skipping"
      failed=$((failed+1))
    fi
  else
    echo "   ! claude CLI failed for $base"
    failed=$((failed+1))
    cat "$tmp_out" | sed 's/^/     /'
  fi

  rm -f "$tmp_in" "$tmp_out"
  trap - EXIT
done

echo ""
echo "summary: $processed rewritten, $skipped skipped, $failed failed"
