"""
Tests for the repo manager tool
"""

import os
import tempfile
import unittest

import candig.metadata.exceptions as exceptions
import candig.metadata.datarepo as datarepo
import candig.metadata.cli.repomanager as cli_repomanager


class TestGetNameFromPath(unittest.TestCase):
    """
    Tests the method for deriving the default name of objects from file
    paths.
    """

    def testError(self):
        self.assertRaises(ValueError, cli_repomanager.getNameFromPath, "")

    def testLocalDirectory(self):
        self.assertEqual(
            cli_repomanager.getNameFromPath("no_extension"), "no_extension")
        self.assertEqual(cli_repomanager.getNameFromPath("x.y"), "x")
        self.assertEqual(cli_repomanager.getNameFromPath("x.y.z"), "x")

    def testFullPaths(self):
        self.assertEqual(
            cli_repomanager.getNameFromPath("/no_ext"), "no_ext")
        self.assertEqual(cli_repomanager.getNameFromPath("/x.y"), "x")
        self.assertEqual(cli_repomanager.getNameFromPath("/x.y.z"), "x")
        self.assertEqual(
            cli_repomanager.getNameFromPath("/a/no_ext"), "no_ext")
        self.assertEqual(cli_repomanager.getNameFromPath("/a/x.y"), "x")
        self.assertEqual(cli_repomanager.getNameFromPath("/a/x.y.z"), "x")

    def testUrls(self):
        self.assertEqual(
            cli_repomanager.getNameFromPath("file:///no_ext"), "no_ext")
        self.assertEqual(
            cli_repomanager.getNameFromPath("http://example.com/x.y"), "x")
        self.assertEqual(
            cli_repomanager.getNameFromPath("ftp://x.y.z"), "x")

    def testDirectoryName(self):
        self.assertEqual(cli_repomanager.getNameFromPath("/a/xy"), "xy")
        self.assertEqual(cli_repomanager.getNameFromPath("/a/xy/"), "xy")
        self.assertEqual(cli_repomanager.getNameFromPath("xy/"), "xy")
        self.assertEqual(cli_repomanager.getNameFromPath("xy"), "xy")


class AbstractRepoManagerTest(unittest.TestCase):
    """
    Base class for repo manager tests.
    """

    def setUp(self):
        fd, self._repoPath = tempfile.mkstemp(prefix="candig_repoman_test")
        os.unlink(self._repoPath)

    def runCommand(self, cmd):
        cli_repomanager.RepoManager.runCommand(cmd.split())

    def tearDown(self):
        os.unlink(self._repoPath)

    def readRepo(self):
        repo = datarepo.SqlDataRepository(self._repoPath)
        repo.open(datarepo.MODE_READ)
        return repo

    def init(self):
        self.runCommand("init {}".format(self._repoPath))

    def addDataset(self, datasetName=None):
        if datasetName is None:
            datasetName = "test_dataset"
            self._datasetName = datasetName
        cmd = "add-dataset {} {}".format(self._repoPath, datasetName)
        self.runCommand(cmd)


class TestAddDataset(AbstractRepoManagerTest):

    def setUp(self):
        super(TestAddDataset, self).setUp()
        self.init()

    def testDefaults(self):
        name = "test_dataset"
        self.runCommand("add-dataset {} {}".format(self._repoPath, name))
        repo = self.readRepo()
        dataset = repo.getDatasetByName(name)
        self.assertEqual(dataset.getLocalId(), name)

    def testSameName(self):
        name = "test_dataset"
        cmd = "add-dataset {} {}".format(self._repoPath, name)
        self.runCommand(cmd)
        self.assertRaises(
            exceptions.RepoManagerException, self.runCommand, cmd)


class TestRemoveDataset(AbstractRepoManagerTest):

    def setUp(self):
        super(TestRemoveDataset, self).setUp()
        self.init()
        self.addDataset()
        self.addReferenceSet()

    def assertDatasetRemoved(self):
        repo = self.readRepo()
        self.assertRaises(
            exceptions.DatasetNameNotFoundException,
            repo.getDatasetByName, self._datasetName)

    def testEmptyDatasetForce(self):
        self.runCommand("remove-dataset {} {} -f".format(
            self._repoPath, self._datasetName))
        self.assertDatasetRemoved()

    def testContainsReadGroupSet(self):
        self.addReadGroupSet()
        self.runCommand("remove-dataset {} {} -f".format(
            self._repoPath, self._datasetName))
        self.assertDatasetRemoved()


class TestVerify(AbstractRepoManagerTest):

    def setUp(self):
        super(TestVerify, self).setUp()

    def testVerify(self):
        self.init()
        self.addDataset()
        cmd = "verify {}".format(self._repoPath)
        self.runCommand(cmd)


class TestDuplicateNameDelete(AbstractRepoManagerTest):
    """
    If two objects exist with the same name in different datasets,
    ensure that only one is deleted on a delete call
    """

    def setUp(self):
        super(TestDuplicateNameDelete, self).setUp()
        self.init()
        self.dataset1Name = "dataset1"
        self.dataset2Name = "dataset2"
        self.addDataset(self.dataset1Name)
        self.addDataset(self.dataset2Name)

    def readDatasets(self):
        repo = self.readRepo()
        self.dataset1 = repo.getDatasetByName(self.dataset1Name)
        self.dataset2 = repo.getDatasetByName(self.dataset2Name)
