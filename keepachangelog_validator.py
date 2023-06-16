import re
import datetime
import argparse
import os
from typing import List, Dict, Any


class Version:
    """
    Represents a version in the changelog.
    """

    def __init__(self, version: str, date: str, sections: List[Dict[str, Any]]):
        """
        Initializes a Version object.

        Args:
            version: The version string.
            date: The release date string.
            sections: The list of sections in the version.
        """
        self._version = version
        self._date = date
        self._sections = sections

    def version(self) -> str:
        """
        Returns the version string.
        """
        return self._version

    def date(self) -> str:
        """
        Returns the release date string.
        """
        return self._date

    def sections(self) -> List[Dict[str, Any]]:
        """
        Returns the list of sections in the version.
        """
        return self._sections

    def has_link_reference(self) -> bool:
        """
        Checks if the version has a link reference.

        Returns:
            True if the version has a link reference, False otherwise.
        """
        return True  # Modify this if you have a way to check for link references


class KACLValidator:
    """
    Validator for Keep a Changelog format.
    """
    semver_regex = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"

    @staticmethod
    def verify_semver(version: str) -> bool:
        """
        Verifies if the given version string matches the semantic version format.

        Args:
            version: The version string.

        Returns:
            True if the version string is a valid semantic version, False otherwise.
        """
        regex = KACLValidator.semver_regex
        if not re.match(regex, version):
            return False
        return True

    @staticmethod
    def verify_date(date: str) -> bool:
        """
        Verifies if the given date string matches the format 'YYYY-MM-DD'.

        Args:
            date: The date string.

        Returns:
            True if the date string is a valid format, False otherwise.
        """
        if not date or len(date) < 1:
            return False
        if not re.match(r"\d{4}-\d{2}-\d{2}", date):
            return False
        return True

    @staticmethod
    def verify_sections(sections: List[Dict[str, Any]], allowed_sections: List[str]) -> bool:
        """
        Verifies if the sections in the given list are valid.

        Args:
            sections: The list of sections.
            allowed_sections: The list of allowed section names.

        Returns:
            True if all sections are valid, False otherwise.
        """
        for section in sections:
            if section['section'] not in allowed_sections:
                print("Section issue:", section['section'])
                return False
        return True

    @staticmethod
    def verify_links(has_link_reference: bool) -> bool:
        """
        Verifies if the version has a link reference.

        Args:
            has_link_reference: True if the version has a link reference, False otherwise.

        Returns:
            True if the version has a link reference or if link verification is not implemented,
            False if the version is linked but no link reference is found in the changelog.
        """
        return True  # Modify this if you have a way to check for link references

    @staticmethod
    def verify_version(version: Version, allowed_sections: List[str]) -> List[str]:
        """
        Verifies a version against the Keep a Changelog format.

        Args:
            version: The Version object to verify.
            allowed_sections: The list of allowed section names.

        Returns:
            A list of error messages. An empty list indicates no errors.
        """
        errors = []

        if not KACLValidator.verify_semver(version.version()):
            errors.append(f"Version {version.version()} is not a valid semantic version.")

        if not KACLValidator.verify_date(version.date()):
            errors.append(f"Version {version.version()} has an invalid release date format.")

        if not KACLValidator.verify_sections(version.sections(), allowed_sections):
            sections_str = ", ".join(allowed_sections)
            errors.append(
                f"Version {version.version()} contains an invalid section. "
                f"Valid sections are: {sections_str}"
            )

        if not KACLValidator.verify_links(version.has_link_reference()):
            errors.append(
                f"Version {version.version()} is linked, but no link reference found in the changelog."
            )

        return errors


