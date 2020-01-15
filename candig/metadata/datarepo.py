"""
The backing data store for the GA4GH server
"""

import json
import os
import datetime

import candig.metadata.datamodel as datamodel
import candig.metadata.datamodel.datasets as datasets
import candig.metadata.exceptions as exceptions
import candig.metadata.repo.models as models
import candig.metadata.datamodel.clinical_metadata as clinical_metadata
import candig.metadata.datamodel.pipeline_metadata as pipeline_metadata

import candig.metadata.protocol as protocol

import peewee

MODE_READ = 'r'
MODE_WRITE = 'w'


class AbstractDataRepository(object):
    """
    An abstract GA4GH data repository
    """
    def __init__(self):
        self._datasetIdMap = {}
        self._datasetNameMap = {}
        self._datasetIds = []

    def addDataset(self, dataset):
        """
        Adds the specified dataset to this data repository.
        """
        id_ = dataset.getId()
        self._datasetIdMap[id_] = dataset
        self._datasetNameMap[dataset.getLocalId()] = dataset
        self._datasetIds.append(id_)

    def getDatasets(self):
        """
        Returns a list of datasets in this data repository
        """
        return [self._datasetIdMap[id_] for id_ in self._datasetIds]

    def getNumDatasets(self):
        """
        Returns the number of datasets in this data repository.
        """
        return len(self._datasetIds)

    def getDataset(self, id_):
        """
        Returns a dataset with the specified ID, or raises a
        DatasetNotFoundException if it does not exist.
        """
        if id_ not in self._datasetIdMap:
            raise exceptions.DatasetNotFoundException(id_)
        return self._datasetIdMap[id_]

    def getDatasetByIndex(self, index):
        """
        Returns the dataset at the specified index.
        """
        return self._datasetIdMap[self._datasetIds[index]]

    def getAuthzDatasetByIndex(self, index, access_map):
        """
        Returns the dataset at the specified index if authorized to do so
        """
        dataset = self._datasetIdMap[self._datasetIds[index]]
        dataset_name = dataset.getLocalId()

        return dataset if dataset_name in access_map else None

    def getDatasetByName(self, name):
        """
        Returns the dataset with the specified name.
        """
        if name not in self._datasetNameMap:
            raise exceptions.DatasetNameNotFoundException(name)
        return self._datasetNameMap[name]

    def allPatient(self):
        """
        Return an iterator over all Patient in the data repo
        """
        for dataset in self.getDatasets():
            for patient in dataset.getPatient():
                yield patient

    def allEnrollment(self):
        """
        Return an iterator over all Enrollment in the data repo
        """
        for dataset in self.getDatasets():
            for enrollment in dataset.getEnrollment():
                yield enrollment

    def allConsent(self):
        """
        Return an iterator over all Consent in the data repo
        """
        for dataset in self.getDatasets():
            for consent in dataset.getConsent():
                yield consent

    def allDiagnosis(self):
        """
        Return an iterator over all Diagnosis in the data repo
        """
        for dataset in self.getDatasets():
            for diagnosis in dataset.getDiagnosis():
                yield diagnosis

    def allSample(self):
        """
        Return an iterator over all Sample in the data repo
        """
        for dataset in self.getDatasets():
            for sample in dataset.getSample():
                yield sample

    def allTreatment(self):
        """
        Return an iterator over all Treatment in the data repo
        """
        for dataset in self.getDatasets():
            for treatment in dataset.getTreatment():
                yield treatment

    def allOutcome(self):
        """
        Return an iterator over all Outcome in the data repo
        """
        for dataset in self.getDatasets():
            for outcome in dataset.getOutcome():
                yield outcome

    def allComplication(self):
        """
        Return an iterator over all Complication in the data repo
        """
        for dataset in self.getDatasets():
            for complication in dataset.getComplication():
                yield complication

    def allTumourboard(self):
        """
        Return an iterator over all Tumourboard in the data repo
        """
        for dataset in self.getDatasets():
            for tumourboard in dataset.getTumourboard():
                yield tumourboard

    def allChemotherapy(self):
        """
        Return an iterator over all Chemotherapy in the data repo
        """
        for dataset in self.getDatasets():
            for chemotherapy in dataset.getChemotherapy():
                yield chemotherapy

    def allRadiotherapy(self):
        """
        Return an iterator over all Radiotherapy in the data repo
        """
        for dataset in self.getDatasets():
            for radiotherapy in dataset.getRadiotherapy():
                yield radiotherapy

    def allSurgery(self):
        """
        Return an iterator over all Surgery in the data repo
        """
        for dataset in self.getDatasets():
            for surgery in dataset.getSurgery():
                yield surgery

    def allImmunotherapy(self):
        """
        Return an iterator over all Immunotherapy in the data repo
        """
        for dataset in self.getDatasets():
            for immunotherapy in dataset.getImmunotherapy():
                yield immunotherapy

    def allCelltransplant(self):
        """
        Return an iterator over all Celltransplant in the data repo
        """
        for dataset in self.getDatasets():
            for celltransplant in dataset.getCelltransplant():
                yield celltransplant

    def allSlide(self):
        """
        Return an iterator over all Slide in the data repo
        """
        for dataset in self.getDatasets():
            for slide in dataset.getSlide():
                yield slide

    def allStudy(self):
        """
        Return an iterator over all Study in the data repo
        """
        for dataset in self.getDatasets():
            for study in dataset.getStudy():
                yield study

    def allLabtest(self):
        """
        Return an iterator over all Labtest in the data repo
        """
        for dataset in self.getDatasets():
            for labtest in dataset.getLabtest():
                yield labtest


class SimulatedDataRepository(AbstractDataRepository):
    """
    A data repository that is simulated
    """
    def __init__(
            self, randomSeed=0, numDatasets=2,
            numVariantSets=1, numCalls=1, variantDensity=0.5,
            numReferenceSets=1, numReferencesPerReferenceSet=1,
            numReadGroupSets=1, numReadGroupsPerReadGroupSet=1,
            numPhenotypeAssociations=2,
            numPhenotypeAssociationSets=1,
            numAlignments=2, numRnaQuantSets=2, numExpressionLevels=2,
            numPeers=1):
        super(SimulatedDataRepository, self).__init__()

        # Datasets
        for i in range(numDatasets):
            seed = randomSeed + i
            localId = "simulatedDataset{}".format(i)
            referenceSet = self.getReferenceSetByIndex(i % numReferenceSets)
            dataset = datasets.SimulatedDataset(
                localId, randomSeed=seed,
            )
            self.addDataset(dataset)


