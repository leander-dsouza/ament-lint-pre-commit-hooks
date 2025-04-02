#!/usr/bin/env python3
import argparse
import os
import sys

import docker
import pydocstyle

DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_IMAGE_NAME = 'ament_pep257_linter'
DOCKERFILE_NAME = 'Dockerfile'

# Define file extensions
PYTHON_EXTENSIONS = ['py']

# Setup pydocstyle conventions
_conventions = set(pydocstyle.conventions.keys())
_conventions.add('ament')

_ament_ignore = [
    'D100', 'D101', 'D102', 'D103', 'D104', 'D105', 'D106', 'D107',
    'D203', 'D212', 'D404'
]


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


def run_pep257(args):
    """Run pep257 checks in Docker and properly handle output."""
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
        cmd = ['ament_pep257']

        # Add error code selection options
        if args.ignore:
            cmd.extend(['--ignore'] + args.ignore)
        if args.select:
            cmd.extend(['--select'] + args.select)
        if args.convention:
            cmd.extend(['--convention', args.convention])
        if args.add_ignore:
            cmd.extend(['--add-ignore'] + args.add_ignore)
        if args.add_select:
            cmd.extend(['--add-select'] + args.add_select)

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
        description='Check docstrings against the style conventions in PEP 257.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    err_code_group = parser.add_mutually_exclusive_group()
    err_code_group.add_argument(
        '--ignore',
        nargs='+',
        default=[],
        help='Choose the list of error codes for pydocstyle NOT to check for.')
    err_code_group.add_argument(
        '--select',
        nargs='+',
        default=[],
        help='Choose the basic list of error codes for pydocstyle to check for.'
    )
    err_code_group.add_argument(
        '--convention',
        choices=_conventions,
        default='ament',
        help=(
            f'Choose a preset list of error codes. Valid options are {_conventions}.'
            f'The "ament" convention is defined as --ignore {_ament_ignore}.'
        ),
    )
    parser.add_argument(
        '--add-ignore',
        nargs='+',
        default=[],
        help='Ignore an extra error code, removing it from the list set by --(select/ignore)')
    parser.add_argument(
        '--add-select',
        nargs='+',
        default=[],
        help='Check an extra error code, adding it to the list set by --(select/ignore).'
    )
    parser.add_argument(
        'paths',
        nargs='*',
        default=[os.curdir],
        help='The files or directories to check. For directories, files ending '
             "in '.py' will be considered.")
    parser.add_argument(
        '--exclude',
        metavar='filename',
        nargs='*',
        default=[],
        dest='excludes',
        help='The filenames to exclude.')

    args = parser.parse_args(argv)
    return run_pep257(args)


if __name__ == '__main__':
    sys.exit(main())
