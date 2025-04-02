#!/usr/bin/env python3
import argparse
import os
import sys
from typing import List, Optional

import docker

DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_IMAGE_NAME = 'ament_mypy_linter'
DOCKERFILE_NAME = 'Dockerfile'

# Define file extensions
PYTHON_EXTENSIONS = ['py']


def is_python_file(path: str) -> bool:
    """Check if path is a Python file we should check."""
    filename = os.path.basename(path)
    return any(filename.endswith(f'.{ext}') for ext in PYTHON_EXTENSIONS)


def filter_python_files(paths: List[str],
                        exclude_patterns: Optional[List[str]] = None) -> List[str]:
    """Filter and return only Python files from the input paths."""
    filtered_files = []
    exclude_patterns = exclude_patterns or []

    for path in paths:
        if os.path.isfile(path) and is_python_file(path):
            if not any(exclude in os.path.basename(path) for exclude in exclude_patterns):
                filtered_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if is_python_file(file):
                        if not any(exclude in file for exclude in exclude_patterns):
                            filtered_files.append(os.path.join(root, file))
    return filtered_files


def run_mypy(args: argparse.Namespace) -> int:
    """Run mypy in Docker and properly handle output."""
    workspace_dir = '/workspace'
    python_files = filter_python_files(args.paths, args.excludes)

    cwd = os.getcwd()
    client = docker.from_env()

    try:
        # Build the image
        client.images.build(
            path=DOCKERFILE_DIR,
            dockerfile=DOCKERFILE_NAME,
            tag=DOCKER_IMAGE_NAME,
        )

        # Prepare command and volumes
        cmd = ['ament_mypy']

        volumes = {
            cwd: {'bind': workspace_dir, 'mode': 'ro'},
        }
        if args.config_file and os.path.exists(args.config_file):
            config_path_in_container = \
                os.path.join(workspace_dir, os.path.relpath(args.config_file, cwd))
            cmd.extend(['--config', config_path_in_container])

        # Add cache directory
        if args.cache_dir and args.cache_dir != os.devnull:
            # Mount the cache directory if it's not the null device
            cmd.extend(['--cache-dir', '/cache'])
            volumes['/cache'] = {'bind': args.cache_dir, 'mode': 'rw'}

        cmd.extend(python_files)

        # Run container with output capture
        container = client.containers.run(
            image=DOCKER_IMAGE_NAME,
            command=cmd,
            volumes=volumes,
            working_dir=workspace_dir,
            remove=False,
            detach=True
        )

        # Stream and capture output
        for line in container.logs(stream=True, follow=True):
            line = line.decode('utf-8').strip()

            if workspace_dir in line:
                # Remove the workspace_dir prefix from the path
                line = line.replace(workspace_dir + '/', '')

            print(line)

        # Get the exit code
        container.reload()
        exit_code = container.attrs['State']['ExitCode']
        container.remove()

        return exit_code

    except docker.errors.BuildError as e:
        print(f'Error building Docker image: {e}', file=sys.stderr)
        return 1
    except docker.errors.APIError as e:
        print(f'Docker API error: {e}', file=sys.stderr)
        return 1
    except Exception as e:
        print(f'Unexpected error: {e}', file=sys.stderr)
        return 1


def main(argv: List[str] = sys.argv[1:]) -> int:
    """Command line tool for static type analysis with mypy."""
    parser = argparse.ArgumentParser(
        description='Check code using mypy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--config',
        metavar='path',
        dest='config_file',
        default=os.path.join(os.path.dirname(__file__), 'configuration', 'ament_mypy.ini'),
        help='The config file'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        default=[os.curdir],
        help='The files or directories to check. For directories files ending '
             "in '.py' will be considered."
    )
    parser.add_argument(
        '--exclude',
        metavar='filename',
        nargs='*',
        dest='excludes',
        help='The filenames to exclude.'
    )
    parser.add_argument(
        '--cache-dir',
        metavar='cache',
        default=os.devnull,
        dest='cache_dir',
        help='The location mypy will place its cache in. Defaults to system '
             'null device'
    )

    args = parser.parse_args(argv)
    return run_mypy(args)


if __name__ == '__main__':
    sys.exit(main())
