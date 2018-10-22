import json

import fastjsonschema
import pkg_resources


def schema_filename():
    return pkg_resources.resource_filename('runrestic', 'config/schema.json')


def validate_configuration(config: dict):
    with open(schema_filename(), 'r') as schema_file:
        schema = json.load(schema_file)

    fastjsonschema.validate(schema, config)
