#!/usr/bin/env bash
# Set up the training environment with uv.
#
# Usage:
#   bash scripts/setup.sh            # full install, including the CUDA kernels (up to an hour)
#   bash scripts/setup.sh --quick    # skip the CUDA kernels (for CPU tests and debugging)
#
# The versions below and in constraints.txt are the ones the released judges were trained with. torch comes only from the
# PyTorch index for its CUDA build, so a newer torch on PyPI built for a different CUDA cannot slip in.
#
# Environment variables:
#   PYTHON_VERSION        Python for the venv (default: 3.11)
#   TORCH_VERSION         torch version (default: 2.11.0)
#   TORCH_CUDA            CUDA build of torch, as in the PyTorch index name (default: cu128)
#   CUDA_HOME             CUDA toolkit used to compile the kernels. Default: /usr/local/cuda-<version of
#                         TORCH_CUDA> if it exists, else /usr/local/cuda. Its nvcc must match torch's CUDA.
#   TORCH_CUDA_ARCH_LIST  GPU arch for kernel builds (default: 9.0 for H100/H200)
#   MAX_JOBS              parallel compile jobs (default: 4)
#   EXTRAS                extra package groups to install (default: qwen35,dev). Add mlflow if needed.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
TORCH_VERSION="${TORCH_VERSION:-2.11.0}"
TORCH_CUDA="${TORCH_CUDA:-cu128}"
TORCH_INDEX_URL="https://download.pytorch.org/whl/${TORCH_CUDA}"
EXTRAS="${EXTRAS:-qwen35,dev}"
export TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-9.0}"
export MAX_JOBS="${MAX_JOBS:-4}"

# cu128 -> 12.8
CUDA_DOTTED="$(echo "${TORCH_CUDA#cu}" | sed -E 's/^([0-9]+)([0-9])$/\1.\2/')"
if [[ -z "${CUDA_HOME:-}" ]]; then
    if [[ -d "/usr/local/cuda-${CUDA_DOTTED}" ]]; then
        CUDA_HOME="/usr/local/cuda-${CUDA_DOTTED}"
    else
        CUDA_HOME="/usr/local/cuda"
    fi
fi
export CUDA_HOME
export PATH="${CUDA_HOME}/bin:${PATH}"

echo "==> Creating .venv (Python ${PYTHON_VERSION})"
uv venv .venv --python "${PYTHON_VERSION}"
export VIRTUAL_ENV="$(pwd)/.venv"

echo "==> Installing torch ${TORCH_VERSION}+${TORCH_CUDA}"
uv pip install "torch==${TORCH_VERSION}" --index-url "${TORCH_INDEX_URL}"
uv pip install packaging ninja setuptools wheel

echo "==> Installing judge_train with extras [${EXTRAS}]"
# The torch already installed satisfies the package's torch requirement, so this leaves it alone.
uv pip install -e ".[${EXTRAS}]" -c constraints.txt

# Qwen3.5 uses GatedDeltaNet linear attention. Without these kernels training
# falls back to a pure PyTorch path that is 3 to 5 times slower.
CUDA_BUILD_PKGS=("causal-conv1d==1.6.2.post1" "flash-attn==2.8.3")
if [[ "${1:-}" == "--quick" ]]; then
    echo "==> Quick mode: skipping the CUDA kernels. Install them later with:"
    echo "    CUDA_HOME=${CUDA_HOME} uv pip install ${CUDA_BUILD_PKGS[*]} --no-build-isolation"
else
    if ! command -v nvcc >/dev/null; then
        echo "ERROR: nvcc not found under CUDA_HOME=${CUDA_HOME}. Set CUDA_HOME to a CUDA ${CUDA_DOTTED} toolkit." >&2
        exit 1
    fi
    NVCC_VERSION="$(nvcc --version | sed -nE 's/.*release ([0-9]+\.[0-9]+).*/\1/p')"
    if [[ "${NVCC_VERSION}" != "${CUDA_DOTTED}" ]]; then
        echo "WARNING: nvcc is CUDA ${NVCC_VERSION} but torch is built for CUDA ${CUDA_DOTTED}." >&2
        echo "         Kernel builds usually fail on a mismatch. Set CUDA_HOME to a CUDA ${CUDA_DOTTED} toolkit." >&2
    fi
    echo "==> Installing CUDA kernels (CUDA_HOME=${CUDA_HOME}, ARCH=${TORCH_CUDA_ARCH_LIST}, JOBS=${MAX_JOBS})"
    uv pip install "${CUDA_BUILD_PKGS[@]}" --no-build-isolation
fi

echo "==> Installed versions"
.venv/bin/python - <<'PY'
import importlib.metadata as md
for p in ("torch", "transformers", "trl", "accelerate", "flash-linear-attention", "flash-attn", "causal-conv1d"):
    try:
        print(f"    {p:24s} {md.version(p)}")
    except md.PackageNotFoundError:
        print(f"    {p:24s} not installed")
PY

echo ""
echo "Done. Activate with: source .venv/bin/activate"
