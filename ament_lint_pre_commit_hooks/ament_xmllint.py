#!/usr/bin/env python3
import argparse
import os
import sys

import docker

DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_IMAGE_NAME = 'ament_xmllint_linter'
DOCKERFILE_NAME = 'Dockerfile'

# Define default file extensions
default_extensions = ['xml']


def is_xml_file(path, extensions):
    """Check if path is an XML file we should lint."""
    filename = os.path.basename(path)
    return any(filename.endswith(f'.{ext}') for ext in extensions)


def filter_xml_files(paths, extensions, exclude_patterns=None):
    """Filter and return only XML files from the input paths."""
    filtered_files = []
    exclude_patterns = exclude_patterns or []

    for path in paths:
        if os.path.isfile(path) and is_xml_file(path, extensions):
            if not any(exclude in os.path.basename(path) for exclude in exclude_patterns):
                filtered_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if is_xml_file(file, extensions):
                        if not any(exclude in file for exclude in exclude_patterns):
                            filtered_files.append(os.path.join(root, file))
    return filtered_files


def run_xmllint(args):
    """Run xmllint in Docker and properly handle output."""
    workspace_dir = '/workspace'
    xml_files = filter_xml_files(args.paths, args.extensions, args.exclude)

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
        cmd = ['ament_xmllint']
        cmd.extend(xml_files)

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
        description='Check XML markup using xmllint.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'paths',
        nargs='*',
        default=[os.curdir],
        help=f'The files or directories to check. For directories, only files ending '
             f'in {', '.join([f'".{e}"' for e in default_extensions])} will be considered '
             f'(unless overruled by the --extensions option)')
    parser.add_argument(
        '--exclude',
        nargs='*',
        default=[],
        help='Exclude specific file names and directory names from the check')
    parser.add_argument(
        '--extensions',
        nargs='*',
        default=default_extensions,
        help='The file extensions of the files to check')

    args = parser.parse_args(argv)
    return run_xmllint(args)


if __name__ == '__main__':
    sys.exit(main())
