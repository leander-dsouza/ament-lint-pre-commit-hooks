#!/usr/bin/env python3
import argparse
import os
import sys
from typing import List, Optional

import docker

DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_IMAGE_NAME = 'ament_mypy_linter'
DOCKERFILE_NAME = 'Dockerfile'

MYPY_CONFIG = os.path.join(DOCKERFILE_DIR, 'config', 'ament_mypy.ini')

# Define file extensions
PYTHON_EXTENSIONS = ['py']


def is_python_file(path: str) -> bool:
    """Check if path is a Python file we should check."""
    filename = os.path.basename(path)
    return any(filename.endswith(f'.{ext}') for ext in PYTHON_EXTENSIONS)


def filter_python_files(
        paths: List[str], exclude_patterns: Optional[List[str]] = None) -> List[str]:
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

        # Default to read-only volumes
        volumes = {cwd: {'bind': workspace_dir, 'mode': 'ro'}}

        # Handle config file
        if args.config_file:
            abs_config_path = os.path.abspath(args.config_file)
            rel_config_path = os.path.relpath(abs_config_path, cwd)
            cmd.extend(['--config', f'/workspace/{rel_config_path}'])
            volumes[abs_config_path] = {'bind': f'/workspace/{rel_config_path}', 'mode': 'ro'}

        # Handle xunit file output
        if args.xunit_file:
            # Create absolute path and ensure directory exists
            abs_xunit_path = os.path.abspath(args.xunit_file)
            os.makedirs(os.path.dirname(abs_xunit_path) or '.', exist_ok=True)
            # Use relative path inside container
            rel_xunit_path = os.path.relpath(abs_xunit_path, cwd)
            cmd.extend(['--xunit-file', f'/workspace/{rel_xunit_path}'])
            # Need write access for workspace to create xunit file
            volumes[cwd]['mode'] = 'rw'

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
        default=MYPY_CONFIG,
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
        '--xunit-file',
        help='Generate a xunit compliant XML file'
    )

    args = parser.parse_args(argv)
    return run_mypy(args)


if __name__ == '__main__':
    sys.exit(main())
