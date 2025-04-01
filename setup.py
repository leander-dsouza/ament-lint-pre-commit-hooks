from __future__ import annotations

from setuptools import setup

setup(
    package_data={
        'ament_lint_pre_commit_hooks': ['Dockerfile'],
    },
    include_package_data=True,
)
