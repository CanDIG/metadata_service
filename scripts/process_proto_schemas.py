#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to process protobuf schemas for CanDIG metadata service.

Steps:
    0) Find protoc (version > 3.0.0)
    2) Find all proto schema files
    3) Run protoc to process schema files
    4) Place compiled pb2 files into destination folder


Usage:
    scripts/process_proto_schemas.py <version>

Options:
   -h --help          Show this screen
   -v --version       Version
"""

import os
import re
import glob
import subprocess
from docopt import docopt


class ProtoBufGenerator():
    """Run protoc to process schema files."""

    def __init__(self, version: str):
        """
        Set version information.

        Parameters
        ----------
        version : str
            Schema version informaiton.

        Returns
        -------
        None.

        """
        self.version = version

    def _find_in_path(self, cmd: str = 'protoc') -> str:
        """
        Find a command in environment PATH.

        Parameters
        ----------
        cmd : str
            Command to look for, like "protoc".

        Returns
        -------
        hits : list of str
            Potential protoc pathes

        """
        hits = []
        for folder in os.environ.get("PATH", os.defpath).split(os.pathsep):

            possible = os.path.join(folder, cmd)

            if os.path.exists(possible):
                hits.append(possible)

        return hits

    # https://stackoverflow.com/questions/22490366/how-to-use-cmp-in-python-3
    def _cmp(self, a, b):
        return (a > b) - (a < b)

    # From http://stackoverflow.com/a/1714190/320546
    def _version_compare(self, version1, version2):
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
        return self._cmp(normalize(version1), normalize(version2))

    def _getProtoc(self) -> str:
        """
        Find protoc that has a version > 3.0.0.

        Parameters
        ----------
            None

        Returns
        -------
        protoc : str
            Protoc path to use.

        """
        protoc = None

        for protoc_program in self._find_in_path('protoc'):

            output = subprocess.check_output(
                [protoc_program, "--version"]).strip()

            try:
                (lib, version) = output.decode('utf-8').split()

                if lib != "libprotoc":
                    raise Exception("lib didn't match 'libprotoc'")

                if self._version_compare("3.0.0", version) > 0:
                    raise Exception("version < 3.0.0")

                protoc = protoc_program
                break

            except Exception:
                print(
                    "Not using {path} because it returned " +
                    "'{version}' rather than \"libprotoc <version>\", where " +
                    "<version> >= 3.0.0").format(
                        path=protoc_program, version=output)

        if protoc is None:
            raise Exception("Can't find a good protoc.")

        print("Using protoc: '{}'".format(protoc))

        return protoc

    def _writeVersionFile(self, destination_path: str):
        """
        Generate an version info file into the destination folder.

        Parameters
        ----------
        destination_path : str
            Path where the info file will be geneated.

        Returns
        -------
        None.

        """
        versionFilePath = os.path.join(
            destination_path, '_protocol_version.py'
            )
        try:
            with open(versionFilePath, "w") as version_file:
                version_file.write("version = '{}'\n".format(self.version))

        except IOError:
            print('Error while writting version information')

    def remove_file_descriptors(self, pb2_filename: str):
        """
        Remove "file=DESCRIPTOR" from the fielddescriptions.

        Some versions of protoc add an extra "file=DESCRIPTOR" into every
        _descriptor.FieldDescriptor of the pb2 file, remove those.

        Parameters
        ----------
        filename : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        print(pb2_filename)
        # Read pb2 file content
        content = ''
        try:
            with open(pb2_filename, 'r') as filehandler:
                for line in filehandler.readlines():
                    # Remove the "file=DESCRIPTOR" terms
                    content = ''.join(
                        (content, line.replace(', file=DESCRIPTOR', ''))
                    )
        except IOError():
            print('Error accessing {0} file'.format(pb2_filename))
        # Overwrite the original file
        try:
            with open(pb2_filename, 'w') as filehandler:
                filehandler.write(content)
        except IOError():
            print('Error could not overwrite {0} file'.format(pb2_filename))

    def run(self, schema_path: str, pb2_path: str):
        """
        Execute schema processing.

        Steps:
            0) Find protoc (version > 3.0.0)
            1) Find all proto schema files
            2) Run protoc to process

        Parameters
        ----------
        schema_path : str
            Path information of the folder contains the proto files.
        pb2_path : str
            Path information where the processed files will be placed.

        Returns
        -------
        None.

        """
        # Find protoc
        protoc = self._getProtoc()

        # Make sure the destination folder exists
        os.makedirs(pb2_path, exist_ok=True)
        with open('{0}/__init__.py'.format(pb2_path), 'w'):
            pass

        # Find all proto schema files
        pattern = '{}/**/*.proto'.format(schema_path)
        for filename in glob.glob(pattern, recursive=True):

            # Run protoc to process the files
            command = '{protoc} -I={schema} --python_out={pb2} {filename}'
            command = command.format(
                protoc=protoc,
                schema=schema_path,
                pb2=pb2_path,
                filename=filename,#.replace(schema_path, ''),
            )
            print(command)

            # Run protoc to process the files
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError:
                print('ERROR running: {}'.format(command))

            self.remove_file_descriptors(
                pb2_filename='{pb2_path}{proto_filename}_pb2.py'.format(
                    pb2_path=pb2_path,
                    proto_filename=filename.replace(
                        schema_path, '').replace('.proto', '')
                ),
            )

        self._writeVersionFile(pb2_path)


def main():
    """
    Handle all functionalities.

    Returns
    -------
    None.

    """
    # Default path information
    schema_path = "./candig/proto/"
    pb2_path = './'  # '/candig/metadata/schemas/'

    arguments = docopt(__doc__)

    protobuf_generator = ProtoBufGenerator(arguments['<version>'])
    protobuf_generator.run(
        schema_path,
        pb2_path,
    )


if __name__ == '__main__':
    main()
