import uuid
import logging
from dataclasses import dataclass
from azure.identity import DefaultAzureCredential
from azure.mgmt.authorization import (
    AuthorizationManagementClient,
)
from azure.mgmt.authorization.models import (
    RoleAssignmentCreateParameters,
)


@dataclass
class Assignment:
    scope: str
    uuid: str


class AzureADManager:
    def __init__(self, subscription_id):
        self._client = AuthorizationManagementClient(
            credential=DefaultAzureCredential(), subscription_id=subscription_id
        )
        self._created_assignments: [Assignment] = []

    def create_role_assignment(
        self,
        scope: str,
        principal_id: str,
    ):
        # DNS Zone Contributor
        role_definition_id = "befefa01-2a29-4197-83a8-272ff33ce314"

        id = str(uuid.uuid4())

        self._client.role_assignments.create(
            scope=scope,
            role_assignment_name=id,
            parameters=RoleAssignmentCreateParameters(
                role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/"
                + role_definition_id,
                principal_type="ServicePrincipal",
                principal_id=principal_id,
            ),
        )
        self._created_assignments.append(Assignment(scope=scope, uuid=id))

    def clean_up_all_resources(self):
        for assignment in self._created_assignments:
            logging.info("Deleting record %s...", assignment.scope)
            try:
                self._client.role_assignments.delete(
                    scope=assignment.scope, role_assignment_name=assignment.uuid
                )
            except Exception:
                logging.exception(
                    "Please manually delete role assignment %s", assignment.scope
                )
