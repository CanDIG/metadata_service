"""
The CanDIG data model. Defines all the methods required to translate
data in existing formats into GA4GH protocol types.
"""

import base64
import glob
import json
import os

import difflib

import candig.metadata.exceptions as exceptions
import candig.metadata.protocol as protocol

from binascii import Error as binascii_error

class CompoundId(object):
    """
    Base class for an id composed of several different parts.  Each
    compound ID consists of a set of fields, each of which corresponds to a
    local ID in the data hierarchy. For example, we might have fields like
    ["dataset", "variantSet"] for a variantSet.  These are available as
    cid.dataset, and cid.variantSet.  The actual IDs of the containing
    objects can be obtained using the corresponding attributes, e.g.
    cid.datasetId and cid.variantSetId.
    """
    fields = []
    """
    The fields that the compound ID is composed of. These are parsed and
    made available as attributes on the object.
    """
    containerIds = []
    """
    The fields of the ID form a breadcrumb trail through the data
    hierarchy, and successive prefixes provide the IDs for objects
    further up the tree. This list is a set of tuples giving the
    name and length of a given prefix forming an identifier.
    """
    differentiator = None
    """
    A string used to guarantee unique ids for objects.  A value of None
    indicates no string is used.  Otherwise, this string will be spliced
    into the object's id.
    """
    differentiatorFieldName = 'differentiator'
    """
    The name of the differentiator field in the fields array for CompoundId
    subclasses.
    """

    def __init__(self, parentCompoundId, *localIds):
        """
        Allocates a new CompoundId for the specified parentCompoundId and
        local identifiers. This compoundId inherits all of the fields and
        values from the parent compound ID, and must have localIds
        corresponding to its fields. If no parent id is present,
        parentCompoundId should be set to None.
        """
        index = 0
        if parentCompoundId is not None:
            for field in parentCompoundId.fields:
                setattr(self, field, getattr(parentCompoundId, field))
                index += 1
        if (self.differentiator is not None and
                self.differentiatorFieldName in self.fields[index:]):
            # insert a differentiator into the localIds if appropriate
            # for this class and we haven't advanced beyond it already
            differentiatorIndex = self.fields[index:].index(
                self.differentiatorFieldName)
            localIds = localIds[:differentiatorIndex] + tuple([
                self.differentiator]) + localIds[differentiatorIndex:]
        for field, localId in zip(self.fields[index:], localIds):
            if not isinstance(localId, str):
                raise exceptions.BadIdentifierNotStringException(localId)
            encodedLocalId = self.encode(localId)
            setattr(self, field, encodedLocalId)
        if len(localIds) != len(self.fields) - index:
            raise ValueError(
                "Incorrect number of fields provided to instantiate ID")
        for idFieldName, prefix in self.containerIds:
            values = [getattr(self, f) for f in self.fields[:prefix + 1]]
            containerId = self.join(values)
            obfuscated = self.obfuscate(containerId)
            setattr(self, idFieldName, obfuscated)

    def __str__(self):
        values = [getattr(self, f) for f in self.fields]
        compoundIdStr = self.join(values)
        return self.obfuscate(compoundIdStr)

    @classmethod
    def join(cls, splits):
        """
        Join an array of ids into a compound id string
        """
        segments = []
        for split in splits:
            segments.append('"{}",'.format(split))
        if len(segments) > 0:
            segments[-1] = segments[-1][:-1]
        jsonString = '[{}]'.format(''.join(segments))
        return jsonString

    @classmethod
    def split(cls, jsonString):
        """
        Split a compound id string into an array of ids
        """
        splits = json.loads(jsonString)
        return splits

    @classmethod
    def encode(cls, idString):
        """
        Encode a string by escaping problematic characters
        """
        return idString.replace('"', '\\"')

    @classmethod
    def decode(cls, encodedString):
        """
        Decode an encoded string
        """
        return encodedString.replace('\\"', '"')

    @classmethod
    def parse(cls, compoundIdStr):
        """
        Parses the specified compoundId string and returns an instance
        of this CompoundId class.

        :raises: An ObjectWithIdNotFoundException if parsing fails. This is
        because this method is a client-facing method, and if a malformed
        identifier (under our internal rules) is provided, the response should
        be that the identifier does not exist.
        """
        if not isinstance(compoundIdStr, str):
            raise exceptions.BadIdentifierException(compoundIdStr)
        try:
            deobfuscated = cls.deobfuscate(compoundIdStr)
        except binascii_error:
            # When a string that cannot be converted to base64 is passed
            # as an argument, b64decode raises a TypeError. We must treat
            # this as an ID not found error.
            # In Python 3, it raises a binascii.Error instead of TypeError
            raise exceptions.ObjectWithIdNotFoundException(compoundIdStr)
        try:
            encodedSplits = cls.split(deobfuscated)
            splits = [cls.decode(split) for split in encodedSplits]
        except (UnicodeDecodeError, ValueError):
            # Sometimes base64 decoding succeeds but we're left with
            # unicode gibberish. This is also and IdNotFound.
            raise exceptions.ObjectWithIdNotFoundException(compoundIdStr)
        # pull the differentiator out of the splits before instantiating
        # the class, if the differentiator exists
        fieldsLength = len(cls.fields)
        if cls.differentiator is not None:
            differentiatorIndex = cls.fields.index(
                cls.differentiatorFieldName)
            if differentiatorIndex < len(splits):
                del splits[differentiatorIndex]
            else:
                raise exceptions.ObjectWithIdNotFoundException(
                    compoundIdStr)
            fieldsLength -= 1
        if len(splits) != fieldsLength:
            raise exceptions.ObjectWithIdNotFoundException(compoundIdStr)
        return cls(None, *splits)

    @classmethod
    def obfuscate(cls, idStr):
        """
        Mildly obfuscates the specified ID string in an easily reversible
        fashion. This is not intended for security purposes, but rather to
        dissuade users from depending on our internal ID structures.
        """
        return base64.urlsafe_b64encode(
            idStr.encode('utf-8')).replace(b'=', b'').decode('utf-8')

    @classmethod
    def deobfuscate(cls, data):
        """
        Reverses the obfuscation done by the :meth:`obfuscate` method.
        If an identifier arrives without correct base64 padding this
        function will append it to the end.
        TODO: Temporary fix. Need to revisit in future.
        """

        decoded_data = base64.urlsafe_b64decode(data + ('A=='[(len(data) - 1) % 4:]))

        try:
            return decoded_data.decode('utf-8')
        except UnicodeDecodeError:
            raise exceptions.ObjectWithIdNotFoundException(decoded_data)

    @classmethod
    def getInvalidIdString(cls):
        """
        Return an id string that is well-formed but probably does not
        correspond to any existing object; used mostly in testing
        """
        return cls.join(['notValid'] * len(cls.fields))


