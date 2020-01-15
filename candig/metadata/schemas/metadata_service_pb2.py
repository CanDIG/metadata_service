# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: candig/metadata/schemas/metadata_service.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from candig.metadata.schemas import metadata_pb2 as candig_dot_metadata_dot_schemas_dot_metadata__pb2
from candig.metadata.schemas.google import annotations_pb2 as candig_dot_metadata_dot_schemas_dot_google_dot_annotations__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='candig/metadata/schemas/metadata_service.proto',
  package='candig.metadata.schemas',
  syntax='proto3',
  serialized_pb=_b('\n.candig/metadata/schemas/metadata_service.proto\x12\x17\x63\x61ndig.metadata.schemas\x1a&candig/metadata/schemas/metadata.proto\x1a\x30\x63\x61ndig/metadata/schemas/google/annotations.proto\">\n\x15SearchDatasetsRequest\x12\x11\n\tpage_size\x18\x01 \x01(\x05\x12\x12\n\npage_token\x18\x02 \x01(\t\"e\n\x16SearchDatasetsResponse\x12\x32\n\x08\x64\x61tasets\x18\x01 \x03(\x0b\x32 .candig.metadata.schemas.Dataset\x12\x17\n\x0fnext_page_token\x18\x02 \x01(\t\"\'\n\x11GetDatasetRequest\x12\x12\n\ndataset_id\x18\x01 \x01(\t2\xad\x02\n\x0fMetadataService\x12\x95\x01\n\x0eSearchDatasets\x12..candig.metadata.schemas.SearchDatasetsRequest\x1a/.candig.metadata.schemas.SearchDatasetsResponse\"\"\x82\xd3\xe4\x93\x02\x1c\"\x17/v0.8.0/datasets/search:\x01*\x12\x81\x01\n\nGetDataset\x12*.candig.metadata.schemas.GetDatasetRequest\x1a .candig.metadata.schemas.Dataset\"%\x82\xd3\xe4\x93\x02\x1f\x12\x1d/v0.8.0/datasets/{dataset_id}b\x06proto3')
  ,
  dependencies=[candig_dot_metadata_dot_schemas_dot_metadata__pb2.DESCRIPTOR,candig_dot_metadata_dot_schemas_dot_google_dot_annotations__pb2.DESCRIPTOR,])




_SEARCHDATASETSREQUEST = _descriptor.Descriptor(
  name='SearchDatasetsRequest',
  full_name='candig.metadata.schemas.SearchDatasetsRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='page_size', full_name='candig.metadata.schemas.SearchDatasetsRequest.page_size', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='page_token', full_name='candig.metadata.schemas.SearchDatasetsRequest.page_token', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=165,
  serialized_end=227,
)


_SEARCHDATASETSRESPONSE = _descriptor.Descriptor(
  name='SearchDatasetsResponse',
  full_name='candig.metadata.schemas.SearchDatasetsResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='datasets', full_name='candig.metadata.schemas.SearchDatasetsResponse.datasets', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='next_page_token', full_name='candig.metadata.schemas.SearchDatasetsResponse.next_page_token', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=229,
  serialized_end=330,
)


_GETDATASETREQUEST = _descriptor.Descriptor(
  name='GetDatasetRequest',
  full_name='candig.metadata.schemas.GetDatasetRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='dataset_id', full_name='candig.metadata.schemas.GetDatasetRequest.dataset_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=332,
  serialized_end=371,
)

_SEARCHDATASETSRESPONSE.fields_by_name['datasets'].message_type = candig_dot_metadata_dot_schemas_dot_metadata__pb2._DATASET
DESCRIPTOR.message_types_by_name['SearchDatasetsRequest'] = _SEARCHDATASETSREQUEST
DESCRIPTOR.message_types_by_name['SearchDatasetsResponse'] = _SEARCHDATASETSRESPONSE
DESCRIPTOR.message_types_by_name['GetDatasetRequest'] = _GETDATASETREQUEST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SearchDatasetsRequest = _reflection.GeneratedProtocolMessageType('SearchDatasetsRequest', (_message.Message,), dict(
  DESCRIPTOR = _SEARCHDATASETSREQUEST,
  __module__ = 'candig.metadata.schemas.metadata_service_pb2'
  # @@protoc_insertion_point(class_scope:candig.metadata.schemas.SearchDatasetsRequest)
  ))
_sym_db.RegisterMessage(SearchDatasetsRequest)

SearchDatasetsResponse = _reflection.GeneratedProtocolMessageType('SearchDatasetsResponse', (_message.Message,), dict(
  DESCRIPTOR = _SEARCHDATASETSRESPONSE,
  __module__ = 'candig.metadata.schemas.metadata_service_pb2'
  # @@protoc_insertion_point(class_scope:candig.metadata.schemas.SearchDatasetsResponse)
  ))
_sym_db.RegisterMessage(SearchDatasetsResponse)

GetDatasetRequest = _reflection.GeneratedProtocolMessageType('GetDatasetRequest', (_message.Message,), dict(
  DESCRIPTOR = _GETDATASETREQUEST,
  __module__ = 'candig.metadata.schemas.metadata_service_pb2'
  # @@protoc_insertion_point(class_scope:candig.metadata.schemas.GetDatasetRequest)
  ))
_sym_db.RegisterMessage(GetDatasetRequest)



_METADATASERVICE = _descriptor.ServiceDescriptor(
  name='MetadataService',
  full_name='candig.metadata.schemas.MetadataService',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=374,
  serialized_end=675,
  methods=[
  _descriptor.MethodDescriptor(
    name='SearchDatasets',
    full_name='candig.metadata.schemas.MetadataService.SearchDatasets',
    index=0,
    containing_service=None,
    input_type=_SEARCHDATASETSREQUEST,
    output_type=_SEARCHDATASETSRESPONSE,
    options=_descriptor._ParseOptions(descriptor_pb2.MethodOptions(), _b('\202\323\344\223\002\034\"\027/v0.8.0/datasets/search:\001*')),
  ),
  _descriptor.MethodDescriptor(
    name='GetDataset',
    full_name='candig.metadata.schemas.MetadataService.GetDataset',
    index=1,
    containing_service=None,
    input_type=_GETDATASETREQUEST,
    output_type=candig_dot_metadata_dot_schemas_dot_metadata__pb2._DATASET,
    options=_descriptor._ParseOptions(descriptor_pb2.MethodOptions(), _b('\202\323\344\223\002\037\022\035/v0.8.0/datasets/{dataset_id}')),
  ),
])
_sym_db.RegisterServiceDescriptor(_METADATASERVICE)

DESCRIPTOR.services_by_name['MetadataService'] = _METADATASERVICE

# @@protoc_insertion_point(module_scope)