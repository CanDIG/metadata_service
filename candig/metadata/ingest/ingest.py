#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ingest.py - Creates a new dataset and parses metadata information into it.

It populates all metadata tables.

Usage:
  metadata_ingest.py <repo_filename> <dataset_name> <metadata_json>

Options:
  -h --help        Show this screen
  -v --version     Version
  <repo_filename>  Repository filename and path information
  <dataset_name>   Dataset name = project name
  <metadata_json>  Metadata json object filename and path information

"""

import json
import os
from docopt import docopt

from candig.metadata.ingest import _version as version

import candig.metadata.datarepo as repo
import candig.metadata.exceptions as exceptions

from candig.metadata.datamodel.datasets import Dataset
from candig.metadata.datamodel.clinical_metadata import Patient
from candig.metadata.datamodel.clinical_metadata import Enrollment
from candig.metadata.datamodel.clinical_metadata import Consent
from candig.metadata.datamodel.clinical_metadata import Diagnosis
from candig.metadata.datamodel.clinical_metadata import Sample
from candig.metadata.datamodel.clinical_metadata import Treatment
from candig.metadata.datamodel.clinical_metadata import Outcome
from candig.metadata.datamodel.clinical_metadata import Complication
from candig.metadata.datamodel.clinical_metadata import Tumourboard
from candig.metadata.datamodel.clinical_metadata import Chemotherapy
from candig.metadata.datamodel.clinical_metadata import Radiotherapy
from candig.metadata.datamodel.clinical_metadata import Immunotherapy
from candig.metadata.datamodel.clinical_metadata import Surgery
from candig.metadata.datamodel.clinical_metadata import Celltransplant
from candig.metadata.datamodel.clinical_metadata import Slide
from candig.metadata.datamodel.clinical_metadata import Study
from candig.metadata.datamodel.clinical_metadata import Labtest
from candig.metadata.datamodel.pipeline_metadata import Extraction
from candig.metadata.datamodel.pipeline_metadata import Sequencing
from candig.metadata.datamodel.pipeline_metadata import Alignment
from candig.metadata.datamodel.pipeline_metadata import VariantCalling
from candig.metadata.datamodel.pipeline_metadata import FusionDetection
from candig.metadata.datamodel.pipeline_metadata import ExpressionAnalysis


class CandigRepo(object):
    """Handles the interaction with the database repo."""

    def __init__(self, filename: str):
        """
        Initialize metadata maps.

        Parameters
        ==========
        filename: str
            Filename and path information of the repository.

        """
        self._filename = filename
        self._repo = None

        self.clinical_metadata_map = {
            'Patient': {
                'table': Patient,
                'local_id': ['patientId'],
                'repo_add': self.add_patient
            },
            'Enrollment': {
                'table': Enrollment,
                'local_id': ["patientId", "enrollmentApprovalDate"],
                'repo_add': self.add_enrollment
            },
            'Consent': {
                'table': Consent,
                'local_id': ["patientId", "consentDate"],
                'repo_add': self.add_consent
            },
            'Diagnosis': {
                'table': Diagnosis,
                'local_id': ["patientId", "diagnosisDate"],
                'repo_add': self.add_diagnosis
            },
            'Sample': {
                'table': Sample,
                'local_id': ["patientId", "sampleId"],
                'repo_add': self.add_sample
            },
            'Treatment': {
                'table': Treatment,
                'local_id': ["patientId", "startDate"],
                'repo_add': self.add_treatment
            },
            'Outcome': {
                'table': Outcome,
                'local_id': ["patientId", "dateOfAssessment"],
                'repo_add': self.add_outcome
            },
            'Complication': {
                'table': Complication,
                'local_id': ["patientId", "date"],
                'repo_add': self.add_complication
            },
            'Tumourboard': {
                'table': Tumourboard,
                'local_id': ["patientId", "dateOfMolecularTumorBoard"],
                'repo_add': self.add_tumourboard
            },
            'Chemotherapy': {
                'table': Chemotherapy,
                'local_id': ["patientId", "treatmentPlanId", "systematicTherapyAgentName"],
                'repo_add': self.add_chemotherapy
            },
            'Radiotherapy': {
                'table': Radiotherapy,
                'local_id': ["patientId", "courseNumber", "treatmentPlanId", "startDate"],
                'repo_add': self.add_radiotherapy
            },
            'Immunotherapy': {
                'table': Immunotherapy,
                'local_id': ["patientId", "treatmentPlanId", "startDate"],
                'repo_add': self.add_immunotherapy
            },
            'Surgery': {
                'table': Surgery,
                'local_id': ["patientId", "treatmentPlanId", "startDate", "sampleId"],
                'repo_add': self.add_surgery
            },
            'Celltransplant': {
                'table': Celltransplant,
                'local_id': ["patientId", "treatmentPlanId", "startDate"],
                'repo_add': self.add_celltransplant
            },
            'Slide': {
                'table': Slide,
                'local_id': ["patientId", "slideId"],
                'repo_add': self.add_slide
            },
            'Study': {
                'table': Study,
                'local_id': ["patientId", "startDate"],
                'repo_add': self.add_study
            },
            'Labtest': {
                'table': Labtest,
                'local_id': ["patientId", "startDate"],
                'repo_add': self.add_labtest
            }
        }
        self.pipeline_metadata_map = {
            'Extraction': {
                'table': Extraction,
                'local_id': ["sampleId", "extractionId"],
                'repo_add': self.add_extraction
            },
            'Sequencing': {
                'table': Sequencing,
                'local_id': ["sampleId", "sequencingId"],
                'repo_add': self.add_sequencing
            },
            'Alignment': {
                'table': Alignment,
                'local_id': ["sampleId", "alignmentId"],
                'repo_add': self.add_alignment
            },
            'VariantCalling': {
                'table': VariantCalling,
                'local_id': ["sampleId", "variantCallingId"],
                'repo_add': self.add_variant_calling
            },
            'FusionDetection': {
                'table': FusionDetection,
                'local_id': ["sampleId", "fusionDetectionId"],
                'repo_add': self.add_fusion_detection
            },
            'ExpressionAnalysis': {
                'table': ExpressionAnalysis,
                'local_id': ["sampleId", "expressionAnalysisId"],
                'repo_add': self.add_expression_analysis
            }
        }

    def __enter__(self):
        self._repo = repo.SqlDataRepository(self._filename)
        self._repo.open(repo.MODE_WRITE)

        if not os.path.isfile(self._filename):
            self._repo.initialise()

        return self

    def __exit__(self, extype, value, traceback):
        self._repo.commit()
        self._repo.verify()
        self._repo.close()

    def add_dataset(self, dataset):
        self._repo.insertDataset(dataset)
        self._repo.commit()
        self._repo.verify()

    def add_patient(self, patient):
        self._repo.insertPatient(patient)
        self._repo.commit()
        self._repo.verify()

    def add_enrollment(self, enrollment):
        self._repo.insertEnrollment(enrollment)
        self._repo.commit()
        self._repo.verify()

    def add_consent(self, consent):
        self._repo.insertConsent(consent)
        self._repo.commit()
        self._repo.verify()

    def add_diagnosis(self, diagnosis):
        self._repo.insertDiagnosis(diagnosis)
        self._repo.commit()
        self._repo.verify()

    def add_sample(self, sample):
        self._repo.insertSample(sample)
        self._repo.commit()
        self._repo.verify()

    def add_treatment(self, treatment):
        self._repo.insertTreatment(treatment)
        self._repo.commit()
        self._repo.verify()

    def add_outcome(self, outcome):
        self._repo.insertOutcome(outcome)
        self._repo.commit()
        self._repo.verify()

    def add_complication(self, complication):
        self._repo.insertComplication(complication)
        self._repo.commit()
        self._repo.verify()

    def add_tumourboard(self, tumourboard):
        self._repo.insertTumourboard(tumourboard)
        self._repo.commit()
        self._repo.verify()

    def add_chemotherapy(self, chemotherapy):
        self._repo.insertChemotherapy(chemotherapy)
        self._repo.commit()
        self._repo.verify()

    def add_radiotherapy(self, radiotherapy):
        self._repo.insertRadiotherapy(radiotherapy)
        self._repo.commit()
        self._repo.verify()

    def add_immunotherapy(self, immunotherapy):
        self._repo.insertImmunotherapy(immunotherapy)
        self._repo.commit()
        self._repo.verify()

    def add_surgery(self, surgery):
        self._repo.insertSurgery(surgery)
        self._repo.commit()
        self._repo.verify()

    def add_celltransplant(self, celltransplant):
        self._repo.insertCelltransplant(celltransplant)
        self._repo.commit()
        self._repo.verify()

    def add_slide(self, slide):
        self._repo.insertSlide(slide)
        self._repo.commit()
        self._repo.verify()

    def add_study(self, study):
        self._repo.insertStudy(study)
        self._repo.commit()
        self._repo.verify()

    def add_labtest(self, labtest):
        self._repo.insertLabtest(labtest)
        self._repo.commit()
        self._repo.verify()

    def add_extraction(self, extraction):
        self._repo.insertExtraction(extraction)
        self._repo.commit()
        self._repo.verify()

    def add_sequencing(self, sequencing):
        self._repo.insertSequencing(sequencing)
        self._repo.commit()
        self._repo.verify()

    def add_alignment(self, alignment):
        self._repo.insertAlignment(alignment)
        self._repo.commit()
        self._repo.verify()

    def add_variant_calling(self, variant_calling):
        self._repo.insertVariantCalling(variant_calling)
        self._repo.commit()
        self._repo.verify()

    def add_fusion_detection(self, fusion_detection):
        self._repo.insertFusionDetection(fusion_detection)
        self._repo.commit()
        self._repo.verify()

    def add_expression_analysis(self, expression_analysis):
        self._repo.insertExpressionAnalysis(expression_analysis)
        self._repo.commit()
        self._repo.verify()


def main():
    """
    """
    # Parse arguments
    args = docopt(__doc__, version='metadata_ingest ' + str(version))
    repo_filename = args['<repo_filename>']
    dataset_name = args['<dataset_name>']
    metadata_json = args['<metadata_json>']

    # Read and parse a metadata json
    try:
        with open(metadata_json, 'r') as json_datafile:
            metadata = json.load(json_datafile)
    except IOError:
        print('IO Error upon openning {}'.format(metadata_json))

    # Create a dataset
    dataset = Dataset(dataset_name)
    dataset.setDescription('CanDIG Metadata service')

    # Open and load the data
    with CandigRepo(repo_filename) as repo:

        with repo._repo.database.transaction():
            # Add dataset
            try:
                repo.add_dataset(dataset)
            except exceptions.DuplicateNameException:
                pass

            metadata_map = {
                'clinical_metadata': repo.clinical_metadata_map,
                'pipeline_metadata': repo.pipeline_metadata_map
            }
            metadata_key = list(metadata.keys())[0]

            # Iterate through metadata file type based on key and update the dataset
            for individual in metadata[metadata_key]:

                for table in individual:
                    if table in metadata_map[metadata_key]:

                        record = individual[table]
                        local_id_list = []
                        for x in metadata_map[metadata_key][table]['local_id']:
                            if record.get(x):
                                local_id_list.append(record[x])
                            else:
                                print("Skipped: Missing 1 or more primary identifiers for record in: {0} needs {1}, received {2}".format(
                                    table,
                                    metadata_map[metadata_key][table]['local_id'],
                                    local_id_list,
                                    ))
                                local_id_list = None
                                break
                        if not local_id_list:
                            continue

                        local_id = "_".join(local_id_list)

                        obj = metadata_map[metadata_key][table]['table'](dataset, localId=local_id)
                        repo_obj = obj.populateFromJson(json.dumps(record))

                        # Add object into the repo file
                        try:
                            metadata_map[metadata_key][table]['repo_add'](repo_obj)
                        except exceptions.DuplicateNameException:
                            print("Skipped: Duplicate {0} detected for local name: {1} {2}".format(
                                table, local_id, metadata_map[metadata_key][table]['local_id']))

    return None


if __name__ == "__main__":
    main()