class DatasetCompoundId(CompoundId):
    """
    The compound id for a data set
    """
    fields = ['dataset']
    containerIds = [('dataset_id', 0)]


class PatientCompoundId(DatasetCompoundId):
    """
    The compound id for an patient
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'patient']
    containerIds = DatasetCompoundId.containerIds + [('patient_id', 3)]
    differentiator = 'pat'


class EnrollmentCompoundId(DatasetCompoundId):
    """
    The compound id for an enrollment
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'enrollment']
    containerIds = DatasetCompoundId.containerIds + [('enrollment_id', 3)]
    differentiator = 'enr'


class ConsentCompoundId(DatasetCompoundId):
    """
    The compound id for an consent
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'consent']
    containerIds = DatasetCompoundId.containerIds + [('consent_id', 3)]
    differentiator = 'con'


class DiagnosisCompoundId(DatasetCompoundId):
    """
    The compound id for an diagnosis
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'diagnosis']
    containerIds = DatasetCompoundId.containerIds + [('diagnosis_id', 3)]
    differentiator = 'dia'


class SampleCompoundId(DatasetCompoundId):
    """
    The compound id for an sample
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'sample']
    containerIds = DatasetCompoundId.containerIds + [('sample_id', 3)]
    differentiator = 'sam'


class TreatmentCompoundId(DatasetCompoundId):
    """
    The compound id for an treatment
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'treatment']
    containerIds = DatasetCompoundId.containerIds + [('treatment_id', 3)]
    differentiator = 'tre'


