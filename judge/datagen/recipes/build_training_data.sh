#!/usr/bin/env bash
# Build judge training data: rubric library -> trace synthesis -> annotation.
# Each stage is a standalone module CLI. This script only passes paths and backend flags.
#
# Usage:
#   # From a concept list, with a self-hosted model behind vLLM
#   bash recipes/build_training_data.sh \
#       --concepts concepts.jsonl --agents agent_registry.jsonl --out out \
#       --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD \
#       --presentations 3 --traces-per-level 2
#
#   # From seed rubrics instead of concepts
#   bash recipes/build_training_data.sh --seeds seed_rubrics.jsonl --agents agent_registry.jsonl ...
#
#   # Reuse an existing rubric library
#   bash recipes/build_training_data.sh --rubric-library out/rubric_library.jsonl --agents ...
#
#   # Dry run with canned replies, no model needed
#   bash recipes/build_training_data.sh --concepts concepts.jsonl --agents agent_registry.jsonl \
#       --out /tmp/judge-dry-run --backend mock --cache none
#
# Set PYTHON to choose the interpreter (default: python3), e.g. PYTHON="uv run python".

set -euo pipefail

SEEDS="" CONCEPTS="" AGENTS="" OUT="" RUBRIC_LIB=""
TRACES_PER_LEVEL=1 PRESENTATIONS=1 SEED=2026 SYNTH_MAX_TOKENS=8192 VERIFY=0
BACKEND_ARGS=() EMBED_ARGS=()

usage() { sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
    case $1 in
        --seeds)             SEEDS="$2"; shift 2 ;;
        --concepts)          CONCEPTS="$2"; shift 2 ;;
        --agents)            AGENTS="$2"; shift 2 ;;
        --out)               OUT="$2"; shift 2 ;;
        --rubric-library)    RUBRIC_LIB="$2"; shift 2 ;;
        --presentations)     PRESENTATIONS="$2"; shift 2 ;;
        --traces-per-level)  TRACES_PER_LEVEL="$2"; shift 2 ;;
        --seed)              SEED="$2"; shift 2 ;;
        --synth-max-tokens)  SYNTH_MAX_TOKENS="$2"; shift 2 ;;
        --verify)            VERIFY=1; shift ;;
        --no-temperature)    BACKEND_ARGS+=("$1"); shift ;;
        --backend|--base-url|--model-id|--api-key|--cache|--concurrency|--chat-template-kwargs|\
--region|--aws-profile|--role-arn|--additional-model-request-fields)
                             BACKEND_ARGS+=("$1" "$2"); shift 2 ;;
        --embed-backend|--embed-model|--embed-base-url|--embed-api-key)
                             EMBED_ARGS+=("$1" "$2"); shift 2 ;;
        -h|--help)           usage; exit 0 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

[[ -z "$AGENTS" ]] && { echo "--agents required" >&2; exit 1; }
[[ -z "$OUT" ]] && { echo "--out required" >&2; exit 1; }

read -r -a PY <<< "${PYTHON:-python3}"
mkdir -p "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*"; }

# ── Phase 1: rubric library ─────────────────────────────────────────────
if [[ -n "$RUBRIC_LIB" ]]; then
    log "Reusing rubric library: $RUBRIC_LIB"
    if [[ "$(cd "$(dirname "$RUBRIC_LIB")" && pwd)/$(basename "$RUBRIC_LIB")" != "$(cd "$OUT" && pwd)/rubric_library.jsonl" ]]; then
        cp "$RUBRIC_LIB" "$OUT/rubric_library.jsonl"
    fi
else
    if [[ -n "$CONCEPTS" ]]; then SRC=(--concepts "$CONCEPTS")
    elif [[ -n "$SEEDS" ]]; then SRC=(--seeds "$SEEDS")
    else echo "one of --concepts, --seeds or --rubric-library is required" >&2; exit 1
    fi
    log "Phase 1: build rubric library"
    "${PY[@]}" -u -m judge_data.rubric_build "${SRC[@]}" \
        --out "$OUT/rubric_library.jsonl" \
        --presentations "$PRESENTATIONS" \
        --seed "$SEED" \
        ${EMBED_ARGS[@]+"${EMBED_ARGS[@]}"} \
        ${BACKEND_ARGS[@]+"${BACKEND_ARGS[@]}"}
fi

# ── Phase 2: trace synthesis ────────────────────────────────────────────
VERIFY_ARGS=()
[[ "$VERIFY" == 1 ]] && VERIFY_ARGS=(--verify)
log "Phase 2: trace synthesis"
"${PY[@]}" -u -m judge_data.trace_synth \
    --rubric-library "$OUT/rubric_library.jsonl" \
    --agent-registry "$AGENTS" \
    --out "$OUT/pairs.jsonl" \
    --traces-per-level "$TRACES_PER_LEVEL" \
    --max-tokens "$SYNTH_MAX_TOKENS" \
    --seed "$SEED" \
    ${VERIFY_ARGS[@]+"${VERIFY_ARGS[@]}"} \
    ${BACKEND_ARGS[@]+"${BACKEND_ARGS[@]}"}

# ── Phase 3: annotation ─────────────────────────────────────────────────
log "Phase 3: annotate"
"${PY[@]}" -u -m judge_data.annotate \
    --pairs "$OUT/pairs.jsonl" \
    --out "$OUT/output.jsonl" \
    --rubric-library "$OUT/rubric_library.jsonl" \
    --agent-registry "$AGENTS" \
    ${BACKEND_ARGS[@]+"${BACKEND_ARGS[@]}"}

log "============================================================"
log "Rubrics: $(wc -l < "$OUT/rubric_library.jsonl" | tr -d " ")"
log "Traces:  $(wc -l < "$OUT/pairs.jsonl" | tr -d " ")"
log "Records: $(wc -l < "$OUT/output.jsonl" | tr -d " ")"
log "Output:  $OUT/output.jsonl"
log "============================================================"
