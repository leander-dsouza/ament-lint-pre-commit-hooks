#!/usr/bin/env python3
import argparse
import os
import sys

import docker

DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_IMAGE_NAME = 'ament_lint_cmake_linter'
DOCKERFILE_NAME = 'Dockerfile'


def is_cmake_file(path):
    """Check if path is a CMake file we should lint."""
    filename = os.path.basename(path)
    return (filename == 'CMakeLists.txt' or
            filename.endswith('.cmake') or
            filename.endswith('.cmake.in'))


def filter_cmake_files(paths):
    """Filter and return only CMake files from the input paths."""
    cmake_files = []
    for path in paths:
        if os.path.isfile(path) and is_cmake_file(path):
            cmake_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if is_cmake_file(file):
                        cmake_files.append(os.path.join(root, file))
    return cmake_files if cmake_files else ['.']


def run_ament_lint_cmake(args):
    """Run ament_lint_cmake in Docker and properly handle output."""
    cmake_files = filter_cmake_files(args.paths)
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
        cmd = ['ament_lint_cmake']
        if args.filters:
            cmd.extend(['--filters', args.filters])
        cmd.extend(['--linelength', str(args.linelength)])
        cmd.extend(cmake_files)

        volumes = {cwd: {'bind': '/workspace', 'mode': 'ro'}}

        # Run container with output capture
        container = client.containers.run(
            image=DOCKER_IMAGE_NAME,
            command=cmd,
            volumes=volumes,
            working_dir='/workspace',
            remove=False,  # Don't remove so we can get logs
            detach=True
        )

        # Stream and capture output
        output = []
        for line in container.logs(stream=True, follow=True):
            line = line.decode('utf-8').strip()
            print(line)
            output.append(line)

        # Get the exit code
        container.reload()
        exit_code = container.attrs['State']['ExitCode']
        container.remove()  # Clean up

        if exit_code != 0 and not output:
            print('Error: Linting failed but no output was captured', file=sys.stderr)

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
        description='Check CMake code against style conventions.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'paths',
        nargs='*',
        default=[os.curdir],
        help='Files/directories to check')
    parser.add_argument(
        '--filters',
        default='',
        help='Filters for lint_cmake')
    parser.add_argument(
        '--linelength',
        metavar='N',
        type=int,
        default=140,
        help='Maximum line length')

    args = parser.parse_args(argv)
    return run_ament_lint_cmake(args)


if __name__ == '__main__':
    sys.exit(main())
