#!/bin/bash
# Patch OnnxStream to disable ARM dotprod micro-kernels.
#
# Why: Pi Zero 2 W (Cortex-A53) is ARMv8.0 and has no dotprod extension.
# XNNPACK defaults XNNPACK_ENABLE_ARM_DOTPROD=ON, which generates vsdot
# assembly instructions the CPU can't execute, causing an Illegal Instruction
# crash at runtime.
#
# This must be patched into the XNNPACK_CMAKE_ARGS list inside CMakeLists.txt
# because XNNPACK is built as an ExternalProject — a top-level cmake flag
# (-DXNNPACK_ENABLE_ARM_DOTPROD=OFF) does NOT propagate to it.
#
# Run from the PaperPiAI install directory:
#   bash scripts/patch_onnxstream_arm.sh

set -e
INSTALL_DIR="$PWD"
CMAKE_FILE="$INSTALL_DIR/OnnxStream/src/CMakeLists.txt"

if [ ! -f "$CMAKE_FILE" ]; then
    echo "ERROR: $CMAKE_FILE not found. Run this from the PaperPiAI directory after cloning OnnxStream."
    exit 1
fi

# Check if already patched
if grep -q "XNNPACK_ENABLE_ARM_DOTPROD" "$CMAKE_FILE"; then
    echo "Already patched — XNNPACK_ENABLE_ARM_DOTPROD found in CMakeLists.txt."
else
    # Insert the flag after -DXNNPACK_LIBRARY_TYPE=static
    sed -i 's/-DXNNPACK_LIBRARY_TYPE=static/-DXNNPACK_LIBRARY_TYPE=static\n\t\t\t-DXNNPACK_ENABLE_ARM_DOTPROD=OFF/' "$CMAKE_FILE"
    echo "Patch applied: XNNPACK_ENABLE_ARM_DOTPROD=OFF added."
fi

echo ""
echo "Cleaning previous build and rebuilding OnnxStream..."
rm -rf "$INSTALL_DIR/OnnxStream/src/build"
mkdir "$INSTALL_DIR/OnnxStream/src/build"
cd "$INSTALL_DIR/OnnxStream/src/build"
cmake ..
cmake --build . --config Release

echo ""
echo "Done. Binary at: $INSTALL_DIR/OnnxStream/src/build/sd"
