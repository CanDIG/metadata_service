#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Loads project definied tier information on a metadata json object.

Usage:
  load_tiers.py <project_name> <json_filepath> <tier_filepath> <output_filepath>

Options:
  -h --help          Show this screen
  -v --version       Version
  <project_name>     Project name the metadata belongs to, like: profyle, tf4cn
  <json_filepath>    Metadata json filename and path information
  <tier_filepath>    Project_tiers datafile filename and path information
  <output_filepath>  Path and filename of the json output
"""

import json
import logging
import pandas as pd
from docopt import docopt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Update metadata json object with tier information from project_tiers for a
    project.
    """
    # Deal with the arguments
    args = docopt(__doc__, version='0.2')
    project = args['<project_name>']
    json_file = args['<json_filepath>']
    tier_file = args['<tier_filepath>']
    output = args['<output_filepath>']

    # Load tier table
    try:
        project_tiers = pd.read_csv(tier_file, sep='\t', index_col=[0, 1])
    except IOError:
        logger.critical('IOError: {tier_file} can not be loaded'.format(
            tier_file=tier_file))
        exit()

    # Check whether requested project has tier information
    if not project.lower() in project_tiers.columns:
        logger.critical('No tier information found for project {project_name}'.format(
            project_name=project))
        exit()

    # Load metadata
    try:
        with open(json_file, 'r') as input_file:
            metadata = json.load(input_file)
    except IOError:
        logger.critical('IOError occoured upon loading from {inputname}'.format(
            inputname=json_file))
        exit()

    # Add tier info
    for metadata_type in metadata:
        # metadata_type is either "metadata" or "pipeline metadata" for the
        # time being
        #TODO Change metadata type to project name in the input json

        for table in metadata[metadata_type]:

            for table_name in table:

                # Updated record contains all data from the original record
                # plus the tier information
                updated_record = {}

                for field in table[table_name]:
                    
                    if field == 'attributes':
                        # Attributes can hold additional fields that are not
                        # part of the CanDIG schema
                        # 'attributes' : {
                        #   'attr': {
                        #       <field_name> : {
                        #           'values': [
                        #                   { int32Value: <value> },
                        #                   { stringValue: <value> },
                        #                   { ... }
                        #               ]
                        #           },
                        #       },
                        #    }
                        
                        updated_record[field] = {'attr': {}}

                        for attribute_field in table[table_name][field]:
                            
                            # Add the field
                            updated_record[field]['attr'][attribute_field] = {
                                'values': [
                                    {'stringValue': str(table[table_name][field][attribute_field])}
                                    ]
                                }
                            
                            name = '{0}.{1}'.format(field, attribute_field)
                            
                            # Add the corresponding tier info
                            if (table_name, name) in project_tiers.index:
                                
                                tier = project_tiers.loc[[(table_name, name)], project.lower()]

                                updated_record[field]['attr']['{0}Tier'.format(attribute_field)] = {
                                    'values': [
                                        {"int32Value": int(tier)}
                                        ]
                                    }
                            else:
                                logger.error('Unassigned tier info for {table}.{field}.{attribute_field}'.format(
                                    table=table_name, 
                                    field=field,
                                    attribute_field=attribute_field,
                                    ))
                        
                    else:
                        # Regular field
                        
                        updated_record[field] = table[table_name][field]

                        if (table_name, field) in project_tiers.index:
    
                            tier = project_tiers.loc[[(table_name, field)], project.lower()]
    
                            updated_record['{0}Tier'.format(field)] = int(tier)
    
                        else:
                            logger.error('Unassigned tier info for {table}.{field}'.format(
                                table=table_name, field=field))

                table[table_name] = updated_record

    # Save results
    with open(output, 'w') as outfile:
        json.dump(metadata, outfile, indent=4, sort_keys=True)

    logger.info('>>> Tiered dataset output to: {output}'.format(output=output))


if __name__ == "__main__":
    main()
