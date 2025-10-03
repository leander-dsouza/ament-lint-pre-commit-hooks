# Use the bare minimum ROS rolling image as a base
FROM ros:rolling-ros-core

# Install only essential packages from ament_lint and ament_mypy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ros-rolling-ament-lint \
    ros-rolling-ament-mypy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
