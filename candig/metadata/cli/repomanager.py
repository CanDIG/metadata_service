"""
repo manager cli
"""

import glob
import json
import os
import sys
import textwrap
import traceback
import urllib.parse

import candig.metadata.cli as cli
import candig.metadata.datamodel.clinical_metadata as clinical_metadata
import candig.metadata.datamodel.pipeline_metadata as pipeline_metadata
import candig.metadata.datamodel.datasets as datasets
import candig.metadata.datarepo as datarepo
import candig.metadata.exceptions as exceptions
from candig.metadata.ontology import OntologyValidator

import candig.metadata.cli.common_cli as common_cli


def getNameFromPath(filePath):
    """
    Returns the filename of the specified path without its extensions.
    This is usually how we derive the default name for a given object.
    """
    if len(filePath) == 0:
        raise ValueError("Cannot have empty path for name")
    fileName = os.path.split(os.path.normpath(filePath))[1]
    # We need to handle things like .fa.gz, so we can't use
    # os.path.splitext
    ret = fileName.split(".")[0]
    assert ret != ""
    return ret


def getRawInput(display):
    """
    Wrapper around raw_input; put into separate function so that it
    can be easily mocked for tests.
    """
    return input(display)


class RepoManager(object):
    """
    Class that provide command line functionality to manage a
    data repository.
    """
    def __init__(self, args):
        self._args = args
        self._registryPath = args.registryPath
        self._repo = datarepo.SqlDataRepository(self._registryPath)

    def _confirmDelete(self, objectType, name, func):
        if self._args.force:
            func()
        else:
            displayString = (
                "Are you sure you want to delete the {} '{}'? "
                "[y|N] ".format(objectType, name))
            userResponse = getRawInput(displayString)
            if userResponse.strip() == 'y':
                func()
            else:
                print("Aborted")

    def _updateRepo(self, func, *args, **kwargs):
        """
        Runs the specified function that updates the repo with the specified
        arguments. This method ensures that all updates are transactional,
        so that if any part of the update fails no changes are made to the
        repo.
        """
        # TODO how do we make this properly transactional?
        self._repo.open(datarepo.MODE_WRITE)
        try:
            func(*args, **kwargs)
            self._repo.commit()
        finally:
            self._repo.close()

    def _validateRepo(self):
        """
        Checks if the specified registry path has a valid repo.
        """
        if not self._repo.exists():
            raise exceptions.RepoManagerException(
                "Repo '{}' does not exist. Please create a new repo "
                "using the 'init' command.".format(self._registryPath))

    def _openRepo(self):
        self._validateRepo()
        self._repo.open(datarepo.MODE_READ)

    def _getFilePath(self, filePath, useRelativePath):
        return filePath if useRelativePath else os.path.abspath(filePath)

    def init(self):
        forceMessage = (
            "Respository '{}' already exists. Use --force to overwrite")
        if self._repo.exists():
            if self._args.force:
                self._repo.delete()
            else:
                raise exceptions.RepoManagerException(
                    forceMessage.format(self._registryPath))
        self._updateRepo(self._repo.initialise)

    def list(self):
        """
        Lists the contents of this repo.
        """
        self._openRepo()
        # TODO this is _very_ crude. We need much more options and detail here.
        self._repo.printSummary()

    def verify(self):
        """
        Checks that the data pointed to in the repository works and
        we don't have any broken URLs, missing files, etc.
        """
        self._openRepo()
        self._repo.verify()

    def addDataset(self):
        """
        Adds a new dataset into this repo.
        """
        self._validateRepo()
        dataset = datasets.Dataset(self._args.datasetName)
        dataset.setDescription(self._args.description)
        dataset.setAttributes(json.loads(self._args.attributes))
        self._updateRepo(self._repo.insertDataset, dataset)

    def addDatasetDuo(self):
        """
        Adds DUO info to existing dataset into this repo.
        """
        self._validateRepo()
        dataset = datasets.Dataset(self._args.datasetName)

        try:
            with open(self._args.dataUseOntologyFile, 'r') as f:
                duo_info = json.load(f)
        except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
            raise exceptions.JsonFileOpenException(e)

        validator = OntologyValidator(duo_info)

        # If the DUO Terms provided are valid.
        if validator.validate_duo():
            duo_list = validator.get_duo_list()
            dataset.setDuoInfo(duo_list)
            self._updateRepo(self._repo.updateDatasetDuo, dataset)
        else:
            print("Aborted.")

    def removeDataset(self):
        """
        Removes a dataset from the repo.
        """
        self._validateRepo()
        dataset = self._repo.getSqlDatasetByName(self._args.datasetName)

        def func():
            self._updateRepo(self._repo.removeDataset, dataset)
        self._confirmDelete("Dataset", dataset.getLocalId(), func)

    def removeDatasetDuo(self):
        """
        Removes a dataset's DUO info from the repo.
        """
        self._validateRepo()
        dataset = self._repo.getSqlDatasetByName(self._args.datasetName)

        def func():
            self._updateRepo(self._repo.deleteDatasetDuo, dataset)
        self._confirmDelete("the Data Use Ontology Info For Dataset", dataset.getLocalId(), func)

    def addPatient(self):
        """
        Adds a new patient into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        patient = clinical_metadata.Patient(
            dataset, self._args.patientName)
        patient.populateFromJson(self._args.patient)
        self._updateRepo(self._repo.insertPatient, patient)

    def removePatient(self):
        """
        Removes an patient from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        patient = dataset.getPatientByName(self._args.patientName)

        def func():
            self._updateRepo(self._repo.removePatient, patient)
        self._confirmDelete("Patient", patient.getLocalId(), func)

    def addEnrollment(self):
        """
        Adds a new enrollment into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        enrollment = clinical_metadata.Enrollment(
            dataset, self._args.enrollmentName)
        enrollment.populateFromJson(self._args.enrollment)
        self._updateRepo(self._repo.insertEnrollment, enrollment)

    def removeEnrollment(self):
        """
        Removes an enrollment from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        enrollment = dataset.getEnrollmentByName(self._args.enrollmentName)

        def func():
            self._updateRepo(self._repo.removeEnrollment, enrollment)
        self._confirmDelete("Enrollment", enrollment.getLocalId(), func)

    def addConsent(self):
        """
        Adds a new consent into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        consent = clinical_metadata.Consent(
            dataset, self._args.consentName)
        consent.populateFromJson(self._args.consent)
        self._updateRepo(self._repo.insertConsent, consent)

    def removeConsent(self):
        """
        Removes an consent from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        consent = dataset.getConsentByName(self._args.consentName)

        def func():
            self._updateRepo(self._repo.removeConsent, consent)
        self._confirmDelete("Consent", consent.getLocalId(), func)

    def addDiagnosis(self):
        """
        Adds a new diagnosis into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        diagnosis = clinical_metadata.Diagnosis(
            dataset, self._args.diagnosisName)
        diagnosis.populateFromJson(self._args.diagnosis)
        self._updateRepo(self._repo.insertDiagnosis, diagnosis)

    def removeDiagnosis(self):
        """
        Removes an diagnosis from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        diagnosis = dataset.getDiagnosisByName(self._args.diagnosisName)

        def func():
            self._updateRepo(self._repo.removeDiagnosis, diagnosis)
        self._confirmDelete("Diagnosis", diagnosis.getLocalId(), func)

    def addSample(self):
        """
        Adds a new sample into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        sample = clinical_metadata.Sample(
            dataset, self._args.sampleName)
        sample.populateFromJson(self._args.sample)
        self._updateRepo(self._repo.insertSample, sample)

    def removeSample(self):
        """
        Removes an sample from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        sample = dataset.getSampleByName(self._args.sampleName)

        def func():
            self._updateRepo(self._repo.removeSample, sample)
        self._confirmDelete("Sample", sample.getLocalId(), func)

    def addTreatment(self):
        """
        Adds a new treatment into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        treatment = clinical_metadata.Treatment(
            dataset, self._args.treatmentName)
        treatment.populateFromJson(self._args.treatment)
        self._updateRepo(self._repo.insertTreatment, treatment)

    def removeTreatment(self):
        """
        Removes an treatment from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        treatment = dataset.getTreatmentByName(self._args.treatmentName)

        def func():
            self._updateRepo(self._repo.removeTreatment, treatment)
        self._confirmDelete("Treatment", treatment.getLocalId(), func)

    def addOutcome(self):
        """
        Adds a new outcome into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        outcome = clinical_metadata.Outcome(
            dataset, self._args.outcomeName)
        outcome.populateFromJson(self._args.outcome)
        self._updateRepo(self._repo.insertOutcome, outcome)

    def removeOutcome(self):
        """
        Removes an outcome from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        outcome = dataset.getOutcomeByName(self._args.outcomeName)

        def func():
            self._updateRepo(self._repo.removeOutcome, outcome)
        self._confirmDelete("Outcome", outcome.getLocalId(), func)

    def addComplication(self):
        """
        Adds a new complication into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        complication = clinical_metadata.Complication(
            dataset, self._args.complicationName)
        complication.populateFromJson(self._args.complication)
        self._updateRepo(self._repo.insertComplication, complication)

    def removeComplication(self):
        """
        Removes an complication from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        complication = dataset.getComplicationByName(self._args.complicationName)

        def func():
            self._updateRepo(self._repo.removeComplication, complication)
        self._confirmDelete("Complication", complication.getLocalId(), func)

    def addTumourboard(self):
        """
        Adds a new tumourboard into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        tumourboard = clinical_metadata.Tumourboard(
            dataset, self._args.tumourboardName)
        tumourboard.populateFromJson(self._args.tumourboard)
        self._updateRepo(self._repo.insertTumourboard, tumourboard)

    def removeTumourboard(self):
        """
        Removes an tumourboard from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        tumourboard = dataset.getTumourboardByName(self._args.tumourboardName)

        def func():
            self._updateRepo(self._repo.removeTumourboard, tumourboard)
        self._confirmDelete("Tumourboard", tumourboard.getLocalId(), func)

    def addChemotherapy(self):
        """
        Adds a new chemotherapy into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        chemotherapy = clinical_metadata.Chemotherapy(
            dataset, self._args.chemotherapyName)
        chemotherapy.populateFromJson(self._args.chemotherapy)
        self._updateRepo(self._repo.insertChemotherapy, chemotherapy)

    def removeChemotherapy(self):
        """
        Removes an chemotherapy from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        chemotherapy = dataset.getChemotherapyByName(self._args.chemotherapyName)

        def func():
            self._updateRepo(self._repo.removeChemotherapy, chemotherapy)
        self._confirmDelete("Chemotherapy", chemotherapy.getLocalId(), func)

    def addRadiotherapy(self):
        """
        Adds a new radiotherapy into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        radiotherapy = clinical_metadata.Radiotherapy(
            dataset, self._args.radiotherapyName)
        radiotherapy.populateFromJson(self._args.radiotherapy)
        self._updateRepo(self._repo.insertRadiotherapy, radiotherapy)

    def removeRadiotherapy(self):
        """
        Removes an radiotherapy from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        radiotherapy = dataset.getRadiotherapyByName(self._args.radiotherapyName)

        def func():
            self._updateRepo(self._repo.removeRadiotherapy, radiotherapy)
        self._confirmDelete("Radiotherapy", radiotherapy.getLocalId(), func)

    def addSurgery(self):
        """
        Adds a new surgery into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        surgery = clinical_metadata.Surgery(
            dataset, self._args.surgeryName)
        surgery.populateFromJson(self._args.surgery)
        self._updateRepo(self._repo.insertSurgery, surgery)

    def removeSurgery(self):
        """
        Removes an surgery from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        surgery = dataset.getSurgeryByName(self._args.surgeryName)

        def func():
            self._updateRepo(self._repo.removeSurgery, surgery)
        self._confirmDelete("Surgery", surgery.getLocalId(), func)

    def addImmunotherapy(self):
        """
        Adds a new immunotherapy into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        immunotherapy = clinical_metadata.Immunotherapy(
            dataset, self._args.immunotherapyName)
        immunotherapy.populateFromJson(self._args.immunotherapy)
        self._updateRepo(self._repo.insertImmunotherapy, immunotherapy)

    def removeImmunotherapy(self):
        """
        Removes an immunotherapy from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        immunotherapy = dataset.getImmunotherapyByName(self._args.immunotherapyName)

        def func():
            self._updateRepo(self._repo.removeImmunotherapy, immunotherapy)
        self._confirmDelete("Immunotherapy", immunotherapy.getLocalId(), func)

    def addCelltransplant(self):
        """
        Adds a new celltransplant into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        celltransplant = clinical_metadata.Celltransplant(
            dataset, self._args.celltransplantName)
        celltransplant.populateFromJson(self._args.celltransplant)
        self._updateRepo(self._repo.insertCelltransplant, celltransplant)

    def removeCelltransplant(self):
        """
        Removes an celltransplant from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        celltransplant = dataset.getCelltransplantByName(self._args.celltransplantName)

        def func():
            self._updateRepo(self._repo.removeCelltransplant, celltransplant)
        self._confirmDelete("Celltransplant", celltransplant.getLocalId(), func)

    def addSlide(self):
        """
        Adds a new slide into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        slide = clinical_metadata.Slide(
            dataset, self._args.slideName)
        slide.populateFromJson(self._args.slide)
        self._updateRepo(self._repo.insertSlide, slide)

    def removeSlide(self):
        """
        Removes an slide from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        slide = dataset.getSlideByName(self._args.slideName)

        def func():
            self._updateRepo(self._repo.removeSlide, slide)
        self._confirmDelete("Slide", slide.getLocalId(), func)

    def addStudy(self):
        """
        Adds a new study into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        study = clinical_metadata.Study(
            dataset, self._args.studyName)
        study.populateFromJson(self._args.study)
        self._updateRepo(self._repo.insertStudy, study)

    def removeStudy(self):
        """
        Removes an study from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        study = dataset.getStudyByName(self._args.studyName)

        def func():
            self._updateRepo(self._repo.removeStudy, study)
        self._confirmDelete("Study", study.getLocalId(), func)

    def addLabtest(self):
        """
        Adds a new labtest into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        labtest = clinical_metadata.Labtest(
            dataset, self._args.labtestName)
        labtest.populateFromJson(self._args.labtest)
        self._updateRepo(self._repo.insertLabtest, labtest)

    def removeLabtest(self):
        """
        Removes an labtest from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        labtest = dataset.getLabtestByName(self._args.labtestName)

        def func():
            self._updateRepo(self._repo.removeLabtest, labtest)
        self._confirmDelete("Labtest", labtest.getLocalId(), func)

    def addExtraction(self):
        """
        Adds a new extraction into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        extraction = pipeline_metadata.Extraction(
            dataset, self._args.extractionName)
        extraction.populateFromJson(self._args.extraction)
        self._updateRepo(self._repo.insertExtraction, extraction)

    def removeExtraction(self):
        """
        Removes an extraction from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        extraction = dataset.getExtractionByName(self._args.extractionName)

        def func():
            self._updateRepo(self._repo.removeExtraction, extraction)

        self._confirmDelete("Extraction", extraction.getLocalId(), func)

    def addSequencing(self):
        """
        Adds a new sequencing into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        sequencing = pipeline_metadata.Sequencing(
            dataset, self._args.sequencingName)
        sequencing.populateFromJson(self._args.sequencing)
        self._updateRepo(self._repo.insertSequencing, sequencing)

    def removeSequencing(self):
        """
        Removes an sequencing from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        sequencing = dataset.getSequencingByName(self._args.sequencingName)

        def func():
            self._updateRepo(self._repo.removeSequencing, sequencing)

        self._confirmDelete("Sequencing", sequencing.getLocalId(), func)

    def addAlignment(self):
        """
        Adds a new alignment into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        alignment = pipeline_metadata.Alignment(
            dataset, self._args.alignmentName)
        alignment.populateFromJson(self._args.alignment)
        self._updateRepo(self._repo.insertAlignment, alignment)

    def removeAlignment(self):
        """
        Removes an alignment from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        alignment = dataset.getAlignmentByName(self._args.alignmentName)

        def func():
            self._updateRepo(self._repo.removeAlignment, alignment)

        self._confirmDelete("Alignment", alignment.getLocalId(), func)

    def addVariantCalling(self):
        """
        Adds a new variantCalling into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        variantCalling = pipeline_metadata.VariantCalling(
            dataset, self._args.variantCallingName)
        variantCalling.populateFromJson(self._args.variantCalling)
        self._updateRepo(self._repo.insertVariantCalling, variantCalling)

    def removeVariantCalling(self):
        """
        Removes an variantCalling from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        variantCalling = dataset.getVariantCallingByName(self._args.variantCallingName)

        def func():
            self._updateRepo(self._repo.removeVariantCalling, variantCalling)

        self._confirmDelete("VariantCalling", variantCalling.getLocalId(), func)

    def addFusionDetection(self):
        """
        Adds a new expressionAnalysis into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        fusionDetection = pipeline_metadata.FusionDetection(
            dataset, self._args.fusionDetectionName)
        fusionDetection.populateFromJson(self._args.fusionDetection)
        self._updateRepo(self._repo.insertFusionDetection, fusionDetection)

    def removeFusionDetection(self):
        """
        Removes an fusionDetection from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        fusionDetection = dataset.getFusionDetectionByName(self._args.fusionDetectionName)

        def func():
            self._updateRepo(self._repo.removeFusionDetection, fusionDetection)

        self._confirmDelete("FusionDetection", fusionDetection.getLocalId(), func)

    def addExpressionAnalysis(self):
        """
        Adds a new expressionAnalysis into this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        expressionAnalysis = pipeline_metadata.ExpressionAnalysis(
            dataset, self._args.expressionAnalysisName)
        expressionAnalysis.populateFromJson(self._args.expressionAnalysis)
        self._updateRepo(self._repo.insertExpressionAnalysis, expressionAnalysis)

    def removeExpressionAnalysis(self):
        """
        Removes an expressionAnalysis from this repo
        """
        self._openRepo()
        dataset = self._repo.getDatasetByName(self._args.datasetName)
        expressionAnalysis = dataset.getExpressionAnalysisByName(self._args.expressionAnalysisName)

        def func():
            self._updateRepo(self._repo.removeExpressionAnalysis, expressionAnalysis)

        self._confirmDelete("ExpressionAnalysis", expressionAnalysis.getLocalId(), func)

    def removeOntology(self):
        """
        Removes an ontology from the repo.
        """
        self._openRepo()
        ontology = self._repo.getOntologyByName(self._args.ontologyName)

        def func():
            self._updateRepo(self._repo.removeOntology, ontology)
        self._confirmDelete("Ontology", ontology.getName(), func)

    #
    # Methods to simplify adding common arguments to the parser.
    #

    @classmethod
    def addRepoArgument(cls, subparser):
        subparser.add_argument(
            "registryPath",
            help="the location of the registry database")

    @classmethod
    def addForceOption(cls, subparser):
        subparser.add_argument(
            "-f", "--force", action='store_true',
            default=False, help="do not prompt for confirmation")

    @classmethod
    def addRelativePathOption(cls, subparser):
        subparser.add_argument(
            "-r", "--relativePath", action='store_true',
            default=False, help="store relative path in database")

    @classmethod
    def addDescriptionOption(cls, subparser, objectType):
        subparser.add_argument(
            "-d", "--description", default="",
            help="The human-readable description of the {}.".format(
                objectType))

    @classmethod
    def addDuoArgument(cls, subparser):
        subparser.add_argument(
            "dataUseOntologyFile", help="Path to your duo config json file.")

    @classmethod
    def addDatasetNameArgument(cls, subparser):
        subparser.add_argument(
            "datasetName", help="the name of the dataset")

    @classmethod
    def addAttributesArgument(cls, subparser):
        subparser.add_argument(
            "-A", "--attributes", default="{}",
            help="additional attributes for the message expressed as JSON")

    @classmethod
    def addReferenceSetNameOption(cls, subparser, objectType):
        helpText = (
            "the name of the reference set to associate with this {}"
        ).format(objectType)
        subparser.add_argument(
            "-R", "--referenceSetName", default=None, help=helpText)

    @classmethod
    def addSequenceOntologyNameOption(cls, subparser, objectType):
        helpText = (
            "the name of the sequence ontology instance used to "
            "translate ontology term names to IDs in this {}"
        ).format(objectType)
        subparser.add_argument(
            "-O", "--ontologyName", default=None, help=helpText)

    @classmethod
    def addOntologyNameArgument(cls, subparser):
        subparser.add_argument(
            "ontologyName",
            help="the name of the ontology")

    @classmethod
    def addUrlArgument(cls, subparser):
        subparser.add_argument(
            "url",
            help="The URL of the given resource")

    @classmethod
    def addReadGroupSetNameArgument(cls, subparser):
        subparser.add_argument(
            "readGroupSetName",
            help="the name of the read group set")

    @classmethod
    def addVariantSetNameArgument(cls, subparser):
        subparser.add_argument(
            "variantSetName",
            help="the name of the variant set")

    @classmethod
    def addFeatureSetNameArgument(cls, subparser):
        subparser.add_argument(
            "featureSetName",
            help="the name of the feature set")

    @classmethod
    def addContinuousSetNameArgument(cls, subparser):
        subparser.add_argument(
            "continuousSetName",
            help="the name of the continuous set")

    @classmethod
    def addIndividualNameArgument(cls, subparser):
        subparser.add_argument(
            "individualName",
            help="the name of the individual")

    @classmethod
    def addPatientNameArgument(cls, subparser):
        subparser.add_argument(
            "patientName",
            help="the name of the patient")

    @classmethod
    def addPatientIdArgument(cls, subparser):
        subparser.add_argument(
            "patientId",
            help="the ID of the patient")

    @classmethod
    def addPatientArgument(cls, subparser):
        subparser.add_argument(
            "patient",
            help="the JSON of the patient")

    @classmethod
    def addEnrollmentNameArgument(cls, subparser):
        subparser.add_argument(
            "enrollmentName",
            help="the name of the enrollment")

    @classmethod
    def addEnrollmentArgument(cls, subparser):
        subparser.add_argument(
            "enrollment",
            help="the JSON of the enrollment")

    @classmethod
    def addConsentNameArgument(cls, subparser):
        subparser.add_argument(
            "consentName",
            help="the name of the consent")

    @classmethod
    def addConsentArgument(cls, subparser):
        subparser.add_argument(
            "consent",
            help="the JSON of the consent")

    @classmethod
    def addDiagnosisNameArgument(cls, subparser):
        subparser.add_argument(
            "diagnosisName",
            help="the name of the diagnosis")

    @classmethod
    def addDiagnosisArgument(cls, subparser):
        subparser.add_argument(
            "diagnosis",
            help="the JSON of the diagnosis")

    @classmethod
    def addSampleNameArgument(cls, subparser):
        subparser.add_argument(
            "sampleName",
            help="the name of the sample")

    @classmethod
    def addSampleIdArgument(cls, subparser):
        subparser.add_argument(
            "sampleId",
            help="the ID of the sample")

    @classmethod
    def addSampleArgument(cls, subparser):
        subparser.add_argument(
            "sample",
            help="the JSON of the sample")

    @classmethod
    def addTreatmentNameArgument(cls, subparser):
        subparser.add_argument(
            "treatmentName",
            help="the name of the treatment")

    @classmethod
    def addTreatmentArgument(cls, subparser):
        subparser.add_argument(
            "treatment",
            help="the JSON of the treatment")

    @classmethod
    def addOutcomeNameArgument(cls, subparser):
        subparser.add_argument(
            "outcomeName",
            help="the name of the outcome")

    @classmethod
    def addOutcomeArgument(cls, subparser):
        subparser.add_argument(
            "outcome",
            help="the JSON of the outcome")

    @classmethod
    def addComplicationNameArgument(cls, subparser):
        subparser.add_argument(
            "complicationName",
            help="the name of the complication")

    @classmethod
    def addComplicationArgument(cls, subparser):
        subparser.add_argument(
            "complication",
            help="the JSON of the complication")

    @classmethod
    def addTumourboardNameArgument(cls, subparser):
        subparser.add_argument(
            "tumourboardName",
            help="the name of the tumourboard")

    @classmethod
    def addTumourboardArgument(cls, subparser):
        subparser.add_argument(
            "tumourboard",
            help="the JSON of the tumourboard")

    @classmethod
    def addChemotherapyNameArgument(cls, subparser):
        subparser.add_argument(
            "chemotherapyName",
            help="the name of the chemotherapy")

    @classmethod
    def addChemotherapyArgument(cls, subparser):
        subparser.add_argument(
            "chemotherapy",
            help="the JSON of the chemotherapy")

    @classmethod
    def addRadiotherapyNameArgument(cls, subparser):
        subparser.add_argument(
            "radiotherapyName",
            help="the name of the radiotherapy")

    @classmethod
    def addRadiotherapyArgument(cls, subparser):
        subparser.add_argument(
            "radiotherapy",
            help="the JSON of the radiotherapy")

    @classmethod
    def addSurgeryNameArgument(cls, subparser):
        subparser.add_argument(
            "surgeryName",
            help="the name of the surgery")

    @classmethod
    def addSurgeryArgument(cls, subparser):
        subparser.add_argument(
            "surgery",
            help="the JSON of the surgery")

    @classmethod
    def addImmunotherapyNameArgument(cls, subparser):
        subparser.add_argument(
            "immunotherapyName",
            help="the name of the immunotherapy")

    @classmethod
    def addImmunotherapyArgument(cls, subparser):
        subparser.add_argument(
            "immunotherapy",
            help="the JSON of the immunotherapy")

    @classmethod
    def addCelltransplantNameArgument(cls, subparser):
        subparser.add_argument(
            "celltransplantName",
            help="the name of the celltransplant")

    @classmethod
    def addCelltransplantArgument(cls, subparser):
        subparser.add_argument(
            "celltransplant",
            help="the JSON of the celltransplant")

    @classmethod
    def addSlideNameArgument(cls, subparser):
        subparser.add_argument(
            "slideName",
            help="the name of the slide")

    @classmethod
    def addSlideArgument(cls, subparser):
        subparser.add_argument(
            "slide",
            help="the JSON of the slide")

    @classmethod
    def addStudyNameArgument(cls, subparser):
        subparser.add_argument(
            "studyName",
            help="the name of the study")

    @classmethod
    def addStudyArgument(cls, subparser):
        subparser.add_argument(
            "study",
            help="the JSON of the study")

    @classmethod
    def addLabtestNameArgument(cls, subparser):
        subparser.add_argument(
            "labtestName",
            help="the name of the labtest")

    @classmethod
    def addLabtestArgument(cls, subparser):
        subparser.add_argument(
            "labtest",
            help="the JSON of the labtest")

    @classmethod
    def addExtractionNameArgument(cls, subparser):
        subparser.add_argument(
            "extractionName",
            help="the name of the extraction")

    @classmethod
    def addExtractionArgument(cls, subparser):
        subparser.add_argument(
            "extraction",
            help="the JSON of the extraction")

    @classmethod
    def addSequencingNameArgument(cls, subparser):
        subparser.add_argument(
            "sequencingName",
            help="the name of the sequencing")

    @classmethod
    def addSequencingArgument(cls, subparser):
        subparser.add_argument(
            "sequencing",
            help="the JSON of the sequencing")

    @classmethod
    def addAlignmentNameArgument(cls, subparser):
        subparser.add_argument(
            "alignmentName",
            help="the name of the alignment")

    @classmethod
    def addAlignmentArgument(cls, subparser):
        subparser.add_argument(
            "alignment",
            help="the JSON of the alignment")

    @classmethod
    def addVariantCallingNameArgument(cls, subparser):
        subparser.add_argument(
            "variantCallingName",
            help="the name of the variantCalling")

    @classmethod
    def addVariantCallingArgument(cls, subparser):
        subparser.add_argument(
            "variantCalling",
            help="the JSON of the variantCalling")

    @classmethod
    def addFusionDetectionNameArgument(cls, subparser):
        subparser.add_argument(
            "fusionDetectionName",
            help="the name of the fusionDetection")

    @classmethod
    def addFusionDetectionArgument(cls, subparser):
        subparser.add_argument(
            "fusionDetection",
            help="the JSON of the fusionDetection")

    @classmethod
    def addExpressionAnalysisNameArgument(cls, subparser):
        subparser.add_argument(
            "expressionAnalysisName",
            help="the name of the expressionAnalysis")

    @classmethod
    def addExpressionAnalysisArgument(cls, subparser):
        subparser.add_argument(
            "expressionAnalysis",
            help="the JSON of the expressionAnalysis")

    @classmethod
    def addBiosampleNameArgument(cls, subparser):
        subparser.add_argument(
            "biosampleName",
            help="the name of the biosample")

    @classmethod
    def addBiosampleArgument(cls, subparser):
        subparser.add_argument(
            "biosample",
            help="the JSON of the biosample")

    @classmethod
    def addExperimentNameArgument(cls, subparser):
        subparser.add_argument(
            "experimentName",
            help="the name of the experiment")

    @classmethod
    def addExperimentArgument(cls, subparser):
        subparser.add_argument(
            "experiment",
            help="the JSON of the experiment")

    @classmethod
    def addAnalysisNameArgument(cls, subparser):
        subparser.add_argument(
            "analysisName",
            help="the name of the analysis")

    @classmethod
    def addAnalysisArgument(cls, subparser):
        subparser.add_argument(
            "analysis",
            help="the JSON of the analysis")

    @classmethod
    def addIndividualArgument(cls, subparser):
        subparser.add_argument(
            "individual",
            help="the JSON of the individual")

    @classmethod
    def addFilePathArgument(cls, subparser, helpText):
        subparser.add_argument("filePath", help=helpText)

    @classmethod
    def addDirPathArgument(cls, subparser, helpText):
        subparser.add_argument("dirPath", help=helpText)

    @classmethod
    def addNameOption(cls, parser, objectType):
        parser.add_argument(
            "-n", "--name", default=None,
            help="The name of the {}".format(objectType))

    @classmethod
    def addNameArgument(cls, parser, objectType):
        parser.add_argument(
            "name", help="The name of the {}".format(objectType))

    @classmethod
    def addRnaQuantificationNameArgument(cls, subparser):
        subparser.add_argument(
            "rnaQuantificationName",
            help="the name of the RNA Quantification")

    @classmethod
    def addClassNameOption(cls, subparser, objectType):
        helpText = (
            "the name of the class used to "
            "fetch features in this {}"
        ).format(objectType)
        subparser.add_argument(
            "-C", "--className",
            default="candig.datamodel.sequence_annotations.Gff3DbFeatureSet",
            help=helpText)

    @classmethod
    def addRnaQuantificationSetNameArgument(cls, subparser):
        subparser.add_argument(
            "rnaQuantificationSetName",
            help="the name of the RNA Quantification Set")

    @classmethod
    def addQuantificationFilePathArgument(cls, subparser, helpText):
        subparser.add_argument("quantificationFilePath", help=helpText)

    @classmethod
    def addRnaFormatArgument(cls, subparser):
        subparser.add_argument(
            "format", help="format of the quantification input data")

    @classmethod
    def addRnaFeatureTypeOption(cls, subparser):
        subparser.add_argument(
            "-t", "--transcript", action="store_true", default=False,
            help="sets the quantification type to transcript")

    @classmethod
    def getParser(cls):
        parser = common_cli.createArgumentParser(
            "CanDIG data repository management tool")
        subparsers = parser.add_subparsers(title='subcommands',)
        cli.addVersionArgument(parser)

        initParser = common_cli.addSubparser(
            subparsers, "init", "Initialize a data repository")
        initParser.set_defaults(runner="init")
        cls.addRepoArgument(initParser)
        cls.addForceOption(initParser)

        verifyParser = common_cli.addSubparser(
            subparsers, "verify",
            "Verifies the repository by examing all data files")
        verifyParser.set_defaults(runner="verify")
        cls.addRepoArgument(verifyParser)

        listParser = common_cli.addSubparser(
            subparsers, "list", "List the contents of the repo")
        listParser.set_defaults(runner="list")
        cls.addRepoArgument(listParser)

        listAnnouncementsParser = common_cli.addSubparser(
            subparsers, "list-announcements", "List the announcements in"
                                              "the repo.")
        listAnnouncementsParser.set_defaults(runner="listAnnouncements")
        cls.addRepoArgument(listAnnouncementsParser)

        clearAnnouncementsParser = common_cli.addSubparser(
            subparsers, "clear-announcements", "List the announcements in"
                                               "the repo.")
        clearAnnouncementsParser.set_defaults(runner="clearAnnouncements")
        cls.addRepoArgument(clearAnnouncementsParser)

        addDatasetParser = common_cli.addSubparser(
            subparsers, "add-dataset", "Add a dataset to the data repo")
        addDatasetParser.set_defaults(runner="addDataset")
        cls.addRepoArgument(addDatasetParser)
        cls.addDatasetNameArgument(addDatasetParser)
        cls.addAttributesArgument(addDatasetParser)
        cls.addDescriptionOption(addDatasetParser, "dataset")

        removeDatasetParser = common_cli.addSubparser(
            subparsers, "remove-dataset",
            "Remove a dataset from the data repo")
        removeDatasetParser.set_defaults(runner="removeDataset")
        cls.addRepoArgument(removeDatasetParser)
        cls.addDatasetNameArgument(removeDatasetParser)
        cls.addForceOption(removeDatasetParser)

        addDatasetDuoParser = common_cli.addSubparser(
            subparsers, "add-dataset-duo", "Add DUO info to a dataset")
        addDatasetDuoParser.set_defaults(runner="addDatasetDuo")
        cls.addRepoArgument(addDatasetDuoParser)
        cls.addDatasetNameArgument(addDatasetDuoParser)
        cls.addDuoArgument(addDatasetDuoParser)

        removeDatasetDuoParser = common_cli.addSubparser(
            subparsers, "remove-dataset-duo", "Remove DUO info from a dataset")
        removeDatasetDuoParser.set_defaults(runner="removeDatasetDuo")
        cls.addRepoArgument(removeDatasetDuoParser)
        cls.addDatasetNameArgument(removeDatasetDuoParser)
        cls.addForceOption(removeDatasetDuoParser)

        addOntologyParser = common_cli.addSubparser(
            subparsers, "add-ontology",
            "Adds an ontology in OBO format to the repo. Currently, "
            "a sequence ontology (SO) instance is required to translate "
            "ontology term names held in annotations to ontology IDs. "
            "Sequence ontology files can be found at "
            "https://github.com/The-Sequence-Ontology/SO-Ontologies")
        addOntologyParser.set_defaults(runner="addOntology")
        cls.addRepoArgument(addOntologyParser)
        cls.addFilePathArgument(
            addOntologyParser,
            "The path of the OBO file defining this ontology.")
        cls.addRelativePathOption(addOntologyParser)
        cls.addNameOption(addOntologyParser, "ontology")

        removeOntologyParser = common_cli.addSubparser(
            subparsers, "remove-ontology",
            "Remove an ontology from the repo")
        removeOntologyParser.set_defaults(runner="removeOntology")
        cls.addRepoArgument(removeOntologyParser)
        cls.addOntologyNameArgument(removeOntologyParser)
        cls.addForceOption(removeOntologyParser)

        addPatientParser = common_cli.addSubparser(
            subparsers, "add-patient", "Add an Patient to the dataset")
        addPatientParser.set_defaults(runner="addPatient")
        cls.addRepoArgument(addPatientParser)
        cls.addDatasetNameArgument(addPatientParser)
        cls.addPatientNameArgument(addPatientParser)
        cls.addPatientArgument(addPatientParser)

        removePatientParser = common_cli.addSubparser(
            subparsers, "remove-patient",
            "Remove an Patient from the repo")
        removePatientParser.set_defaults(runner="removePatient")
        cls.addRepoArgument(removePatientParser)
        cls.addDatasetNameArgument(removePatientParser)
        cls.addPatientNameArgument(removePatientParser)
        cls.addForceOption(removePatientParser)

        addEnrollmentParser = common_cli.addSubparser(
            subparsers, "add-enrollment", "Add an Enrollment to the dataset")
        addEnrollmentParser.set_defaults(runner="addEnrollment")
        cls.addRepoArgument(addEnrollmentParser)
        cls.addDatasetNameArgument(addEnrollmentParser)
        cls.addEnrollmentNameArgument(addEnrollmentParser)
        cls.addEnrollmentArgument(addEnrollmentParser)

        removeEnrollmentParser = common_cli.addSubparser(
            subparsers, "remove-enrollment",
            "Remove an Enrollment from the repo")
        removeEnrollmentParser.set_defaults(runner="removeEnrollment")
        cls.addRepoArgument(removeEnrollmentParser)
        cls.addDatasetNameArgument(removeEnrollmentParser)
        cls.addEnrollmentNameArgument(removeEnrollmentParser)
        cls.addForceOption(removeEnrollmentParser)

        addConsentParser = common_cli.addSubparser(
            subparsers, "add-consent", "Add an Consent to the dataset")
        addConsentParser.set_defaults(runner="addConsent")
        cls.addRepoArgument(addConsentParser)
        cls.addDatasetNameArgument(addConsentParser)
        cls.addConsentNameArgument(addConsentParser)
        cls.addConsentArgument(addConsentParser)

        removeConsentParser = common_cli.addSubparser(
            subparsers, "remove-consent",
            "Remove an Consent from the repo")
        removeConsentParser.set_defaults(runner="removeConsent")
        cls.addRepoArgument(removeConsentParser)
        cls.addDatasetNameArgument(removeConsentParser)
        cls.addConsentNameArgument(removeConsentParser)
        cls.addForceOption(removeConsentParser)

        addDiagnosisParser = common_cli.addSubparser(
            subparsers, "add-diagnosis", "Add an Diagnosis to the dataset")
        addDiagnosisParser.set_defaults(runner="addDiagnosis")
        cls.addRepoArgument(addDiagnosisParser)
        cls.addDatasetNameArgument(addDiagnosisParser)
        cls.addDiagnosisNameArgument(addDiagnosisParser)
        cls.addDiagnosisArgument(addDiagnosisParser)

        removeDiagnosisParser = common_cli.addSubparser(
            subparsers, "remove-diagnosis",
            "Remove an Diagnosis from the repo")
        removeDiagnosisParser.set_defaults(runner="removeDiagnosis")
        cls.addRepoArgument(removeDiagnosisParser)
        cls.addDatasetNameArgument(removeDiagnosisParser)
        cls.addDiagnosisNameArgument(removeDiagnosisParser)
        cls.addForceOption(removeDiagnosisParser)

        addSampleParser = common_cli.addSubparser(
            subparsers, "add-sample", "Add an Sample to the dataset")
        addSampleParser.set_defaults(runner="addSample")
        cls.addRepoArgument(addSampleParser)
        cls.addDatasetNameArgument(addSampleParser)
        cls.addSampleNameArgument(addSampleParser)
        cls.addSampleArgument(addSampleParser)

        removeSampleParser = common_cli.addSubparser(
            subparsers, "remove-sample",
            "Remove an Sample from the repo")
        removeSampleParser.set_defaults(runner="removeSample")
        cls.addRepoArgument(removeSampleParser)
        cls.addDatasetNameArgument(removeSampleParser)
        cls.addSampleNameArgument(removeSampleParser)
        cls.addForceOption(removeSampleParser)

        addTreatmentParser = common_cli.addSubparser(
            subparsers, "add-treatment", "Add an Treatment to the dataset")
        addTreatmentParser.set_defaults(runner="addTreatment")
        cls.addRepoArgument(addTreatmentParser)
        cls.addDatasetNameArgument(addTreatmentParser)
        cls.addTreatmentNameArgument(addTreatmentParser)
        cls.addTreatmentArgument(addTreatmentParser)

        removeTreatmentParser = common_cli.addSubparser(
            subparsers, "remove-treatment",
            "Remove an Treatment from the repo")
        removeTreatmentParser.set_defaults(runner="removeTreatment")
        cls.addRepoArgument(removeTreatmentParser)
        cls.addDatasetNameArgument(removeTreatmentParser)
        cls.addTreatmentNameArgument(removeTreatmentParser)
        cls.addForceOption(removeTreatmentParser)

        addOutcomeParser = common_cli.addSubparser(
            subparsers, "add-outcome", "Add an Outcome to the dataset")
        addOutcomeParser.set_defaults(runner="addOutcome")
        cls.addRepoArgument(addOutcomeParser)
        cls.addDatasetNameArgument(addOutcomeParser)
        cls.addOutcomeNameArgument(addOutcomeParser)
        cls.addOutcomeArgument(addOutcomeParser)

        removeOutcomeParser = common_cli.addSubparser(
            subparsers, "remove-outcome",
            "Remove an Outcome from the repo")
        removeOutcomeParser.set_defaults(runner="removeOutcome")
        cls.addRepoArgument(removeOutcomeParser)
        cls.addDatasetNameArgument(removeOutcomeParser)
        cls.addOutcomeNameArgument(removeOutcomeParser)
        cls.addForceOption(removeOutcomeParser)

        addComplicationParser = common_cli.addSubparser(
            subparsers, "add-complication", "Add an Complication to the dataset")
        addComplicationParser.set_defaults(runner="addComplication")
        cls.addRepoArgument(addComplicationParser)
        cls.addDatasetNameArgument(addComplicationParser)
        cls.addComplicationNameArgument(addComplicationParser)
        cls.addComplicationArgument(addComplicationParser)

        removeComplicationParser = common_cli.addSubparser(
            subparsers, "remove-complication",
            "Remove an Complication from the repo")
        removeComplicationParser.set_defaults(runner="removeComplication")
        cls.addRepoArgument(removeComplicationParser)
        cls.addDatasetNameArgument(removeComplicationParser)
        cls.addComplicationNameArgument(removeComplicationParser)
        cls.addForceOption(removeComplicationParser)

        addTumourboardParser = common_cli.addSubparser(
            subparsers, "add-tumourboard", "Add an Tumourboard to the dataset")
        addTumourboardParser.set_defaults(runner="addTumourboard")
        cls.addRepoArgument(addTumourboardParser)
        cls.addDatasetNameArgument(addTumourboardParser)
        cls.addTumourboardNameArgument(addTumourboardParser)
        cls.addTumourboardArgument(addTumourboardParser)

        removeTumourboardParser = common_cli.addSubparser(
            subparsers, "remove-tumourboard",
            "Remove an Tumourboard from the repo")
        removeTumourboardParser.set_defaults(runner="removeTumourboard")
        cls.addRepoArgument(removeTumourboardParser)
        cls.addDatasetNameArgument(removeTumourboardParser)
        cls.addTumourboardNameArgument(removeTumourboardParser)
        cls.addForceOption(removeTumourboardParser)

        addChemotherapyParser = common_cli.addSubparser(
            subparsers, "add-chemotherapy", "Add an Chemotherapy to the dataset")
        addChemotherapyParser.set_defaults(runner="addChemotherapy")
        cls.addRepoArgument(addChemotherapyParser)
        cls.addDatasetNameArgument(addChemotherapyParser)
        cls.addChemotherapyNameArgument(addChemotherapyParser)
        cls.addChemotherapyArgument(addChemotherapyParser)

        removeChemotherapyParser = common_cli.addSubparser(
            subparsers, "remove-chemotherapy",
            "Remove an Chemotherapy from the repo")
        removeChemotherapyParser.set_defaults(runner="removeChemotherapy")
        cls.addRepoArgument(removeChemotherapyParser)
        cls.addDatasetNameArgument(removeChemotherapyParser)
        cls.addChemotherapyNameArgument(removeChemotherapyParser)
        cls.addForceOption(removeChemotherapyParser)

        addRadiotherapyParser = common_cli.addSubparser(
            subparsers, "add-radiotherapy", "Add an Radiotherapy to the dataset")
        addRadiotherapyParser.set_defaults(runner="addRadiotherapy")
        cls.addRepoArgument(addRadiotherapyParser)
        cls.addDatasetNameArgument(addRadiotherapyParser)
        cls.addRadiotherapyNameArgument(addRadiotherapyParser)
        cls.addRadiotherapyArgument(addRadiotherapyParser)

        removeRadiotherapyParser = common_cli.addSubparser(
            subparsers, "remove-radiotherapy",
            "Remove an Radiotherapy from the repo")
        removeRadiotherapyParser.set_defaults(runner="removeRadiotherapy")
        cls.addRepoArgument(removeRadiotherapyParser)
        cls.addDatasetNameArgument(removeRadiotherapyParser)
        cls.addRadiotherapyNameArgument(removeRadiotherapyParser)
        cls.addForceOption(removeRadiotherapyParser)

        addSurgeryParser = common_cli.addSubparser(
            subparsers, "add-surgery", "Add an Surgery to the dataset")
        addSurgeryParser.set_defaults(runner="addSurgery")
        cls.addRepoArgument(addSurgeryParser)
        cls.addDatasetNameArgument(addSurgeryParser)
        cls.addSurgeryNameArgument(addSurgeryParser)
        cls.addSurgeryArgument(addSurgeryParser)

        removeSurgeryParser = common_cli.addSubparser(
            subparsers, "remove-surgery",
            "Remove an Surgery from the repo")
        removeSurgeryParser.set_defaults(runner="removeSurgery")
        cls.addRepoArgument(removeSurgeryParser)
        cls.addDatasetNameArgument(removeSurgeryParser)
        cls.addSurgeryNameArgument(removeSurgeryParser)
        cls.addForceOption(removeSurgeryParser)

        addImmunotherapyParser = common_cli.addSubparser(
            subparsers, "add-immunotherapy", "Add an Immunotherapy to the dataset")
        addImmunotherapyParser.set_defaults(runner="addImmunotherapy")
        cls.addRepoArgument(addImmunotherapyParser)
        cls.addDatasetNameArgument(addImmunotherapyParser)
        cls.addImmunotherapyNameArgument(addImmunotherapyParser)
        cls.addImmunotherapyArgument(addImmunotherapyParser)

        removeImmunotherapyParser = common_cli.addSubparser(
            subparsers, "remove-immunotherapy",
            "Remove an Immunotherapy from the repo")
        removeImmunotherapyParser.set_defaults(runner="removeImmunotherapy")
        cls.addRepoArgument(removeImmunotherapyParser)
        cls.addDatasetNameArgument(removeImmunotherapyParser)
        cls.addImmunotherapyNameArgument(removeImmunotherapyParser)
        cls.addForceOption(removeImmunotherapyParser)

        addCelltransplantParser = common_cli.addSubparser(
            subparsers, "add-celltransplant", "Add an Celltransplant to the dataset")
        addCelltransplantParser.set_defaults(runner="addCelltransplant")
        cls.addRepoArgument(addCelltransplantParser)
        cls.addDatasetNameArgument(addCelltransplantParser)
        cls.addCelltransplantNameArgument(addCelltransplantParser)
        cls.addCelltransplantArgument(addCelltransplantParser)

        removeCelltransplantParser = common_cli.addSubparser(
            subparsers, "remove-celltransplant",
            "Remove an Celltransplant from the repo")
        removeCelltransplantParser.set_defaults(runner="removeCelltransplant")
        cls.addRepoArgument(removeCelltransplantParser)
        cls.addDatasetNameArgument(removeCelltransplantParser)
        cls.addCelltransplantNameArgument(removeCelltransplantParser)
        cls.addForceOption(removeCelltransplantParser)

        addSlideParser = common_cli.addSubparser(
            subparsers, "add-slide", "Add an Slide to the dataset")
        addSlideParser.set_defaults(runner="addSlide")
        cls.addRepoArgument(addSlideParser)
        cls.addDatasetNameArgument(addSlideParser)
        cls.addSlideNameArgument(addSlideParser)
        cls.addSlideArgument(addSlideParser)

        removeSlideParser = common_cli.addSubparser(
            subparsers, "remove-slide",
            "Remove an Slide from the repo")
        removeSlideParser.set_defaults(runner="removeSlide")
        cls.addRepoArgument(removeSlideParser)
        cls.addDatasetNameArgument(removeSlideParser)
        cls.addSlideNameArgument(removeSlideParser)
        cls.addForceOption(removeSlideParser)

        addStudyParser = common_cli.addSubparser(
            subparsers, "add-study", "Add an Study to the dataset")
        addStudyParser.set_defaults(runner="addStudy")
        cls.addRepoArgument(addStudyParser)
        cls.addDatasetNameArgument(addStudyParser)
        cls.addStudyNameArgument(addStudyParser)
        cls.addStudyArgument(addStudyParser)

        removeStudyParser = common_cli.addSubparser(
            subparsers, "remove-study",
            "Remove an Study from the repo")
        removeStudyParser.set_defaults(runner="removeStudy")
        cls.addRepoArgument(removeStudyParser)
        cls.addDatasetNameArgument(removeStudyParser)
        cls.addStudyNameArgument(removeStudyParser)
        cls.addForceOption(removeStudyParser)

        addLabtestParser = common_cli.addSubparser(
            subparsers, "add-labtest", "Add an Labtest to the dataset")
        addLabtestParser.set_defaults(runner="addLabtest")
        cls.addRepoArgument(addLabtestParser)
        cls.addDatasetNameArgument(addLabtestParser)
        cls.addLabtestNameArgument(addLabtestParser)
        cls.addLabtestArgument(addLabtestParser)

        removeLabtestParser = common_cli.addSubparser(
            subparsers, "remove-labtest",
            "Remove an Labtest from the repo")
        removeLabtestParser.set_defaults(runner="removeLabtest")
        cls.addRepoArgument(removeLabtestParser)
        cls.addDatasetNameArgument(removeLabtestParser)
        cls.addLabtestNameArgument(removeLabtestParser)
        cls.addForceOption(removeLabtestParser)

        addExtractionParser = common_cli.addSubparser(
            subparsers, "add-extraction", "Add a Extraction to the dataset")
        addExtractionParser.set_defaults(runner="addExtraction")
        cls.addRepoArgument(addExtractionParser)
        cls.addDatasetNameArgument(addExtractionParser)
        cls.addExtractionNameArgument(addExtractionParser)
        cls.addExtractionArgument(addExtractionParser)

        removeExtractionParser = common_cli.addSubparser(
            subparsers, "remove-extraction",
            "Remove an Extraction from the repo")
        removeExtractionParser.set_defaults(runner="removeExtraction")
        cls.addRepoArgument(removeExtractionParser)
        cls.addDatasetNameArgument(removeExtractionParser)
        cls.addExtractionNameArgument(removeExtractionParser)
        cls.addForceOption(removeExtractionParser)

        addSequencingParser = common_cli.addSubparser(
            subparsers, "add-sequencing", "Add a Sequencing to the dataset")
        addSequencingParser.set_defaults(runner="addSequencing")
        cls.addRepoArgument(addSequencingParser)
        cls.addDatasetNameArgument(addSequencingParser)
        cls.addSequencingNameArgument(addSequencingParser)
        cls.addSequencingArgument(addSequencingParser)

        removeSequencingParser = common_cli.addSubparser(
            subparsers, "remove-sequencing",
            "Remove an Sequencing from the repo")
        removeSequencingParser.set_defaults(runner="removeSequencing")
        cls.addRepoArgument(removeSequencingParser)
        cls.addDatasetNameArgument(removeSequencingParser)
        cls.addSequencingNameArgument(removeSequencingParser)
        cls.addForceOption(removeSequencingParser)

        addAlignmentParser = common_cli.addSubparser(
            subparsers, "add-alignment", "Add a Alignment to the dataset")
        addAlignmentParser.set_defaults(runner="addAlignment")
        cls.addRepoArgument(addAlignmentParser)
        cls.addDatasetNameArgument(addAlignmentParser)
        cls.addAlignmentNameArgument(addAlignmentParser)
        cls.addAlignmentArgument(addAlignmentParser)

        removeAlignmentParser = common_cli.addSubparser(
            subparsers, "remove-alignment",
            "Remove an Alignment from the repo")
        removeAlignmentParser.set_defaults(runner="removeAlignment")
        cls.addRepoArgument(removeAlignmentParser)
        cls.addDatasetNameArgument(removeAlignmentParser)
        cls.addAlignmentNameArgument(removeAlignmentParser)
        cls.addForceOption(removeAlignmentParser)

        addVariantCallingParser = common_cli.addSubparser(
            subparsers, "add-variantcalling", "Add a VariantCalling to the dataset")
        addVariantCallingParser.set_defaults(runner="addVariantCalling")
        cls.addRepoArgument(addVariantCallingParser)
        cls.addDatasetNameArgument(addVariantCallingParser)
        cls.addVariantCallingNameArgument(addVariantCallingParser)
        cls.addVariantCallingArgument(addVariantCallingParser)

        removeVariantCallingParser = common_cli.addSubparser(
            subparsers, "remove-variantcalling",
            "Remove an VariantCalling from the repo")
        removeVariantCallingParser.set_defaults(runner="removeVariantCalling")
        cls.addRepoArgument(removeVariantCallingParser)
        cls.addDatasetNameArgument(removeVariantCallingParser)
        cls.addVariantCallingNameArgument(removeVariantCallingParser)
        cls.addForceOption(removeVariantCallingParser)

        addFusionDetectionParser = common_cli.addSubparser(
            subparsers, "add-fusiondetection", "Add a FusionDetection to the dataset")
        addFusionDetectionParser.set_defaults(runner="addFusionDetection")
        cls.addRepoArgument(addFusionDetectionParser)
        cls.addDatasetNameArgument(addFusionDetectionParser)
        cls.addFusionDetectionNameArgument(addFusionDetectionParser)
        cls.addFusionDetectionArgument(addFusionDetectionParser)

        removeFusionDetectionParser = common_cli.addSubparser(
            subparsers, "remove-fusiondetection",
            "Remove an FusionDetection from the repo")
        removeFusionDetectionParser.set_defaults(runner="removeFusionDetection")
        cls.addRepoArgument(removeFusionDetectionParser)
        cls.addDatasetNameArgument(removeFusionDetectionParser)
        cls.addFusionDetectionNameArgument(removeFusionDetectionParser)
        cls.addForceOption(removeFusionDetectionParser)

        addExpressionAnalysisParser = common_cli.addSubparser(
            subparsers, "add-expressionanalysis", "Add a ExpressionAnalysis to the dataset")
        addExpressionAnalysisParser.set_defaults(runner="addExpressionAnalysis")
        cls.addRepoArgument(addExpressionAnalysisParser)
        cls.addDatasetNameArgument(addExpressionAnalysisParser)
        cls.addExpressionAnalysisNameArgument(addExpressionAnalysisParser)
        cls.addExpressionAnalysisArgument(addExpressionAnalysisParser)

        removeExpressionAnalysisParser = common_cli.addSubparser(
            subparsers, "remove-expressionanalysis",
            "Remove an ExpressionAnalysis from the repo")
        removeExpressionAnalysisParser.set_defaults(runner="removeExpressionAnalysis")
        cls.addRepoArgument(removeExpressionAnalysisParser)
        cls.addDatasetNameArgument(removeExpressionAnalysisParser)
        cls.addExpressionAnalysisNameArgument(removeExpressionAnalysisParser)
        cls.addForceOption(removeExpressionAnalysisParser)

        return parser

    @classmethod
    def runCommand(cls, args):
        parser = cls.getParser()
        parsedArgs = parser.parse_args(args)
        if "runner" not in parsedArgs:
            parser.print_help()
        manager = RepoManager(parsedArgs)
        runMethod = getattr(manager, parsedArgs.runner)
        runMethod()


def getRepoManagerParser():
    """
    Used by sphinx.argparse.
    """
    return RepoManager.getParser()


def repoExitError(message):
    """
    Exits the repo manager with error status.
    TODO: Look into how the message is formatted
    """
    wrapper = textwrap.TextWrapper(
        break_on_hyphens=False, break_long_words=False)
    formatted = wrapper.fill("{}: error: {}".format(sys.argv[0], message))
    sys.exit(formatted)


def repo_main(args=None):
    try:
        RepoManager.runCommand(args)
    except exceptions.RepoManagerException as exception:
        # These are exceptions that happen throughout the CLI, and are
        # used to communicate back to the user
        repoExitError(str(exception))
    except exceptions.NotFoundException as exception:
        # We expect NotFoundExceptions to occur when we're looking for
        # datasets, readGroupsets, etc.
        repoExitError(str(exception))
    except exceptions.DataException as exception:
        # We expect DataExceptions to occur when a file open fails,
        # a URL cannot be reached, etc.
        repoExitError(str(exception))
    except exceptions.NoInternetConnectionException as exception:
        # When there's no internet at the time of ingesting ontology file
        repoExitError(str(exception))
    except exceptions.FailToParseOntologyException as exception:
        # When the Ontology file is corrupted
        repoExitError(str(exception))
    except Exception as exception:
        # Uncaught exception: this is a bug
        message = """
An internal error has occurred.  Please file a bug report at
https://github.com/candig/metadata_service/issues
with all the relevant details, and the following stack trace.
"""
        print("{}: error:".format(sys.argv[0]), file=sys.stderr)
        print(message, file=sys.stderr)
        traceback.print_exception(*sys.exc_info())
        sys.exit(1)
