"""
Tests the cli
"""

import unittest
import shlex

import candig.metadata.cli.server as cli_server
import candig.metadata.cli.repomanager as cli_repomanager

import candig.metadata.protocol as protocol


class TestServerArguments(unittest.TestCase):
    """
    Tests that the server can parse expected arguments
    """
    def testParseArguments(self):
        cliInput = """--port 7777 --host 123.4.5.6 --config MockConfigName
        --config-file /path/to/config --tls --dont-use-reloader"""
        parser = cli_server.getServerParser()
        args = parser.parse_args(cliInput.split())
        self.assertEqual(args.port, 7777)
        self.assertEqual(args.host, "123.4.5.6")
        self.assertEqual(args.config, "MockConfigName")
        self.assertEqual(args.config_file, "/path/to/config")
        self.assertTrue(args.tls)
        self.assertTrue(args.dont_use_reloader)


class TestRepoManagerCli(unittest.TestCase):

    def setUp(self):
        self.parser = cli_repomanager.RepoManager.getParser()
        self.registryPath = 'a/repo/path'
        self.datasetName = "datasetName"
        self.filePath = 'a/file/path'
        self.dirPath = 'a/dir/path/'
        self.individualName = "test"
        self.biosampleName = "test"
        self.individual = protocol.toJson(
            protocol.Individual(
                name="test",
                created="2016-05-19T21:00:19Z",
                updated="2016-05-19T21:00:19Z"))
        self.biosample = protocol.toJson(
            protocol.Biosample(
                name="test",
                created="2016-05-19T21:00:19Z",
                updated="2016-05-19T21:00:19Z"))

    def testInit(self):
        cliInput = "init {}".format(self.registryPath)
        args = self.parser.parse_args(cliInput.split())
        self.assertEqual(args.registryPath, self.registryPath)
        self.assertEqual(args.runner, "init")

    def testVerify(self):
        cliInput = "verify {}".format(self.registryPath)
        args = self.parser.parse_args(cliInput.split())
        self.assertEqual(args.registryPath, self.registryPath)
        self.assertEqual(args.runner, "verify")

    def testList(self):
        cliInput = "list {}".format(self.registryPath)
        args = self.parser.parse_args(cliInput.split())
        self.assertEqual(args.registryPath, self.registryPath)
        self.assertEqual(args.runner, "list")

    def testAddDataset(self):
        cliInput = "add-dataset {} {}".format(
            self.registryPath, self.datasetName)
        args = self.parser.parse_args(cliInput.split())
        self.assertEqual(args.registryPath, self.registryPath)
        self.assertEqual(args.datasetName, self.datasetName)
        self.assertEqual(args.runner, "addDataset")

    def testRemoveDataset(self):
        cliInput = "remove-dataset {} {} -f".format(
            self.registryPath, self.datasetName)
        args = self.parser.parse_args(cliInput.split())
        self.assertEqual(args.registryPath, self.registryPath)
        self.assertEqual(args.datasetName, self.datasetName)
        self.assertEqual(args.runner, "removeDataset")
        self.assertEqual(args.force, True)
