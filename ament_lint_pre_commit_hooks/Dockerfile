FROM ros:rolling

# Install ament_lint and ament_mypy
RUN apt-get update && \
    apt-get install -y \
    ros-rolling-ament-lint \
    ros-rolling-ament-mypy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
