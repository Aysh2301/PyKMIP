# Copyright (c) 2014 The Johns Hopkins University/Applied Physics Laboratory
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from kmip.core.enums import AttributeType
from kmip.core.enums import CredentialType
from kmip.core.enums import CryptographicAlgorithm
from kmip.core.enums import Operation
from kmip.core.enums import ResultStatus
from kmip.core.enums import NameType

from kmip.demos import utils

from kmip.core.factories.attributes import AttributeFactory
from kmip.core.factories.credentials import CredentialFactory

from kmip.core.attributes import Name

from kmip.core.objects import CommonTemplateAttribute
from kmip.core.objects import PrivateKeyTemplateAttribute
from kmip.core.objects import PublicKeyTemplateAttribute
from kmip.core.objects import Attribute

from kmip.services.kmip_client import KMIPProxy

import logging
import os
import sys


if __name__ == '__main__':
    # Build and parse arguments
    parser = utils.build_cli_parser(Operation.CREATE_KEY_PAIR)
    opts, args = parser.parse_args(sys.argv[1:])

    username = opts.username
    password = opts.password
    algorithm = opts.algorithm
    length = opts.length

    # Exit early if the arguments are not specified
    if algorithm is None:
        logging.debug('No algorithm provided, exiting early from demo')
        sys.exit()
    if length is None:
        logging.debug("No key length provided, exiting early from demo")
        sys.exit()

    attribute_type = AttributeType.CRYPTOGRAPHIC_ALGORITHM
    algorithm_enum = getattr(CryptographicAlgorithm, algorithm, None)

    if algorithm_enum is None:
        logging.debug("{0} not found".format(algorithm))
        logging.debug("Invalid algorithm specified, exiting early from demo")
        sys.exit()

    # Build and setup logging and needed factories
    f_log = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                         'logconfig.ini')
    logging.config.fileConfig(f_log)
    logger = logging.getLogger(__name__)

    attribute_factory = AttributeFactory()
    credential_factory = CredentialFactory()

    # Build the KMIP server account credentials
    # TODO (peter-hamilton) Move up into KMIPProxy
    if (username is None) and (password is None):
        credential = None
    else:
        credential_type = CredentialType.USERNAME_AND_PASSWORD
        credential_value = {'Username': username,
                            'Password': password}
        credential = credential_factory.create_credential(credential_type,
                                                          credential_value)
    # Build the client and connect to the server
    client = KMIPProxy()
    client.open()

    algorithm_obj = attribute_factory.create_attribute(attribute_type,
                                                       algorithm_enum)

    attribute_type = AttributeType.CRYPTOGRAPHIC_LENGTH
    length_obj = attribute_factory.create_attribute(attribute_type,
                                                    length)

    name = Attribute.AttributeName('Name')
    name_value = Name.NameValue('Test Key')
    name_type = Name.NameType(NameType.UNINTERPRETED_TEXT_STRING)
    value = Name(name_value=name_value, name_type=name_type)
    name = Attribute(attribute_name=name, attribute_value=value)

    attributes = [algorithm_obj, length_obj, name]
    common = CommonTemplateAttribute(attributes=attributes)
    private = PrivateKeyTemplateAttribute(attributes=attributes)
    public = PublicKeyTemplateAttribute(attributes=attributes)

    # Create the SYMMETRIC_KEY object
    result = client.create_key_pair(common_template_attribute=common,
                                    private_key_template_attribute=private,
                                    public_key_template_attribute=public)
    client.close()

    # Display operation results
    logger.debug('create_key_pair() result status: {}'.format(
        result.result_status.enum))

    if result.result_status.enum == ResultStatus.SUCCESS:
        logger.debug('created private key UUID: {}'.format(
            result.private_key_uuid))
        logger.debug('created public key UUID: {}'.format(
            result.public_key_uuid))
        logger.debug('created private key template attribute: {}'.format(
            result.private_key_template_attribute))
        logger.debug('created public key template attribute: {}'.format(
            result.public_key_template_attribute))
    else:
        logger.debug('create() result reason: {}'.format(
            result.result_reason.enum))
        logger.debug('create() result message: {}'.format(
            result.result_message.value))
