#!/usr/bin/env python
import sys
import toml
import os

def check_version():
    # Get git tag version from environment variable
    tag_version = os.environ.get('GITHUB_REF_NAME', '')
    if not tag_version.startswith('v'):
        print("Error: Tag must start with 'v'")
        sys.exit(1)
    
    tag_version = tag_version[1:]
    
    try:
        with open('pyproject.toml', 'r') as f:
            pyproject = toml.load(f)
            pyproject_version = pyproject['project']['version']
    except Exception as e:
        print("Error reading pyproject.toml: {}".format(e))
        sys.exit(1)
    
    if tag_version != pyproject_version:
        print("Version mismatch:")
        print("  Git tag version: {}".format(tag_version))
        print("  pyproject.toml version: {}".format(pyproject_version))
        sys.exit(1)
    
    print("Version check passed: {}".format(tag_version))

if __name__ == '__main__':
    check_version()