class OutcomeCompoundId(DatasetCompoundId):
    """
    The compound id for an outcome
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'outcome']
    containerIds = DatasetCompoundId.containerIds + [('outcome_id', 3)]
    differentiator = 'out'


class ComplicationCompoundId(DatasetCompoundId):
    """
    The compound id for an complication
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'complication']
    containerIds = DatasetCompoundId.containerIds + [('complication_id', 3)]
    differentiator = 'com'


class TumourboardCompoundId(DatasetCompoundId):
    """
    The compound id for an tumourboard
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'tumourboard']
    containerIds = DatasetCompoundId.containerIds + [('tumourboard_id', 3)]
    differentiator = 'tum'


class ChemotherapyCompoundId(DatasetCompoundId):
    """
    The compound id for an chemotherapy
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'chemotherapy']
    containerIds = DatasetCompoundId.containerIds + [('chemotherapy_id', 3)]
    differentiator = 'che'


class RadiotherapyCompoundId(DatasetCompoundId):
    """
    The compound id for an radiotherapy
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'radiotherapy']
    containerIds = DatasetCompoundId.containerIds + [('radiotherapy_id', 3)]
    differentiator = 'rad'


class SurgeryCompoundId(DatasetCompoundId):
    """
    The compound id for an surgery
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'surgery']
    containerIds = DatasetCompoundId.containerIds + [('surgery_id', 3)]
    differentiator = 'sur'


class ImmunotherapyCompoundId(DatasetCompoundId):
    """
    The compound id for an immunotherapy
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'immunotherapy']
    containerIds = DatasetCompoundId.containerIds + [('immunotherapy_id', 3)]
    differentiator = 'imm'


class CelltransplantCompoundId(DatasetCompoundId):
    """
    The compound id for an celltransplant
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'celltransplant']
    containerIds = DatasetCompoundId.containerIds + [('celltransplant_id', 3)]
    differentiator = 'cel'


class SlideCompoundId(DatasetCompoundId):
    """
    The compound id for an slide
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'slide']
    containerIds = DatasetCompoundId.containerIds + [('slide_id', 3)]
    differentiator = 'sli'


class StudyCompoundId(DatasetCompoundId):
    """
    The compound id for an study
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'study']
    containerIds = DatasetCompoundId.containerIds + [('study_id', 3)]
    differentiator = 'stu'


class LabtestCompoundId(DatasetCompoundId):
    """
    The compound id for an labtest
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'labtest']
    containerIds = DatasetCompoundId.containerIds + [('labtest_id', 3)]
    differentiator = 'lab'


class ExtractionCompoundId(DatasetCompoundId):
    """
    The compound id for extraction metadata
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'extraction']
    containerIds = DatasetCompoundId.containerIds + [('extraction_id', 3)]
    differentiator = 'ext'


class SequencingCompoundId(DatasetCompoundId):
    """
    The compound id for sequencing metadata
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'sequencing']
    containerIds = DatasetCompoundId.containerIds + [('sequencing_id', 3)]
    differentiator = 'seq'


class AlignmentCompoundId(DatasetCompoundId):
    """
    The compound id for alignment tool metadata
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'alignment']
    containerIds = DatasetCompoundId.containerIds + [('alignment_id', 3)]
    differentiator = 'aln'


class VariantCallingCompoundId(DatasetCompoundId):
    """
    The compound id for variant calling metadata
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'variant_calling']
    containerIds = DatasetCompoundId.containerIds + [('variant_calling_id', 3)]
    differentiator = 'vac'


class FusionDetectionCompoundId(DatasetCompoundId):
    """
    The compound id for fusion detection metadata
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'fusion_detection']
    containerIds = DatasetCompoundId.containerIds + [('fusion_detection_id', 3)]
    differentiator = 'fdn'


class ExpressionAnalysisCompoundId(DatasetCompoundId):
    """
    The compound id for expression analysis metadata
    """
    fields = DatasetCompoundId.fields + [
        CompoundId.differentiatorFieldName, 'expression_analysis']
    containerIds = DatasetCompoundId.containerIds + [('expression_analysis_id', 3)]
    differentiator = 'exa'


