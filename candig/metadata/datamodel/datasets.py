"""Dataset objects."""

import json
import candig.metadata.datamodel as datamodel
import candig.metadata.exceptions as exceptions
from candig.metadata.ontology import OntologyParser, OntObjectInitiator

import candig.metadata.pb as pb
import candig.metadata.protocol as protocol


DUO_BASIC_OWL = 'https://raw.githubusercontent.com/EBISPOT/DUO/master/src/ontology/duo-basic.owl'


class Dataset(datamodel.DatamodelObject):
    """The base class of datasets containing just metadata."""

    compoundIdClass = datamodel.DatasetCompoundId

    def __init__(self, localId: str):
        """
        Initialize the dataset instance.

        Parameters
        ----------
        localId : str
            Base64 coded name.

        Returns
        -------
        None.

        """
        super(Dataset, self).__init__(None, localId)
        self._description = None
        self._info = []

        # Patient
        self._patientIds = []
        self._patientIdMap = {}
        self._patientNameMap = {}

        # Enrollment
        self._enrollmentIds = []
        self._enrollmentIdMap = {}
        self._enrollmentNameMap = {}

        # Consent
        self._consentIds = []
        self._consentIdMap = {}
        self._consentNameMap = {}

        # Diagnosis
        self._diagnosisIds = []
        self._diagnosisIdMap = {}
        self._diagnosisNameMap = {}

        # Sample
        self._sampleIds = []
        self._sampleIdMap = {}
        self._sampleNameMap = {}

        # Treatment
        self._treatmentIds = []
        self._treatmentIdMap = {}
        self._treatmentNameMap = {}

        # Outcome
        self._outcomeIds = []
        self._outcomeIdMap = {}
        self._outcomeNameMap = {}

        # Complication
        self._complicationIds = []
        self._complicationIdMap = {}
        self._complicationNameMap = {}

        # Tumourboard
        self._tumourboardIds = []
        self._tumourboardIdMap = {}
        self._tumourboardNameMap = {}

        # Chemotherapy
        self._chemotherapyIds = []
        self._chemotherapyIdMap = {}
        self._chemotherapyNameMap = {}

        # Radiotherapy
        self._radiotherapyIds = []
        self._radiotherapyIdMap = {}
        self._radiotherapyNameMap = {}

        # Surgery
        self._surgeryIds = []
        self._surgeryIdMap = {}
        self._surgeryNameMap = {}

        # Immunotherapy
        self._immunotherapyIds = []
        self._immunotherapyIdMap = {}
        self._immunotherapyNameMap = {}

        # Celltransplant
        self._celltransplantIds = []
        self._celltransplantIdMap = {}
        self._celltransplantNameMap = {}

        # Slide
        self._slideIds = []
        self._slideIdMap = {}
        self._slideNameMap = {}

        # Study
        self._studyIds = []
        self._studyIdMap = {}
        self._studyNameMap = {}

        # Labtest
        self._labtestIds = []
        self._labtestIdMap = {}
        self._labtestNameMap = {}

        # Extraction
        self._extractionIds = []
        self._extractionIdMap = {}
        self._extractionNameMap = {}

        # Sequencing
        self._sequencingIds = []
        self._sequencingIdMap = {}
        self._sequencingNameMap = {}

        # Alignment
        self._alignmentIds = []
        self._alignmentIdMap = {}
        self._alignmentNameMap = {}

        # VariantCalling
        self._variantCallingIds = []
        self._variantCallingIdMap = {}
        self._variantCallingNameMap = {}

        # FusionDetection
        self._fusionDetectionIds = []
        self._fusionDetectionIdMap = {}
        self._fusionDetectionNameMap = {}

        # Extraction
        self._expressionAnalysisIds = []
        self._expressionAnalysisIdMap = {}
        self._expressionAnalysisNameMap = {}

    def populateFromRow(self, dataset):
        """
        Populate dataset instance from a specified database row.

        Parameters
        ----------
        dataset : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self._description = dataset.description
        self.setAttributesJson(dataset.attributes)

    def populateDuoInfo(self, dataset):
        """Populate DUO info by attaching definition to the DUO term."""
        if dataset.info is not None:
            parsed_info = json.loads(dataset.info)

            ont = OntObjectInitiator(DUO_BASIC_OWL).get_ont()

            results = []

            for term in parsed_info:
                term_parser = OntologyParser(ont, term["id"])
                term["term_id"] = term["id"]
                term["shorthand"] = term_parser.get_shorthand()
                term["definition"] = term_parser.get_definition()
                term["term"] = term_parser.get_name()

                results.append(term)

            self._info = results
        else:
            self._info = []

    def setDescription(self, description):
        """Set the description for this dataset to the specified value."""
        self._description = description

    def setDuoInfo(self, duo_list):
        """Set the DUO list of this dataset."""
        self._info = duo_list

    def addVariantSet(self, variantSet):
        """Add the specified variantSet to this dataset."""
        id_ = variantSet.getId()
        self._variantSetIdMap[id_] = variantSet
        self._variantSetNameMap[variantSet.getLocalId()] = variantSet
        self._variantSetIds.append(id_)

    def addBiosample(self, biosample):
        """Add the specified biosample to this dataset."""
        id_ = biosample.getId()
        self._biosampleIdMap[id_] = biosample
        self._biosampleIds.append(id_)
        self._biosampleNameMap[biosample.getName()] = biosample

    def addIndividual(self, individual):
        """Add the specified individual to this dataset."""
        id_ = individual.getId()
        self._individualIdMap[id_] = individual
        self._individualIds.append(id_)
        self._individualNameMap[individual.getName()] = individual

    def addPatient(self, patient):
        """Add the specified patient to this dataset."""
        id_ = patient.getId()
        self._patientIdMap[id_] = patient
        self._patientIds.append(id_)
        self._patientNameMap[patient.getName()] = patient

    def addEnrollment(self, enrollment):
        """Add the specified enrollment to this dataset."""
        id_ = enrollment.getId()
        self._enrollmentIdMap[id_] = enrollment
        self._enrollmentIds.append(id_)
        self._enrollmentNameMap[enrollment.getName()] = enrollment

    def addConsent(self, consent):
        """Add the specified consent to this dataset."""
        id_ = consent.getId()
        self._consentIdMap[id_] = consent
        self._consentIds.append(id_)
        self._consentNameMap[consent.getName()] = consent

    def addDiagnosis(self, diagnosis):
        """Add the specified diagnosis to this dataset."""
        id_ = diagnosis.getId()
        self._diagnosisIdMap[id_] = diagnosis
        self._diagnosisIds.append(id_)
        self._diagnosisNameMap[diagnosis.getName()] = diagnosis

    def addSample(self, sample):
        """Add the specified sample to this dataset."""
        id_ = sample.getId()
        self._sampleIdMap[id_] = sample
        self._sampleIds.append(id_)
        self._sampleNameMap[sample.getName()] = sample

    def addTreatment(self, treatment):
        """Add the specified treatment to this dataset."""
        id_ = treatment.getId()
        self._treatmentIdMap[id_] = treatment
        self._treatmentIds.append(id_)
        self._treatmentNameMap[treatment.getName()] = treatment

    def addOutcome(self, outcome):
        """Add the specified outcome to this dataset."""
        id_ = outcome.getId()
        self._outcomeIdMap[id_] = outcome
        self._outcomeIds.append(id_)
        self._outcomeNameMap[outcome.getName()] = outcome

    def addComplication(self, complication):
        """Add the specified complication to this dataset."""
        id_ = complication.getId()
        self._complicationIdMap[id_] = complication
        self._complicationIds.append(id_)
        self._complicationNameMap[complication.getName()] = complication

    def addTumourboard(self, tumourboard):
        """Add the specified tumourboard to this dataset."""
        id_ = tumourboard.getId()
        self._tumourboardIdMap[id_] = tumourboard
        self._tumourboardIds.append(id_)
        self._tumourboardNameMap[tumourboard.getName()] = tumourboard

    def addChemotherapy(self, chemotherapy):
        """Add the specified chemotherapy to this dataset."""
        id_ = chemotherapy.getId()
        self._chemotherapyIdMap[id_] = chemotherapy
        self._chemotherapyIds.append(id_)
        self._chemotherapyNameMap[chemotherapy.getName()] = chemotherapy

    def addRadiotherapy(self, radiotherapy):
        """Add the specified radiotherapy to this dataset."""
        id_ = radiotherapy.getId()
        self._radiotherapyIdMap[id_] = radiotherapy
        self._radiotherapyIds.append(id_)
        self._radiotherapyNameMap[radiotherapy.getName()] = radiotherapy

    def addSurgery(self, surgery):
        """Add the specified surgery to this dataset."""
        id_ = surgery.getId()
        self._surgeryIdMap[id_] = surgery
        self._surgeryIds.append(id_)
        self._surgeryNameMap[surgery.getName()] = surgery

    def addImmunotherapy(self, immunotherapy):
        """Add the specified immunotherapy to this dataset."""
        id_ = immunotherapy.getId()
        self._immunotherapyIdMap[id_] = immunotherapy
        self._immunotherapyIds.append(id_)
        self._immunotherapyNameMap[immunotherapy.getName()] = immunotherapy

    def addCelltransplant(self, celltransplant):
        """Add the specified celltransplant to this dataset."""
        id_ = celltransplant.getId()
        self._celltransplantIdMap[id_] = celltransplant
        self._celltransplantIds.append(id_)
        self._celltransplantNameMap[celltransplant.getName()] = celltransplant

    def addSlide(self, slide):
        """Add the specified slide to this dataset."""
        id_ = slide.getId()
        self._slideIdMap[id_] = slide
        self._slideIds.append(id_)
        self._slideNameMap[slide.getName()] = slide

    def addStudy(self, study):
        """Add the specified study to this dataset."""
        id_ = study.getId()
        self._studyIdMap[id_] = study
        self._studyIds.append(id_)
        self._studyNameMap[study.getName()] = study

    def addLabtest(self, labtest):
        """Add the specified labtest to this dataset."""
        id_ = labtest.getId()
        self._labtestIdMap[id_] = labtest
        self._labtestIds.append(id_)
        self._labtestNameMap[labtest.getName()] = labtest

    def addExtraction(self, extraction):
        """Add the specified extraction to this dataset."""
        id_ = extraction.getId()
        self._extractionIdMap[id_] = extraction
        self._extractionIds.append(id_)
        self._extractionNameMap[extraction.getName()] = extraction

    def addSequencing(self, sequencing):
        """Add the specified extraction to this dataset."""
        id_ = sequencing.getId()
        self._sequencingIdMap[id_] = sequencing
        self._sequencingIds.append(id_)
        self._sequencingNameMap[sequencing.getName()] = sequencing

    def addAlignment(self, alignment):
        """Add the specified extraction to this dataset."""
        id_ = alignment.getId()
        self._alignmentIdMap[id_] = alignment
        self._alignmentIds.append(id_)
        self._alignmentNameMap[alignment.getName()] = alignment

    def addVariantCalling(self, variantCalling):
        """Add the specified extraction to this dataset."""
        id_ = variantCalling.getId()
        self._variantCallingIdMap[id_] = variantCalling
        self._variantCallingIds.append(id_)
        self._variantCallingNameMap[variantCalling.getName()] = variantCalling

    def addFusionDetection(self, fusionDetection):
        """Add the specified extraction to this dataset."""
        id_ = fusionDetection.getId()
        self._fusionDetectionIdMap[id_] = fusionDetection
        self._fusionDetectionIds.append(id_)
        self._fusionDetectionNameMap[
            fusionDetection.getName()] = fusionDetection

    def addExpressionAnalysis(self, expressionAnalysis):
        """Add the specified extraction to this dataset."""
        id_ = expressionAnalysis.getId()
        self._expressionAnalysisIdMap[id_] = expressionAnalysis
        self._expressionAnalysisIds.append(id_)
        self._expressionAnalysisNameMap[
            expressionAnalysis.getName()] = expressionAnalysis

    def toProtocolElement(self, tier=0):
        """
        Populate dataset.

        Parameters
        ----------
        tier : TYPE, optional
            DESCRIPTION. The default is 0.

        Returns
        -------
        dataset : TYPE
            DESCRIPTION.

        """
        dataset = protocol.Dataset()
        dataset.id = self.getId()
        dataset.name = pb.string(self.getLocalId())
        dataset.description = pb.string(self.getDescription())
        # Populate DUO info by extending the list
        self.serializeAttributes(dataset)

        return dataset

    def getPatients(self):
        """Return the list of patients in this dataset."""
        return [self._patientIdMap[id_] for id_ in self._patientIds]

    def getPatientByName(self, name):
        """
        Return a Patient record with the specified name.

        or raises a
        PatientNameNotFoundException if it does not exist.
        """
        if name not in self._patientNameMap:
            raise exceptions.PatientNameNotFoundException(name)
        return self._patientNameMap[name]

    def getPatient(self, id_):
        """
        Return a Patient record with the specified id.

        or raises PatientNotFoundException otherwise.
        """
        if id_ not in self._patientIdMap:
            raise exceptions.PatientNotFoundException(id_)
        return self._patientIdMap[id_]

    def getEnrollments(self):
        """Return the list of enrollments in this dataset."""
        return [self._enrollmentIdMap[id_] for id_ in self._enrollmentIds]

    def getEnrollmentByName(self, name):
        """
        Return an Enrollment record with the specified name.

        Or raises EnrollmentNameNotFoundException if it does not exist.
        """
        if name not in self._enrollmentNameMap:
            raise exceptions.EnrollmentNameNotFoundException(name)
        return self._enrollmentNameMap[name]

    def getEnrollment(self, id_):
        """Return the Enrollment record with the specified id.

        Or raises EnrollmentNotFoundException otherwise.
        """
        if id_ not in self._enrollmentIdMap:
            raise exceptions.EnrollmentNotFoundException(id_)
        return self._enrollmentIdMap[id_]

    def getConsents(self):
        """Return the list of consents in this dataset."""
        return [self._consentIdMap[id_] for id_ in self._consentIds]

    def getConsentByName(self, name):
        """
        Return a Consent record with the specified name.

        Or raises ConsentNameNotFoundException if it does not exist.
        """
        if name not in self._consentNameMap:
            raise exceptions.ConsentNameNotFoundException(name)
        return self._consentNameMap[name]

    def getConsent(self, id_):
        """Return the Consent with the specified id.

        Or raises ConsentNotFoundException otherwise.
        """
        if id_ not in self._consentIdMap:
            raise exceptions.ConsentNotFoundException(id_)
        return self._consentIdMap[id_]

    def getDiagnoses(self):
        """Return the list of diagnoses in this dataset."""
        return [self._diagnosisIdMap[id_] for id_ in self._diagnosisIds]

    def getDiagnosisByName(self, name):
        """
        Return a Diagnosis record with the specified name.

        Or raises DiagnosisNameNotFoundException if it does not exist.
        """
        if name not in self._diagnosisNameMap:
            raise exceptions.DiagnosisNameNotFoundException(name)
        return self._diagnosisNameMap[name]

    def getDiagnosis(self, id_):
        """Return a Diagnosis record with the specified id.

        Or raises DiagnosisNotFoundException otherwise.
        """
        if id_ not in self._diagnosisIdMap:
            raise exceptions.DiagnosisNotFoundException(id_)
        return self._diagnosisIdMap[id_]

    def getSamples(self):
        """Return the list of samples in this dataset."""
        return [self._sampleIdMap[id_] for id_ in self._sampleIds]

    def getSampleByName(self, name):
        """Return a Sample record with the specified name.

        Or raises SampleNameNotFoundException if it does not exist.
        """
        if name not in self._sampleNameMap:
            raise exceptions.SampleNameNotFoundException(name)
        return self._sampleNameMap[name]

    def getSample(self, id_):
        """Return a Sample record with the specified id.

        Or raises SampleNotFoundException otherwise.
        """
        if id_ not in self._sampleIdMap:
            raise exceptions.SampleNotFoundException(id_)
        return self._sampleIdMap[id_]

    def getTreatments(self):
        """Return the list of treatments in this dataset."""
        return [self._treatmentIdMap[id_] for id_ in self._treatmentIds]

    def getTreatmentByName(self, name):
        """
        Return a Treatment record with the specified name.

        Or raises TreatmentNameNotFoundException if it does not exist.
        """
        if name not in self._treatmentNameMap:
            raise exceptions.TreatmentNameNotFoundException(name)
        return self._treatmentNameMap[name]

    def getTreatment(self, id_):
        """Return a Treatment record with the specified id.

        Or raises TreatmentNotFoundException otherwise.
        """
        if id_ not in self._treatmentIdMap:
            raise exceptions.TreatmentNotFoundException(id_)
        return self._treatmentIdMap[id_]

    def getOutcomes(self):
        """Return the list of outcomes in this dataset."""
        return [self._outcomeIdMap[id_] for id_ in self._outcomeIds]

    def getOutcomeByName(self, name):
        """Return an Outcome record with the specified name.

        Or raises OutcomeNameNotFoundException if it does not exist.
        """
        if name not in self._outcomeNameMap:
            raise exceptions.OutcomeNameNotFoundException(name)
        return self._outcomeNameMap[name]

    def getOutcome(self, id_):
        """Return an Outcome record with the specified id.

        Or raises OutcomeNotFoundException otherwise.
        """
        if id_ not in self._outcomeIdMap:
            raise exceptions.OutcomeNotFoundException(id_)
        return self._outcomeIdMap[id_]

    def getComplications(self):
        """Return the list of complications in this dataset."""
        return [self._complicationIdMap[id_] for id_ in self._complicationIds]

    def getComplicationByName(self, name):
        """Return a Complication record with the specified name.

        Or raises ComplicationNameNotFoundException if it does not exist.
        """
        if name not in self._complicationNameMap:
            raise exceptions.ComplicationNameNotFoundException(name)
        return self._complicationNameMap[name]

    def getComplication(self, id_):
        """Return a Complication record with the specified id.

        Or raises ComplicationNotFoundException otherwise.
        """
        if id_ not in self._complicationIdMap:
            raise exceptions.ComplicationNotFoundException(id_)
        return self._complicationIdMap[id_]

    def getTumourboards(self):
        """Return the list of tumourboards in this dataset."""
        return [self._tumourboardIdMap[id_] for id_ in self._tumourboardIds]

    def getTumourboardByName(self, name):
        """
        Return a Tumourboard record with the specified name.

        Or raises TumourboardNameNotFoundException if it does not exist.
        """
        if name not in self._tumourboardNameMap:
            raise exceptions.TumourboardNameNotFoundException(name)
        return self._tumourboardNameMap[name]

    def getTumourboard(self, id_):
        """Return a Tumourboard record with the specified id.

        Or raises TumourboardNotFoundException otherwise.
        """
        if id_ not in self._tumourboardIdMap:
            raise exceptions.TumourboardNotFoundException(id_)
        return self._tumourboardIdMap[id_]

    def getChemotherapies(self):
        """Return the list of chemotherapys in this dataset."""
        return [self._chemotherapyIdMap[id_] for id_ in self._chemotherapyIds]

    def getChemotherapyByName(self, name):
        """
        Return a Chemotherapy record with the specified name.

        Or raises ChemotherapyNameNotFoundException if it does not exist.
        """
        if name not in self._chemotherapyNameMap:
            raise exceptions.ChemotherapyNameNotFoundException(name)
        return self._chemotherapyNameMap[name]

    def getChemotherapy(self, id_):
        """Return a Chemotherapy record with the specified id.

        Or raises ChemotherapyNotFoundException otherwise.
        """
        if id_ not in self._chemotherapyIdMap:
            raise exceptions.ChemotherapyNotFoundException(id_)
        return self._chemotherapyIdMap[id_]

    def getRadiotherapies(self):
        """Return the list of radiotherapys in this dataset."""
        return [self._radiotherapyIdMap[id_] for id_ in self._radiotherapyIds]

    def getRadiotherapyByName(self, name):
        """Return an radiotherapy with the specified name.

        Or raises RadiotherapyNameNotFoundException if it does not exist.
        """
        if name not in self._radiotherapyNameMap:
            raise exceptions.RadiotherapyNameNotFoundException(name)
        return self._radiotherapyNameMap[name]

    def getRadiotherapy(self, id_):
        """Return the Radiotherapy with the specified id.

        Or raises RadiotherapyNotFoundException otherwise.
        """
        if id_ not in self._radiotherapyIdMap:
            raise exceptions.RadiotherapyNotFoundException(id_)
        return self._radiotherapyIdMap[id_]

    def getSurgeries(self):
        """Return the list of surgerys in this dataset."""
        return [self._surgeryIdMap[id_] for id_ in self._surgeryIds]

    def getSurgeryByName(self, name):
        """Return a Surgery record with the specified name.

        Or raises SurgeryNameNotFoundException if it does not exist.
        """
        if name not in self._surgeryNameMap:
            raise exceptions.SurgeryNameNotFoundException(name)
        return self._surgeryNameMap[name]

    def getSurgery(self, id_):
        """Return a Surgery record with the specified id.

        Or raises SurgeryNotFoundException otherwise.
        """
        if id_ not in self._surgeryIdMap:
            raise exceptions.SurgeryNotFoundException(id_)
        return self._surgeryIdMap[id_]

    def getImmunotherapies(self):
        """Return the list of immunotherapys in this dataset."""
        return [self._immunotherapyIdMap[id_]
                for id_ in self._immunotherapyIds]

    def getImmunotherapyByName(self, name):
        """Return an Immunotherapy record with the specified name.

        Or raises ImmunotherapyNameNotFoundException if it does not exist.
        """
        if name not in self._immunotherapyNameMap:
            raise exceptions.ImmunotherapyNameNotFoundException(name)
        return self._immunotherapyNameMap[name]

    def getImmunotherapy(self, id_):
        """Return the Immunotherapy with the specified id.

        Or raises ImmunotherapyNotFoundException otherwise.
        """
        if id_ not in self._immunotherapyIdMap:
            raise exceptions.ImmunotherapyNotFoundException(id_)
        return self._immunotherapyIdMap[id_]

    def getCelltransplants(self):
        """Return the list of celltransplants in this dataset."""
        return [self._celltransplantIdMap[id_]
                for id_ in self._celltransplantIds]

    def getCelltransplantByName(self, name):
        """Return a Celltransplant record with the specified name.

        Or raises CelltransplantNameNotFoundException if it does not exist.
        """
        if name not in self._celltransplantNameMap:
            raise exceptions.CelltransplantNameNotFoundException(name)
        return self._celltransplantNameMap[name]

    def getCelltransplant(self, id_):
        """Return a Celltransplant record with the specified id.

        Or raises CelltransplantNotFoundException otherwise.
        """
        if id_ not in self._celltransplantIdMap:
            raise exceptions.CelltransplantNotFoundException(id_)
        return self._celltransplantIdMap[id_]

    def getSlides(self):
        """Return the list of slides in this dataset."""
        return [self._slideIdMap[id_] for id_ in self._slideIds]

    def getSlideByName(self, name):
        """Return a Slide with the specified name.

        Or raises SlideNameNotFoundException if it does not exist.
        """
        if name not in self._slideNameMap:
            raise exceptions.SlideNameNotFoundException(name)
        return self._slideNameMap[name]

    def getSlide(self, id_):
        """Return a Slide record with the specified id.

        Or raises SlideNotFoundException otherwise.
        """
        if id_ not in self._slideIdMap:
            raise exceptions.SlideNotFoundException(id_)
        return self._slideIdMap[id_]

    def getStudies(self):
        """Return the list of studys in this dataset."""
        return [self._studyIdMap[id_] for id_ in self._studyIds]

    def getStudyByName(self, name):
        """Return a Study record with the specified name.

        Or raises StudyNameNotFoundException if it does not exist.
        """
        if name not in self._studyNameMap:
            raise exceptions.StudyNameNotFoundException(name)
        return self._studyNameMap[name]

    def getStudy(self, id_):
        """Return a Study record with the specified id.

        Or raises StudyNotFoundException otherwise.
        """
        if id_ not in self._studyIdMap:
            raise exceptions.StudyNotFoundException(id_)
        return self._studyIdMap[id_]

    def getLabtests(self):
        """Return the list of labtests in this dataset."""
        return [self._labtestIdMap[id_] for id_ in self._labtestIds]

    def getLabtestByName(self, name):
        """Return a Labtest record with the specified name.

        Or raises LabtestNameNotFoundException if it does not exist.
        """
        if name not in self._labtestNameMap:
            raise exceptions.LabtestNameNotFoundException(name)
        return self._labtestNameMap[name]

    def getLabtest(self, id_):
        """Return a Labtest record with the specified id.

        Or raises LabtestNotFoundException otherwise.
        """
        if id_ not in self._labtestIdMap:
            raise exceptions.LabtestNotFoundException(id_)
        return self._labtestIdMap[id_]

    def getExtractions(self):
        """Return the list of extractions in this dataset."""
        return [self._extractionIdMap[id_] for id_ in self._extractionIds]

    def getExtractionByName(self, name):
        """Return an Extraction record with the specified name.

        Or raises extractionNameNotFoundException if it does not exist.
        """
        if name not in self._extractionNameMap:
            raise exceptions.ObjectNameNotFoundException(name)
        return self._extractionNameMap[name]

    def getExtraction(self, id_):
        """Return an Extraction record with the specified id.

        Or raises extractionNotFoundException otherwise.
        """
        if id_ not in self._extractionIdMap:
            raise exceptions.ObjectNotFoundException(id_)
        return self._extractionIdMap[id_]

    def getSequencings(self):
        """Return the list of sequencings in this dataset."""
        return [self._sequencingIdMap[id_] for id_ in self._sequencingIds]

    def getSequencingByName(self, name):
        """Return a Sequencing record with the specified name.

        Or raises sequencingNameNotFoundException if it does not exist.
        """
        if name not in self._sequencingNameMap:
            raise exceptions.ObjectNameNotFoundException(name)
        return self._sequencingNameMap[name]

    def getSequencing(self, id_):
        """Return a Sequencing record with the specified id.

        Or raises sequencingNotFoundException otherwise.
        """
        if id_ not in self._sequencingIdMap:
            raise exceptions.ObjectNotFoundException(id_)
        return self._sequencingIdMap[id_]

    def getAlignments(self):
        """Return the list of alignments in this dataset."""
        return [self._alignmentIdMap[id_] for id_ in self._alignmentIds]

    def getAlignmentByName(self, name):
        """Return an Alignment record with the specified name.

        Or raises alignmentNameNotFoundException if it does not exist.
        """
        if name not in self._alignmentNameMap:
            raise exceptions.ObjectNameNotFoundException(name)
        return self._alignmentNameMap[name]

    def getAlignment(self, id_):
        """Return an Alignment record with the specified id.

        Or raises alignmentNotFoundException otherwise.
        """
        if id_ not in self._alignmentIdMap:
            raise exceptions.ObjectNotFoundException(id_)
        return self._alignmentIdMap[id_]

    def getVariantCallings(self):
        """Return the list of variantCallings in this dataset."""
        return [self._variantCallingIdMap[id_]
                for id_ in self._variantCallingIds]

    def getVariantCallingByName(self, name):
        """Return a VariantCalling record with the specified name.

        Or raises variantCallingNameNotFoundException if it does not exist.
        """
        if name not in self._variantCallingNameMap:
            raise exceptions.ObjectNameNotFoundException(name)
        return self._variantCallingNameMap[name]

    def getVariantCalling(self, id_):
        """Return a variantCalling record with the specified id.

        Or raises variantCallingNotFoundException otherwise.
        """
        if id_ not in self._variantCallingIdMap:
            raise exceptions.ObjectNotFoundException(id_)
        return self._variantCallingIdMap[id_]

    def getFusionDetections(self):
        """Return the list of fusionDetections in this dataset."""
        return [self._fusionDetectionIdMap[id_]
                for id_ in self._fusionDetectionIds]

    def getFusionDetectionByName(self, name):
        """Return a fusionDetection record with the specified name.

        Or raises fusionDetectionNameNotFoundException if it does not exist.
        """
        if name not in self._fusionDetectionNameMap:
            raise exceptions.ObjectNameNotFoundException(name)
        return self._fusionDetectionNameMap[name]

    def getFusionDetection(self, id_):
        """Return a fusionDetection record with the specified id.

        Or raises fusionDetectionNotFoundException otherwise.
        """
        if id_ not in self._fusionDetectionIdMap:
            raise exceptions.ObjectNotFoundException(id_)
        return self._fusionDetectionIdMap[id_]

    def getExpressionAnalyses(self):
        """Return the list of expressionAnalyses in this dataset."""
        return [self._expressionAnalysisIdMap[id_]
                for id_ in self._expressionAnalysisIds]

    def getExpressionAnalysisByName(self, name):
        """Return an expressionAnalysis record with the specified name.

        Or raises expressionAnalysisNameNotFoundException if it does not exist.
        """
        if name not in self._expressionAnalysisNameMap:
            raise exceptions.ObjectNameNotFoundException(name)
        return self._expressionAnalysisNameMap[name]

    def getExpressionAnalysis(self, id_):
        """Return an expressionAnalysis record with the specified id.

        Or raises expressionAnalysisNotFoundException otherwise.
        """
        if id_ not in self._expressionAnalysisIdMap:
            raise exceptions.ObjectNotFoundException(id_)
        return self._expressionAnalysisIdMap[id_]

    def getInfo(self):
        """Return the info of this dataset."""
        return self._info

    def getDescription(self):
        """Return the free text description of this dataset."""
        return self._description


class SimulatedDataset(Dataset):
    """A simulated dataset."""

    def __init__(
            self, localId, randomSeed=0):
        """
        Initialize the simulated dataset object.

        Parameters
        ----------
        localId : TYPE
            DESCRIPTION.
        randomSeed : TYPE, optional
            DESCRIPTION. The default is 0.

        Returns
        -------
        None.

        """
        super(SimulatedDataset, self).__init__(localId)
        self._description = "Simulated dataset {}".format(localId)
        self._info = [{"id": "DUO:0000042"}]

        # TODO create a simulated Ontology
