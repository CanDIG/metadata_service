"""Centralizes hardcoded paths, names, etc. used in tests."""

import os


packageName = 'candig'


def getProjectRootFilePath():
    # assumes we're in a directory one level below the project root
    return os.path.dirname(os.path.dirname(__file__))


def getGa4ghFilePath():
    return os.path.join(getProjectRootFilePath(), packageName)


testDir = 'tests'
testDataDir = os.path.join(testDir, 'data')
testDataRepo = os.path.join(testDataDir, 'registry.db')
testAccessList = os.path.join(testDataDir, 'acl.tsv')

# datasets
datasetName = "dataset1"
datasetsDir = os.path.join(testDataDir, "datasets")
datasetDir = os.path.join(datasetsDir, "dataset1")

# misc.
landingMessageHtml = os.path.join(testDataDir, "test.html")
