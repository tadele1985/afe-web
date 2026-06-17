from collections import OrderedDict
from enum import Enum

from core.models import (
    AfeUser,
    Sector,
    OperationType,
    Location,
    OperationPlan,
    ActivityType,
    ActivityResourceType,
    ActivityPlan,
    DetailActivityType,
    DetailActivity,
    ActivityResource,
    ActualActivityResource,
    FormSubmission,
)
from .serializers import (
    UserSerializer,
    SectorSerializer,
    OperationTypeSerializer,
    LocationSerializer,
    OperationPlanSerializer,
    ActivityTypeSerializer,
    ActivityResourceTypeSerializer,
    ActivityPlanSerializer,
    DetailActivityTypeSerializer,
    DetailActivitySerializer,
    ActivityResourceSerializer,
    ActualActivityResourceSerializer,
    FormSubmissionSerializer,
)


class SyncType(Enum):
    PUSH = (0,)
    PULL = (1,)
    PUSH_PULL = 2


class SyncContext(Enum):
    GLOBAL = (0,)
    WOREDA = (2,)
    WOREDA_ORGANIZATIONS = 3
    SYNC_WOREDA_CONTEXT = (4,)
    USER = 5


class SyncEntityLookup:
    def __init__(
        self,
        entity,
        serializer,
        sync_type=SyncType.PUSH_PULL,
        sync_context=SyncContext.GLOBAL,
    ):
        self.entity = entity
        self.serializer = serializer
        self.sync_type = sync_type
        self.sync_context = sync_context


sync_entities_lookup = OrderedDict(
    [
        (
            "locations",
            SyncEntityLookup(
                entity=Location,
                serializer=LocationSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "operationTypes",
            SyncEntityLookup(
                entity=OperationType,
                serializer=OperationTypeSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "sectors",
            SyncEntityLookup(
                entity=Sector,
                serializer=SectorSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "operationPlans",
            SyncEntityLookup(
                entity=OperationPlan,
                serializer=OperationPlanSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "activityTypes",
            SyncEntityLookup(
                entity=ActivityType,
                serializer=ActivityTypeSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "activityResourceTypes",
            SyncEntityLookup(
                entity=ActivityResourceType,
                serializer=ActivityResourceTypeSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "activityPlans",
            SyncEntityLookup(
                entity=ActivityPlan,
                serializer=ActivityPlanSerializer,
                sync_type=SyncType.PUSH_PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "detailActivityTypes",
            SyncEntityLookup(
                entity=DetailActivityType,
                serializer=DetailActivityTypeSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "detailActivities",
            SyncEntityLookup(
                entity=DetailActivity,
                serializer=DetailActivitySerializer,
                sync_type=SyncType.PUSH_PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "activityResources",
            SyncEntityLookup(
                entity=ActivityResource,
                serializer=ActivityResourceSerializer,
                sync_type=SyncType.PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "actualResources",
            SyncEntityLookup(
                entity=ActualActivityResource,
                serializer=ActualActivityResourceSerializer,
                sync_type=SyncType.PUSH_PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
        (
            "formSubmissions",
            SyncEntityLookup(
                entity=FormSubmission,
                serializer=FormSubmissionSerializer,
                sync_type=SyncType.PUSH_PULL,
                sync_context=SyncContext.GLOBAL,
            ),
        ),
    ]
)


# class SyncEntityLookup:
#     def __init__(self, entity, serializer, sync_type=SyncType.PUSH_PULL, sync_context=SyncContext.GLOBAL):
#         self.entity = entity
#         self.serializer = serializer
#         self.sync_type = sync_type
#         self.sync_context = sync_context


# sync_entities_lookup = OrderedDict([
#     ("users",
#     SyncEntityLookup(entity=AfeUser,
#                     serializer=UserSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),
#     ("locations",
#     SyncEntityLookup(entity=Location,
#                     serializer=LocationSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),

#     ("sectors",
#     SyncEntityLookup(entity=Sector,
#                     serializer=SectorSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),

#     ("operationTypes",
#     SyncEntityLookup(entity=OperationType,
#                     serializer=OperationTypeSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),


#     ("operationPlans",
#     SyncEntityLookup(entity=OperationPlan,
#                     serializer=OperationPlanSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),

#     ("activityTypes",
#     SyncEntityLookup(entity=ActivityType,
#                     serializer=ActivityTypeSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),


#     ("activityResourceTypes",
#     SyncEntityLookup(entity=ActivityResourceType,
#                     serializer=ActivityResourceTypeSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),


#     ("activityPlans",
#     SyncEntityLookup(entity=ActivityPlan,
#                     serializer=ActivityPlanSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),


#     ("detailActivityTypes",
#     SyncEntityLookup(entity=DetailActivityType,
#                     serializer=DetailActivityTypeSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),


#     ("detailActivities",
#     SyncEntityLookup(entity=DetailActivity,
#                     serializer=DetailActivitySerializer,
#                     sync_type=SyncType.PUSH_PULL,
#                     sync_context=SyncContext.GLOBAL)),


#     ("activityResources",
#     SyncEntityLookup(entity=ActivityResource,
#                     serializer=ActivityResourceSerializer,
#                     sync_type=SyncType.PULL,
#                     sync_context=SyncContext.GLOBAL)),
# ])
