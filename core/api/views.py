import datetime
import time
import logging
import json
from collections import OrderedDict

import dateutil.parser
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.db import IntegrityError
from django.contrib.auth import login
from rest_framework import exceptions
from rest_framework import status
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response

from core.api.sync_lookup import sync_entities_lookup, SyncContext, SyncType
from core.attachable_forms.forms import FormCallbackMapper
from core.models import ImageSyncMeta
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
)
from .serializers import (
    ChangePasswordSerializer,
    PullSerializer,
    PullUserSerializer,
    UserSerializer,
)
from knox.views import LoginView
from knox.auth import TokenAuthentication
from rest_framework import permissions

logger = logging.getLogger(__name__)


# ============================================
# SERIALIZERS
# ============================================

class ImageSyncSerializer(serializers.ModelSerializer):
    """Serializer for ImageSyncMeta model"""
    
    class Meta:
        model = ImageSyncMeta
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


# ============================================
# AUTHENTICATION VIEWS
# ============================================

class KnoxLogin(LoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")
        login(request, user)
        return super().post(request, format=None)

    def get_user_serializer_class(self):
        return UserSerializer


class PasswordChange(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not self.request.user.check_password(
            serializer.validated_data["old_password"]
        ):
            return Response({"message": "Incorrect old password"}, status=400)

        self.request.user.set_password(serializer.validated_data["new_password1"])
        self.request.user.save()
        update_session_auth_hash(request, request.user)
        return Response({"message": "Password changed successfully"})


class Login(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", None)
        password = request.POST.get("password", None)
        # pin = request.data.get('pin')
        if (username is None) or (password is None):
            raise exceptions.AuthenticationFailed("username and password required")

        user = AfeUser.objects.filter(username=username).first()

        if user is None:
            raise exceptions.AuthenticationFailed("user not found")
        if not user.check_password(password):
            raise exceptions.AuthenticationFailed("wrong password")
        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        token, created = Token.objects.get_or_create(user=user)

        result = {"user": user, "auth_token": token}

        serializer = PullUserSerializer(result)
        return Response(serializer.data)


# ============================================
# PULL REQUESTS (GET DATA FROM SERVER)
# ============================================

class PullRequestView(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user_id = self.request.query_params.get("userId")

        try:
            user = AfeUser.objects.get(id=user_id)

        except AfeUser.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        version_code = self.request.query_params.get("appVersionCode")
        version_name = self.request.query_params.get("appVersionName")
        tables_to_be_migrated = self.request.query_params.get(
            "tablesToBeMigrated", ""
        ).split(";")

        last_sync_date = self.request.query_params.get("lastSyncDate")

        logger.error("SYNC: PULL LAST SYNC DATE: %s", last_sync_date)

        # updatedDate >= lastSyncDate
        # non-deleted rows
        updated_date_query = {"updatedDate__gte": last_sync_date}

        to_date = self.request.query_params.get("toDate")
        logger.error("SYNC: PULL TO_DATE: %s", to_date)

        if to_date:
            updated_date_query["updatedDate__lt"] = to_date

        non_deleted_query = {"deleted": False}

        # context query string
        entities_dict = {}
        for item in sync_entities_lookup.items():
            context_query = context_query_str(item[1].sync_context, request.user)

            # Ignore updated date query if this entity is requested by the app as a migration
            new_updated_query = (
                {} if item[0] in tables_to_be_migrated else updated_date_query
            )

            if item[1].sync_type == SyncType.PUSH:
                pass
            elif len(context_query) > 0:
                entities_dict[item[0]] = item[1].entity.objects.filter(
                    **new_updated_query, **non_deleted_query, **context_query
                )
            else:
                entities_dict[item[0]] = item[1].entity.objects.filter(
                    **new_updated_query, **non_deleted_query
                )
                if item[0] == "operationPlans":
                    entities_dict[item[0]] = entities_dict[item[0]].filter(
                        stage="FINAL"
                    )
                elif item[0] == "activityPlans":
                    entities_dict[item[0]] = entities_dict[item[0]].filter(
                        operation_plan__stage="FINAL"
                    )
                elif item[0] == "detailActivities":
                    entities_dict[item[0]] = entities_dict[item[0]].filter(
                        activity_plan__operation_plan__stage="FINAL"
                    )
                elif item[0] == "activityResources":
                    entities_dict[item[0]] = entities_dict[item[0]].filter(
                        detail_activity__activity_plan__operation_plan__stage="FINAL"
                    )
                elif item[0] == "actualResources":
                    entities_dict[item[0]] = entities_dict[item[0]].filter(
                        activity_resource__detail_activity__activity_plan__operation_plan__stage="FINAL"
                    )

        obj_serializer = PullSerializer(entities_dict)

        logger.debug("SYNC: pulled records: %s", obj_serializer.data)

        return Response(obj_serializer.data)


class PullDeletedRequestView(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user_id = self.request.query_params.get("userId")

        try:
            user = AfeUser.objects.get(id=user_id)
        except AfeUser.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        last_sync_date = self.request.query_params.get("lastSyncDate")

        logger.debug("SYNC: PULL DELETED LAST SYNC DATE: %s", last_sync_date)

        # updatedDate >= lastSyncDate
        # non-deleted rows
        updated_date_query = {"updatedDate__gte": last_sync_date}

        to_date = self.request.query_params.get("toDate")
        logger.debug("SYNC: PULL DELETED TO_DATE: %s", to_date)

        if to_date:
            updated_date_query["updatedDate__lt"] = to_date

        deleted_query = {"deleted": True}

        # context query string
        entities_dict = {}
        for item in sync_entities_lookup.items():
            context_query = context_query_str(item[1].sync_context, user)
            if item[1].sync_type == SyncType.PUSH:
                pass
            elif len(context_query) > 0:
                entities_dict[item[0]] = item[1].entity.objects.filter(
                    **updated_date_query, **deleted_query, **context_query
                )
            else:
                entities_dict[item[0]] = item[1].entity.objects.filter(
                    **updated_date_query, **deleted_query
                )

        obj_serializer = PullSerializer(entities_dict)

        reversed_dict = {}
        # Traverse through the reversed list of keys and add them to a new dictionary
        for i in reversed(obj_serializer.data):
            reversed_dict[i] = obj_serializer.data[i]

        logger.debug("SYNC: pulled deleted records: %s", reversed_dict)

        return Response(reversed_dict)


def context_query_str(context, user):
    query = {}
    if context == SyncContext.GLOBAL:
        pass
    elif context == SyncContext.WOREDA:
        query = {"woreda": user.woreda_id}
    elif context == SyncContext.SYNC_WOREDA_CONTEXT:
        query = {"syncWoredaContext": user.woreda_id}
    elif context == SyncContext.USER:
        query = {"userId": user.id}
    elif context == SyncContext.WOREDA_ORGANIZATIONS:
        organizations = Location.objects.filter(name=user.woreda_id)
        organization_ids = list(map(lambda org: org.id, organizations))
        query = {"organizationId__in": organization_ids}

    return query


# ============================================
# PUSH REQUESTS (SEND DATA TO SERVER)
# ============================================

class PushRequestView(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def upsert(self, request):
        user_id = self.request.query_params.get("userId")
        last_pull_time = dateutil.parser.isoparse(
            self.request.query_params.get("last_pull_time")
        )

        try:
            user = AfeUser.objects.get(id=user_id)
        except AfeUser.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        try:
            parsed_data = JSONParser().parse(request)
            key = parsed_data["key"]

            logger.debug("SYNC pushing %s", parsed_data)

            if sync_entities_lookup[key] is not None:
                for item in parsed_data["data"]:
                    # check if item exists
                    try:
                        row_item = sync_entities_lookup[key].entity.objects.get(
                            id=item["id"]
                        )

                        entity_serializer = sync_entities_lookup[key].serializer(
                            row_item, data=item
                        )

                        if row_item.updatedDate <= last_pull_time:
                            if entity_serializer.is_valid():
                                updated_obj = entity_serializer.save()
                                print("updated", updated_obj)
                                logger.debug("SYNC PUSH updated obj: %s", updated_obj)
                            else:
                                failed_row = {
                                    "user_id": user_id,
                                    "data": item,
                                    "model": key,
                                    "error": entity_serializer.errors,
                                }
                                logger.error("failed_row", failed_row)
                                return Response(
                                    entity_serializer.errors.__repr__(),
                                    status=status.HTTP_400_BAD_REQUEST,
                                )

                    except sync_entities_lookup[key].entity.DoesNotExist:
                        entity_serializer = sync_entities_lookup[key].serializer(
                            data=item
                        )
                        if entity_serializer.is_valid():
                            saved_obj = entity_serializer.save()
                            if key == "formSubmissions":
                                saved_obj.detail_activity_id = item[
                                    "detail_activity_id"
                                ]
                                saved_obj.save()
                                func = FormCallbackMapper.on_submit(saved_obj, user)
                                if func:
                                    result = func()
                                    if not result:
                                        logger.error("Form Callback Function failed")
                                else:
                                    logger.error("Form Callback Function not found")
                            logger.debug("SYNC PUSH saved_obj %s", saved_obj)
                        else:
                            failed_row = {
                                "user_id": user_id,
                                "data": item,
                                "model": key,
                                "error": entity_serializer.errors,
                            }
                            logger.error(entity_serializer.errors)

        except ParseError as error:
            return Response(
                "Invalid JSON - {0}".format(error.detail),
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_200_OK)


class PushDeletedRecordsView(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def soft_delete_records(self, request):
        user_id = self.request.query_params.get("userId")

        try:
            user = AfeUser.objects.get(id=user_id)
        except AfeUser.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        parsed_data = JSONParser().parse(request)

        logger.debug("SYNC: pushing deleted records: request:  %s", parsed_data)

        for table_items in parsed_data:
            entity = sync_entities_lookup[table_items["entityKey"]].entity
            for row_id in table_items["ids"]:
                try:
                    row_item = entity.objects.get(id=row_id)
                    row_item.deleted = True
                    row_item.save()
                    logger.debug("SYNC: success: updated deleted record:  %s", row_id)
                except entity.DoesNotExist:
                    logger.warning("SYNC: deleted record not found:  %s", row_id)
                    pass
        logger.debug("SYNC: soft delete records response: %s", Response())
        return Response(status=status.HTTP_200_OK)


# ============================================
# IMAGE SYNC VIEWS
# ============================================

class UploadImages(viewsets.ViewSet):
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def upload(self, request):
        logger.debug("upload request %s", request.data)
        user_id = self.request.query_params.get("userId")

        try:
            user = AfeUser.objects.get(id=user_id)
        except AfeUser.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        logger.debug("uploading images data %s", self.request.data)

        try:
            model_id = request.data.get("model_id")
            row_item = ImageSyncMeta.objects.get(model_id=model_id)
            row_item.deleted = False
            serializer = ImageSyncSerializer(row_item, data=self.request.data)

            if serializer.is_valid():
                serializer.save()
                logger.info("image uploaded successfully")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error("image upload update serializer error: %s", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ImageSyncMeta.DoesNotExist:
            serializer = ImageSyncSerializer(data=self.request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info("image uploaded successfully")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error("image upload save serializer error: %s", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetSyncImagesMetaView(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user_id = self.request.query_params.get("userId")

        try:
            user = AfeUser.objects.get(id=user_id)
        except AfeUser.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        parsed_data = JSONParser().parse(request)

        model_ids = parsed_data["ids"]
        last_sync_date = parsed_data["lastSyncDate"]

        logger.debug("image meta request for model_ids %s", model_ids)

        images_meta = ImageSyncMeta.objects.filter(
            model_id__in=model_ids, uploaded_date__gt=last_sync_date
        )

        result = []
        for image_meta in images_meta:
            result.append(
                {
                    "model_id": str(image_meta.model_id),
                    "model_name": image_meta.model_name,
                    "uploaded_date": image_meta.uploaded_date,
                    "deleted": image_meta.deleted,
                }
            )

        logger.debug("Images meta request result %s", result)
        return Response(result)


class PushDeletedImagesView(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete_images(self, request):
        user_id = self.request.query_params.get("userId")

        try:
            user = AfeUser.objects.get(id=user_id)
        except AfeUser.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        if not user.userrole_set.filter(
            role__code__in=["SYNC", "SYSTEM_ADMINISTRATOR", "BRANCH_USER"]
        ).exists():
            raise exceptions.AuthenticationFailed("permission denied")

        parsed_data = JSONParser().parse(request)

        model_ids = parsed_data["ids"]

        try:
            rows_items = ImageSyncMeta.objects.filter(model_id__in=model_ids)
            for row_item in rows_items:
                row_item.deleted = True
                if hasattr(row_item, 'image') and row_item.image:
                    row_item.image.delete(save=False)
                row_item.save()
                logger.debug("SYNC: success: updated deleted image record: %s", row_item)

        except Exception as e:
            logger.error("Could not remove images: %s", str(e))
            return Response(
                "Could not remove images", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(status=status.HTTP_200_OK)


# ============================================
# UTILITY VIEWS
# ============================================

class GetCurrentTimeMillis(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_time_millis = int(time.time() * 1000)
        result = {"current_time_millis": current_time_millis}
        return Response(result)