FROM ros:rolling

# Install ament_lint
RUN apt-get update && \
    apt-get install -y \
    ros-rolling-ament-lint \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
