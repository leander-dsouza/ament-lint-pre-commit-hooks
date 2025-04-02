#!/usr/bin/env python3
import argparse
import os
import sys

import docker

DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_IMAGE_NAME = 'ament_flake8_linter'
DOCKERFILE_NAME = 'Dockerfile'

# Define file extensions
PYTHON_EXTENSIONS = ['py']


def is_python_file(path):
    """Check if path is a Python file we should lint."""
    filename = os.path.basename(path)
    return any(filename.endswith(f'.{ext}') for ext in PYTHON_EXTENSIONS)


def filter_python_files(paths, exclude_patterns=None):
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


def run_flake8(args):
    """Run flake8 in Docker and properly handle output."""
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
        cmd = ['ament_flake8']

        # Add linelength if specified
        if args.linelength:
            cmd.extend(['--linelength', str(args.linelength)])

        cmd.extend(python_files)

        volumes = {
            cwd: {'bind': workspace_dir, 'mode': 'ro'},
        }

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


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='Check code using flake8.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--linelength', metavar='N', type=int,
        help='The maximum line length (default: specified in the config file)')
    parser.add_argument(
        'paths',
        nargs='*',
        default=[os.curdir],
        help='The files or directories to check. For directories files ending '
             'in ".py" will be considered.')
    parser.add_argument(
        '--exclude',
        metavar='filename',
        nargs='*',
        dest='excludes',
        help='The filenames to exclude.')

    args = parser.parse_args(argv)
    return run_flake8(args)


if __name__ == '__main__':
    sys.exit(main())