class SqlDataRepository(AbstractDataRepository):
    """
    A data repository based on a SQL database.
    """
    class SchemaVersion(object):
        """
        The version of the data repository SQL schema
        """
        def __init__(self, versionString):
            splits = versionString.split('.')
            assert len(splits) == 2
            self.major = splits[0]
            self.minor = splits[1]

        def __str__(self):
            return "{}.{}".format(self.major, self.minor)

    version = SchemaVersion("2.1")
    systemKeySchemaVersion = "schemaVersion"
    systemKeyCreationTimeStamp = "creationTimeStamp"

    def __init__(self, fileName):
        super(SqlDataRepository, self).__init__()
        self._dbFilename = fileName
        # We open the repo in either read or write mode. When we want to
        # update the repo we open it in write mode. For normal online
        # server use, we open it in read mode.
        self._openMode = None
        # Values filled in using the DB. These will all be None until
        # we have called load()
        self._schemaVersion = None
        # Connection to the DB.
        self.database = models.SqliteDatabase(self._dbFilename, **{})
        models.databaseProxy.initialize(self.database)

    def _checkWriteMode(self):
        if self._openMode != MODE_WRITE:
            raise ValueError("Repo must be opened in write mode")

    def tableToTsv(self, model):
        """
        Takes a model class and attempts to create a table in TSV format
        that can be imported into a spreadsheet program.
        """
        first = True
        for item in model.select():
            if first:
                header = "".join(
                    ["{}\t".format(x) for x in model._meta.fields.keys()])
                print(header)
                first = False
            row = "".join(
                ["{}\t".format(
                    getattr(item, key)) for key in model._meta.fields.keys()])
            print(row)

    def printAnnouncements(self):
        """
        Prints the announcement table to the log in tsv format.
        """
        self.tableToTsv(models.Announcement)

    def clearAnnouncements(self):
        """
        Flushes the announcement table.
        """
        try:
            q = models.Announcement.delete().where(
                models.Announcement.id > 0)
            q.execute()
        except Exception as e:
            raise exceptions.RepoManagerException(e)

    def insertAnnouncement(self, announcement):
        """
        Adds an announcement to the registry for later analysis.
        """
        url = announcement.get('url', None)
        try:
            peers.Peer(url)
        except:
            raise exceptions.BadUrlException(url)
        try:
            # TODO get more details about the user agent
            models.Announcement.create(
                url=announcement.get('url'),
                attributes=json.dumps(announcement.get('attributes', {})),
                remote_addr=announcement.get('remote_addr', None),
                user_agent=announcement.get('user_agent', None))
        except Exception as e:
            raise exceptions.RepoManagerException(e)

    def open(self, mode=MODE_READ):
        """
        Opens this repo in the specified mode.

        TODO: figure out the correct semantics of this and document
        the intended future behaviour as well as the current
        transitional behaviour.
        """
        if mode not in [MODE_READ, MODE_WRITE]:
            error = "Open mode must be '{}' or '{}'".format(
                MODE_READ, MODE_WRITE)
            raise ValueError(error)
        self._openMode = mode
        if mode == MODE_READ:
            self.assertExists()
        if mode == MODE_READ:
            # This is part of the transitional behaviour where
            # we load the whole DB into memory to get access to
            # the data model.
            self.load()

    def commit(self):
        """
        Commits any changes made to the repo. It is an error to call
        this function if the repo is not opened in write-mode.
        """
        self._checkWriteMode()

    def close(self):
        """
        Closes this repo.
        """
        if self._openMode is None:
            raise ValueError("Repo already closed")
        self._openMode = None

    def verify(self):
        """
        Verifies that the data in the repository is consistent.
        """
        pass

    def _createSystemTable(self):
        self.database.create_tables([models.System])
        models.System.create(
            key=self.systemKeySchemaVersion, value=self.version)
        models.System.create(
            key=self.systemKeyCreationTimeStamp, value=datetime.datetime.now())

    def _readSystemTable(self):
        if not self.exists():
            raise exceptions.RepoNotFoundException(
                self._dbFilename)
        try:
            self._schemaVersion = models.System.get(
                models.System.key == self.systemKeySchemaVersion).value
        except Exception:
            raise exceptions.RepoInvalidDatabaseException(self._dbFilename)
        schemaVersion = self.SchemaVersion(self._schemaVersion)
        if schemaVersion.major != self.version.major:
            raise exceptions.RepoSchemaVersionMismatchException(
                schemaVersion, self.version)


    def insertDataset(self, dataset):
        """
        Inserts the specified dataset into this repository.
        """
        try:
            models.Dataset.create(
                id=dataset.getId(),
                name=dataset.getLocalId(),
                description=dataset.getDescription(),
                attributes=json.dumps(dataset.getAttributes()))
        except Exception:
            raise exceptions.DuplicateNameException(
                dataset.getLocalId())

    def updateDatasetDuo(self, dataset):
        """
        Create or update the DUO info of a dataset
        """
        models.Dataset.update({models.Dataset.info: dataset._info}).where(models.Dataset.id == dataset.getId()).execute()

    def deleteDatasetDuo(self, dataset):
        """
        Delete the DUO info of a dataset
        """
        models.Dataset.update({models.Dataset.info: None}).where(models.Dataset.id == dataset.getId()).execute()

    def removeDataset(self, dataset):
        """
        Removes the specified dataset from this repository. This performs
        a cascading removal of all items within this dataset.
        """
        for datasetRecord in models.Dataset.select().where(
                models.Dataset.id == dataset.getId()):
                    datasetRecord.delete_instance(recursive=True)

    def _readDatasetTable(self):
        for datasetRecord in models.Dataset.select():
            dataset = datasets.Dataset(datasetRecord.name)
            dataset.populateFromRow(datasetRecord)
            dataset.populateDuoInfo(datasetRecord)
            assert dataset.getId() == datasetRecord.id
            # Insert the dataset into the memory-based object model.
            self.addDataset(dataset)

    def removePatient(self, patient):
        """
        Removes the specified patient from this repository.
        """
        q = models.Patient.delete().where(
            models.Patient.id == patient.getId())
        q.execute()

    def removeEnrollment(self, enrollment):
        """
        Removes the specified enrollment from this repository.
        """
        q = models.Enrollment.delete().where(
            models.Enrollment.id == enrollment.getId())
        q.execute()

    def removeConsent(self, consent):
        """
        Removes the specified consent from this repository.
        """
        q = models.Consent.delete().where(
            models.Consent.id == consent.getId())
        q.execute()

    def removeDiagnosis(self, diagnosis):
        """
        Removes the specified diagnosis from this repository.
        """
        q = models.Diagnosis.delete().where(
            models.Diagnosis.id == diagnosis.getId())
        q.execute()

    def removeSample(self, sample):
        """
        Removes the specified sample from this repository.
        """
        q = models.Sample.delete().where(
            models.Sample.id == sample.getId())
        q.execute()

    def removeTreatment(self, treatment):
        """
        Removes the specified treatment from this repository.
        """
        q = models.Treatment.delete().where(
            models.Treatment.id == treatment.getId())
        q.execute()

    def removeOutcome(self, outcome):
        """
        Removes the specified outcome from this repository.
        """
        q = models.Outcome.delete().where(
            models.Outcome.id == outcome.getId())
        q.execute()

    def removeComplication(self, complication):
        """
        Removes the specified complication from this repository.
        """
        q = models.Complication.delete().where(
            models.Complication.id == complication.getId())
        q.execute()

    def removeTumourboard(self, tumourboard):
        """
        Removes the specified tumourboard from this repository.
        """
        q = models.Tumourboard.delete().where(
            models.Tumourboard.id == tumourboard.getId())
        q.execute()

    def removeChemotherapy(self, chemotherapy):
        """
        Removes the specified chemotherapy from this repository.
        """
        q = models.Chemotherapy.delete().where(
            models.Chemotherapy.id == chemotherapy.getId())
        q.execute()

    def removeRadiotherapy(self, radiotherapy):
        """
        Removes the specified radiotherapy from this repository.
        """
        q = models.Radiotherapy.delete().where(
            models.Radiotherapy.id == radiotherapy.getId())
        q.execute()

    def removeSurgery(self, surgery):
        """
        Removes the specified surgery from this repository.
        """
        q = models.Surgery.delete().where(
            models.Surgery.id == surgery.getId())
        q.execute()

    def removeImmunotherapy(self, immunotherapy):
        """
        Removes the specified immunotherapy from this repository.
        """
        q = models.Immunotherapy.delete().where(
            models.Immunotherapy.id == immunotherapy.getId())
        q.execute()

    def removeCelltransplant(self, celltransplant):
        """
        Removes the specified celltransplant from this repository.
        """
        q = models.Celltransplant.delete().where(
            models.Celltransplant.id == celltransplant.getId())
        q.execute()

    def removeSlide(self, slide):
        """
        Removes the specified slide from this repository.
        """
        q = models.Slide.delete().where(
            models.Slide.id == slide.getId())
        q.execute()

    def removeStudy(self, study):
        """
        Removes the specified study from this repository.
        """
        q = models.Study.delete().where(
            models.Study.id == study.getId())
        q.execute()

    def removeLabtest(self, labtest):
        """
        Removes the specified labtest from this repository.
        """
        q = models.Labtest.delete().where(
            models.Labtest.id == labtest.getId())
        q.execute()

    def removeExtraction(self, extraction):
        """
        Removes the specified diagnosis from this repository.
        """
        q = models.Extraction.delete().where(
            models.Extraction.id == extraction.getId())
        q.execute()

    def removeSequencing(self, sequencing):
        """
        Removes the specified sample from this repository.
        """
        q = models.Sequencing.delete().where(
            models.Sequencing.id == sequencing.getId())
        q.execute()

    def removeAlignment(self, alignment):
        """
        Removes the specified treatment from this repository.
        """
        q = models.Alignment.delete().where(
            models.Alignment.id == alignment.getId())
        q.execute()

    def removeVariantCalling(self, variantCalling):
        """
        Removes the specified outcome from this repository.
        """
        q = models.VariantCalling.delete().where(
            models.VariantCalling.id == variantCalling.getId())
        q.execute()

    def removeFusionDetection(self, fusionDetection):
        """
        Removes the specified complication from this repository.
        """
        q = models.FusionDetection.delete().where(
            models.FusionDetection.id == fusionDetection.getId())
        q.execute()

    def removeExpressionAnalysis(self, expressionAnalysis):
        """
        Removes the specified tumourboard from this repository.
        """
        q = models.ExpressionAnalysis.delete().where(
            models.ExpressionAnalysis.id == expressionAnalysis.getId())
        q.execute()

    def _createDatasetTable(self):
        self.database.create_tables([models.Dataset])

    def insertDataset(self, dataset):
        """
        Inserts the specified dataset into this repository.
        """
        try:
            models.Dataset.create(
                id=dataset.getId(),
                name=dataset.getLocalId(),
                description=dataset.getDescription(),
                attributes=json.dumps(dataset.getAttributes()))
        except Exception:
            raise exceptions.DuplicateNameException(
                dataset.getLocalId())

    def updateDatasetDuo(self, dataset):
        """
        Create or update the DUO info of a dataset
        """
        models.Dataset.update({models.Dataset.info: dataset._info}).where(models.Dataset.id == dataset.getId()).execute()

    def deleteDatasetDuo(self, dataset):
        """
        Delete the DUO info of a dataset
        """
        models.Dataset.update({models.Dataset.info: None}).where(models.Dataset.id == dataset.getId()).execute()

    def removeDataset(self, dataset):
        """
        Removes the specified dataset from this repository. This performs
        a cascading removal of all items within this dataset.
        """
        for datasetRecord in models.Dataset.select().where(
                models.Dataset.id == dataset.getId()):
                    datasetRecord.delete_instance(recursive=True)

    def _createPatientTable(self):
        self.database.create_tables([models.Patient])

    def insertPatient(self, patient):
        """
        Inserts the specified patient into this repository.
        """
        try:
            models.Patient.create(
                # Common fields
                id=patient.getId(),
                datasetId=patient.getParentContainer().getId(),
                created=patient.getCreated(),
                updated=patient.getUpdated(),
                name=patient.getLocalId(),
                description=patient.getDescription(),
                attributes=json.dumps(patient.getAttributes()),
                # Unique fields
                patientId = patient.getPatientId(),
                patientIdTier = patient.getPatientIdTier(),
                otherIds = patient.getOtherIds(),
                otherIdsTier = patient.getOtherIdsTier(),
                dateOfBirth = patient.getDateOfBirth(),
                dateOfBirthTier = patient.getDateOfBirthTier(),
                gender = patient.getGender(),
                genderTier = patient.getGenderTier(),
                ethnicity = patient.getEthnicity(),
                ethnicityTier = patient.getEthnicityTier(),
                race = patient.getRace(),
                raceTier = patient.getRaceTier(),
                provinceOfResidence = patient.getProvinceOfResidence(),
                provinceOfResidenceTier = patient.getProvinceOfResidenceTier(),
                dateOfDeath = patient.getDateOfDeath(),
                dateOfDeathTier = patient.getDateOfDeathTier(),
                causeOfDeath = patient.getCauseOfDeath(),
                causeOfDeathTier = patient.getCauseOfDeathTier(),
                autopsyTissueForResearch = patient.getAutopsyTissueForResearch(),
                autopsyTissueForResearchTier = patient.getAutopsyTissueForResearchTier(),
                priorMalignancy = patient.getPriorMalignancy(),
                priorMalignancyTier = patient.getPriorMalignancyTier(),
                dateOfPriorMalignancy = patient.getDateOfPriorMalignancy(),
                dateOfPriorMalignancyTier = patient.getDateOfPriorMalignancyTier(),
                familyHistoryAndRiskFactors = patient.getFamilyHistoryAndRiskFactors(),
                familyHistoryAndRiskFactorsTier = patient.getFamilyHistoryAndRiskFactorsTier(),
                familyHistoryOfPredispositionSyndrome = patient.getFamilyHistoryOfPredispositionSyndrome(),
                familyHistoryOfPredispositionSyndromeTier = patient.getFamilyHistoryOfPredispositionSyndromeTier(),
                detailsOfPredispositionSyndrome = patient.getDetailsOfPredispositionSyndrome(),
                detailsOfPredispositionSyndromeTier = patient.getDetailsOfPredispositionSyndromeTier(),
                geneticCancerSyndrome = patient.getGeneticCancerSyndrome(),
                geneticCancerSyndromeTier = patient.getGeneticCancerSyndromeTier(),
                otherGeneticConditionOrSignificantComorbidity = patient.getOtherGeneticConditionOrSignificantComorbidity(),
                otherGeneticConditionOrSignificantComorbidityTier = patient.getOtherGeneticConditionOrSignificantComorbidityTier(),
                occupationalOrEnvironmentalExposure = patient.getOccupationalOrEnvironmentalExposure(),
                occupationalOrEnvironmentalExposureTier = patient.getOccupationalOrEnvironmentalExposureTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                patient.getLocalId(),
                patient.getParentContainer().getLocalId())

    def _readClinPipeTable(self, dataset, pw_model, datamodel, addMethod):
        """
        A helper that reads clin/pipe table into memory
        """
        for record in pw_model.select().where(pw_model.datasetId == dataset.getId()):
            result = datamodel(dataset, record.name)
            result.populateFromRow(record)
            assert result.getId() == record.id
            addMethod(result)

    def _readPatientTable(self):
        """
        Read the Patient table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Patient, clinical_metadata.Patient, dataset.addPatient)

    def _createEnrollmentTable(self):
        self.database.create_tables([models.Enrollment])

    def insertEnrollment(self, enrollment):
        """
        Inserts the specified enrollment into this repository.
        """
        try:
            models.Enrollment.create(
                # Common fields
                id=enrollment.getId(),
                datasetId=enrollment.getParentContainer().getId(),
                created=enrollment.getCreated(),
                updated=enrollment.getUpdated(),
                name=enrollment.getLocalId(),
                description=enrollment.getDescription(),
                attributes=json.dumps(enrollment.getAttributes()),

                # Unique fields
                patientId=enrollment.getPatientId(),
                patientIdTier = enrollment.getPatientIdTier(),
                enrollmentInstitution = enrollment.getEnrollmentInstitution(),
                enrollmentInstitutionTier = enrollment.getEnrollmentInstitutionTier(),
                enrollmentApprovalDate = enrollment.getEnrollmentApprovalDate(),
                enrollmentApprovalDateTier = enrollment.getEnrollmentApprovalDateTier(),
                crossEnrollment = enrollment.getCrossEnrollment(),
                crossEnrollmentTier = enrollment.getCrossEnrollmentTier(),
                otherPersonalizedMedicineStudyName = enrollment.getOtherPersonalizedMedicineStudyName(),
                otherPersonalizedMedicineStudyNameTier = enrollment.getOtherPersonalizedMedicineStudyNameTier(),
                otherPersonalizedMedicineStudyId = enrollment.getOtherPersonalizedMedicineStudyId(),
                otherPersonalizedMedicineStudyIdTier = enrollment.getOtherPersonalizedMedicineStudyIdTier(),
                ageAtEnrollment = enrollment.getAgeAtEnrollment(),
                ageAtEnrollmentTier = enrollment.getAgeAtEnrollmentTier(),
                eligibilityCategory = enrollment.getEligibilityCategory(),
                eligibilityCategoryTier = enrollment.getEligibilityCategoryTier(),
                statusAtEnrollment = enrollment.getStatusAtEnrollment(),
                statusAtEnrollmentTier = enrollment.getStatusAtEnrollmentTier(),
                primaryOncologistName = enrollment.getPrimaryOncologistName(),
                primaryOncologistNameTier = enrollment.getPrimaryOncologistNameTier(),
                primaryOncologistContact = enrollment.getPrimaryOncologistContact(),
                primaryOncologistContactTier = enrollment.getPrimaryOncologistContactTier(),
                referringPhysicianName = enrollment.getReferringPhysicianName(),
                referringPhysicianNameTier = enrollment.getReferringPhysicianNameTier(),
                referringPhysicianContact = enrollment.getReferringPhysicianContact(),
                referringPhysicianContactTier = enrollment.getReferringPhysicianContactTier(),
                summaryOfIdRequest = enrollment.getSummaryOfIdRequest(),
                summaryOfIdRequestTier = enrollment.getSummaryOfIdRequestTier(),
                treatingCentreName = enrollment.getTreatingCentreName(),
                treatingCentreNameTier = enrollment.getTreatingCentreNameTier(),
                treatingCentreProvince = enrollment.getTreatingCentreProvince(),
                treatingCentreProvinceTier = enrollment.getTreatingCentreProvinceTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                enrollment.getLocalId(),
                enrollment.getParentContainer().getLocalId())

    def _readEnrollmentTable(self):
        """
        Read the Enrollment table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Enrollment, clinical_metadata.Enrollment, dataset.addEnrollment)

    def _createConsentTable(self):
        self.database.create_tables([models.Consent])

    def insertConsent(self, consent):
        """
        Inserts the specified consent into this repository.
        """
        try:
            models.Consent.create(
                # Common fields
                id=consent.getId(),
                datasetId=consent.getParentContainer().getId(),
                created=consent.getCreated(),
                updated=consent.getUpdated(),
                name=consent.getLocalId(),
                description=consent.getDescription(),
                attributes=json.dumps(consent.getAttributes()),

                # Unique fields
                patientId = consent.getPatientId(),
                patientIdTier = consent.getPatientIdTier(),
                consentId = consent.getConsentId(),
                consentIdTier = consent.getConsentIdTier(),
                consentDate = consent.getConsentDate(),
                consentDateTier = consent.getConsentDateTier(),
                consentVersion = consent.getConsentVersion(),
                consentVersionTier = consent.getConsentVersionTier(),
                patientConsentedTo = consent.getPatientConsentedTo(),
                patientConsentedToTier = consent.getPatientConsentedToTier(),
                reasonForRejection = consent.getReasonForRejection(),
                reasonForRejectionTier = consent.getReasonForRejectionTier(),
                wasAssentObtained = consent.getWasAssentObtained(),
                wasAssentObtainedTier = consent.getWasAssentObtainedTier(),
                dateOfAssent = consent.getDateOfAssent(),
                dateOfAssentTier = consent.getDateOfAssentTier(),
                assentFormVersion = consent.getAssentFormVersion(),
                assentFormVersionTier = consent.getAssentFormVersionTier(),
                ifAssentNotObtainedWhyNot = consent.getIfAssentNotObtainedWhyNot(),
                ifAssentNotObtainedWhyNotTier = consent.getIfAssentNotObtainedWhyNotTier(),
                reconsentDate = consent.getReconsentDate(),
                reconsentDateTier = consent.getReconsentDateTier(),
                reconsentVersion = consent.getReconsentVersion(),
                reconsentVersionTier = consent.getReconsentVersionTier(),
                consentingCoordinatorName = consent.getConsentingCoordinatorName(),
                consentingCoordinatorNameTier = consent.getConsentingCoordinatorNameTier(),
                previouslyConsented = consent.getPreviouslyConsented(),
                previouslyConsentedTier = consent.getPreviouslyConsentedTier(),
                nameOfOtherBiobank = consent.getNameOfOtherBiobank(),
                nameOfOtherBiobankTier = consent.getNameOfOtherBiobankTier(),
                hasConsentBeenWithdrawn = consent.getHasConsentBeenWithdrawn(),
                hasConsentBeenWithdrawnTier = consent.getHasConsentBeenWithdrawnTier(),
                dateOfConsentWithdrawal = consent.getDateOfConsentWithdrawal(),
                dateOfConsentWithdrawalTier = consent.getDateOfConsentWithdrawalTier(),
                typeOfConsentWithdrawal = consent.getTypeOfConsentWithdrawal(),
                typeOfConsentWithdrawalTier = consent.getTypeOfConsentWithdrawalTier(),
                reasonForConsentWithdrawal = consent.getReasonForConsentWithdrawal(),
                reasonForConsentWithdrawalTier = consent.getReasonForConsentWithdrawalTier(),
                consentFormComplete = consent.getConsentFormComplete(),
                consentFormCompleteTier = consent.getConsentFormCompleteTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                consent.getLocalId(),
                consent.getParentContainer().getLocalId())

    def _readConsentTable(self):
        """
        Read the Consent table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Consent, clinical_metadata.Consent, dataset.addConsent)

    def _createDiagnosisTable(self):
        self.database.create_tables([models.Diagnosis])

    def insertDiagnosis(self, diagnosis):
        """
        Inserts the specified diagnosis into this repository.
        """
        try:
            models.Diagnosis.create(
                # Common fields
                id=diagnosis.getId(),
                datasetId=diagnosis.getParentContainer().getId(),
                created=diagnosis.getCreated(),
                updated=diagnosis.getUpdated(),
                name=diagnosis.getLocalId(),
                description=diagnosis.getDescription(),
                attributes=json.dumps(diagnosis.getAttributes()),

                # Unique fields
                patientId = diagnosis.getPatientId(),
                patientIdTier = diagnosis.getPatientIdTier(),
                diagnosisId = diagnosis.getDiagnosisId(),
                diagnosisIdTier = diagnosis.getDiagnosisIdTier(),
                diagnosisDate = diagnosis.getDiagnosisDate(),
                diagnosisDateTier = diagnosis.getDiagnosisDateTier(),
                ageAtDiagnosis = diagnosis.getAgeAtDiagnosis(),
                ageAtDiagnosisTier = diagnosis.getAgeAtDiagnosisTier(),
                cancerType = diagnosis.getCancerType(),
                cancerTypeTier = diagnosis.getCancerTypeTier(),
                classification = diagnosis.getClassification(),
                classificationTier = diagnosis.getClassificationTier(),
                cancerSite = diagnosis.getCancerSite(),
                cancerSiteTier = diagnosis.getCancerSiteTier(),
                histology = diagnosis.getHistology(),
                histologyTier = diagnosis.getHistologyTier(),
                methodOfDefinitiveDiagnosis = diagnosis.getMethodOfDefinitiveDiagnosis(),
                methodOfDefinitiveDiagnosisTier = diagnosis.getMethodOfDefinitiveDiagnosisTier(),
                sampleType = diagnosis.getSampleType(),
                sampleTypeTier = diagnosis.getSampleTypeTier(),
                sampleSite = diagnosis.getSampleSite(),
                sampleSiteTier = diagnosis.getSampleSiteTier(),
                tumorGrade = diagnosis.getTumorGrade(),
                tumorGradeTier = diagnosis.getTumorGradeTier(),
                gradingSystemUsed = diagnosis.getGradingSystemUsed(),
                gradingSystemUsedTier = diagnosis.getGradingSystemUsedTier(),
                sitesOfMetastases = diagnosis.getSitesOfMetastases(),
                sitesOfMetastasesTier = diagnosis.getSitesOfMetastasesTier(),
                stagingSystem = diagnosis.getStagingSystem(),
                stagingSystemTier = diagnosis.getStagingSystemTier(),
                versionOrEditionOfTheStagingSystem = diagnosis.getVersionOrEditionOfTheStagingSystem(),
                versionOrEditionOfTheStagingSystemTier = diagnosis.getVersionOrEditionOfTheStagingSystemTier(),
                specificTumorStageAtDiagnosis = diagnosis.getSpecificTumorStageAtDiagnosis(),
                specificTumorStageAtDiagnosisTier = diagnosis.getSpecificTumorStageAtDiagnosisTier(),
                prognosticBiomarkers = diagnosis.getPrognosticBiomarkers(),
                prognosticBiomarkersTier = diagnosis.getPrognosticBiomarkersTier(),
                biomarkerQuantification = diagnosis.getBiomarkerQuantification(),
                biomarkerQuantificationTier = diagnosis.getBiomarkerQuantificationTier(),
                additionalMolecularTesting = diagnosis.getAdditionalMolecularTesting(),
                additionalMolecularTestingTier = diagnosis.getAdditionalMolecularTestingTier(),
                additionalTestType = diagnosis.getAdditionalTestType(),
                additionalTestTypeTier = diagnosis.getAdditionalTestTypeTier(),
                laboratoryName = diagnosis.getLaboratoryName(),
                laboratoryNameTier = diagnosis.getLaboratoryNameTier(),
                laboratoryAddress = diagnosis.getLaboratoryAddress(),
                laboratoryAddressTier = diagnosis.getLaboratoryAddressTier(),
                siteOfMetastases = diagnosis.getSiteOfMetastases(),
                siteOfMetastasesTier = diagnosis.getSiteOfMetastasesTier(),
                stagingSystemVersion = diagnosis.getStagingSystemVersion(),
                stagingSystemVersionTier = diagnosis.getStagingSystemVersionTier(),
                specificStage = diagnosis.getSpecificStage(),
                specificStageTier = diagnosis.getSpecificStageTier(),
                cancerSpecificBiomarkers = diagnosis.getCancerSpecificBiomarkers(),
                cancerSpecificBiomarkersTier = diagnosis.getCancerSpecificBiomarkersTier(),
                additionalMolecularDiagnosticTestingPerformed = diagnosis.getAdditionalMolecularDiagnosticTestingPerformed(),
                additionalMolecularDiagnosticTestingPerformedTier = diagnosis.getAdditionalMolecularDiagnosticTestingPerformedTier(),
                additionalTest = diagnosis.getAdditionalTest(),
                additionalTestTier = diagnosis.getAdditionalTestTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                diagnosis.getLocalId(),
                diagnosis.getParentContainer().getLocalId())

    def _readDiagnosisTable(self):
        """
        Read the Diagnosis table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Diagnosis, clinical_metadata.Diagnosis, dataset.addDiagnosis)

    def _createSampleTable(self):
        self.database.create_tables([models.Sample])

    def insertSample(self, sample):
        """
        Inserts the specified sample into this repository.
        """
        try:
            models.Sample.create(
                # Common fields
                id=sample.getId(),
                datasetId=sample.getParentContainer().getId(),
                created=sample.getCreated(),
                updated=sample.getUpdated(),
                name=sample.getLocalId(),
                description=sample.getDescription(),
                attributes=json.dumps(sample.getAttributes()),

                # Unique fields
                patientId = sample.getPatientId(),
                patientIdTier = sample.getPatientIdTier(),
                sampleId = sample.getSampleId(),
                sampleIdTier = sample.getSampleIdTier(),
                diagnosisId = sample.getDiagnosisId(),
                diagnosisIdTier = sample.getDiagnosisIdTier(),
                localBiobankId = sample.getLocalBiobankId(),
                localBiobankIdTier = sample.getLocalBiobankIdTier(),
                collectionDate = sample.getCollectionDate(),
                collectionDateTier = sample.getCollectionDateTier(),
                collectionHospital = sample.getCollectionHospital(),
                collectionHospitalTier = sample.getCollectionHospitalTier(),
                sampleType = sample.getSampleType(),
                sampleTypeTier = sample.getSampleTypeTier(),
                tissueDiseaseState = sample.getTissueDiseaseState(),
                tissueDiseaseStateTier = sample.getTissueDiseaseStateTier(),
                anatomicSiteTheSampleObtainedFrom = sample.getAnatomicSiteTheSampleObtainedFrom(),
                anatomicSiteTheSampleObtainedFromTier = sample.getAnatomicSiteTheSampleObtainedFromTier(),
                cancerType = sample.getCancerType(),
                cancerTypeTier = sample.getCancerTypeTier(),
                cancerSubtype = sample.getCancerSubtype(),
                cancerSubtypeTier = sample.getCancerSubtypeTier(),
                pathologyReportId = sample.getPathologyReportId(),
                pathologyReportIdTier = sample.getPathologyReportIdTier(),
                morphologicalCode = sample.getMorphologicalCode(),
                morphologicalCodeTier = sample.getMorphologicalCodeTier(),
                topologicalCode = sample.getTopologicalCode(),
                topologicalCodeTier = sample.getTopologicalCodeTier(),
                shippingDate = sample.getShippingDate(),
                shippingDateTier = sample.getShippingDateTier(),
                receivedDate = sample.getReceivedDate(),
                receivedDateTier = sample.getReceivedDateTier(),
                qualityControlPerformed = sample.getQualityControlPerformed(),
                qualityControlPerformedTier = sample.getQualityControlPerformedTier(),
                estimatedTumorContent = sample.getEstimatedTumorContent(),
                estimatedTumorContentTier = sample.getEstimatedTumorContentTier(),
                quantity = sample.getQuantity(),
                quantityTier = sample.getQuantityTier(),
                units = sample.getUnits(),
                unitsTier = sample.getUnitsTier(),
                associatedBiobank = sample.getAssociatedBiobank(),
                associatedBiobankTier = sample.getAssociatedBiobankTier(),
                otherBiobank = sample.getOtherBiobank(),
                otherBiobankTier = sample.getOtherBiobankTier(),
                sopFollowed = sample.getSopFollowed(),
                sopFollowedTier = sample.getSopFollowedTier(),
                ifNotExplainAnyDeviation = sample.getIfNotExplainAnyDeviation(),
                ifNotExplainAnyDeviationTier = sample.getIfNotExplainAnyDeviationTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                sample.getLocalId(),
                sample.getParentContainer().getLocalId())

    def _readSampleTable(self):
        """
        Read the Sample table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Sample, clinical_metadata.Sample, dataset.addSample)

    def _createTreatmentTable(self):
        self.database.create_tables([models.Treatment])

    def insertTreatment(self, treatment):
        """
        Inserts the specified treatment into this repository.
        """
        try:
            models.Treatment.create(
                # Common fields
                id=treatment.getId(),
                datasetId=treatment.getParentContainer().getId(),
                created=treatment.getCreated(),
                updated=treatment.getUpdated(),
                name=treatment.getLocalId(),
                description=treatment.getDescription(),
                attributes=json.dumps(treatment.getAttributes()),

                # Unique fields
                patientId = treatment.getPatientId(),
                patientIdTier = treatment.getPatientIdTier(),
                courseNumber = treatment.getCourseNumber(),
                courseNumberTier = treatment.getCourseNumberTier(),
                therapeuticModality = treatment.getTherapeuticModality(),
                therapeuticModalityTier = treatment.getTherapeuticModalityTier(),
                treatmentPlanType = treatment.getTreatmentPlanType(),
                treatmentPlanTypeTier = treatment.getTreatmentPlanTypeTier(),
                treatmentIntent = treatment.getTreatmentIntent(),
                treatmentIntentTier = treatment.getTreatmentIntentTier(),
                startDate = treatment.getStartDate(),
                startDateTier = treatment.getStartDateTier(),
                stopDate = treatment.getStopDate(),
                stopDateTier = treatment.getStopDateTier(),
                reasonForEndingTheTreatment = treatment.getReasonForEndingTheTreatment(),
                reasonForEndingTheTreatmentTier = treatment.getReasonForEndingTheTreatmentTier(),
                responseToTreatment = treatment.getResponseToTreatment(),
                responseToTreatmentTier = treatment.getResponseToTreatmentTier(),
                responseCriteriaUsed = treatment.getResponseCriteriaUsed(),
                responseCriteriaUsedTier = treatment.getResponseCriteriaUsedTier(),
                dateOfRecurrenceOrProgressionAfterThisTreatment = treatment.getDateOfRecurrenceOrProgressionAfterThisTreatment(),
                dateOfRecurrenceOrProgressionAfterThisTreatmentTier = treatment.getDateOfRecurrenceOrProgressionAfterThisTreatmentTier(),
                unexpectedOrUnusualToxicityDuringTreatment = treatment.getUnexpectedOrUnusualToxicityDuringTreatment(),
                unexpectedOrUnusualToxicityDuringTreatmentTier = treatment.getUnexpectedOrUnusualToxicityDuringTreatmentTier()
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                treatment.getLocalId(),
                treatment.getParentContainer().getLocalId())

    def _readTreatmentTable(self):
        """
        Read the Treatment table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Treatment, clinical_metadata.Treatment, dataset.addTreatment)

    def _createOutcomeTable(self):
        self.database.create_tables([models.Outcome])

    def insertOutcome(self, outcome):
        """
        Inserts the specified outcome into this repository.
        """
        try:
            models.Outcome.create(
                # Common fields
                id=outcome.getId(),
                datasetId=outcome.getParentContainer().getId(),
                created=outcome.getCreated(),
                updated=outcome.getUpdated(),
                name=outcome.getLocalId(),
                description=outcome.getDescription(),
                attributes=json.dumps(outcome.getAttributes()),

                # Unique fields
                patientId = outcome.getPatientId(),
                patientIdTier = outcome.getPatientIdTier(),
                physicalExamId = outcome.getPhysicalExamId(),
                physicalExamIdTier = outcome.getPhysicalExamIdTier(),
                dateOfAssessment = outcome.getDateOfAssessment(),
                dateOfAssessmentTier = outcome.getDateOfAssessmentTier(),
                diseaseResponseOrStatus = outcome.getDiseaseResponseOrStatus(),
                diseaseResponseOrStatusTier = outcome.getDiseaseResponseOrStatusTier(),
                otherResponseClassification = outcome.getOtherResponseClassification(),
                otherResponseClassificationTier = outcome.getOtherResponseClassificationTier(),
                minimalResidualDiseaseAssessment = outcome.getMinimalResidualDiseaseAssessment(),
                minimalResidualDiseaseAssessmentTier = outcome.getMinimalResidualDiseaseAssessmentTier(),
                methodOfResponseEvaluation = outcome.getMethodOfResponseEvaluation(),
                methodOfResponseEvaluationTier = outcome.getMethodOfResponseEvaluationTier(),
                responseCriteriaUsed = outcome.getResponseCriteriaUsed(),
                responseCriteriaUsedTier = outcome.getResponseCriteriaUsedTier(),
                summaryStage = outcome.getSummaryStage(),
                summaryStageTier = outcome.getSummaryStageTier(),
                sitesOfAnyProgressionOrRecurrence = outcome.getSitesOfAnyProgressionOrRecurrence(),
                sitesOfAnyProgressionOrRecurrenceTier = outcome.getSitesOfAnyProgressionOrRecurrenceTier(),
                vitalStatus = outcome.getVitalStatus(),
                vitalStatusTier = outcome.getVitalStatusTier(),
                height = outcome.getHeight(),
                heightTier = outcome.getHeightTier(),
                weight = outcome.getWeight(),
                weightTier = outcome.getWeightTier(),
                heightUnits = outcome.getHeightUnits(),
                heightUnitsTier = outcome.getHeightUnitsTier(),
                weightUnits = outcome.getWeightUnits(),
                weightUnitsTier = outcome.getWeightUnitsTier(),
                performanceStatus = outcome.getPerformanceStatus(),
                performanceStatusTier = outcome.getPerformanceStatusTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                outcome.getLocalId(),
                outcome.getParentContainer().getLocalId())

    def _readOutcomeTable(self):
        """
        Read the Outcome table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Outcome, clinical_metadata.Outcome, dataset.addOutcome)

    def _createComplicationTable(self):
        self.database.create_tables([models.Complication])

    def insertComplication(self, complication):
        """
        Inserts the specified complication into this repository.
        """
        try:
            models.Complication.create(
                # Common fields
                id=complication.getId(),
                datasetId=complication.getParentContainer().getId(),
                created=complication.getCreated(),
                updated=complication.getUpdated(),
                name=complication.getLocalId(),
                description=complication.getDescription(),
                attributes=json.dumps(complication.getAttributes()),

                # Unique fields
                patientId = complication.getPatientId(),
                patientIdTier = complication.getPatientIdTier(),
                date = complication.getDate(),
                dateTier = complication.getDateTier(),
                lateComplicationOfTherapyDeveloped = complication.getLateComplicationOfTherapyDeveloped(),
                lateComplicationOfTherapyDevelopedTier = complication.getLateComplicationOfTherapyDevelopedTier(),
                lateToxicityDetail = complication.getLateToxicityDetail(),
                lateToxicityDetailTier = complication.getLateToxicityDetailTier(),
                suspectedTreatmentInducedNeoplasmDeveloped = complication.getSuspectedTreatmentInducedNeoplasmDeveloped(),
                suspectedTreatmentInducedNeoplasmDevelopedTier = complication.getSuspectedTreatmentInducedNeoplasmDevelopedTier(),
                treatmentInducedNeoplasmDetails = complication.getTreatmentInducedNeoplasmDetails(),
                treatmentInducedNeoplasmDetailsTier = complication.getTreatmentInducedNeoplasmDetailsTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                complication.getLocalId(),
                complication.getParentContainer().getLocalId())

    def _readComplicationTable(self):
        """
        Read the Complication table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Complication, clinical_metadata.Complication, dataset.addComplication)

    def _createTumourboardTable(self):
        self.database.create_tables([models.Tumourboard])

    def insertTumourboard(self, tumourboard):
        """
        Inserts the specified tumourboard into this repository.
        """
        try:
            models.Tumourboard.create(
                # Common fields
                id=tumourboard.getId(),
                datasetId=tumourboard.getParentContainer().getId(),
                created=tumourboard.getCreated(),
                updated=tumourboard.getUpdated(),
                name=tumourboard.getLocalId(),
                description=tumourboard.getDescription(),
                attributes=json.dumps(tumourboard.getAttributes()),

                # Unique fields
                patientId = tumourboard.getPatientId(),
                patientIdTier = tumourboard.getPatientIdTier(),
                dateOfMolecularTumorBoard = tumourboard.getDateOfMolecularTumorBoard(),
                dateOfMolecularTumorBoardTier = tumourboard.getDateOfMolecularTumorBoardTier(),
                typeOfSampleAnalyzed = tumourboard.getTypeOfSampleAnalyzed(),
                typeOfSampleAnalyzedTier = tumourboard.getTypeOfSampleAnalyzedTier(),
                typeOfTumourSampleAnalyzed = tumourboard.getTypeOfTumourSampleAnalyzed(),
                typeOfTumourSampleAnalyzedTier = tumourboard.getTypeOfTumourSampleAnalyzedTier(),
                analysesDiscussed = tumourboard.getAnalysesDiscussed(),
                analysesDiscussedTier = tumourboard.getAnalysesDiscussedTier(),
                somaticSampleType = tumourboard.getSomaticSampleType(),
                somaticSampleTypeTier = tumourboard.getSomaticSampleTypeTier(),
                normalExpressionComparator = tumourboard.getNormalExpressionComparator(),
                normalExpressionComparatorTier = tumourboard.getNormalExpressionComparatorTier(),
                diseaseExpressionComparator = tumourboard.getDiseaseExpressionComparator(),
                diseaseExpressionComparatorTier = tumourboard.getDiseaseExpressionComparatorTier(),
                hasAGermlineVariantBeenIdentifiedByProfilingThatMayPredisposeToCancer = tumourboard.getHasAGermlineVariantBeenIdentifiedByProfilingThatMayPredisposeToCancer(),
                hasAGermlineVariantBeenIdentifiedByProfilingThatMayPredisposeToCancerTier = tumourboard.getHasAGermlineVariantBeenIdentifiedByProfilingThatMayPredisposeToCancerTier(),
                actionableTargetFound = tumourboard.getActionableTargetFound(),
                actionableTargetFoundTier = tumourboard.getActionableTargetFoundTier(),
                molecularTumorBoardRecommendation = tumourboard.getMolecularTumorBoardRecommendation(),
                molecularTumorBoardRecommendationTier = tumourboard.getMolecularTumorBoardRecommendationTier(),
                germlineDnaSampleId = tumourboard.getGermlineDnaSampleId(),
                germlineDnaSampleIdTier = tumourboard.getGermlineDnaSampleIdTier(),
                tumorDnaSampleId = tumourboard.getTumorDnaSampleId(),
                tumorDnaSampleIdTier = tumourboard.getTumorDnaSampleIdTier(),
                tumorRnaSampleId = tumourboard.getTumorRnaSampleId(),
                tumorRnaSampleIdTier = tumourboard.getTumorRnaSampleIdTier(),
                germlineSnvDiscussed = tumourboard.getGermlineSnvDiscussed(),
                germlineSnvDiscussedTier = tumourboard.getGermlineSnvDiscussedTier(),
                somaticSnvDiscussed = tumourboard.getSomaticSnvDiscussed(),
                somaticSnvDiscussedTier = tumourboard.getSomaticSnvDiscussedTier(),
                cnvsDiscussed = tumourboard.getCnvsDiscussed(),
                cnvsDiscussedTier = tumourboard.getCnvsDiscussedTier(),
                structuralVariantDiscussed = tumourboard.getStructuralVariantDiscussed(),
                structuralVariantDiscussedTier = tumourboard.getStructuralVariantDiscussedTier(),
                classificationOfVariants = tumourboard.getClassificationOfVariants(),
                classificationOfVariantsTier = tumourboard.getClassificationOfVariantsTier(),
                clinicalValidationProgress = tumourboard.getClinicalValidationProgress(),
                clinicalValidationProgressTier = tumourboard.getClinicalValidationProgressTier(),
                typeOfValidation = tumourboard.getTypeOfValidation(),
                typeOfValidationTier = tumourboard.getTypeOfValidationTier(),
                agentOrDrugClass = tumourboard.getAgentOrDrugClass(),
                agentOrDrugClassTier = tumourboard.getAgentOrDrugClassTier(),
                levelOfEvidenceForExpressionTargetAgentMatch = tumourboard.getLevelOfEvidenceForExpressionTargetAgentMatch(),
                levelOfEvidenceForExpressionTargetAgentMatchTier = tumourboard.getLevelOfEvidenceForExpressionTargetAgentMatchTier(),
                didTreatmentPlanChangeBasedOnProfilingResult = tumourboard.getDidTreatmentPlanChangeBasedOnProfilingResult(),
                didTreatmentPlanChangeBasedOnProfilingResultTier = tumourboard.getDidTreatmentPlanChangeBasedOnProfilingResultTier(),
                howTreatmentHasAlteredBasedOnProfiling = tumourboard.getHowTreatmentHasAlteredBasedOnProfiling(),
                howTreatmentHasAlteredBasedOnProfilingTier = tumourboard.getHowTreatmentHasAlteredBasedOnProfilingTier(),
                reasonTreatmentPlanDidNotChangeBasedOnProfiling = tumourboard.getReasonTreatmentPlanDidNotChangeBasedOnProfiling(),
                reasonTreatmentPlanDidNotChangeBasedOnProfilingTier = tumourboard.getReasonTreatmentPlanDidNotChangeBasedOnProfilingTier(),
                detailsOfTreatmentPlanImpact = tumourboard.getDetailsOfTreatmentPlanImpact(),
                detailsOfTreatmentPlanImpactTier = tumourboard.getDetailsOfTreatmentPlanImpactTier(),
                patientOrFamilyInformedOfGermlineVariant = tumourboard.getPatientOrFamilyInformedOfGermlineVariant(),
                patientOrFamilyInformedOfGermlineVariantTier = tumourboard.getPatientOrFamilyInformedOfGermlineVariantTier(),
                patientHasBeenReferredToAHereditaryCancerProgramBasedOnThisMolecularProfiling = tumourboard.getPatientHasBeenReferredToAHereditaryCancerProgramBasedOnThisMolecularProfiling(),
                patientHasBeenReferredToAHereditaryCancerProgramBasedOnThisMolecularProfilingTier = tumourboard.getPatientHasBeenReferredToAHereditaryCancerProgramBasedOnThisMolecularProfilingTier(),
                summaryReport = tumourboard.getSummaryReport(),
                summaryReportTier = tumourboard.getSummaryReportTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                tumourboard.getLocalId(),
                tumourboard.getParentContainer().getLocalId())

    def _readTumourboardTable(self):
        """
        Read the Tumourboard table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Tumourboard, clinical_metadata.Tumourboard, dataset.addTumourboard)

    def _createChemotherapyTable(self):
        self.database.create_tables([models.Chemotherapy])

    def insertChemotherapy(self, chemotherapy):
        """
        Inserts the specified chemotherapy into this repository.
        """
        try:
            models.Chemotherapy.create(
                # Common fields
                id=chemotherapy.getId(),
                datasetId=chemotherapy.getParentContainer().getId(),
                created=chemotherapy.getCreated(),
                updated=chemotherapy.getUpdated(),
                name=chemotherapy.getLocalId(),
                description=chemotherapy.getDescription(),
                attributes=json.dumps(chemotherapy.getAttributes()),

                # Unique fields
                patientId=chemotherapy.getPatientId(),
                patientIdTier=chemotherapy.getPatientIdTier(),
                courseNumber=chemotherapy.getCourseNumber(),
                courseNumberTier=chemotherapy.getCourseNumberTier(),
                startDate=chemotherapy.getStartDate(),
                startDateTier=chemotherapy.getStartDateTier(),
                stopDate=chemotherapy.getStopDate(),
                stopDateTier=chemotherapy.getStopDateTier(),
                systematicTherapyAgentName=chemotherapy.getSystematicTherapyAgentName(),
                systematicTherapyAgentNameTier=chemotherapy.getSystematicTherapyAgentNameTier(),
                route=chemotherapy.getRoute(),
                routeTier=chemotherapy.getRouteTier(),
                dose=chemotherapy.getDose(),
                doseTier=chemotherapy.getDoseTier(),
                doseFrequency=chemotherapy.getDoseFrequency(),
                doseFrequencyTier=chemotherapy.getDoseFrequencyTier(),
                doseUnit=chemotherapy.getDoseUnit(),
                doseUnitTier=chemotherapy.getDoseUnitTier(),
                daysPerCycle=chemotherapy.getDaysPerCycle(),
                daysPerCycleTier=chemotherapy.getDaysPerCycleTier(),
                numberOfCycle=chemotherapy.getNumberOfCycle(),
                numberOfCycleTier=chemotherapy.getNumberOfCycleTier(),
                treatmentIntent=chemotherapy.getTreatmentIntent(),
                treatmentIntentTier=chemotherapy.getTreatmentIntentTier(),
                treatingCentreName=chemotherapy.getTreatingCentreName(),
                treatingCentreNameTier=chemotherapy.getTreatingCentreNameTier(),
                type=chemotherapy.getType(),
                typeTier=chemotherapy.getTypeTier(),
                protocolCode=chemotherapy.getProtocolCode(),
                protocolCodeTier=chemotherapy.getProtocolCodeTier(),
                recordingDate=chemotherapy.getRecordingDate(),
                recordingDateTier=chemotherapy.getRecordingDateTier(),
                treatmentPlanId=chemotherapy.getTreatmentPlanId(),
                treatmentPlanIdTier=chemotherapy.getTreatmentPlanIdTier(),
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                chemotherapy.getLocalId(),
                chemotherapy.getParentContainer().getLocalId())

    def _readChemotherapyTable(self):
        """
        Read the Chemotherapy table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Chemotherapy, clinical_metadata.Chemotherapy, dataset.addChemotherapy)

    def _createRadiotherapyTable(self):
        self.database.create_tables([models.Radiotherapy])

    def insertRadiotherapy(self, radiotherapy):
        """
        Inserts the specified radiotherapy into this repository.
        """
        try:
            models.Radiotherapy.create(
                # Common fields
                id=radiotherapy.getId(),
                datasetId=radiotherapy.getParentContainer().getId(),
                created=radiotherapy.getCreated(),
                updated=radiotherapy.getUpdated(),
                name=radiotherapy.getLocalId(),
                description=radiotherapy.getDescription(),
                attributes=json.dumps(radiotherapy.getAttributes()),

                # Unique fields
                patientId=radiotherapy.getPatientId(),
                patientIdTier=radiotherapy.getPatientIdTier(),
                courseNumber=radiotherapy.getCourseNumber(),
                courseNumberTier=radiotherapy.getCourseNumberTier(),
                startDate=radiotherapy.getStartDate(),
                startDateTier=radiotherapy.getStartDateTier(),
                stopDate=radiotherapy.getStopDate(),
                stopDateTier=radiotherapy.getStopDateTier(),
                therapeuticModality=radiotherapy.getTherapeuticModality(),
                therapeuticModalityTier=radiotherapy.getTherapeuticModalityTier(),
                baseline=radiotherapy.getBaseline(),
                baselineTier=radiotherapy.getBaselineTier(),
                testResult=radiotherapy.getTestResult(),
                testResultTier=radiotherapy.getTestResultTier(),
                testResultStd=radiotherapy.getTestResultStd(),
                testResultStdTier=radiotherapy.getTestResultStdTier(),
                treatingCentreName=radiotherapy.getTreatingCentreName(),
                treatingCentreNameTier=radiotherapy.getTreatingCentreNameTier(),
                startIntervalRad=radiotherapy.getStartIntervalRad(),
                startIntervalRadTier=radiotherapy.getStartIntervalRadTier(),
                startIntervalRadRaw=radiotherapy.getStartIntervalRadRaw(),
                startIntervalRadRawTier=radiotherapy.getStartIntervalRadRawTier(),
                recordingDate=radiotherapy.getRecordingDate(),
                recordingDateTier=radiotherapy.getRecordingDateTier(),
                adjacentFields=radiotherapy.getAdjacentFields(),
                adjacentFieldsTier=radiotherapy.getAdjacentFieldsTier(),
                adjacentFractions=radiotherapy.getAdjacentFractions(),
                adjacentFractionsTier=radiotherapy.getAdjacentFractionsTier(),
                complete=radiotherapy.getComplete(),
                completeTier=radiotherapy.getCompleteTier(),
                brachytherapyDose=radiotherapy.getBrachytherapyDose(),
                brachytherapyDoseTier=radiotherapy.getBrachytherapyDoseTier(),
                radiotherapyDose=radiotherapy.getRadiotherapyDose(),
                radiotherapyDoseTier=radiotherapy.getRadiotherapyDoseTier(),
                siteNumber=radiotherapy.getSiteNumber(),
                siteNumberTier=radiotherapy.getSiteNumberTier(),
                technique=radiotherapy.getTechnique(),
                techniqueTier=radiotherapy.getTechniqueTier(),
                treatedRegion=radiotherapy.getTreatedRegion(),
                treatedRegionTier=radiotherapy.getTreatedRegionTier(),
                treatmentPlanId=radiotherapy.getTreatmentPlanId(),
                treatmentPlanIdTier=radiotherapy.getTreatmentPlanIdTier(),
                radiationType=radiotherapy.getRadiationType(),
                radiationTypeTier=radiotherapy.getRadiationTypeTier(),
                radiationSite=radiotherapy.getRadiationSite(),
                radiationSiteTier=radiotherapy.getRadiationSiteTier(),
                totalDose=radiotherapy.getTotalDose(),
                totalDoseTier=radiotherapy.getTotalDoseTier(),
                boostSite=radiotherapy.getBoostSite(),
                boostSiteTier=radiotherapy.getBoostSiteTier(),
                boostDose=radiotherapy.getBoostDose(),
                boostDoseTier=radiotherapy.getBoostDoseTier()

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                radiotherapy.getLocalId(),
                radiotherapy.getParentContainer().getLocalId())

    def _readRadiotherapyTable(self):
        """
        Read the Radiotherapy table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Radiotherapy, clinical_metadata.Radiotherapy, dataset.addRadiotherapy)

    def _createSurgeryTable(self):
        self.database.create_tables([models.Surgery])

    def insertSurgery(self, surgery):
        """
        Inserts the specified surgery into this repository.
        """
        try:
            models.Surgery.create(
                # Common fields
                id=surgery.getId(),
                datasetId=surgery.getParentContainer().getId(),
                created=surgery.getCreated(),
                updated=surgery.getUpdated(),
                name=surgery.getLocalId(),
                description=surgery.getDescription(),
                attributes=json.dumps(surgery.getAttributes()),

                # Unique fields
                patientId=surgery.getPatientId(),
                patientIdTier=surgery.getPatientIdTier(),
                startDate=surgery.getStartDate(),
                startDateTier=surgery.getStartDateTier(),
                stopDate=surgery.getStopDate(),
                stopDateTier=surgery.getStopDateTier(),
                sampleId=surgery.getSampleId(),
                sampleIdTier=surgery.getSampleIdTier(),
                collectionTimePoint=surgery.getCollectionTimePoint(),
                collectionTimePointTier=surgery.getCollectionTimePointTier(),
                diagnosisDate=surgery.getDiagnosisDate(),
                diagnosisDateTier=surgery.getDiagnosisDateTier(),
                site=surgery.getSite(),
                siteTier=surgery.getSiteTier(),
                type=surgery.getType(),
                typeTier=surgery.getTypeTier(),
                recordingDate=surgery.getRecordingDate(),
                recordingDateTier=surgery.getRecordingDateTier(),
                treatmentPlanId=surgery.getTreatmentPlanId(),
                treatmentPlanIdTier=surgery.getTreatmentPlanIdTier(),
                courseNumber=surgery.getCourseNumber(),
                courseNumberTier=surgery.getCourseNumberTier()

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                surgery.getLocalId(),
                surgery.getParentContainer().getLocalId())

    def _readSurgeryTable(self):
        """
        Read the Surgery table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Surgery, clinical_metadata.Surgery, dataset.addSurgery)

    def _createImmunotherapyTable(self):
        self.database.create_tables([models.Immunotherapy])

    def insertImmunotherapy(self, immunotherapy):
        """
        Inserts the specified immunotherapy into this repository.
        """
        try:
            models.Immunotherapy.create(
                # Common fields
                id=immunotherapy.getId(),
                datasetId=immunotherapy.getParentContainer().getId(),
                created=immunotherapy.getCreated(),
                updated=immunotherapy.getUpdated(),
                name=immunotherapy.getLocalId(),
                description=immunotherapy.getDescription(),
                attributes=json.dumps(immunotherapy.getAttributes()),

                # Unique fields
                patientId=immunotherapy.getPatientId(),
                patientIdTier=immunotherapy.getPatientIdTier(),
                startDate=immunotherapy.getStartDate(),
                startDateTier=immunotherapy.getStartDateTier(),
                immunotherapyType=immunotherapy.getImmunotherapyType(),
                immunotherapyTypeTier=immunotherapy.getImmunotherapyTypeTier(),
                immunotherapyTarget=immunotherapy.getImmunotherapyTarget(),
                immunotherapyTargetTier=immunotherapy.getImmunotherapyTargetTier(),
                immunotherapyDetail=immunotherapy.getImmunotherapyDetail(),
                immunotherapyDetailTier=immunotherapy.getImmunotherapyDetailTier(),
                treatmentPlanId=immunotherapy.getTreatmentPlanId(),
                treatmentPlanIdTier=immunotherapy.getTreatmentPlanIdTier(),
                courseNumber=immunotherapy.getCourseNumber(),
                courseNumberTier=immunotherapy.getCourseNumberTier()

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                immunotherapy.getLocalId(),
                immunotherapy.getParentContainer().getLocalId())

    def _readImmunotherapyTable(self):
        """
        Read the Immunotherapy table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Immunotherapy, clinical_metadata.Immunotherapy, dataset.addImmunotherapy)

    def _createCelltransplantTable(self):
        self.database.create_tables([models.Celltransplant])

    def insertCelltransplant(self, celltransplant):
        """
        Inserts the specified celltransplant into this repository.
        """
        try:
            models.Celltransplant.create(
                # Common fields
                id=celltransplant.getId(),
                datasetId=celltransplant.getParentContainer().getId(),
                created=celltransplant.getCreated(),
                updated=celltransplant.getUpdated(),
                name=celltransplant.getLocalId(),
                description=celltransplant.getDescription(),
                attributes=json.dumps(celltransplant.getAttributes()),

                # Unique fields
                patientId=celltransplant.getPatientId(),
                patientIdTier=celltransplant.getPatientIdTier(),
                startDate=celltransplant.getStartDate(),
                startDateTier=celltransplant.getStartDateTier(),
                cellSource=celltransplant.getCellSource(),
                cellSourceTier=celltransplant.getCellSourceTier(),
                donorType=celltransplant.getDonorType(),
                donorTypeTier=celltransplant.getDonorTypeTier(),
                treatmentPlanId=celltransplant.getTreatmentPlanId(),
                treatmentPlanIdTier=celltransplant.getTreatmentPlanIdTier(),
                courseNumber=celltransplant.getCourseNumber(),
                courseNumberTier=celltransplant.getCourseNumberTier()

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                celltransplant.getLocalId(),
                celltransplant.getParentContainer().getLocalId())

    def _readCelltransplantTable(self):
        """
        Read the Celltransplant table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Celltransplant, clinical_metadata.Celltransplant, dataset.addCelltransplant)

    def _createSlideTable(self):
        self.database.create_tables([models.Slide])

    def insertSlide(self, slide):
        """
        Inserts the specified slide into this repository.
        """
        try:
            models.Slide.create(
                # Common fields
                id=slide.getId(),
                datasetId=slide.getParentContainer().getId(),
                created=slide.getCreated(),
                updated=slide.getUpdated(),
                name=slide.getLocalId(),
                description=slide.getDescription(),
                attributes=json.dumps(slide.getAttributes()),

                # Unique fields
                patientId=slide.getPatientId(),
                patientIdTier=slide.getPatientIdTier(),
                sampleId=slide.getSampleId(),
                sampleIdTier=slide.getSampleIdTier(),
                slideId=slide.getSlideId(),
                slideIdTier=slide.getSlideIdTier(),
                slideOtherId=slide.getSlideOtherId(),
                slideOtherIdTier=slide.getSlideOtherIdTier(),
                lymphocyteInfiltrationPercent=slide.getLymphocyteInfiltrationPercent(),
                lymphocyteInfiltrationPercentTier=slide.getLymphocyteInfiltrationPercentTier(),
                tumorNucleiPercent=slide.getTumorNucleiPercent(),
                tumorNucleiPercentTier=slide.getTumorNucleiPercentTier(),
                monocyteInfiltrationPercent=slide.getMonocyteInfiltrationPercent(),
                monocyteInfiltrationPercentTier=slide.getMonocyteInfiltrationPercentTier(),
                normalCellsPercent=slide.getNormalCellsPercent(),
                normalCellsPercentTier=slide.getNormalCellsPercentTier(),
                tumorCellsPercent=slide.getTumorCellsPercent(),
                tumorCellsPercentTier=slide.getTumorCellsPercentTier(),
                stromalCellsPercent=slide.getStromalCellsPercent(),
                stromalCellsPercentTier=slide.getStromalCellsPercentTier(),
                eosinophilInfiltrationPercent=slide.getEosinophilInfiltrationPercent(),
                eosinophilInfiltrationPercentTier=slide.getEosinophilInfiltrationPercentTier(),
                neutrophilInfiltrationPercent=slide.getNeutrophilInfiltrationPercent(),
                neutrophilInfiltrationPercentTier=slide.getNeutrophilInfiltrationPercentTier(),
                granulocyteInfiltrationPercent=slide.getGranulocyteInfiltrationPercent(),
                granulocyteInfiltrationPercentTier=slide.getGranulocyteInfiltrationPercentTier(),
                necrosisPercent=slide.getNecrosisPercent(),
                necrosisPercentTier=slide.getNecrosisPercentTier(),
                inflammatoryInfiltrationPercent=slide.getInflammatoryInfiltrationPercent(),
                inflammatoryInfiltrationPercentTier=slide.getInflammatoryInfiltrationPercentTier(),
                proliferatingCellsNumber=slide.getProliferatingCellsNumber(),
                proliferatingCellsNumberTier=slide.getProliferatingCellsNumberTier(),
                sectionLocation=slide.getSectionLocation(),
                sectionLocationTier=slide.getSectionLocationTier(),

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                slide.getLocalId(),
                slide.getParentContainer().getLocalId())

    def _readSlideTable(self):
        """
        Read the Slide table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Slide, clinical_metadata.Slide, dataset.addSlide)

    def _createStudyTable(self):
        self.database.create_tables([models.Study])

    def insertStudy(self, study):
        """
        Inserts the specified study into this repository.
        """
        try:
            models.Study.create(
                # Common fields
                id=study.getId(),
                datasetId=study.getParentContainer().getId(),
                created=study.getCreated(),
                updated=study.getUpdated(),
                name=study.getLocalId(),
                description=study.getDescription(),
                attributes=json.dumps(study.getAttributes()),

                # Unique fields
                patientId=study.getPatientId(),
                patientIdTier=study.getPatientIdTier(),
                startDate=study.getStartDate(),
                startDateTier=study.getStartDateTier(),
                endDate=study.getEndDate(),
                endDateTier=study.getEndDateTier(),
                status=study.getStatus(),
                statusTier=study.getStatusTier(),
                recordingDate=study.getRecordingDate(),
                recordingDateTier=study.getRecordingDateTier(),

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                study.getLocalId(),
                study.getParentContainer().getLocalId())

    def _readStudyTable(self):
        """
        Read the Study table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Study, clinical_metadata.Study, dataset.addStudy)

    def _createLabtestTable(self):
        self.database.create_tables([models.Labtest])

    def insertLabtest(self, labtest):
        """
        Inserts the specified labtest into this repository.
        """
        try:
            models.Labtest.create(
                # Common fields
                id=labtest.getId(),
                datasetId=labtest.getParentContainer().getId(),
                created=labtest.getCreated(),
                updated=labtest.getUpdated(),
                name=labtest.getLocalId(),
                description=labtest.getDescription(),
                attributes=json.dumps(labtest.getAttributes()),

                # Unique fields
                patientId=labtest.getPatientId(),
                patientIdTier=labtest.getPatientIdTier(),
                startDate=labtest.getStartDate(),
                startDateTier=labtest.getStartDateTier(),
                collectionDate=labtest.getCollectionDate(),
                collectionDateTier=labtest.getCollectionDateTier(),
                endDate=labtest.getEndDate(),
                endDateTier=labtest.getEndDateTier(),
                eventType=labtest.getEventType(),
                eventTypeTier=labtest.getEventTypeTier(),
                testResults=labtest.getTestResults(),
                testResultsTier=labtest.getTestResultsTier(),
                timePoint=labtest.getTimePoint(),
                timePointTier=labtest.getTimePointTier(),
                recordingDate=labtest.getRecordingDate(),
                recordingDateTier=labtest.getRecordingDateTier(),

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                labtest.getLocalId(),
                labtest.getParentContainer().getLocalId())

    def _readLabtestTable(self):
        """
        Read the Labtest table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Labtest, clinical_metadata.Labtest, dataset.addLabtest)

    def _createExtractionTable(self):
        self.database.create_tables([models.Extraction])

    def insertExtraction(self, extraction):
        """
        Inserts the specified patient into this repository.
        """
        try:
            models.Extraction.create(
                # Common fields
                id=extraction.getId(),
                datasetId=extraction.getParentContainer().getId(),
                created=extraction.getCreated(),
                updated=extraction.getUpdated(),
                name=extraction.getLocalId(),
                description=extraction.getDescription(),
                attributes=json.dumps(extraction.getAttributes()),
                # Unique fields
                extractionId=extraction.getExtractionId(),
                extractionIdTier=extraction.getExtractionIdTier(),
                sampleId=extraction.getSampleId(),
                sampleIdTier=extraction.getSampleIdTier(),
                rnaBlood=extraction.getRnaBlood(),
                rnaBloodTier=extraction.getRnaBloodTier(),
                dnaBlood=extraction.getDnaBlood(),
                dnaBloodTier=extraction.getDnaBloodTier(),
                rnaTissue=extraction.getRnaTissue(),
                rnaTissueTier=extraction.getRnaTissueTier(),
                dnaTissue=extraction.getDnaTissue(),
                dnaTissueTier=extraction.getDnaTissueTier(),
                site=extraction.getSite(),
                siteTier=extraction.getSiteTier()
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                extraction.getLocalId(),
                extraction.getParentContainer().getLocalId())

    def _readExtractionTable(self):
        """
        Read the Extraction table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Extraction, pipeline_metadata.Extraction, dataset.addExtraction)

    def _createSequencingTable(self):
        self.database.create_tables([models.Sequencing])

    def insertSequencing(self, sequencing):
        """
        Inserts the specified patient into this repository.
        """
        try:
            models.Sequencing.create(
                # Common fields
                id=sequencing.getId(),
                datasetId=sequencing.getParentContainer().getId(),
                created=sequencing.getCreated(),
                updated=sequencing.getUpdated(),
                name=sequencing.getLocalId(),
                description=sequencing.getDescription(),
                attributes=json.dumps(sequencing.getAttributes()),
                # Unique fields
                sequencingId=sequencing.getSequencingId(),
                sequencingIdTier=sequencing.getSequencingIdTier(),
                sampleId=sequencing.getSampleId(),
                sampleIdTier=sequencing.getSampleIdTier(),
                dnaLibraryKit=sequencing.getDnaLibraryKit(),
                dnaLibraryKitTier=sequencing.getDnaLibraryKitTier(),
                dnaSeqPlatform=sequencing.getDnaSeqPlatform(),
                dnaSeqPlatformTier=sequencing.getDnaSeqPlatformTier(),
                dnaReadLength=sequencing.getDnaReadLength(),
                dnaReadLengthTier=sequencing.getDnaReadLengthTier(),
                rnaLibraryKit=sequencing.getRnaLibraryKit(),
                rnaLibraryKitTier=sequencing.getRnaLibraryKitTier(),
                rnaSeqPlatform=sequencing.getRnaSeqPlatform(),
                rnaSeqPlatformTier=sequencing.getRnaSeqPlatformTier(),
                rnaReadLength=sequencing.getRnaReadLength(),
                rnaReadLengthTier=sequencing.getRnaReadLengthTier(),
                pcrCycles=sequencing.getPcrCycles(),
                pcrCyclesTier=sequencing.getPcrCyclesTier(),
                extractionId=sequencing.getExtractionId(),
                extractionIdTier=sequencing.getExtractionIdTier(),
                site=sequencing.getSite(),
                siteTier=sequencing.getSiteTier()
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                sequencing.getLocalId(),
                sequencing.getParentContainer().getLocalId())

    def _readSequencingTable(self):
        """
        Read the Sequencing table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Sequencing, pipeline_metadata.Sequencing, dataset.addSequencing)

    def _createAlignmentTable(self):
        self.database.create_tables([models.Alignment])

    def insertAlignment(self, alignment):
        """
        Inserts the specified patient into this repository.
        """
        try:
            models.Alignment.create(
                # Common fields
                id=alignment.getId(),
                datasetId=alignment.getParentContainer().getId(),
                created=alignment.getCreated(),
                updated=alignment.getUpdated(),
                name=alignment.getLocalId(),
                description=alignment.getDescription(),
                attributes=json.dumps(alignment.getAttributes()),
                # Unique fields
                alignmentId=alignment.getAlignmentId(),
                alignmentIdTier=alignment.getAlignmentIdTier(),
                sampleId=alignment.getSampleId(),
                sampleIdTier=alignment.getSampleIdTier(),
                alignmentTool=alignment.getAlignmentTool(),
                alignmentToolTier=alignment.getAlignmentToolTier(),
                mergeTool=alignment.getMergeTool(),
                mergeToolTier=alignment.getMergeToolTier(),
                inHousePipeline=alignment.getInHousePipeline(),
                inHousePipelineTier=alignment.getInHousePipelineTier(),
                markDuplicates=alignment.getMarkDuplicates(),
                markDuplicatesTier=alignment.getMarkDuplicatesTier(),
                realignerTarget=alignment.getRealignerTarget(),
                realignerTargetTier=alignment.getRealignerTargetTier(),
                indelRealigner=alignment.getIndelRealigner(),
                indelRealignerTier=alignment.getIndelRealignerTier(),
                coverage=alignment.getCoverage(),
                coverageTier=alignment.getCoverageTier(),
                baseRecalibrator=alignment.getBaseRecalibrator(),
                baseRecalibratorTier=alignment.getBaseRecalibratorTier(),
                printReads=alignment.getPrintReads(),
                printReadsTier=alignment.getPrintReadsTier(),
                idxStats=alignment.getIdxStats(),
                idxStatsTier=alignment.getIdxStatsTier(),
                flagStat=alignment.getFlagStat(),
                flagStatTier=alignment.getFlagStatTier(),
                insertSizeMetrics=alignment.getInsertSizeMetrics(),
                insertSizeMetricsTier=alignment.getInsertSizeMetricsTier(),
                fastqc=alignment.getFastqc(),
                fastqcTier=alignment.getFastqcTier(),
                reference=alignment.getReference(),
                referenceTier=alignment.getReferenceTier(),
                sequencingId=alignment.getSequencingId(),
                sequencingIdTier=alignment.getSequencingIdTier(),
                site=alignment.getSite(),
                siteTier=alignment.getSiteTier()
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                alignment.getLocalId(),
                alignment.getParentContainer().getLocalId())

    def _readAlignmentTable(self):
        """
        Read the Alignment table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.Alignment, pipeline_metadata.Alignment, dataset.addAlignment)

    def _createVariantCallingTable(self):
        self.database.create_tables([models.VariantCalling])

    def insertVariantCalling(self, variantCalling):
        """
        Inserts the specified patient into this repository.
        """
        try:
            models.VariantCalling.create(
                # Common fields
                id=variantCalling.getId(),
                datasetId=variantCalling.getParentContainer().getId(),
                created=variantCalling.getCreated(),
                updated=variantCalling.getUpdated(),
                name=variantCalling.getLocalId(),
                description=variantCalling.getDescription(),
                attributes=json.dumps(variantCalling.getAttributes()),
                # Unique fields
                variantCallingId=variantCalling.getVariantCallingId(),
                variantCallingIdTier=variantCalling.getVariantCallingIdTier(),
                sampleId=variantCalling.getSampleId(),
                sampleIdTier=variantCalling.getSampleIdTier(),
                variantCaller=variantCalling.getVariantCaller(),
                variantCallerTier=variantCalling.getVariantCallerTier(),
                tabulate=variantCalling.getTabulate(),
                tabulateTier=variantCalling.getTabulateTier(),
                inHousePipeline=variantCalling.getInHousePipeline(),
                inHousePipelineTier=variantCalling.getInHousePipelineTier(),
                annotation=variantCalling.getAnnotation(),
                annotationTier=variantCalling.getAnnotationTier(),
                mergeTool=variantCalling.getMergeTool(),
                mergeToolTier=variantCalling.getMergeToolTier(),
                rdaToTab=variantCalling.getRdaToTab(),
                rdaToTabTier=variantCalling.getRdaToTabTier(),
                delly=variantCalling.getDelly(),
                dellyTier=variantCalling.getDellyTier(),
                postFilter=variantCalling.getPostFilter(),
                postFilterTier=variantCalling.getPostFilterTier(),
                clipFilter=variantCalling.getClipFilter(),
                clipFilterTier=variantCalling.getClipFilterTier(),
                cosmic=variantCalling.getCosmic(),
                cosmicTier=variantCalling.getCosmicTier(),
                dbSnp=variantCalling.getDbSnp(),
                dbSnpTier=variantCalling.getDbSnpTier(),
                alignmentId=variantCalling.getAlignmentId(),
                alignmentIdTier=variantCalling.getAlignmentIdTier(),
                site=variantCalling.getSite(),
                siteTier=variantCalling.getSiteTier()

            )
        except Exception:
            raise exceptions.DuplicateNameException(
                variantCalling.getLocalId(),
                variantCalling.getParentContainer().getLocalId())

    def _readVariantCallingTable(self):
        """
        Read the VariantCalling table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.VariantCalling, pipeline_metadata.VariantCalling, dataset.addVariantCalling)

    def _createFusionDetectionTable(self):
        self.database.create_tables([models.FusionDetection])

    def insertFusionDetection(self, fusionDetection):
        """
        Inserts the specified patient into this repository.
        """
        try:
            models.FusionDetection.create(
                # Common fields
                id=fusionDetection.getId(),
                datasetId=fusionDetection.getParentContainer().getId(),
                created=fusionDetection.getCreated(),
                updated=fusionDetection.getUpdated(),
                name=fusionDetection.getLocalId(),
                description=fusionDetection.getDescription(),
                attributes=json.dumps(fusionDetection.getAttributes()),
                # Unique fields
                fusionDetectionId=fusionDetection.getFusionDetectionId(),
                fusionDetectionIdTier=fusionDetection.getFusionDetectionIdTier(),
                sampleId=fusionDetection.getSampleId(),
                sampleIdTier=fusionDetection.getSampleIdTier(),
                inHousePipeline=fusionDetection.getInHousePipeline(),
                inHousePipelineTier=fusionDetection.getInHousePipelineTier(),
                svDetection=fusionDetection.getSvDetection(),
                svDetectionTier=fusionDetection.getSvDetectionTier(),
                fusionDetection=fusionDetection.getFusionDetection(),
                fusionDetectionTier=fusionDetection.getFusionDetectionTier(),
                realignment=fusionDetection.getRealignment(),
                realignmentTier=fusionDetection.getRealignmentTier(),
                annotation=fusionDetection.getAnnotation(),
                annotationTier=fusionDetection.getAnnotationTier(),
                genomeReference=fusionDetection.getGenomeReference(),
                genomeReferenceTier=fusionDetection.getGenomeReferenceTier(),
                geneModels=fusionDetection.getGeneModels(),
                geneModelsTier=fusionDetection.getGeneModelsTier(),
                alignmentId=fusionDetection.getAlignmentId(),
                alignmentIdTier=fusionDetection.getAlignmentIdTier(),
                site=fusionDetection.getSite(),
                siteTier=fusionDetection.getSiteTier()
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                fusionDetection.getLocalId(),
                fusionDetection.getParentContainer().getLocalId())

    def _readFusionDetectionTable(self):
        """
        Read the FusionDetection table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.FusionDetection, pipeline_metadata.FusionDetection, dataset.addFusionDetection)

    def _createExpressionAnalysisTable(self):
        self.database.create_tables([models.ExpressionAnalysis])

    def insertExpressionAnalysis(self, expressionAnalysis):
        """
        Inserts the specified patient into this repository.
        """
        try:
            models.ExpressionAnalysis.create(
                # Common fields
                id=expressionAnalysis.getId(),
                datasetId=expressionAnalysis.getParentContainer().getId(),
                created=expressionAnalysis.getCreated(),
                updated=expressionAnalysis.getUpdated(),
                name=expressionAnalysis.getLocalId(),
                description=expressionAnalysis.getDescription(),
                attributes=json.dumps(expressionAnalysis.getAttributes()),
                # Unique fields
                expressionAnalysisId=expressionAnalysis.getExpressionAnalysisId(),
                expressionAnalysisIdTier=expressionAnalysis.getExpressionAnalysisIdTier(),
                sampleId=expressionAnalysis.getSampleId(),
                sampleIdTier=expressionAnalysis.getSampleIdTier(),
                readLength=expressionAnalysis.getReadLength(),
                readLengthTier=expressionAnalysis.getReadLengthTier(),
                reference=expressionAnalysis.getReference(),
                referenceTier=expressionAnalysis.getReferenceTier(),
                alignmentTool=expressionAnalysis.getAlignmentTool(),
                alignmentToolTier=expressionAnalysis.getAlignmentToolTier(),
                bamHandling=expressionAnalysis.getBamHandling(),
                bamHandlingTier=expressionAnalysis.getBamHandlingTier(),
                expressionEstimation=expressionAnalysis.getExpressionEstimation(),
                expressionEstimationTier=expressionAnalysis.getExpressionEstimationTier(),
                sequencingId=expressionAnalysis.getSequencingId(),
                sequencingIdTier=expressionAnalysis.getSequencingIdTier(),
                site=expressionAnalysis.getSite(),
                siteTier=expressionAnalysis.getSiteTier()
            )
        except Exception:
            raise exceptions.DuplicateNameException(
                expressionAnalysis.getLocalId(),
                expressionAnalysis.getParentContainer().getLocalId())

    def _readExpressionAnalysisTable(self):
        """
        Read the ExpressionAnalysis table upon load
        """
        for dataset in self.getDatasets():
            self._readClinPipeTable(dataset, models.ExpressionAnalysis, pipeline_metadata.ExpressionAnalysis, dataset.addExpressionAnalysis)


    def initialise(self):
        """
        Initialise this data repository, creating any necessary directories
        and file paths.
        """
        self._checkWriteMode()
        self._createSystemTable()
        self._createDatasetTable()
        self._createPatientTable()
        self._createEnrollmentTable()
        self._createConsentTable()
        self._createDiagnosisTable()
        self._createSampleTable()
        self._createTreatmentTable()
        self._createOutcomeTable()
        self._createComplicationTable()
        self._createTumourboardTable()
        self._createChemotherapyTable()
        self._createRadiotherapyTable()
        self._createSurgeryTable()
        self._createImmunotherapyTable()
        self._createCelltransplantTable()
        self._createSlideTable()
        self._createStudyTable()
        self._createLabtestTable()
        self._createExtractionTable()
        self._createSequencingTable()
        self._createAlignmentTable()
        self._createVariantCallingTable()
        self._createFusionDetectionTable()
        self._createExpressionAnalysisTable()

    def exists(self):
        """
        Checks that this data repository exists in the file system and has the
        required structure.
        """
        # TODO should this invoke a full load operation or just check the DB
        # exists?
        return os.path.exists(self._dbFilename)

    def assertExists(self):
        if not self.exists():
            raise exceptions.RepoNotFoundException(self._dbFilename)

    def delete(self):
        """
        Delete this data repository by recursively removing all directories.
        This will delete ALL data stored within the repository!!
        """
        os.unlink(self._dbFilename)

    def load(self):
        """
        Loads this data repository into memory.
        """
        self._readSystemTable()
        self._readDatasetTable()
        self._readPatientTable()
        self._readEnrollmentTable()
        self._readConsentTable()
        self._readDiagnosisTable()
        self._readSampleTable()
        self._readTreatmentTable()
        self._readOutcomeTable()
        self._readComplicationTable()
        self._readTumourboardTable()
        self._readChemotherapyTable()
        self._readRadiotherapyTable()
        self._readSurgeryTable()
        self._readImmunotherapyTable()
        self._readCelltransplantTable()
        self._readSlideTable()
        self._readStudyTable()
        self._readLabtestTable()
        self._readExtractionTable()
        self._readSequencingTable()
        self._readAlignmentTable()
        self._readVariantCallingTable()
        self._readFusionDetectionTable()
        self._readExpressionAnalysisTable()