class DatamodelObject(object):
    """
    Superclass of all datamodel types.

    A datamodel object is a concrete
    representation of some data, either a single observation (such as a
    read) or an aggregated set of related observations (such as a dataset).
    Every datamodel object has an ID and a localId. The ID is an identifier
    which uniquely idenfifies the object within a server instance. The
    localId is a name that identifies the object with a given its
    parent container.
    """

    compoundIdClass = None
    """ The class for compoundIds. Must be set in concrete subclasses.  """

    def __init__(self, parentContainer, localId):
        self._parentContainer = parentContainer
        self._localId = localId
        parentId = None
        if parentContainer is not None:
            parentId = parentContainer.getCompoundId()
        self._compoundId = self.compoundIdClass(parentId, localId)
        self._attributes = {}
        self._objectAttr = {}

    def getId(self):
        """
        Returns the string identifying this DatamodelObject within the
        server.
        """
        return str(self._compoundId)

    def getCompoundId(self):
        """
        Returns the CompoundId instance that identifies this object
        within the server.
        """
        return self._compoundId

    def getLocalId(self):
        """
        Returns the localId of this DatamodelObject. The localId of a
        DatamodelObject is a name that identifies it within its parent
        container.
        """
        return self._localId

    def getParentContainer(self):
        """
        Returns the parent container for this DatamodelObject. This the
        object that is one-level above this object in the data hierarchy.
        For example, for a Variant this is the VariantSet that it belongs
        to.
        """
        return self._parentContainer

    def setAttributes(self, attributes):
        """
        Sets the attributes message to the provided value.
        """
        self._attributes = attributes

    def setAttributesJson(self, attributesJson):
        """
        Sets the attributes dictionary from a JSON string.
        """
        if attributesJson is not None:
            self._attributes = json.loads(attributesJson)
        else:
            self._attributes = {}

    def validateAttribute(self, attribute_name, attributes, tier=0):
        """
        Return True if the access level is higher than the required, False otherwise.
        """

        if attribute_name.endswith("Tier"):
            return False

        else:
            attrTierObj = attributes.get(attribute_name + 'Tier', None)

            if attrTierObj is not None:
                attrTier = attrTierObj[0].get('int32Value', None)

            if attrTierObj is None or attrTier is None or tier < attrTier:
                return False

            else:
                return True

    def serializeMetadataAttributes(self, msg, tier=0):
        """
        Sets the attrbutes of a message for metadata during serialization.
        """
        attributes = self.getAttributes()

        for attribute_name in attributes:
            if self.validateAttribute(attribute_name, attributes, tier) is True:
                values = []
                for dictionary in attributes[attribute_name]:
                    for key in dictionary:
                        values.append(dictionary[key])

                protocol.setAttribute(
                    msg.attributes.attr[attribute_name].values, values)

        return msg

    def serializeAttributes(self, msg):
        """
        Sets the attrbutes of a message during serialization.
        """
        attributes = self.getAttributes()
        for key in attributes:
            protocol.setAttribute(
                msg.attributes.attr[key].values, attributes[key])
        return msg

    def getAttributes(self):
        """
        Returns the attributes for the DatamodelObject.
        """
        return self._attributes

    def _scanDataFiles(self, dataDir, patterns):
        """
        Scans the specified directory for files with the specified globbing
        pattern and calls self._addDataFile for each. Raises an
        EmptyDirException if no data files are found.
        """
        numDataFiles = 0
        for pattern in patterns:
            scanPath = os.path.join(dataDir, pattern)
            for filename in glob.glob(scanPath):
                self._addDataFile(filename)
                numDataFiles += 1
        if numDataFiles == 0:
            raise exceptions.EmptyDirException(dataDir, patterns)

    def mapper(self, field):
        """
        This function maps the requested field to the related Getter
        :param field: specified in the request
        :return: corresponding value of the field
        """
        try:
            return self._objectAttr[field]()
        except (AttributeError, KeyError):
            try:
                closeMatch = difflib.get_close_matches(field, list(self._objectAttr.keys()))[0]
                raise exceptions.BadFieldNameException(field, closeMatch)
            except IndexError:
                raise exceptions.BadFieldNameNoCloseMatchException(field)

