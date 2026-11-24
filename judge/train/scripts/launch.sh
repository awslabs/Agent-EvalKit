#!/usr/bin/env bash
# Launch judge_train.train with `accelerate launch` and FSDP.
#
# Single node (all local GPUs):
#   bash scripts/launch.sh configs/examples/qwen3.5-4b.yaml
#
# Multi-node: run the same command on every node with these env vars set.
#   NUM_NODES    total number of nodes (default: 1)
#   NODE_RANK    this node's rank, 0 to NUM_NODES-1 (default: 0)
#   MASTER_ADDR  address of the rank 0 node, reachable from every node (default: 127.0.0.1)
#   MASTER_PORT  rendezvous port on the rank 0 node (default: 29500)
#
#   # on node 0
#   NUM_NODES=4 NODE_RANK=0 MASTER_ADDR=10.0.0.1 bash scripts/launch.sh configs/examples/qwen3.5-4b.yaml
#   # on node 1, 2, 3
#   NUM_NODES=4 NODE_RANK=1 MASTER_ADDR=10.0.0.1 bash scripts/launch.sh configs/examples/qwen3.5-4b.yaml
#
# Other env vars:
#   CONFIG              training config, used when no argument is given
#   GPUS_PER_NODE       default: number of GPUs reported by nvidia-smi
#   ACCELERATE_CONFIG   default: configs/accelerate/fsdp.yaml
#   RDZV_BACKEND        default: static. Set to c10d to let ranks join in any order.
#
# Any cluster scheduler works. It only has to start this script once per node
# with the env vars above.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-${CONFIG:-}}"
if [[ -z "${CONFIG}" ]]; then
    echo "Usage: bash scripts/launch.sh <training-config.yaml>   (or set CONFIG)" >&2
    exit 1
fi
NUM_NODES="${NUM_NODES:-1}"
NODE_RANK="${NODE_RANK:-0}"
MASTER_ADDR="${MASTER_ADDR:-127.0.0.1}"
MASTER_PORT="${MASTER_PORT:-29500}"
RDZV_BACKEND="${RDZV_BACKEND:-static}"
ACCELERATE_CONFIG="${ACCELERATE_CONFIG:-${SCRIPT_DIR}/../configs/accelerate/fsdp.yaml}"
if [[ -z "${GPUS_PER_NODE:-}" ]]; then
    GPUS_PER_NODE="$(nvidia-smi --list-gpus 2>/dev/null | wc -l | tr -d ' ')"
    [[ "${GPUS_PER_NODE}" -gt 0 ]] || GPUS_PER_NODE=8
fi
NUM_PROCESSES=$((NUM_NODES * GPUS_PER_NODE))

echo "=== accelerate launch (FSDP) ==="
echo "Nodes: ${NUM_NODES} | Node rank: ${NODE_RANK} | GPUs/node: ${GPUS_PER_NODE} | Processes: ${NUM_PROCESSES}"
echo "Master: ${MASTER_ADDR}:${MASTER_PORT} | Rendezvous: ${RDZV_BACKEND}"
echo "Config: ${CONFIG}"
echo "================================"

exec accelerate launch \
    --config_file "${ACCELERATE_CONFIG}" \
    --num_processes "${NUM_PROCESSES}" \
    --num_machines "${NUM_NODES}" \
    --machine_rank "${NODE_RANK}" \
    --main_process_ip "${MASTER_ADDR}" \
    --main_process_port "${MASTER_PORT}" \
    --rdzv_backend "${RDZV_BACKEND}" \
    -m judge_train.train \
    --config "${CONFIG}"