def parse_changelog(changelog_content: str, allowed_sections: List[str]) -> List[Dict[str, Any]]:
    """
    Parses the changelog content and returns a list of versions with sections.

    Args:
        changelog_content: The content of the changelog.
        allowed_sections: The list of allowed section names.

    Returns:
        A list of dictionaries representing the versions in the changelog, each with a version, date, and sections.
    """
    changelog = []
    versions = re.findall(r'## \[(.*?)\] - (\d{4}-\d{2}-\d{2})', changelog_content)
    for version, date in versions:
        sections = re.findall(r'### (.*?)\n(.*?)(?=\n###|\Z)', changelog_content, re.DOTALL)
        parsed_sections = []
        for title, changes in sections:
            if title.strip() in allowed_sections:
                parsed_sections.append({'section': title.strip(), 'changes': changes.strip().split('\n- ')})
            else:
                print('\033[93m', "Not allowed section:", title, '\033[0m')
                return []
        changelog.append({'version': version, 'date': date, 'sections': parsed_sections})
    return changelog


def verify_changelog_format(changelog_content: str) -> bool:
    """
    Verifies the format of the changelog content.

    Args:
        changelog_content: The content of the changelog.

    Returns:
        True if the format is valid, False otherwise.
    """
    # Check section "Changelog"
    if not re.search(r"# Changelog", changelog_content):
        print("No 'Changelog' header found.")
        return False

    # Check section "Unreleased"
    if not re.search(r"## \[Unreleased\]", changelog_content):
        print("'Unreleased' section is missing from the Changelog.")
        return False

    content_lines = changelog_content.split("\n")

    # Check the format "## [M.m.p] - YYYY-MM-DD"
    for line in content_lines:
        if line.startswith('##') and "[Unreleased]" not in line and "###" not in line:
            version_match = re.match(r'## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})$', line.strip())
            if not version_match:
                print('\033[93m', "Format not allowed:", line, '\033[0m')
                return False

    # check versions, dates order
    pattern = r"## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})"
    matches = re.findall(pattern, changelog_content)

    if len(matches) < 2:
        print("Versions need to be defined with a release date in the following format 'YYYY-MM-DD'")
        return False

    for i in range(1, len(matches)):
        version_current = matches[i][0]
        version_previous = matches[i - 1][0]

        date_current = datetime.datetime.strptime(matches[i][1], "%Y-%m-%d")
        date_previous = datetime.datetime.strptime(matches[i - 1][1], "%Y-%m-%d")

        if version_current >= version_previous:
            print("Versions are not in descending order. v1:", version_current, "v2:", version_previous)
            return False

        if date_current > date_previous:
            print("Dates are not in chronological order. t1:", date_current, "t2:", date_previous)
            return False

    return True

def find_changelog_file():
    """
    Find the first changelog file in the current directory.
    """
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if file.lower() == "changelog.md":
                return os.path.join(root, file)
    return None

def main():
    """
    Entry point of the script.
    """
    parser = argparse.ArgumentParser(description='Keep a Changelog Validator')
    parser.add_argument('--file', help='Path to the changelog file')
    parser.add_argument('--auto', action='store_true', help='Automatically find changelog.md file in the directory')
    args = parser.parse_args()

    if args.auto:
        changelog_file = find_changelog_file()
        if changelog_file is None:
            print("No changelog.md file found in the directory or its subdirectories.")
            exit(1)
    else:
        if args.file is None:
            print("Please provide the path to the changelog file using the --file argument or use --auto to automatically find the file.")
            exit(1)
        changelog_file = args.file

    allowed_sections = ['Added', 'Changed', 'Fixed', 'Deprecated', 'Removed']

    with open(changelog_file, 'r') as file:
        changelog_content = file.read()

    if not verify_changelog_format(changelog_content):
        print('Changelog format is invalid.')
        exit(1)

    changelog = parse_changelog(changelog_content, allowed_sections)

    if not changelog:
        print("Issue with changelog parsing")
        exit(1)

    for version_data in changelog:
        version = version_data['version']
        date = version_data['date']
        sections = version_data['sections']

        version_obj = Version(version, date, sections)

        # Verify the version
        errors = KACLValidator.verify_version(version_obj, allowed_sections)

        if errors:
            print(f"Errors found in version {version}:")
            for error in errors:
                print(f"- {error}")
            exit(1)
        else:
            print(f"Version {version} is valid.")


if __name__ == "__main__":
    main()
