from rest_framework import serializers
import uuid
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
from core.views.operation_plan_views import operation_plan
from datetime import datetime


class CustomDateField(serializers.Field):
    def to_internal_value(self, data):
        # Convert the datetime string to a date object
        try:
            # Try parsing as datetime first
            return datetime.strptime(data, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        except ValueError:
            return datetime.strptime(data, "%Y-%m-%d").date()

    def to_representation(self, value):
        # Convert the date object to a string for output
        return value.strftime("%Y-%m-%d")


class UserSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="last_name")
    phoneNumber = serializers.CharField(source="phone_number", allow_blank=True)

    class Meta:
        model = AfeUser
        exclude = ("password", "group")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError("Password and confirmation don't match")
        return data


class LocationSerializer(serializers.ModelSerializer):
    # id = serializers.UUIDField()

    class Meta:
        model = Location
        fields = "__all__"
        # exclude = ("users",)


class PullUsersSerializer(serializers.Serializer):
    users = UserSerializer(many=True)
    auth_token = serializers.CharField(source="auth_token")
    locations = LocationSerializer(many=True)


class PullUserSerializer(serializers.Serializer):
    user = UserSerializer(many=False)
    auth_token = serializers.CharField()


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = "__all__"


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        # fields = '__all__'
        exclude = ("sectors", "hierarchy_type")


class OperationPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationPlan
        # fields = '__all__'
        exclude = ("sector", "stage")


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        # fields = '__all__'
        exclude = ("operation_types",)


class ActivityResourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityResourceType
        fields = "__all__"


class ActivityPlanSerializer(serializers.ModelSerializer):
    # start_date = CustomDateField(required=False)
    # end_date = CustomDateField(required=False)
    class Meta:
        model = ActivityPlan
        fields = "__all__"


class DetailActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailActivityType
        # fields = '__all__'
        exclude = ("activites",)


class DetailActivitySerializer(serializers.ModelSerializer):
    # date_started = CustomDateField(required=False)
    # date_ended = CustomDateField(required=False)
    # start_date = CustomDateField(required=False)
    # end_date = CustomDateField(required=False)
    class Meta:
        model = DetailActivity
        exclude = ("document", "image")


class ActivityResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityResource
        fields = "__all__"


class ActualActivityResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActualActivityResource
        fields = "__all__"


class UUIDField(serializers.Field):
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        return uuid.UUID(data)


class FormSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSubmission
        fields = "__all__"


class PullSerializer(serializers.Serializer):
    # locations = LocationNodeSerializer(many=True)
    users = UserSerializer(many=True, required=False)
    locations = LocationSerializer(many=True, required=False)
    sectors = SectorSerializer(many=True, required=False)
    operationTypes = OperationTypeSerializer(many=True, required=False)
    operationPlans = OperationPlanSerializer(many=True, required=False)
    activityTypes = ActivityTypeSerializer(many=True, required=False)
    activityResourceTypes = ActivityResourceTypeSerializer(many=True, required=False)
    activityPlans = ActivityPlanSerializer(many=True, required=False)
    detailActivityTypes = DetailActivityTypeSerializer(many=True, required=False)
    detailActivities = DetailActivitySerializer(many=True, required=False)
    activityResources = ActivityResourceSerializer(many=True, required=False)
    formSubmissions = FormSubmissionSerializer(many=True, required=False)
    actualResources = ActualActivityResourceSerializer(many=True, required=False)
