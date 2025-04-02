#!/usr/bin/env python3
import argparse
import os
import sys

import docker

DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_IMAGE_NAME = 'ament_cpplint_linter'
DOCKERFILE_NAME = 'Dockerfile'


def is_cpp_file(path):
    """Check if path is a C/C++ file we should lint."""
    filename = os.path.basename(path)
    extensions = ['c', 'cc', 'cpp', 'cxx', 'h', 'hh', 'hpp', 'hxx']
    return any(filename.endswith('.' + ext) for ext in extensions)


def filter_cpp_files(paths, exclude_patterns=None):
    """Filter and return only C/C++ files from the input paths."""
    filtered_files = []
    exclude_patterns = exclude_patterns or []

    for path in paths:
        if os.path.isfile(path) and is_cpp_file(path):
            if not any(exclude in path for exclude in exclude_patterns):
                filtered_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if is_cpp_file(file_path):
                        if not any(exclude in file_path for exclude in exclude_patterns):
                            filtered_files.append(file_path)
    return filtered_files


def run_cpplint(args):
    """Run cpplint in Docker and properly handle output."""
    workspace_dir = '/workspace'
    cpp_files = filter_cpp_files(args.paths, args.exclude)

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
        cmd = ['ament_cpplint']
        if args.filters:
            cmd.extend(['--filter', args.filters])
        if args.root:
            cmd.extend(['--root', args.root])
        if args.output:
            cmd.extend(['--output', args.output])
        cmd.extend(['--linelength', str(args.linelength)])

        # Handle xunit file output
        if args.xunit_file:
            # Create absolute path and ensure directory exists
            abs_xunit_path = os.path.abspath(args.xunit_file)
            os.makedirs(os.path.dirname(abs_xunit_path) or '.', exist_ok=True)
            # Use relative path inside container
            rel_xunit_path = os.path.relpath(abs_xunit_path, cwd)
            cmd.extend(['--xunit-file', rel_xunit_path])
            # Mount as read-write to allow file creation
            volumes = {cwd: {'bind': workspace_dir, 'mode': 'rw'}}
        else:
            volumes = {cwd: {'bind': workspace_dir, 'mode': 'ro'}}

        cmd.extend(cpp_files)

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


def main(argv=sys.argv[1:]):
    extensions = ['c', 'cc', 'cpp', 'cxx']
    headers = ['h', 'hh', 'hpp', 'hxx']

    parser = argparse.ArgumentParser(
        description='Check code against the Google style conventions using '
                    'cpplint.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--filters', metavar='FILTER,FILTER,...', type=str,
        help='A comma separated list of category filters to apply')
    parser.add_argument(
        '--linelength', metavar='N', type=int, default=100,
        help='The maximum line length')
    parser.add_argument(
        '--root', type=str,
        help='The --root option for cpplint')
    parser.add_argument(
        '--exclude', default=[],
        nargs='*',
        help='Exclude C/C++ files from being checked.')
    parser.add_argument(
        '--output', type=str,
        help='The --output option for cpplint')
    parser.add_argument(
        'paths',
        nargs='*',
        default=[os.curdir],
        help=f'The files or directories to check. For directories files ending '
             f'in {", ".join([f"'.{e}'" for e in extensions + headers])} will be considered.')
    parser.add_argument(
        '--xunit-file',
        help='Generate a xunit compliant XML file')
    args = parser.parse_args(argv)
    return run_cpplint(args)


if __name__ == '__main__':
    sys.exit(main())
