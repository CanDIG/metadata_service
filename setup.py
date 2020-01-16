# Don't import __future__ packages here; they make setup fail

# First, we try to use setuptools. If it's not available locally,
# we fall back on ez_setup.
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

with open("README.rst") as readmeFile:
    long_description = readmeFile.read()

install_requires = []
with open("requirements.txt") as requirementsFile:
    for line in requirementsFile:
        line = line.strip()
        if line and not line.startswith('#'):
            if line.find('-c constraints.txt') == -1:
                pinnedVersion = line.split()[0]
                install_requires.append(pinnedVersion)

dependency_links = []
try:
    with open("constraints.txt") as constraintsFile:
        for line in constraintsFile:
            line = line.strip()
            if line and not line.startswith('#'):
                dependency_links.append(line)
except EnvironmentError:
    print('No constraints file found, proceeding without '
          'creating dependency links.')

setup(
    name="metadata_service",
    description="Metadata service implementation of the CanDIG APIs",
    packages=[
        "candig",
        "candig.metadata",
        "candig.metadata.datamodel",
        "candig.metadata.cli",
        "candig.metadata.repo",
        "candig.metadata.schemas",
        "candig.metadata.schemas.google",
        "candig.metadata.ingest",
        "candig.metadata.templates",
        "candig.metadata.static",
        "candig.metadata.static.dist",
    ],
    namespace_packages=[
        "candig",
        # "candig.metadata",
    ],
    zip_safe=False,
    url="https://github.com/CanDIG/metadata_service",
    use_scm_version=True,
    # use_scm_version={
    #     'root': '..',
    #     "write_to": "_version.py"
    #     },
    entry_points={
        'console_scripts': [
            # 'candig_configtest=candig.metadata.cli.configtest:configtest_main',
            'metadata_server=candig.metadata.cli.server:server_main',
            'metadata_repo=candig.metadata.cli.repomanager:repo_main',
            'metadata_ingest=candig.metadata.ingest.ingest:main',
            'metadata_load_tier=candig.metadata.ingest.load_tiers:main',
        ]
    },
    long_description=long_description,
    install_requires=install_requires,
    dependency_links=dependency_links,
    license='Apache License 2.0',
    include_package_data=True,
    author="CanDIG Team",
    author_email="info@distributedgenomics.ca",
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    keywords=['genomics', 'candig', 'metadata'],
    # Use setuptools_scm to set the version number automatically from Git
    setup_requires=['setuptools_scm'],
)
