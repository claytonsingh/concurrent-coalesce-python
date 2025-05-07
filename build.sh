# Install build tools
pip install -r requirements-dev.txt

# Build the package
if [ "$(python -c 'import sys; print(sys.version_info[0])')" = "2" ]; then
    python -m build --no-isolation --wheel
else
    python -m build
fi

# Check and upload to PyPI
# twine check dist/*
# twine upload dist/*
