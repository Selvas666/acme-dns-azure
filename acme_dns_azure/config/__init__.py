import base64
import os
import re

from urllib.parse import urlparse
from strictyaml import load as validate

from acme_dns_azure.log import setup_custom_logger
from acme_dns_azure.exceptions import ConfigurationError
from .schema import schema

logger = setup_custom_logger(__name__)


def load(config_yaml: str = ""):
    try:
        config = validate(config_yaml, schema).data
    except Exception as e:
        logger.exception("Unable to parse configuration.")
        raise ConfigurationError("Unable to parse configuration") from e

    if "ARM_CLIENT_ID" in os.environ and "ARM_CLIENT_SECRET" in os.environ:
        config["sp_client_id"] = os.environ["ARM_CLIENT_ID"]
        config["sp_client_secret"] = os.environ["ARM_CLIENT_SECRET"]

    config, result, message = validate_azure_credentials_use(config)

    if result is False:
        raise ConfigurationError(message)

    if config["keyvault_account_secret_name"] == "":
        config["keyvault_account_secret_name"] = "acme-account-%s" % (
            re.sub("[^-a-zA-Z0-9]+", "-", urlparse(config["server"]).netloc)
        )

    return config


def load_from_base64_env_var(env_var: str = None):
    try:
        env_config_b64 = os.environ.get(env_var)
        if env_config_b64:
            logger.debug("Loading config from environment variable '%s'.", env_var)
            return load(base64.b64decode(env_config_b64).decode("utf8"))
        else:
            raise ConfigurationError(
                "Environment variable '%s' has an empty value.", env_var
            )
    except base64.binascii.Error as e:
        raise ConfigurationError(
            "Unable to base64 decode configuration provided in environment variable '%s': %s"
            % (env_var, e)
        )
    except Exception as e:
        raise ConfigurationError("Error while loading configuration: %s" % e)


def load_from_file(filename: str = None):
    try:
        logger.debug("Loading config from file '%s'." % filename)
        with open(filename, "r") as file:
            return load(file.read())
    except FileNotFoundError:
        raise ConfigurationError("Config file not found at '%s'" % filename)
    except OSError as e:
        raise ConfigurationError(
            "Unable to read configuration from '%s': %s" % (filename, e.strerror)
        )
    except Exception as e:
        raise ConfigurationError("Error while loading configuration: %s" % e)


def validate_azure_credentials_use(config: dict):
    """
    Validates config for valid Azure credentials configuration.

    Args:
        config (dict): pre validated config.yaml as dict.

    Returns:
        config (dict): config modified as applicable.
        result (bool): result of the validation, false if validation failed.
        message (string): a string describing the result or why the validation failed.
    """
    # check if only one identity flag is set to true
    credential_flags = 0
    if "use_system_assigned_identity_credentials" in config:
        if config["use_system_assigned_identity_credentials"] is True:
            credential_flags += 1
    if "use_azure_cli_credentials" in config:
        if config["use_azure_cli_credentials"] is True:
            credential_flags += 1
    if "use_workload_identity_credentials" in config:
        if config["use_workload_identity_credentials"] is True:
            credential_flags += 1
    if "use_managed_identity_credentials" in config:
        if config["use_managed_identity_credentials"] is True:
            credential_flags += 1
    if "use_provided_service_principal_credentials" in config:
        if config["use_provided_service_principal_credentials"] is True:
            credential_flags += 1

    # to avoid confusion we only accept one flag to be set to true
    if credential_flags > 1:
        message = f'{credential_flags} "use_*_identity" flags set to true.'
        return config, False, message

    # if no flags are set to true we check if other fields are enough for authentication, this was done for backwards compatibility. The old logic of preferring the sp credentials is preserved here.
    if credential_flags == 0:
        if not ("sp_client_id" in config and "sp_client_secret" in config):
            if "managed_identity_id" not in config:
                message = "Azure credentials not specified or incomplete."
                return config, False, message
            else:
                config["use_managed_identity_credentials"] = True
        else:
            config["use_provided_service_principal_credentials"] = True

    message = "Validation successful!"
    return config, True, message
