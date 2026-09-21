#!/bin/zsh
set -eu
cd "$(dirname "$0")"
if [[ -x .venv/bin/python ]]; then
    runtime="$PWD/.venv/bin/python"
else
    runtime="$PWD/../../work/venv/bin/python"
fi
if [[ ! -x "$runtime" ]]; then
    echo "No Python environment found. Follow the setup instructions in README.md."
    exit 1
fi
# The prepared macOS environment uses the OpenMP runtime bundled with scikit-learn.
if [[ "$(uname -s)" == Darwin ]]; then
    runtime_libs="$("$runtime" -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/sklearn/.dylibs"
    export DYLD_LIBRARY_PATH="$runtime_libs${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi
exec "$runtime" -m streamlit run app.py --server.address=127.0.0.1
