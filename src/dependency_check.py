"""
Python Dependency Check Utility

This script is a command-line utility that compares defined packages from a requirements.txt
file to the latest stable version on the PyPI index.

Usage:
  dependency_check.py [options] <requirements_file>

Options:
  -h, --help            Show this help message and exit.
  -o OUTPUT, --output=OUTPUT
                        Specify an output file or folder to write the results (CSV format).
"""

import argparse
import subprocess
import re
import os
import csv
from tqdm import tqdm


def compare_versions(current_version: str, latest_version: str) -> str:
    """Helper function to compare versions and categorize result

    :param current_version: Current package semantic version number
    :type current_version: str
    :param latest_version: Latest pypi package semantic version number
    :type latest_version: str
    :return: Categorized result of comparison (match, major, minor, etc)
    :rtype: str
    """

    if current_version == 'n/a' or latest_version == 'n/a':
        return 'n/a'
    elif current_version == latest_version:
        return 'match'
    sem_version = {
        0: 'major',
        1: 'minor',
        2: 'patch'
    }
    # Iterate each element of semantic version for comparison
    for idx, (current, latest) in enumerate(zip(current_version.split('.'), latest_version.split('.'))):
        if current != latest:
            return sem_version[idx]
    return 'n/a'


def compare_packages(requirements_file: str, output_file: str = '') -> None:
    """Function to check packages in a requirements file against
    the latest stable version on the pip index

    :param requirements_file: properly formatted requirements.txt file
    :type requirements_file: str
    :param output_file: location to write CSV output file
    :type output_file: str
    """

    # Read list of packages from a file
    with open(requirements_file, 'r') as f:
        packages = f.read().splitlines()
    print(f'Comparing {len(packages)
                       } packages from requirements to latest on index')

    # Instantiate array to capture results
    version_compare = [
        ['package', 'version', 'latest', 'compare']
    ]

    # Iterate packages to check latest version
    for package in tqdm(packages):
        # Split package string into name and version or path
        if '==' in package:
            package_info = package.split('==')
        else:
            package_info = package.split(' @ ')
        # Parse version from package and later pip message
        package_string = package_info[0].replace('-', '[\\-_]')
        version_pattern = f'{package_string}\\-(\\d+\\.\\d+\\.\\d+)'
        if package_info[1].startswith('file') or package_info[1].startswith('http'):
            file_version = re.search(
                version_pattern, package_info[1], re.IGNORECASE)
            if file_version:
                package_info[1] = file_version[1]
            else:
                package_info[1] = package_info[1].split('/')[-1]
        # Dry run pip install to check latest version
        dry_install = subprocess.run([
            'pip', 'install',
            '--upgrade', '--upgrade-strategy', 'eager',
            '--dry-run', '--no-cache-dir', '--force-reinstall',
            package_info[0]], capture_output=True)
        if dry_install.returncode == 0:
            version_search = re.search(version_pattern, str(
                dry_install.stdout), re.IGNORECASE)
            if version_search:
                version = version_search[1]
            else:
                version = 'n/a'
        else:
            version = 'n/a'
        comparison = compare_versions(package_info[1], version)
        version_compare.append([*package_info, version, comparison])

    if output_file:
        # Validate and format output file format
        if os.path.isdir(output_file):
            output_file += '/version_check.csv'
        elif not output_file.endswith('.csv'):
            output_file += '.csv'
        with open(output_file, 'w') as fp:
            csvwriter = csv.writer(fp)
            csvwriter.writerows(version_compare)
    else:
        column_widths = [max(len(str(value)) for value in column)
                         for column in zip(*version_compare)]
        compare_string = '\n'.join(
            ["  ".join(f"{value:<{width}}" for value, width in zip(
                row, column_widths)) for row in version_compare]
        )
        print(compare_string)


def main() -> None:
    """Main function to capture arguments and 
    """
    # Configure parser for requirements file
    parser = argparse.ArgumentParser(
        prog='DependencyCheck',
        description='Checks requirements.txt file against latest available versions'
    )
    parser.add_argument('filename', help='Path to requirements.txt file')
    parser.add_argument('-o', '--output', dest='output',
                        help='Location to write CSV file with results')
    args = parser.parse_args()

    # Call package comparison function with arguments
    compare_packages(args.filename, args.output)


if __name__ == '__main__':
    main()
