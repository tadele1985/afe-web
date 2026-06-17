import re
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .storage import OverwriteStorage
from .utils import get_current_user, hash_sha256

from enum import Enum


# Create your models here.
class AfeBaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    createdDate = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")
    updatedDate = models.DateTimeField(auto_now=True, verbose_name="Updated Date")
    createdBy = models.UUIDField(blank=True, null=True)
    updatedBy = models.UUIDField(blank=True, null=True)
    deleted = models.BooleanField(default=False)
    syncWoredaContext = models.UUIDField(blank=True, null=True)

    class AfeBaseModelManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().exclude(deleted=True)

    objects = AfeBaseModelManager()

    # IMPORTANT!!  when changing this make sure that changes are also reflected in  bulk updates throughout the app git
    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            self.updatedBy = user.id
            if self._state.adding:
                self.createdBy = user.id
        super(AfeBaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True  # abstract base class


class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def model_to_dict(self):
        return {
            "pk": self.pk,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AfeUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    pin = models.CharField(null=True, blank=True, max_length=64)  # sha-256
    phone_number = models.CharField(blank=True, max_length=12)
    middle_name = models.CharField(max_length=50, null=True, blank=True)

    group = models.ForeignKey(
        UserGroup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="core_user_groups",
    )

    authToken = models.CharField(null=True, max_length=1000)

    createdDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)
    createdBy = models.UUIDField(blank=True, null=True)
    updatedBy = models.UUIDField(blank=True, null=True)
    deleted = models.BooleanField(default=False)
    location = models.ForeignKey("Location", on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if self.pin is not None and len(self.pin) < 64:
            self.pin = hash_sha256(self.pin)

        super().save(*args, **kwargs)

    def model_to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username if self.username else "",
            "pin": self.pin,
            "firstName": self.first_name,
            "middleName": self.middle_name,
            "lastName": self.last_name,
            "fullName": self.get_full_name(),
            "name": f"{self.get_full_name()} ({self.username})",
            "phoneNumber": self.phone_number,
            "email": self.email,
            "isActive": self.is_active,
            "roles": self.group_names_str(),
            "dateJoined": self.date_joined,
            "authToken": self.authToken,
            "dateCreated": self.createdDate,
            "dateUpdated": self.updatedDate,
            "deleted": self.deleted,
        }

    def group_names_str(self):
        return ",".join([group.name for group in self.groups.all()])

    def get_full_name(self):
        if not self.first_name and not self.middle_name and not self.last_name:
            return None
    def get_full_name(self) -> str | None:
        parts = [p for p in [self.first_name, self.middle_name, self.last_name] if p]
        return " ".join(parts) if parts else None



class RoleCode(models.TextChoices):
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR", "System Administrator"
    DATA_ADMINISTRATOR = "DATA_ADMINISTRATOR", "Data Administrator"
    DATA_ANALYST = "DATA_ANALYST", "Data Analyst"
    MAIN_OFFICE_USER = "MAIN_OFFICE_USER", "Main Office User"
    BRANCH_DATA_ADMINISTRATOR = "BRANCH_DATA_ADMINISTRATOR", "Branch Data Administrator"
    BRANCH_DATA_ANALYST = "BRANCH_DATA_ANALYST", "Branch Data Analyst"
    BRANCH_USER = "BRANCH_USER", "Branch user"


class Role(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=100,
        choices=RoleCode,
    )

    def __str__(self):
        return self.name


class UserRole(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        AfeUser,
        unique=True,
        on_delete=models.PROTECT,
    )


class Sector(AfeBaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


LOCATION_TYPE_CHOICES = (
    ("HQ", "HQ"),
    ("BRANCH", "Branch"),
    ("NURSERY", "Nursery"),
    ("FOREST_ESTABLISTMENT", "Forest establishment"),
    ("SAWMILL", "Sawmill"),
    ("SEED_SOURCE", "Seed source"),
    ("FOREST_SITE", "Forest site"),
    ("BLOCK", "Block"),
    ("COMPARTMENT", "Compartment"),
    ("SUB_COMPARTMENT", "Sub compartment"),
)


location_hierarchy = {
    "HQ": ["Branch"],
    "Branch": ["Nursery", "Sawmill", "Forest site", "Seed source"],
    "Nursery": [],
    "Sawmill": [],
    "Seed source": [],
    "Forest site": ["Block"],
    "Block": ["Compartment"],
    "Compartment": ["Sub compartment"],
}


location_type_to_reference_field_map = {
    "FOREST_SITE": ["remark"],
    "NURSERY": ["zone", "district", "kebele", "location_on_map", "area", "remark"],
    "SAWMILL": [
        "zone",
        "district",
        "kebele",
        "location_on_map",
        "log_depo_storage_area",
    ],
    "SEED_SOURCE": ["region", "zone", "district", "kebele", "location_on_map"],
    "SUB_COMPARTMENT": [
        "unique_code",
        "productive_area",
        "non_productive_area",
        "CENTROID_COORDINATE",
        "owner",
        "types_of_species_to_be_planted",
    ],
}


def get_parent_location_types(location):
    for key, values in location_hierarchy.items():
        if location in values:
            return get_parent_location_types(key) + [location]
    return [location]


class OperationType(AfeBaseModel):
    name = models.CharField(max_length=50)
    sectors = models.ManyToManyField(Sector)
    hierarchy_type = models.CharField(
        max_length=50, choices=LOCATION_TYPE_CHOICES, default="HQ"
    )

    def __str__(self):
        return self.name


class Location(AfeBaseModel):
    name = models.CharField(max_length=50)
    type = models.CharField(
        max_length=50,
        choices=LOCATION_TYPE_CHOICES,
        verbose_name="Location Type",
        db_index=True,
    )
    code = models.CharField(max_length=50, null=True, blank=True)
    zone = models.TextField(null=True, blank=True)
    district = models.TextField(null=True, blank=True)
    kebele = models.TextField(null=True, blank=True)
    location_on_map = models.TextField(null=True, blank=True)
    area = models.TextField(null=True, blank=True)
    unique_code = models.TextField(null=True, blank=True)
    productive_area = models.TextField(null=True, blank=True)
    non_productive_area = models.TextField(null=True, blank=True)
    centroid_coordinate = models.TextField(null=True, blank=True)
    owner = models.TextField(null=True, blank=True)
    types_of_species_to_be_planted = models.TextField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    log_depo_storage_area = models.TextField(null=True, blank=True)
    region = models.TextField(null=True, blank=True)
    parent = models.ForeignKey(
        "Location",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        db_index=True,
    )

    class Meta:
        unique_together = ("type", "name", "parent")

    @property
    def property_mapper(self):
        property_mapper = {}
        for field in self._meta.fields:
            match field.name:
                case (
                    "location_on_map"
                    | "unique_code"
                    | "productive_area"
                    | "non_productive_area"
                    | "CENTROID_COORDINATE"
                    | "types_of_species_to_be_planted"
                    | "log_depo_storage_area"
                ):
                    property_mapper[field.name.lower()] = re.sub(
                        r"_([a-zA-Z])",
                        lambda m: " " + m.group(1).upper(),
                        field.name.lower(),
                    ).capitalize()
                case _:
                    property_mapper[field.name] = field.verbose_name.capitalize()

        return property_mapper

    @property
    def detail_info(self):
        properties = location_type_to_reference_field_map.get(self.type, [])
        detail_info = {
            "Name": self.name,
            "Created Date": self.createdDate,
            "Location Type": self.get_type_display(),
        }
        if self.parent:
            detail_info["Parent"] = self.parent.name

        for property in properties:
            detail_info[self.property_mapper[property.lower()]] = getattr(
                self, property.lower()
            )

        return detail_info

    @staticmethod
    def get_friendly_name(location_type):
        for location in LOCATION_TYPE_CHOICES:
            formal, friendly = location
            if formal == location_type:
                return friendly
        return None

    def get_location_type(self, location_type: str):
        current = self
        while current is not None and current.type != location_type:
            current = current.parent

        return current

    @property
    def inventory_model(self):
        match self.type:
            case "NURSERY":
                return Item
            case "SAWMILL":
                return Item
            case _:
                return Item

    def get_all_children(self):
        children = []
        for child in self.children.all():
            children.append(child)
            children += child.get_all_children()
        return children

    def get_all_children_ids(self):
        children = []
        for child in self.children.all():
            children.append(str(child.id))
            children += child.get_all_children_ids()

        return children

    def __str__(self):
        return self.name


PLAN_STATUS = (
    ("TODO", "Todo"),
    ("STARTED", "Started"),
    ("ON_HOLD", "On hold"),
    ("CANCELLED", "Cancelled"),
    ("COMPLETED", "Completed"),
)


PLAN_STAGE = (
    ("DRAFT", "Draft"),
    ("FINAL", "Final"),
)


class OperationPlan(AfeBaseModel):
    year = models.IntegerField(null=True)
    start_year = models.DateField(null=True)
    end_year = models.DateField(null=True)
    sector = models.ForeignKey(
        Sector,
        db_column="sector",
        null=True,
        on_delete=models.CASCADE,
        related_name="operation_plans",
    )
    operation_type = models.ForeignKey(
        OperationType,
        db_column="operation_type",
        null=True,
        on_delete=models.CASCADE,
        related_name="operation_plans",
    )
    location = models.ForeignKey(
        Location,
        null=True,
        on_delete=models.CASCADE,
        related_name="location",
    )
    assignee = models.ForeignKey(
        AfeUser,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="operation_plan_assignee",
    )
    status = models.CharField(
        max_length=50, null=True, blank=True, choices=PLAN_STATUS, default="TODO"
    )
    stage = models.CharField(
        max_length=50, null=True, blank=True, choices=PLAN_STAGE, default="DRAFT"
    )
    status_last_updated = models.DateTimeField(null=True, blank=True)
    status_last_updated_by = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            org_instance = OperationPlan.objects.get(pk=self.pk)
            if org_instance.status != self.status:
                self.status_last_updated = timezone.now()
        except OperationPlan.DoesNotExist:
            self.status_last_updated = timezone.now()
        super().save(*args, **kwargs)


class ActivityType(AfeBaseModel):
    name = models.CharField(max_length=300)
    operation_types = models.ManyToManyField(OperationType)

    def __str__(self):
        return self.name


ACTIVITY_RESOURCE_TYPES = (
    ("TOOL", "Tool"),
    ("RESOURCE", "Resource"),
    ("INPUT", "Input"),
)


class ActivityResourceType(AfeBaseModel):
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=20, choices=ACTIVITY_RESOURCE_TYPES)
    norm_unit = models.CharField(max_length=50, null=True)
    achievment_unit = models.CharField(max_length=50, null=True)
    payment_unit = models.CharField(max_length=50, null=True)
    utility_rate = models.BooleanField(default=True)
    completion_rate = models.BooleanField(default=True)
    sectors = models.ManyToManyField(Sector)
    operation_types = models.ManyToManyField(OperationType)
    formula_type = models.IntegerField(default=1)

    def __str__(self):
        return self.name


class ActivityPlan(AfeBaseModel):
    operation_plan = models.ForeignKey(
        OperationPlan,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="operation_activity_plan",
    )
    type = models.ForeignKey(
        ActivityType,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="activity_plan_type",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    assignee = models.ForeignKey(
        AfeUser,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="activity_assignee",
    )
    status = models.CharField(
        max_length=50, null=True, blank=True, choices=PLAN_STATUS, default="TODO"
    )
    status_last_updated = models.DateTimeField(null=True, blank=True)
    status_last_updated_by = models.DateTimeField(null=True, blank=True)
    date_started = models.DateField(null=True, blank=True)
    date_ended = models.DateField(null=True, blank=True)


DOCUMENT_ATTACHMENT_CHOICES = (
    ("REQUIRED", "Required"),
    ("OPTIONAL", "Optional"),
    ("NOT_ALLOWED", "Not Allowed"),
)


def get_image_upload_path(instance, filepath):
    return f"detail_activity/images/{instance.id}"


def get_document_upload_path(instance, filepath):
    return f"detail_activity/documents/{instance.id}"


class DetailActivity(AfeBaseModel):
    activity_plan = models.ForeignKey(
        ActivityPlan,
        null=True,
        on_delete=models.CASCADE,
        related_name="activity_detail",
    )
    detail_type = models.ForeignKey(
        "DetailActivityType",
        null=True,
        on_delete=models.CASCADE,
        related_name="activity_detail_type",
    )
    assignee = models.ForeignKey(
        AfeUser,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="detail_activity_assignee",
    )

    start_date = models.DateField()
    end_date = models.DateField()

    started = models.BooleanField(default=False)
    is_ended = models.BooleanField(default=False)

    date_started = models.DateField(null=True, blank=True)
    date_ended = models.DateField(null=True, blank=True)

    unit = models.CharField(max_length=50, null=True, blank=True)

    document = models.FileField(
        null=True,
        blank=True,
        upload_to=get_document_upload_path,
        storage=OverwriteStorage(),
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_image_upload_path,
        storage=OverwriteStorage(),
    )
    status = models.CharField(
        max_length=50, null=True, blank=True, choices=PLAN_STATUS, default="TODO"
    )
    status_last_updated = models.DateTimeField(null=True, blank=True)
    status_last_updated_by = models.DateTimeField(null=True, blank=True)

    @property
    def planned_sum(self):
        planned_sum = 0
        count = 0
        for activity_resource in self.activityresource_set.filter(
            resource_type=self.detail_type.annual_resource_type
        ):
            planned_sum += activity_resource.achievement
            count += 1

        if count == 0:
            return 0

        return planned_sum

    @property
    def actual_sum(self):
        actual_sum = 0
        count = 0
        for activity_resource in self.activityresource_set.filter(
            resource_type=self.detail_type.annual_resource_type
        ):
            actual_sum += activity_resource.actual_plan_sum
            count += 1

        if count == 0:
            return 0

        return actual_sum

    @property
    def completion_rate(self):
        rate_sum = 0
        count = 0
        for activity_resource in self.activityresource_set.all():
            rate_sum += activity_resource.completion_rate
            count += 1

        if count == 0:
            return 0

        return round(rate_sum / count, 2)

    @property
    def utilization_rate(self):
        rate_sum = 0
        count = 0
        for activity_resource in self.activityresource_set.all():
            rate_sum += activity_resource.utilization_rate
            count += 1
        if count == 0:
            return 0
        return round(rate_sum / count, 2)

    @property
    def cost_utilization_rate(self):
        rate_sum = 0
        count = 0
        for activity_resource in self.activityresource_set.all():
            rate_sum += activity_resource.cost_utilization_rate
            count += 1
        if count == 0:
            return 0
        return round(rate_sum / count, 2)

    def __str__(self):
        return self.detail_type.name


class ActivityResource(AfeBaseModel):
    detail_activity = models.ForeignKey(DetailActivity, on_delete=models.CASCADE)
    resource_type = models.ForeignKey(
        ActivityResourceType,
        null=True,
        on_delete=models.CASCADE,
        related_name="activity_resource_type",
    )
    work_norm = models.FloatField(verbose_name="Work norm")
    achievement = models.FloatField(verbose_name="Planned achievement")
    payment = models.FloatField(verbose_name="Payment")

    @property
    def actual_plan_sum(self):
        actual_sum = 0
        for actual_activity in self.actual_activities.all():
            actual_sum += actual_activity.achievement

        if self.get_cost() == 0:
            return 0

        return actual_sum

    def get_cost(self):
        match self.resource_type.formula_type:
            case 1:
                return round(self.work_norm * self.achievement * self.payment, 2)
            case 2:
                return round(self.work_norm * self.payment, 2)
            case 3:
                return round((self.achievement / self.work_norm) * self.payment, 2)
            case 4:
                return round(self.achievement * self.payment, 2)
            case _:
                return 0

    @staticmethod
    def calculate_cost(work_norm, achievement, payment, formula_type):
        match formula_type:
            case 1:
                return round(work_norm * achievement * payment, 2)
            case 2:
                return round(work_norm * payment, 2)
            case 3:
                return round((achievement / work_norm) * payment, 2)
            case 4:
                return round(achievement * payment, 2)
            case _:
                return 0

    @property
    def completion_rate(self) -> float:
     if not self.achievement:
        return 0.0
     actual_achievements = sum(a.achievement for a in self.actual_activities.all())
     return round((actual_achievements * 100) / self.achievement, 2)


    @property
    def utilization_rate(self):
        total_resource = self.work_norm * self.achievement
        actual_resources = 0
        for actual_activity in self.actual_activities.all():
            actual_resources += actual_activity.work_norm
        utilization_rate = actual_resources * (100 / total_resource)
        return round(utilization_rate, 2)

    @property
    def cost_utilization_rate(self):
        total_cost = 0
        for actual_activity in self.actual_activities.all():
            total_cost += actual_activity.get_cost()

        if self.get_cost() == 0:
            return 0

        cost_utilization_rate = (total_cost * 100) / self.get_cost()
        return round(cost_utilization_rate, 2)


class ActualActivityResource(AfeBaseModel):
    activity_resource = models.ForeignKey(
        ActivityResource,
        null=True,
        on_delete=models.CASCADE,
        related_name="actual_activities",
    )
    work_norm = models.FloatField(verbose_name="Actual Work norm")
    achievement = models.FloatField(verbose_name="Actual achievement")
    payment = models.FloatField(verbose_name="Actual Payment")

    def get_cost(self):
        match self.activity_resource.resource_type.formula_type:
            case 1:
                return round(self.work_norm * self.achievement * self.payment, 2)
            case 2:
                return round(self.work_norm * self.payment, 2)
            case 3:
                return round((self.achievement / self.work_norm) * self.payment, 2)
            case 4:
                return round(self.achievement * self.payment, 2)
            case _:
                return 0


class Customer(AfeBaseModel):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        null=True,
    )

    name = models.CharField(max_length=200, verbose_name="Full Name")
    phone_number = models.CharField(max_length=12)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=50, null=True, blank=True)
    tin_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self) -> str:
        return self.name

class ItemType(models.TextChoices):
    SEED = "SEED", "Seed"
    SOWED_SEED = "SOWED_SEED", "Sowed Seed"
    GERMINATED_SEED = "GERMINATED_SEED", "Germinated Seed"
    GRADE1_SEED = "GRADE1_SEED", "Grade 1 Seed"
    GRADE2_SEED = "GRADE2_SEED", "Grade 2 Seed"
    GRADE3_SEED = "GRADE3_SEED", "Grade 3 Seed"
    SEEDLING = "SEEDLING", "Seedling"
    PRODUCT = "PRODUCT", "Product"
    RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"
    TREE = "TREE", "Tree"


class ProductName(models.TextChoices):
    Yegidgida_mager_5cm__7cm_mid_diameter_before_debarking_CONSTRUCTION_WOOD = (
        "Yegidgida mager - 5cm - 7cm mid diameter before debarking CONSTRUCTION_WOOD",
        "Yegidgida mager - 5cm - 7cm mid diameter before debarking CONSTRUCTION_WOOD",
    )
    Yekorkoro__mager_7cm_9cm_mid_diameter_before_debarking_CONSTRUCTION_WOOD = (
        "Yekorkoro  mager: 7cm - 9cm mid diameter before debarking CONSTRUCTION_WOOD",
        "Yekorkoro  mager: 7cm - 9cm mid diameter before debarking CONSTRUCTION_WOOD",
    )
    Weraj_mid_diamter_from_9cm_to_11cm_CONSTRUCTION_WOOD = (
        "Weraj : mid diamter from 9cm to 11cm CONSTRUCTION_WOOD",
        "Weraj : mid diamter from 9cm to 11cm CONSTRUCTION_WOOD",
    )
    Quami_Dinbil_mid_diameter_11cm_to_13cm_before_debarking__CONSTRUCTION_WOOD = (
        "Quami/Dinbil (mid diameter 11cm to 13cm before debarking  CONSTRUCTION_WOOD",
        "Quami/Dinbil (mid diameter 11cm to 13cm before debarking  CONSTRUCTION_WOOD",
    )
    Kench_Esatekela_Ashegagari_Teshekami_mid_diameter_13_15_cm_before_debarking__CONSTRUCTION_WOOD = (
        "Kench/Esatekela/Ashegagari/Teshekami: mid diameter 13 15 cm before debarking  CONSTRUCTION_WOOD",
        "Kench/Esatekela/Ashegagari/Teshekami: mid diameter 13 15 cm before debarking  CONSTRUCTION_WOOD",
    )
    Construction_filt_terb_preparation_for_one_split_length_4_5m_5_7cm_mid__CONSTRUCTION_WOOD = (
        "Construction filt/terb preparation (for one split (length 4-5m, 5-7cm mid  CONSTRUCTION_WOOD",
        "Construction filt/terb preparation (for one split (length 4-5m, 5-7cm mid  CONSTRUCTION_WOOD",
    )

    ESSENTIAL_OIL_1 = "250ml ESSENTIAL_OIL", "250ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_2 = "500ml ESSENTIAL_OIL", "500ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_3 = "1000ml ESSENTIAL_OIL", "1000ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_4 = "1500ml ESSENTIAL_OIL", "1500ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_5 = "2000ml ESSENTIAL_OIL", "2000ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_6 = "5000ml ESSENTIAL_OIL", "5000ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_7 = "10000ml ESSENTIAL_OIL", "10000ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_8 = "15000ml ESSENTIAL_OIL", "15000ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_9 = "20000ml ESSENTIAL_OIL", "20000ml ESSENTIAL_OIL"
    ESSENTIAL_OIL_10 = "25000ml ESSENTIAL_OIL", "25000ml ESSENTIAL_OIL"
    From_cutting_into_pieces_FIREWOOD = (
        "From cutting into pieces FIREWOOD",
        "From cutting into pieces FIREWOOD",
    )
    From_cutting_log_into_final_splitting_pieces_FIREWOOD = (
        "From cutting log into final splitting pieces FIREWOOD",
        "From cutting log into final splitting pieces FIREWOOD",
    )
    From__branch_and_left_over_into_split_FIREWOOD = (
        "From  branch and left over into split FIREWOOD",
        "From  branch and left over into split FIREWOOD",
    )
    Stand_TO_DRY = (
        "From Stand and dried trees into final split (dimension of products, Length 1m,1.5m,2m, Thickness 7-10cm FIREWOOD",
        "From Stand and dried trees into final split (dimension of products, Length 1m,1.5m,2m, Thickness 7-10cm FIREWOOD",
    )
    FELL_DRIED_FIREWOOD = (
        "From felled and dried trees/collected logs FIREWOOD",
        "From felled and dried trees/collected logs FIREWOOD",
    )
    DRIED_FELLED_TREE = (
        "Collecting and stacking dried & felled trees that is ready for marketing FIREWOOD",
        "Collecting and stacking dried & felled trees that is ready for marketing FIREWOOD",
    )
    Thinning_bypdoduct_for_Fire_wood_FIREWOOD = (
        "Thinning bypdoduct for Fire wood FIREWOOD",
        "Thinning bypdoduct for Fire wood FIREWOOD",
    )
    Coppice_singling_byproduct_for_fire_wood_FIREWOOD = (
        "Coppice singling byproduct for fire wood FIREWOOD",
        "Coppice singling byproduct for fire wood FIREWOOD",
    )
    LOG_TIMBER_PREPARATION_1 = (
        "6-9.99 cm average diameter LOG_TIMBER_PREPARATION",
        "6-9.99 cm average diameter LOG_TIMBER_PREPARATION",
    )
    LOG_TIMBER_PREPARATION_2 = (
        "≥ 10 cm average diameter LOG_TIMBER_PREPARATION",
        "≥ 10 cm average diameter LOG_TIMBER_PREPARATION",
    )
    LUMBER_1 = "0.5x0.025x0.04 LUMBER", "0.5x0.025x0.04 LUMBER"
    LUMBER_2 = "0.5x0.025x0.05 LUMBER", "0.5x0.025x0.05 LUMBER"
    LUMBER_3 = "0.5x0.025x0.075 LUMBER", "0.5x0.025x0.075 LUMBER"
    LUMBER_4 = "0.5x0.025x0.1 LUMBER", "0.5x0.025x0.1 LUMBER"
    LUMBER_5 = "0.5x0.025x0.125 LUMBER", "0.5x0.025x0.125 LUMBER"
    LUMBER_6 = "0.5x0.025x0.15 LUMBER", "0.5x0.025x0.15 LUMBER"
    LUMBER_7 = "0.5x0.025x0.175 LUMBER", "0.5x0.025x0.175 LUMBER"
    LUMBER_8 = "0.5x0.025x0.2 LUMBER", "0.5x0.025x0.2 LUMBER"
    LUMBER_9 = "0.5x0.025x0.225 LUMBER", "0.5x0.025x0.225 LUMBER"
    LUMBER_10 = "0.5x0.025x0.25 LUMBER", "0.5x0.025x0.25 LUMBER"
    LUMBER_11 = "0.5x0.025x0.275 LUMBER", "0.5x0.025x0.275 LUMBER"
    LUMBER_12 = "0.5x0.025x0.3 LUMBER", "0.5x0.025x0.3 LUMBER"
    LUMBER_13 = "0.5x0.025x0.325 LUMBER", "0.5x0.025x0.325 LUMBER"
    LUMBER_14 = "0.5x0.025x0.35 LUMBER", "0.5x0.025x0.35 LUMBER"
    LUMBER_15 = "0.5x0.05x0.04 LUMBER", "0.5x0.05x0.04 LUMBER"
    LUMBER_16 = "0.5x0.05x0.05 LUMBER", "0.5x0.05x0.05 LUMBER"
    LUMBER_17 = "0.5x0.05x0.075 LUMBER", "0.5x0.05x0.075 LUMBER"
    LUMBER_18 = "0.5x0.05x0.1 LUMBER", "0.5x0.05x0.1 LUMBER"
    LUMBER_19 = "0.5x0.05x0.125 LUMBER", "0.5x0.05x0.125 LUMBER"
    LUMBER_20 = "0.5x0.05x0.15 LUMBER", "0.5x0.05x0.15 LUMBER"
    LUMBER_21 = "0.5x0.05x0.175 LUMBER", "0.5x0.05x0.175 LUMBER"
    LUMBER_22 = "0.5x0.05x0.2 LUMBER", "0.5x0.05x0.2 LUMBER"
    LUMBER_23 = "0.5x0.05x0.225 LUMBER", "0.5x0.05x0.225 LUMBER"
    LUMBER_24 = "0.5x0.05x0.25 LUMBER", "0.5x0.05x0.25 LUMBER"
    LUMBER_25 = "0.5x0.05x0.275 LUMBER", "0.5x0.05x0.275 LUMBER"
    LUMBER_26 = "0.5x0.05x0.3 LUMBER", "0.5x0.05x0.3 LUMBER"
    LUMBER_27 = "0.5x0.05x0.325 LUMBER", "0.5x0.05x0.325 LUMBER"
    LUMBER_28 = "0.5x0.05x0.35 LUMBER", "0.5x0.05x0.35 LUMBER"
    LUMBER_29 = "0.6x0.025x0.04 LUMBER", "0.6x0.025x0.04 LUMBER"
    LUMBER_30 = "0.6x0.025x0.05 LUMBER", "0.6x0.025x0.05 LUMBER"
    LUMBER_31 = "0.6x0.025x0.075 LUMBER", "0.6x0.025x0.075 LUMBER"
    LUMBER_32 = "0.6x0.025x0.1 LUMBER", "0.6x0.025x0.1 LUMBER"
    LUMBER_33 = "0.6x0.025x0.125 LUMBER", "0.6x0.025x0.125 LUMBER"
    LUMBER_34 = "0.6x0.025x0.15 LUMBER", "0.6x0.025x0.15 LUMBER"
    LUMBER_35 = "0.6x0.025x0.175 LUMBER", "0.6x0.025x0.175 LUMBER"
    LUMBER_36 = "0.6x0.025x0.2 LUMBER", "0.6x0.025x0.2 LUMBER"
    LUMBER_37 = "0.6x0.025x0.225 LUMBER", "0.6x0.025x0.225 LUMBER"
    LUMBER_38 = "0.6x0.025x0.25 LUMBER", "0.6x0.025x0.25 LUMBER"
    LUMBER_39 = "0.6x0.025x0.275 LUMBER", "0.6x0.025x0.275 LUMBER"
    LUMBER_40 = "0.6x0.025x0.3 LUMBER", "0.6x0.025x0.3 LUMBER"
    LUMBER_41 = "0.6x0.025x0.325 LUMBER", "0.6x0.025x0.325 LUMBER"
    LUMBER_42 = "0.6x0.025x0.35 LUMBER", "0.6x0.025x0.35 LUMBER"
    LUMBER_43 = "0.6x0.05x0.04 LUMBER", "0.6x0.05x0.04 LUMBER"
    LUMBER_44 = "0.6x0.05x0.05 LUMBER", "0.6x0.05x0.05 LUMBER"
    LUMBER_45 = "0.6x0.05x0.075 LUMBER", "0.6x0.05x0.075 LUMBER"
    LUMBER_46 = "0.6x0.05x0.1 LUMBER", "0.6x0.05x0.1 LUMBER"
    LUMBER_47 = "0.6x0.05x0.125 LUMBER", "0.6x0.05x0.125 LUMBER"
    LUMBER_48 = "0.6x0.05x0.15 LUMBER", "0.6x0.05x0.15 LUMBER"
    LUMBER_49 = "0.6x0.05x0.175 LUMBER", "0.6x0.05x0.175 LUMBER"
    LUMBER_50 = "0.6x0.05x0.2 LUMBER", "0.6x0.05x0.2 LUMBER"
    LUMBER_51 = "0.6x0.05x0.225 LUMBER", "0.6x0.05x0.225 LUMBER"
    LUMBER_52 = "0.6x0.05x0.25 LUMBER", "0.6x0.05x0.25 LUMBER"
    LUMBER_53 = "0.6x0.05x0.275 LUMBER", "0.6x0.05x0.275 LUMBER"
    LUMBER_54 = "0.6x0.05x0.3 LUMBER", "0.6x0.05x0.3 LUMBER"
    LUMBER_55 = "0.6x0.05x0.325 LUMBER", "0.6x0.05x0.325 LUMBER"
    LUMBER_56 = "0.6x0.05x0.35 LUMBER", "0.6x0.05x0.35 LUMBER"
    LUMBER_57 = "0.7x0.025x0.04 LUMBER", "0.7x0.025x0.04 LUMBER"
    LUMBER_58 = "0.7x0.025x0.05 LUMBER", "0.7x0.025x0.05 LUMBER"
    LUMBER_59 = "0.7x0.025x0.075 LUMBER", "0.7x0.025x0.075 LUMBER"
    LUMBER_60 = "0.7x0.025x0.1 LUMBER", "0.7x0.025x0.1 LUMBER"
    LUMBER_61 = "0.7x0.025x0.125 LUMBER", "0.7x0.025x0.125 LUMBER"
    LUMBER_62 = "0.7x0.025x0.15 LUMBER", "0.7x0.025x0.15 LUMBER"
    LUMBER_63 = "0.7x0.025x0.175 LUMBER", "0.7x0.025x0.175 LUMBER"
    LUMBER_64 = "0.7x0.025x0.2 LUMBER", "0.7x0.025x0.2 LUMBER"
    LUMBER_65 = "0.7x0.025x0.225 LUMBER", "0.7x0.025x0.225 LUMBER"
    LUMBER_66 = "0.7x0.025x0.25 LUMBER", "0.7x0.025x0.25 LUMBER"
    LUMBER_67 = "0.7x0.025x0.275 LUMBER", "0.7x0.025x0.275 LUMBER"
    LUMBER_68 = "0.7x0.025x0.3 LUMBER", "0.7x0.025x0.3 LUMBER"
    LUMBER_69 = "0.7x0.025x0.325 LUMBER", "0.7x0.025x0.325 LUMBER"
    LUMBER_70 = "0.7x0.025x0.35 LUMBER", "0.7x0.025x0.35 LUMBER"
    LUMBER_71 = "0.7x0.05x0.04 LUMBER", "0.7x0.05x0.04 LUMBER"
    LUMBER_72 = "0.7x0.05x0.05 LUMBER", "0.7x0.05x0.05 LUMBER"
    LUMBER_73 = "0.7x0.05x0.075 LUMBER", "0.7x0.05x0.075 LUMBER"
    LUMBER_74 = "0.7x0.05x0.1 LUMBER", "0.7x0.05x0.1 LUMBER"
    LUMBER_75 = "0.7x0.05x0.125 LUMBER", "0.7x0.05x0.125 LUMBER"
    LUMBER_76 = "0.7x0.05x0.15 LUMBER", "0.7x0.05x0.15 LUMBER"
    LUMBER_77 = "0.7x0.05x0.175 LUMBER", "0.7x0.05x0.175 LUMBER"
    LUMBER_78 = "0.7x0.05x0.2 LUMBER", "0.7x0.05x0.2 LUMBER"
    LUMBER_79 = "0.7x0.05x0.225 LUMBER", "0.7x0.05x0.225 LUMBER"
    LUMBER_80 = "0.7x0.05x0.25 LUMBER", "0.7x0.05x0.25 LUMBER"
    LUMBER_81 = "0.7x0.05x0.275 LUMBER", "0.7x0.05x0.275 LUMBER"
    LUMBER_82 = "0.7x0.05x0.3 LUMBER", "0.7x0.05x0.3 LUMBER"
    LUMBER_83 = "0.7x0.05x0.325 LUMBER", "0.7x0.05x0.325 LUMBER"
    LUMBER_84 = "0.7x0.05x0.35 LUMBER", "0.7x0.05x0.35 LUMBER"
    LUMBER_85 = "0.8x0.025x0.04 LUMBER", "0.8x0.025x0.04 LUMBER"
    LUMBER_86 = "0.8x0.025x0.05 LUMBER", "0.8x0.025x0.05 LUMBER"
    LUMBER_87 = "0.8x0.025x0.075 LUMBER", "0.8x0.025x0.075 LUMBER"
    LUMBER_88 = "0.8x0.025x0.1 LUMBER", "0.8x0.025x0.1 LUMBER"
    LUMBER_89 = "0.8x0.025x0.125 LUMBER", "0.8x0.025x0.125 LUMBER"
    LUMBER_90 = "0.8x0.025x0.15 LUMBER", "0.8x0.025x0.15 LUMBER"
    LUMBER_91 = "0.8x0.025x0.175 LUMBER", "0.8x0.025x0.175 LUMBER"
    LUMBER_92 = "0.8x0.025x0.2 LUMBER", "0.8x0.025x0.2 LUMBER"
    LUMBER_93 = "0.8x0.025x0.225 LUMBER", "0.8x0.025x0.225 LUMBER"
    LUMBER_94 = "0.8x0.025x0.25 LUMBER", "0.8x0.025x0.25 LUMBER"
    LUMBER_95 = "0.8x0.05x0.04 LUMBER", "0.8x0.05x0.04 LUMBER"
    LUMBER_96 = "0.8x0.05x0.05 LUMBER", "0.8x0.05x0.05 LUMBER"
    LUMBER_97 = "0.8x0.05x0.075 LUMBER", "0.8x0.05x0.075 LUMBER"
    LUMBER_98 = "0.8x0.05x0.1 LUMBER", "0.8x0.05x0.1 LUMBER"
    LUMBER_99 = "0.8x0.05x0.125 LUMBER", "0.8x0.05x0.125 LUMBER"
    LUMBER_100 = "0.8x0.05x0.15 LUMBER", "0.8x0.05x0.15 LUMBER"
    LUMBER_101 = "0.8x0.05x0.175 LUMBER", "0.8x0.05x0.175 LUMBER"
    LUMBER_102 = "0.8x0.05x0.20 LUMBER", "0.8x0.05x0.20 LUMBER"
    LUMBER_103 = "0.8x0.05x0.225 LUMBER", "0.8x0.05x0.225 LUMBER"
    LUMBER_104 = "0.8x0.05x0.25 LUMBER", "0.8x0.05x0.25 LUMBER"
    LUMBER_105 = "0.8x0.05x0.275 LUMBER", "0.8x0.05x0.275 LUMBER"
    LUMBER_106 = "0.8x0.05x0.3 LUMBER", "0.8x0.05x0.3 LUMBER"
    LUMBER_107 = "0.8x0.05x0.325 LUMBER", "0.8x0.05x0.325 LUMBER"
    LUMBER_108 = "0.8x0.05x0.35 LUMBER", "0.8x0.05x0.35 LUMBER"
    LUMBER_109 = "0.9x0.025x0.04 LUMBER", "0.9x0.025x0.04 LUMBER"
    LUMBER_110 = "0.9x0.025x0.05 LUMBER", "0.9x0.025x0.05 LUMBER"
    LUMBER_111 = "0.9x0.025x0.075 LUMBER", "0.9x0.025x0.075 LUMBER"
    LUMBER_112 = "0.9x0.025x0.1 LUMBER", "0.9x0.025x0.1 LUMBER"
    LUMBER_113 = "0.9x0.025x0.125 LUMBER", "0.9x0.025x0.125 LUMBER"
    LUMBER_114 = "0.9x0.025x0.15 LUMBER", "0.9x0.025x0.15 LUMBER"
    LUMBER_115 = "0.9x0.025x0.175 LUMBER", "0.9x0.025x0.175 LUMBER"
    LUMBER_116 = "0.9x0.025x0.2 LUMBER", "0.9x0.025x0.2 LUMBER"
    LUMBER_117 = "0.9x0.025x0.225 LUMBER", "0.9x0.025x0.225 LUMBER"
    LUMBER_118 = "0.9x0.025x0.25 LUMBER", "0.9x0.025x0.25 LUMBER"
    LUMBER_119 = "0.9x0.025x0.275 LUMBER", "0.9x0.025x0.275 LUMBER"
    LUMBER_120 = "0.9x0.025x0.3 LUMBER", "0.9x0.025x0.3 LUMBER"
    LUMBER_121 = "0.9x0.025x0.325 LUMBER", "0.9x0.025x0.325 LUMBER"
    LUMBER_122 = "0.9x0.05x0.04 LUMBER", "0.9x0.05x0.04 LUMBER"
    LUMBER_123 = "0.9x0.05x0.05 LUMBER", "0.9x0.05x0.05 LUMBER"
    LUMBER_124 = "0.9x0.05x0.075 LUMBER", "0.9x0.05x0.075 LUMBER"
    LUMBER_125 = "0.9x0.05x0.1 LUMBER", "0.9x0.05x0.1 LUMBER"
    LUMBER_126 = "0.9x0.05x0.125 LUMBER", "0.9x0.05x0.125 LUMBER"
    LUMBER_127 = "0.9x0.05x0.15 LUMBER", "0.9x0.05x0.15 LUMBER"
    LUMBER_128 = "0.9x0.05x0.175 LUMBER", "0.9x0.05x0.175 LUMBER"
    LUMBER_129 = "0.9x0.05x0.2 LUMBER", "0.9x0.05x0.2 LUMBER"
    LUMBER_130 = "0.9x0.05x0.225 LUMBER", "0.9x0.05x0.225 LUMBER"
    LUMBER_131 = "0.9x0.05x0.25 LUMBER", "0.9x0.05x0.25 LUMBER"
    LUMBER_132 = "0.9x0.05x0.275 LUMBER", "0.9x0.05x0.275 LUMBER"
    LUMBER_133 = "0.9x0.05x0.3 LUMBER", "0.9x0.05x0.3 LUMBER"
    LUMBER_134 = "0.9x0.05x0.325 LUMBER", "0.9x0.05x0.325 LUMBER"
    LUMBER_135 = "0.9x0.05x0.35 LUMBER", "0.9x0.05x0.35 LUMBER"
    LUMBER_136 = "0.9x0.25x0.35 LUMBER", "0.9x0.25x0.35 LUMBER"
    LUMBER_137 = "1.2x0.025x0.04 LUMBER", "1.2x0.025x0.04 LUMBER"
    LUMBER_138 = "1.2x0.025x0.05 LUMBER", "1.2x0.025x0.05 LUMBER"
    LUMBER_139 = "1.2x0.025x0.075 LUMBER", "1.2x0.025x0.075 LUMBER"
    LUMBER_140 = "1.2x0.025x0.1 LUMBER", "1.2x0.025x0.1 LUMBER"
    LUMBER_141 = "1.2x0.025x0.125 LUMBER", "1.2x0.025x0.125 LUMBER"
    LUMBER_142 = "1.2x0.025x0.15 LUMBER", "1.2x0.025x0.15 LUMBER"
    LUMBER_143 = "1.2x0.025x0.175 LUMBER", "1.2x0.025x0.175 LUMBER"
    LUMBER_144 = "1.2x0.025x0.2 LUMBER", "1.2x0.025x0.2 LUMBER"
    LUMBER_145 = "1.2x0.025x0.225 LUMBER", "1.2x0.025x0.225 LUMBER"
    LUMBER_146 = "1.2x0.025x0.25 LUMBER", "1.2x0.025x0.25 LUMBER"
    LUMBER_147 = "1.2x0.025x0.275 LUMBER", "1.2x0.025x0.275 LUMBER"
    LUMBER_148 = "1.2x0.025x0.3 LUMBER", "1.2x0.025x0.3 LUMBER"
    LUMBER_149 = "1.2x0.025x0.325 LUMBER", "1.2x0.025x0.325 LUMBER"
    LUMBER_150 = "1.2x0.025x0.35 LUMBER", "1.2x0.025x0.35 LUMBER"
    LUMBER_151 = "1.2x0.05x0.04 LUMBER", "1.2x0.05x0.04 LUMBER"
    LUMBER_152 = "1.2x0.05x0.05 LUMBER", "1.2x0.05x0.05 LUMBER"
    LUMBER_153 = "1.2x0.05x0.075 LUMBER", "1.2x0.05x0.075 LUMBER"
    LUMBER_154 = "1.2x0.05x0.1 LUMBER", "1.2x0.05x0.1 LUMBER"
    LUMBER_155 = "1.2x0.05x0.125 LUMBER", "1.2x0.05x0.125 LUMBER"
    LUMBER_156 = "1.2x0.05x0.15 LUMBER", "1.2x0.05x0.15 LUMBER"
    LUMBER_157 = "1.2x0.05x0.175 LUMBER", "1.2x0.05x0.175 LUMBER"
    LUMBER_158 = "1.2x0.05x0.2 LUMBER", "1.2x0.05x0.2 LUMBER"
    LUMBER_159 = "1.2x0.05x0.225 LUMBER", "1.2x0.05x0.225 LUMBER"
    LUMBER_160 = "1.2x0.05x0.25 LUMBER", "1.2x0.05x0.25 LUMBER"
    LUMBER_161 = "1.2x0.05x0.275 LUMBER", "1.2x0.05x0.275 LUMBER"
    LUMBER_162 = "1.2x0.05x0.3 LUMBER", "1.2x0.05x0.3 LUMBER"
    LUMBER_163 = "1.2x0.05x0.325 LUMBER", "1.2x0.05x0.325 LUMBER"
    LUMBER_164 = "1.2x0.05x0.35 LUMBER", "1.2x0.05x0.35 LUMBER"
    LUMBER_165 = "1.3x0.025x0.04 LUMBER", "1.3x0.025x0.04 LUMBER"
    LUMBER_166 = "1.3x0.025x0.05 LUMBER", "1.3x0.025x0.05 LUMBER"
    LUMBER_167 = "1.3x0.025x0.075 LUMBER", "1.3x0.025x0.075 LUMBER"
    LUMBER_168 = "1.3x0.025x0.1 LUMBER", "1.3x0.025x0.1 LUMBER"
    LUMBER_169 = "1.3x0.025x0.125 LUMBER", "1.3x0.025x0.125 LUMBER"
    LUMBER_170 = "1.3x0.025x0.15 LUMBER", "1.3x0.025x0.15 LUMBER"
    LUMBER_171 = "1.3x0.025x0.175 LUMBER", "1.3x0.025x0.175 LUMBER"
    LUMBER_172 = "1.3x0.025x0.2 LUMBER", "1.3x0.025x0.2 LUMBER"
    LUMBER_173 = "1.3x0.025x0.225 LUMBER", "1.3x0.025x0.225 LUMBER"
    LUMBER_174 = "1.3x0.025x0.25 LUMBER", "1.3x0.025x0.25 LUMBER"
    LUMBER_175 = "1.3x0.025x0.275 LUMBER", "1.3x0.025x0.275 LUMBER"
    LUMBER_176 = "1.3x0.025x0.3 LUMBER", "1.3x0.025x0.3 LUMBER"
    LUMBER_177 = "1.3x0.025x0.325 LUMBER", "1.3x0.025x0.325 LUMBER"
    LUMBER_178 = "1.3x0.025x0.35 LUMBER", "1.3x0.025x0.35 LUMBER"
    LUMBER_179 = "1.3x0.05x0.04 LUMBER", "1.3x0.05x0.04 LUMBER"
    LUMBER_180 = "1.3x0.05x0.05 LUMBER", "1.3x0.05x0.05 LUMBER"
    LUMBER_181 = "1.3x0.05x0.075 LUMBER", "1.3x0.05x0.075 LUMBER"
    LUMBER_182 = "1.3x0.05x0.1 LUMBER", "1.3x0.05x0.1 LUMBER"
    LUMBER_183 = "1.3x0.05x0.125 LUMBER", "1.3x0.05x0.125 LUMBER"
    LUMBER_184 = "1.3x0.05x0.15 LUMBER", "1.3x0.05x0.15 LUMBER"
    LUMBER_185 = "1.3x0.05x0.175 LUMBER", "1.3x0.05x0.175 LUMBER"
    LUMBER_186 = "1.3x0.05x0.2 LUMBER", "1.3x0.05x0.2 LUMBER"
    LUMBER_187 = "1.3x0.05x0.225 LUMBER", "1.3x0.05x0.225 LUMBER"
    LUMBER_188 = "1.3x0.05x0.25 LUMBER", "1.3x0.05x0.25 LUMBER"
    LUMBER_189 = "1.3x0.05x0.275 LUMBER", "1.3x0.05x0.275 LUMBER"
    LUMBER_190 = "1.3x0.05x0.3 LUMBER", "1.3x0.05x0.3 LUMBER"
    LUMBER_191 = "1.3x0.05x0.325 LUMBER", "1.3x0.05x0.325 LUMBER"
    LUMBER_192 = "1.3x0.05x0.35 LUMBER", "1.3x0.05x0.35 LUMBER"
    LUMBER_193 = "1.5x0.025x0.04 LUMBER", "1.5x0.025x0.04 LUMBER"
    LUMBER_194 = "1.5x0.025x0.05 LUMBER", "1.5x0.025x0.05 LUMBER"
    LUMBER_195 = "1.5x0.025x0.075 LUMBER", "1.5x0.025x0.075 LUMBER"
    LUMBER_196 = "1.5x0.025x0.1 LUMBER", "1.5x0.025x0.1 LUMBER"
    LUMBER_197 = "1.5x0.025x0.125 LUMBER", "1.5x0.025x0.125 LUMBER"
    LUMBER_198 = "1.5x0.025x0.15 LUMBER", "1.5x0.025x0.15 LUMBER"
    LUMBER_199 = "1.5x0.025x0.175 LUMBER", "1.5x0.025x0.175 LUMBER"
    LUMBER_200 = "1.5x0.025x0.2 LUMBER", "1.5x0.025x0.2 LUMBER"
    LUMBER_201 = "1.5x0.025x0.225 LUMBER", "1.5x0.025x0.225 LUMBER"
    LUMBER_202 = "1.5x0.025x0.25 LUMBER", "1.5x0.025x0.25 LUMBER"
    LUMBER_203 = "1.5x0.025x0.275 LUMBER", "1.5x0.025x0.275 LUMBER"
    LUMBER_204 = "1.5x0.025x0.3 LUMBER", "1.5x0.025x0.3 LUMBER"
    LUMBER_205 = "1.5x0.025x0.325 LUMBER", "1.5x0.025x0.325 LUMBER"
    LUMBER_206 = "1.5x0.025x0.35 LUMBER", "1.5x0.025x0.35 LUMBER"
    LUMBER_207 = "1.5x0.05x0.04 LUMBER", "1.5x0.05x0.04 LUMBER"
    LUMBER_208 = "1.5x0.05x0.05 LUMBER", "1.5x0.05x0.05 LUMBER"
    LUMBER_209 = "1.5x0.05x0.075 LUMBER", "1.5x0.05x0.075 LUMBER"
    LUMBER_210 = "1.5x0.05x0.1 LUMBER", "1.5x0.05x0.1 LUMBER"
    LUMBER_211 = "1.5x0.05x0.125 LUMBER", "1.5x0.05x0.125 LUMBER"
    LUMBER_212 = "1.5x0.05x0.15 LUMBER", "1.5x0.05x0.15 LUMBER"
    LUMBER_213 = "1.5x0.05x0.175 LUMBER", "1.5x0.05x0.175 LUMBER"
    LUMBER_214 = "1.5x0.05x0.2 LUMBER", "1.5x0.05x0.2 LUMBER"
    LUMBER_215 = "1.5x0.05x0.225 LUMBER", "1.5x0.05x0.225 LUMBER"
    LUMBER_216 = "1.5x0.05x0.25 LUMBER", "1.5x0.05x0.25 LUMBER"
    LUMBER_217 = "1.5x0.05x0.275 LUMBER", "1.5x0.05x0.275 LUMBER"
    LUMBER_218 = "1.5x0.05x0.3 LUMBER", "1.5x0.05x0.3 LUMBER"
    LUMBER_219 = "1.5x0.05x0.325 LUMBER", "1.5x0.05x0.325 LUMBER"
    LUMBER_220 = "1.5x0.05x0.35 LUMBER", "1.5x0.05x0.35 LUMBER"
    LUMBER_221 = "2.5x0.025x0.04 LUMBER", "2.5x0.025x0.04 LUMBER"
    LUMBER_222 = "2.5x0.025x0.05 LUMBER", "2.5x0.025x0.05 LUMBER"
    LUMBER_223 = "2.5x0.025x0.075 LUMBER", "2.5x0.025x0.075 LUMBER"
    LUMBER_224 = "2.5x0.025x0.1 LUMBER", "2.5x0.025x0.1 LUMBER"
    LUMBER_225 = "2.5x0.025x0.125 LUMBER", "2.5x0.025x0.125 LUMBER"
    LUMBER_226 = "2.5x0.025x0.175 LUMBER", "2.5x0.025x0.175 LUMBER"
    LUMBER_227 = "2.5x0.025x0.2 LUMBER", "2.5x0.025x0.2 LUMBER"
    LUMBER_228 = "2.5x0.025x0.225 LUMBER", "2.5x0.025x0.225 LUMBER"
    LUMBER_229 = "2.5x0.025x0.25 LUMBER", "2.5x0.025x0.25 LUMBER"
    LUMBER_230 = "2.5x0.025x0.275 LUMBER", "2.5x0.025x0.275 LUMBER"
    LUMBER_231 = "2.5x0.025x0.3 LUMBER", "2.5x0.025x0.3 LUMBER"
    LUMBER_232 = "2.5x0.025x0.325 LUMBER", "2.5x0.025x0.325 LUMBER"
    LUMBER_233 = "2.5x0.025x0.35 LUMBER", "2.5x0.025x0.35 LUMBER"
    LUMBER_234 = "2.5x0.05x0.04 LUMBER", "2.5x0.05x0.04 LUMBER"
    LUMBER_235 = "2.5x0.05x0.05 LUMBER", "2.5x0.05x0.05 LUMBER"
    LUMBER_236 = "2.5x0.05x0.075 LUMBER", "2.5x0.05x0.075 LUMBER"
    LUMBER_237 = "2.5x0.05x0.1 LUMBER", "2.5x0.05x0.1 LUMBER"
    LUMBER_238 = "2.5x0.05x0.125 LUMBER", "2.5x0.05x0.125 LUMBER"
    LUMBER_239 = "2.5x0.05x0.15 LUMBER", "2.5x0.05x0.15 LUMBER"
    LUMBER_240 = "2.5x0.05x0.175 LUMBER", "2.5x0.05x0.175 LUMBER"
    LUMBER_241 = "2.5x0.05x0.2 LUMBER", "2.5x0.05x0.2 LUMBER"
    LUMBER_242 = "2.5x0.05x0.225 LUMBER", "2.5x0.05x0.225 LUMBER"
    LUMBER_243 = "2.5x0.05x0.25 LUMBER", "2.5x0.05x0.25 LUMBER"
    LUMBER_244 = "2.5x0.05x0.275 LUMBER", "2.5x0.05x0.275 LUMBER"
    LUMBER_245 = "2.5x0.05x0.3 LUMBER", "2.5x0.05x0.3 LUMBER"
    LUMBER_246 = "2.5x0.05x0.325 LUMBER", "2.5x0.05x0.325 LUMBER"
    LUMBER_247 = "2.5x0.05x0.35 LUMBER", "2.5x0.05x0.35 LUMBER"
    LUMBER_248 = "2x0.025x0.04 LUMBER", "2x0.025x0.04 LUMBER"
    LUMBER_249 = "2x0.025x0.05 LUMBER", "2x0.025x0.05 LUMBER"
    LUMBER_250 = "2x0.025x0.075 LUMBER", "2x0.025x0.075 LUMBER"
    LUMBER_251 = "2x0.025x0.1 LUMBER", "2x0.025x0.1 LUMBER"
    LUMBER_252 = "2x0.025x0.125 LUMBER", "2x0.025x0.125 LUMBER"
    LUMBER_253 = "2x0.025x0.15 LUMBER", "2x0.025x0.15 LUMBER"
    LUMBER_254 = "2x0.025x0.175 LUMBER", "2x0.025x0.175 LUMBER"
    LUMBER_255 = "2x0.025x0.2 LUMBER", "2x0.025x0.2 LUMBER"
    LUMBER_256 = "2x0.025x0.225 LUMBER", "2x0.025x0.225 LUMBER"
    LUMBER_257 = "2x0.025x0.25 LUMBER", "2x0.025x0.25 LUMBER"
    LUMBER_258 = "2x0.025x0.275 LUMBER", "2x0.025x0.275 LUMBER"
    LUMBER_259 = "2x0.025x0.3 LUMBER", "2x0.025x0.3 LUMBER"
    LUMBER_260 = "2x0.025x0.325 LUMBER", "2x0.025x0.325 LUMBER"
    LUMBER_261 = "2x0.025x0.35 LUMBER", "2x0.025x0.35 LUMBER"
    LUMBER_262 = "2x0.05x0.04 LUMBER", "2x0.05x0.04 LUMBER"
    LUMBER_263 = "2x0.05x0.05 LUMBER", "2x0.05x0.05 LUMBER"
    LUMBER_264 = "2x0.05x0.075 LUMBER", "2x0.05x0.075 LUMBER"
    LUMBER_265 = "2x0.05x0.1 LUMBER", "2x0.05x0.1 LUMBER"
    LUMBER_266 = "2x0.05x0.125 LUMBER", "2x0.05x0.125 LUMBER"
    LUMBER_267 = "2x0.05x0.15 LUMBER", "2x0.05x0.15 LUMBER"
    LUMBER_268 = "2x0.05x0.175 LUMBER", "2x0.05x0.175 LUMBER"
    LUMBER_269 = "2x0.05x0.2 LUMBER", "2x0.05x0.2 LUMBER"
    LUMBER_270 = "2x0.05x0.225 LUMBER", "2x0.05x0.225 LUMBER"
    LUMBER_271 = "2x0.05x0.25 LUMBER", "2x0.05x0.25 LUMBER"
    LUMBER_272 = "2x0.05x0.275 LUMBER", "2x0.05x0.275 LUMBER"
    LUMBER_273 = "2x0.05x0.3 LUMBER", "2x0.05x0.3 LUMBER"
    LUMBER_274 = "2x0.05x0.325 LUMBER", "2x0.05x0.325 LUMBER"
    LUMBER_275 = "2x0.05x0.35 LUMBER", "2x0.05x0.35 LUMBER"
    LUMBER_276 = "3.5x0.025x0.05 LUMBER", "3.5x0.025x0.05 LUMBER"
    LUMBER_277 = "3.5x0.025x0.075 LUMBER", "3.5x0.025x0.075 LUMBER"
    LUMBER_278 = "3.5x0.025x0.1 LUMBER", "3.5x0.025x0.1 LUMBER"
    LUMBER_279 = "3.5x0.025x0.125 LUMBER", "3.5x0.025x0.125 LUMBER"
    LUMBER_280 = "3.5x0.025x0.15 LUMBER", "3.5x0.025x0.15 LUMBER"
    LUMBER_281 = "3.5x0.025x0.175 LUMBER", "3.5x0.025x0.175 LUMBER"
    LUMBER_282 = "3.5x0.025x0.2 LUMBER", "3.5x0.025x0.2 LUMBER"
    LUMBER_283 = "3.5x0.025x0.225 LUMBER", "3.5x0.025x0.225 LUMBER"
    LUMBER_284 = "3.5x0.025x0.25 LUMBER", "3.5x0.025x0.25 LUMBER"
    LUMBER_285 = "3.5x0.025x0.275 LUMBER", "3.5x0.025x0.275 LUMBER"
    LUMBER_286 = "3.5x0.025x0.325 LUMBER", "3.5x0.025x0.325 LUMBER"
    LUMBER_287 = "3.5x0.025x0.35 LUMBER", "3.5x0.025x0.35 LUMBER"
    LUMBER_288 = "3.5x0.05x0.04 LUMBER", "3.5x0.05x0.04 LUMBER"
    LUMBER_289 = "3.5x0.05x0.05 LUMBER", "3.5x0.05x0.05 LUMBER"
    LUMBER_290 = "3.5x0.05x0.075 LUMBER", "3.5x0.05x0.075 LUMBER"
    LUMBER_291 = "3.5x0.05x0.1 LUMBER", "3.5x0.05x0.1 LUMBER"
    LUMBER_292 = "3.5x0.05x0.125 LUMBER", "3.5x0.05x0.125 LUMBER"
    LUMBER_293 = "3.5x0.05x0.15 LUMBER", "3.5x0.05x0.15 LUMBER"
    LUMBER_294 = "3.5x0.05x0.175 LUMBER", "3.5x0.05x0.175 LUMBER"
    LUMBER_295 = "3.5x0.05x0.2 LUMBER", "3.5x0.05x0.2 LUMBER"
    LUMBER_296 = "3.5x0.05x0.225 LUMBER", "3.5x0.05x0.225 LUMBER"
    LUMBER_298 = "3.5x0.05x0.25 LUMBER", "3.5x0.05x0.25 LUMBER"
    LUMBER_300 = "3.5x0.05x0.275 LUMBER", "3.5x0.05x0.275 LUMBER"
    LUMBER_301 = "3.5x0.05x0.3 LUMBER", "3.5x0.05x0.3 LUMBER"
    LUMBER_302 = "3.5x0.05x0.325 LUMBER", "3.5x0.05x0.325 LUMBER"
    LUMBER_303 = "3.5x0.05x0.35 LUMBER", "3.5x0.05x0.35 LUMBER"
    LUMBER_304 = "3.5x0.25x0.3 LUMBER", "3.5x0.25x0.3 LUMBER"
    LUMBER_305 = "3x0.025x0.04 LUMBER", "3x0.025x0.04 LUMBER"
    LUMBER_306 = "3x0.025x0.05 LUMBER", "3x0.025x0.05 LUMBER"
    LUMBER_307 = "3x0.025x0.1 LUMBER", "3x0.025x0.1 LUMBER"
    LUMBER_308 = "3x0.025x0.125 LUMBER", "3x0.025x0.125 LUMBER"
    LUMBER_309 = "3x0.025x0.15 LUMBER", "3x0.025x0.15 LUMBER"
    LUMBER_310 = "3x0.025x0.175 LUMBER", "3x0.025x0.175 LUMBER"
    LUMBER_311 = "3x0.025x0.2 LUMBER", "3x0.025x0.2 LUMBER"
    LUMBER_312 = "3x0.025x0.225 LUMBER", "3x0.025x0.225 LUMBER"
    LUMBER_313 = "3x0.025x0.25 LUMBER", "3x0.025x0.25 LUMBER"
    LUMBER_314 = "3x0.025x0.275 LUMBER", "3x0.025x0.275 LUMBER"
    LUMBER_315 = "3x0.025x0.3 LUMBER", "3x0.025x0.3 LUMBER"
    LUMBER_316 = "3x0.025x0.325 LUMBER", "3x0.025x0.325 LUMBER"
    LUMBER_317 = "3x0.025x0.35 LUMBER", "3x0.025x0.35 LUMBER"
    LUMBER_318 = "3x0.025x0.75 LUMBER", "3x0.025x0.75 LUMBER"
    LUMBER_319 = "3x0.05x0.04 LUMBER", "3x0.05x0.04 LUMBER"
    LUMBER_320 = "3x0.05x0.05 LUMBER", "3x0.05x0.05 LUMBER"
    LUMBER_321 = "3x0.05x0.075 LUMBER", "3x0.05x0.075 LUMBER"
    LUMBER_322 = "3x0.05x0.1 LUMBER", "3x0.05x0.1 LUMBER"
    LUMBER_323 = "3x0.05x0.125 LUMBER", "3x0.05x0.125 LUMBER"
    LUMBER_324 = "3x0.05x0.15 LUMBER", "3x0.05x0.15 LUMBER"
    LUMBER_325 = "3x0.05x0.175 LUMBER", "3x0.05x0.175 LUMBER"
    LUMBER_326 = "3x0.05x0.2 LUMBER", "3x0.05x0.2 LUMBER"
    LUMBER_328 = "3x0.05x0.225 LUMBER", "3x0.05x0.225 LUMBER"
    LUMBER_329 = "3x0.05x0.25 LUMBER", "3x0.05x0.25 LUMBER"
    LUMBER_331 = "3x0.05x0.275 LUMBER", "3x0.05x0.275 LUMBER"
    LUMBER_332 = "3x0.05x0.3 LUMBER", "3x0.05x0.3 LUMBER"
    LUMBER_333 = "3x0.05x0.325 LUMBER", "3x0.05x0.325 LUMBER"
    LUMBER_334 = "3x0.05x0.35 LUMBER", "3x0.05x0.35 LUMBER"
    LUMBER_335 = "4x0.0250.175 LUMBER", "4x0.0250.175 LUMBER"
    LUMBER_336 = "4x0.025x0.05 LUMBER", "4x0.025x0.05 LUMBER"
    LUMBER_337 = "4x0.025x0.075 LUMBER", "4x0.025x0.075 LUMBER"
    LUMBER_338 = "4x0.025x0.1 LUMBER", "4x0.025x0.1 LUMBER"
    LUMBER_339 = "4x0.025x0.125 LUMBER", "4x0.025x0.125 LUMBER"
    LUMBER_340 = "4x0.025x0.15 LUMBER", "4x0.025x0.15 LUMBER"
    LUMBER_341 = "4x0.025x0.2 LUMBER", "4x0.025x0.2 LUMBER"
    LUMBER_342 = "4x0.025x0.225 LUMBER", "4x0.025x0.225 LUMBER"
    LUMBER_343 = "4x0.025x0.25 LUMBER", "4x0.025x0.25 LUMBER"
    LUMBER_344 = "4x0.025x0.275 LUMBER", "4x0.025x0.275 LUMBER"
    LUMBER_345 = "4x0.025x0.3 LUMBER", "4x0.025x0.3 LUMBER"
    LUMBER_346 = "4x0.025x0.325 LUMBER", "4x0.025x0.325 LUMBER"
    LUMBER_347 = "4x0.05*0.15 LUMBER", "4x0.05*0.15 LUMBER"
    LUMBER_348 = "4x0.05x0.04 LUMBER", "4x0.05x0.04 LUMBER"
    LUMBER_349 = "4x0.05x0.05 LUMBER", "4x0.05x0.05 LUMBER"
    LUMBER_350 = "4x0.05x0.075 LUMBER", "4x0.05x0.075 LUMBER"
    LUMBER_351 = "4x0.05x0.1 LUMBER", "4x0.05x0.1 LUMBER"
    LUMBER_352 = "4x0.05x0.125 LUMBER", "4x0.05x0.125 LUMBER"
    LUMBER_353 = "4x0.05x0.175 LUMBER", "4x0.05x0.175 LUMBER"
    LUMBER_354 = "4x0.05x0.2 LUMBER", "4x0.05x0.2 LUMBER"
    LUMBER_355 = "4x0.05x0.225 LUMBER", "4x0.05x0.225 LUMBER"
    LUMBER_356 = "4x0.05x0.25 LUMBER", "4x0.05x0.25 LUMBER"
    LUMBER_357 = "4x0.05x0.275 LUMBER", "4x0.05x0.275 LUMBER"
    LUMBER_358 = "4x0.05x0.3 LUMBER", "4x0.05x0.3 LUMBER"
    LUMBER_359 = "4x0.05x0.325 LUMBER", "4x0.05x0.325 LUMBER"
    Grade1_LUMBER = "Grade1 LUMBER", "Grade1 LUMBER"
    Grade2_LUMBER = "Grade2 LUMBER", "Grade2 LUMBER"
    Grade3_LUMBER = "Grade3 LUMBER", "Grade3 LUMBER"
    Scrabs_LUMBER = "Scrabs LUMBER", "Scrabs LUMBER"
    Sawudust_LUMBER = "Sawudust LUMBER", "Sawudust LUMBER"
    MDF_1 = "2.44x1.22x0.1 MDF", "2.44x1.22x0.1 MDF"
    MDF_2 = "2.44x1.22x0.12 MDF", "2.44x1.22x0.12 MDF"
    MDF_3 = "2.44x1.22x0.14 MDF", "2.44x1.22x0.14 MDF"
    MDF_4 = "2.44x1.22x0.16 MDF", "2.44x1.22x0.16 MDF"
    MDF_5 = "2.44x1.22x0.18 MDF", "2.44x1.22x0.18 MDF"
    Bamboo_NON_TIMBER_PRODUCT = "Bamboo NON_TIMBER_PRODUCT", "Bamboo NON_TIMBER_PRODUCT"
    Coffee_NON_TIMBER_PRODUCT = "Coffee NON_TIMBER_PRODUCT", "Coffee NON_TIMBER_PRODUCT"
    Incence__NON_TIMBER_PRODUCT = (
        "Incence  NON_TIMBER_PRODUCT",
        "Incence  NON_TIMBER_PRODUCT",
    )
    Gum_NON_TIMBER_PRODUCT = "Gum NON_TIMBER_PRODUCT", "Gum NON_TIMBER_PRODUCT"
    PLYWOOD_1 = "2.44x1.22x0.03 PLYWOOD", "2.44x1.22x0.03 PLYWOOD"
    PLYWOOD_2 = "2.44x1.22x0.06 PLYWOOD", "2.44x1.22x0.06 PLYWOOD"
    PLYWOOD_3 = "2.44x1.22x0.08 PLYWOOD", "2.44x1.22x0.08 PLYWOOD"
    PLYWOOD_4 = "2.44x1.22x0.1 PLYWOOD", "2.44x1.22x0.1 PLYWOOD"
    PLYWOOD_5 = "2.44x1.22x0.14 PLYWOOD", "2.44x1.22x0.14 PLYWOOD"
    PLYWOOD_6 = "2.44x1.22x0.16 PLYWOOD", "2.44x1.22x0.16 PLYWOOD"
    PLYWOOD_7 = "2.44x1.22x0.18 PLYWOOD", "2.44x1.22x0.18 PLYWOOD"
    PLYWOOD_8 = "2.4x1.22x0.08 PLYWOOD", "2.4x1.22x0.08 PLYWOOD"
    TRANSMISSION_POLE_1 = "10m length TRANSMISSION_POLE", "10m length TRANSMISSION_POLE"
    TRANSMISSION_POLE_2 = "11m length TRANSMISSION_POLE", "11m length TRANSMISSION_POLE"
    TRANSMISSION_POLE_3 = "12m length TRANSMISSION_POLE", "12m length TRANSMISSION_POLE"
    TRANSMISSION_POLE_4 = "7m length TRANSMISSION_POLE", "7m length TRANSMISSION_POLE"
    TRANSMISSION_POLE_5 = "8m length TRANSMISSION_POLE", "8m length TRANSMISSION_POLE"
    TRANSMISSION_POLE_6 = "9m length TRANSMISSION_POLE", "9m length TRANSMISSION_POLE"
    SAWDUST = "SAWDUST", "Sawdust"
    SLAB_1 = "Grade1", "Grade 1"
    SLAB_2 = "Grade2", "Grade 2"
    SLAB_3 = "Grade3", "Grade 3"
    SCRABS = "SCRABS", "Scrabs"


class ProductType(models.TextChoices):
    TRANSMISSION_POLE = "TRANSMISSION_POLE", "Transmission Pole"
    CONSTRUCTION_WOOD = "CONSTRUCTION_WOOD", "Construction Wood"
    LOG = "LOG", "Log"
    LUMBER = "LUMBER", "Lumber"
    NON_TIMBER_PRODUCT = "NON_TIMBER_PRODUCT", "Non Timber Product"
    LOG_TIMBER_PREPARATION = "LOG_TIMBER_PREPARATION", "Log Timber Preparation"
    FIREWOOD = "FIREWOOD", "Firewood"
    CHARCOAL_BRIQUETTE = "CHARCOAL_BRIQUETTE", "Charcoal Briquette"
    ESSENTIAL_OIL = "ESSENTIAL_OIL", "Essential oil"
    PLYWOOD = "PLYWOOD", "Plywood"
    MDF = "MDF", "MDF"
    SAWDUST = "SAWDUST", "Sawdust"
    SLAB = "SLAB", "Slab"
    SCRABS = "SCRABS", "Scrabs"


# Entities for additional forms
class Item(models.Model):
    title = models.CharField(
        max_length=200, null=True, blank=True, choices=ProductName, db_index=True
    )
    species = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    date = models.DateField(null=False, blank=False, default=timezone.now)
    metadata = models.JSONField(null=True, blank=True)
    item_type = models.CharField(
        max_length=25, null=False, blank=False, choices=ItemType, db_index=True
    )
    product_type = models.CharField(
        max_length=200, null=True, blank=True, choices=ProductType, db_index=True
    )
    unit = models.CharField(max_length=100, null=True, blank=True)
    stock_code = models.CharField(max_length=100, null=True, blank=True)
    code_single = models.CharField(max_length=100, null=True, blank=True)
    length = models.FloatField(null=True, blank=True)
    bottom_diameter = models.FloatField(null=True, blank=True)
    middle_diameter = models.FloatField(null=True, blank=True)
    top_diameter = models.FloatField(null=True, blank=True)

    @staticmethod
    def get_item(title, species, item_type, unit=None):
        item = Item.objects.filter(species=species, item_type=item_type).first()
        if item:
            return item

        new_item = Item(title=title, species=species, item_type=item_type, unit=unit)
        new_item.save()
        return new_item

    @staticmethod
    def get_product(title, species, product_type, unit=None):
        product = Item.objects.filter(
            species=species,
            item_type=ItemType.PRODUCT,
            product_type=product_type,
            title=title,
        ).first()
        if product:
            return product

        new_product = Item(
            title=title,
            species=species,
            item_type=ItemType.PRODUCT,
            product_type=product_type,
            unit=unit,
        )
        new_product.save()
        return new_product

    def __str__(self) -> str:
        if self.item_type != ItemType.PRODUCT:
            return f"{self.title} - {self.species}"
        return f"{self.title}"


class Batch(models.Model):
    batch_number = models.CharField(
        max_length=100, null=False, blank=False, db_index=True
    )
    source_site = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="source_site_batch",
        db_index=True,
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="item_batches", db_index=True
    )

    class Meta:
        unique_together = ("batch_number", "item")

    @staticmethod
    def get_batch(batch_number, source_site_id=None, item_id=None):
        batch = Batch.objects.filter(batch_number=batch_number, item_id=item_id).first()
        if not batch:
            if (
                not source_site_id
                or not Location.objects.filter(id=source_site_id).exists()
            ):
                raise ValueError("Source site is required to create a new batch")
            if not item_id or not Item.objects.filter(id=item_id).exists():
                raise ValueError("Item is required to create a new batch")
            batch = Batch(
                batch_number=batch_number,
                source_site_id=source_site_id,
                item_id=item_id,
            )
            batch.save()
            return batch

        return batch

    @staticmethod
    def get_batch_by_item(batch_number, item_id):
        batch = Batch.objects.filter(batch_number=batch_number, item_id=item_id)

        if not batch.exists():
            prev_batch = Batch.objects.filter(batch_number=batch_number).first()
            if not prev_batch:
                raise ValueError("Batch not found")
            else:
                new_batch = Batch(
                    batch_number=batch_number,
                    source_site=prev_batch.source_site,
                    item_id=item_id,
                )
                new_batch.save()
                return new_batch
        else:
            return batch.first()

    def __str__(self) -> str:
        return self.batch_number


class ItemInventory(models.Model):
    code = models.CharField(max_length=100, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, null=False, blank=False)
    subsection = models.CharField(max_length=100, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True, default=0.0)
    date = models.DateField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    cost = models.FloatField(null=True, blank=True, default=0.0)
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name="inventories"
    )
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    source_site = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="source_site_inventories",
    )

    @staticmethod
    def get_inventory(item: Item, location: Location, source_site: Location):
        inventory = ItemInventory.objects.filter(
            item=item, location=location, source_site=source_site
        )
        if inventory.exists():
            return inventory.first()
        inventory = ItemInventory(
            item=item, location=location, source_site=source_site, amount=0
        )
        inventory.save()
        return inventory

    @staticmethod
    def get_inventory_by_batch(location: Location, batch: Batch):
        inventory = ItemInventory.objects.filter(
            item=batch.item, location=location, batch=batch
        )
        if inventory.exists():
            return inventory.first()

        inventory = ItemInventory(
            item=batch.item,
            location=location,
            batch=batch,
            amount=0,
            source_site=batch.source_site,
        )
        inventory.save()
        return inventory

    def set_amount(self, amount, reason, location=None, source_site=None):
        log = ItemInventoryLog(
            affector_location=location,
            affector_source_site=source_site,
            reason=reason,
            amount_before_transaction=self.amount,
            amount_after_transaction=amount,
            inventory=self,
            cost=self.cost,
        )
        self.amount = float(amount)
        log.save()
        return log

    def decrease(self, amount, reason, location=None, source_site=None):
        log = ItemInventoryLog(
            affector_location=location,
            affector_source_site=source_site,
            reason=reason,
            amount_before_transaction=self.amount,
            amount_after_transaction=self.amount - float(amount),
            inventory=self,
            cost=self.cost,
        )
        self.amount -= float(amount)
        log.save()
        return log

    def increase(self, amount, reason, location=None, source_site=None):
        log = ItemInventoryLog(
            affector_location=location,
            affector_source_site=source_site,
            reason=reason,
            amount_before_transaction=self.amount,
            amount_after_transaction=self.amount + float(amount),
            inventory=self,
            cost=self.cost,
        )
        self.amount += float(amount)
        log.save()
        return log


class InventoryAffectorType(models.TextChoices):
    RECIEVE = "RECIEVE", "Recieve"
    TRANSPORT = "TRANSPORT", "Transport"
    PURCHASE = "PURCHASE", "Purchase"
    SALE = "SALE", "Sale"
    GIVE_AWAY = "GIVE_AWAY", "Give Away"
    GRADING = "GRADING", "Grading"
    TEST = "TEST", "Test"
    SURVIVAL_COUNT = "SURVIVAL_COUNT", "Survival Count"
    GRADE1 = "GRADE1", "Grade 1"
    GRADE3 = "GRADE3", "Grade 3"
    SOWING = "SOWING", "Sowing"
    GERMINATION = "GERMINATION", "Germination"
    THINNING = "THINNING", "Thinning"
    THINNING_SALE = "THINNING_SALE", "Thinning Sale"
    COPPICE_SALE = "COPPICE_SALE", "Coppice Sale"
    REGISTER_PRODUCT = "REGISTER_PRODUCT", "Register Product"
    FOREST_INVENTORY = "FOREST_INVENTORY", "Forest Inventory"


class ItemInventoryLog(models.Model):
    affector_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True
    )
    affector_source_site = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="source_site_log",
    )
    reason = models.CharField(
        max_length=100,
        choices=InventoryAffectorType,
        default=InventoryAffectorType.RECIEVE,
    )
    date = models.DateTimeField(default=timezone.now)
    amount_before_transaction = models.FloatField()
    amount_after_transaction = models.FloatField()
    inventory = models.ForeignKey(ItemInventory, on_delete=models.CASCADE)
    cost = models.FloatField()

    @property
    def amount(self):
        return self.amount_after_transaction - self.amount_before_transaction


class FormModelsBase(models.Model):
    createdDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)
    createdBy = models.ForeignKey(
        AfeUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Submitted By",
    )

    class Meta:
        abstract = True


class ItemTransportation(FormModelsBase):
    driver_name = models.CharField(max_length=100, null=True, blank=True)
    plate_number = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    from_location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="from_transportion",
        null=True,
        blank=True,
        db_index=True,
    )
    to_location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="to_transportion",
        null=True,
        blank=True,
        db_index=True,
    )
    source_site = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True, db_index=True
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT, db_index=True)
    amount = models.FloatField(null=True, blank=True)
    voucher_no = models.CharField(max_length=100, null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    receiver = models.ForeignKey(
        AfeUser, on_delete=models.CASCADE, null=True, blank=True, db_index=True
    )
    polygon_name = models.CharField(max_length=100, null=True, blank=True)
    polygon_centroid_location = models.TextField(null=True, blank=True)
    product_category = models.CharField(
        max_length=200, choices=ProductName, null=True, blank=True
    )
    expert_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.from_location} to {self.to_location}"

    def get_by_distinct_voucher(exclude_empty_batch=True, **filters):
        transportations = ItemTransportation.objects.filter(**filters)

        if exclude_empty_batch:
            transportations = transportations.exclude(batch__isnull=True)

        distinct = transportations.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for transport in distinct:
            if transport["voucher_no"] not in found_vouchers:
                found_vouchers.append(transport["voucher_no"])
                ids.append(transport["id"])
        return transportations.filter(id__in=ids).filter(itemrecieve__isnull=True)


class ItemPurchase(FormModelsBase):
    purity_percentage = models.FloatField(null=True, blank=True)
    amount = models.FloatField(null=False, blank=False)
    cost = models.FloatField(null=False, blank=False)
    unit = models.CharField(max_length=100, null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    collection_date = models.DateField(null=True, blank=True)
    collector = models.CharField(max_length=100, null=True, blank=True)
    expert = models.CharField(max_length=100, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    voucher_no = models.CharField(max_length=100, null=False, blank=False)
    resource = models.ForeignKey(
        ActivityResource, on_delete=models.CASCADE, null=True, blank=True
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class SaleType(models.TextChoices):
    STAMPAGE = "STAMPAGE", "Stampage"
    DEFAULT = "DEFAULT", "Default"


class ItemSale(FormModelsBase):
    # Core fields
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_index=True, verbose_name="Item")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True, db_index=True, verbose_name="Batch")
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True, db_index=True, verbose_name="Location"
    )
    date = models.DateField(null=True, blank=True, db_index=True, verbose_name="Sale Date")
    
    # Sale details
    amount = models.FloatField(null=True, blank=True, verbose_name="Amount", help_text="Quantity sold")
    unit_price = models.FloatField(null=True, blank=True, verbose_name="Unit Price")
    sale_price = models.FloatField(null=True, blank=True, verbose_name="Sale Price")
    total_rev_before_vat = models.FloatField(null=True, blank=True, verbose_name="Total Revenue Before VAT")
    
    # Customer/Vendor info
    client = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Client", db_index=True
    )
    seller = models.ForeignKey(
        AfeUser, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Seller", db_index=True
    )
    
    # Costs
    operational_cost = models.FloatField(null=True, blank=True, verbose_name="Operational Cost")
    seed_collection_cost = models.FloatField(null=True, blank=True, verbose_name="Seed Collection Cost")
    
    # Document fields
    voucher_no = models.CharField(max_length=100, null=True, blank=True, db_index=True, verbose_name="Voucher Number")
    order_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Order Number")
    tin_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="TIN Number")
    
    # Location/Polygon fields
    polygon_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Polygon Name")
    polygon_centroid_location = models.TextField(null=True, blank=True, verbose_name="Polygon Centroid Location")
    
    # Additional fields
    no_stand_trees_sold = models.IntegerField(null=True, blank=True, verbose_name="Number of Stand Trees Sold")
    product_category = models.CharField(
        max_length=200, null=True, blank=True, choices=ProductName, verbose_name="Product Category"
    )
    sale_type = models.CharField(
        max_length=100, choices=SaleType, default=SaleType.DEFAULT, verbose_name="Sale Type"
    )
    harvesting_start_date = models.DateField(null=True, blank=True, verbose_name="Harvesting Start Date")
    harvesting_end_date = models.DateField(null=True, blank=True, verbose_name="Harvesting End Date")
    
    # Missing fields that views expect
    createdBy = models.ForeignKey(
        AfeUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="item_sales",
        verbose_name="Created By"
    )
    unit = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="Unit",
        help_text="e.g., kg, pieces, tons, cubic meters"
    )
    product_type = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Product Type",
        help_text="Type of product being sold"
    )
    
    # Audit fields
    createdDate = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")
    updatedDate = models.DateTimeField(auto_now=True, verbose_name="Updated Date")
    
    class Meta:
        verbose_name = "Item Sale"
        verbose_name_plural = "Item Sales"
        ordering = ['-date', 'voucher_no']
        indexes = [
            models.Index(fields=['voucher_no', 'date']),
            models.Index(fields=['location', 'client']),
            models.Index(fields=['batch', 'item']),
            models.Index(fields=['sale_type', 'date']),
        ]
    
    def __str__(self):
        return f"{self.voucher_no} - {self.client} - {self.date}"
    
    @property
    def total_price(self):
     if self.amount and self.unit_price:
        return self.amount * self.unit_price
        return 0
            
    
    @property
    def calculated_total_rev_before_vat(self):
        """Calculate total revenue before VAT"""
        return self.total_price
    
    @property
    def vat_amount(self):
        """Calculate VAT amount (assuming 15% VAT)"""
        return self.total_price * 0.15
    
    @property
    def total_rev_after_vat(self):
        """Calculate total revenue after VAT"""
        return self.total_price + self.vat_amount
    
    @property
    def profit_margin(self):
        """Calculate profit margin"""
        if self.operational_cost and self.total_price:
            return self.total_price - self.operational_cost
        return 0.0
    
    @property
    def harvesting_duration_days(self):
        """Calculate harvesting duration in days"""
        if self.harvesting_start_date and self.harvesting_end_date:
            return (self.harvesting_end_date - self.harvesting_start_date).days
        return 0
    
    def get_revenue(self):
        """Get revenue (compatible with existing code)"""
        if self.total_rev_before_vat:
            return self.total_rev_before_vat
        return self.total_price
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure non-negative values
        if self.amount and self.amount < 0:
            raise ValidationError({"amount": "Amount cannot be negative"})
        
        if self.operational_cost and self.operational_cost < 0:
            raise ValidationError({"operational_cost": "Operational cost cannot be negative"})
        
        if self.seed_collection_cost and self.seed_collection_cost < 0:
            raise ValidationError({"seed_collection_cost": "Seed collection cost cannot be negative"})
        
        if self.sale_price and self.sale_price < 0:
            raise ValidationError({"sale_price": "Sale price cannot be negative"})
        
        # Validate dates
        if self.harvesting_start_date and self.harvesting_end_date:
            if self.harvesting_start_date > self.harvesting_end_date:
                raise ValidationError({
                    "harvesting_start_date": "Harvesting start date cannot be after end date"
                })
        
        # Date cannot be in the future
        if self.date and self.date > timezone.now().date():
            raise ValidationError({"date": "Date cannot be in the future"})
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_rev_before_vat if not set
        if not self.total_rev_before_vat and self.amount and self.unit_price:
            try:
                self.total_rev_before_vat = self.amount * float(self.unit_price)
            except (ValueError, TypeError):
                pass
        
        self.clean()
        super().save(*args, **kwargs)


class ItemRecieve(FormModelsBase):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True, db_index=True
    )
    date = models.DateField(null=False, blank=False)
    amount = models.FloatField(null=False, blank=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    from_location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sent_items",
    )
    to_location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="received_items",
    )
    source_site = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="source_site_received_items",
    )
    received_transportation = models.ForeignKey(
        ItemTransportation, on_delete=models.CASCADE, null=True, blank=True
    )
    voucher_no = models.CharField(max_length=100, null=True, blank=True)
    driver_name = models.CharField(max_length=100, null=True, blank=True)
    unit = models.CharField(max_length=100, null=True, blank=True)
    plate_number = models.CharField(max_length=100, null=True, blank=True)
    collection_date = models.DateField(null=True, blank=True)
    polygon_name = models.CharField(max_length=100, null=True, blank=True)
    polygon_centroid_location = models.TextField(null=True, blank=True)
    receiver = models.ForeignKey(
        AfeUser, on_delete=models.CASCADE, null=True, blank=True, db_index=True
    )
    expert_name = models.CharField(max_length=100, null=True, blank=True)


class TestResult(models.TextChoices):
    PASS = "PASS", "Pass"
    FAIL = "FAIL", "Fail"


class TestType(models.TextChoices):
    TEST = "TEST", "Test"
    QUARANTINE = "Quarantine", "Quarantine"


round_choices = (("1", "1"), ("2", "2"), ("3", "3"))


class Test(FormModelsBase):
    type = models.CharField(max_length=100, choices=TestType)
    tested_by = models.ForeignKey(
        AfeUser, on_delete=models.CASCADE, null=True, blank=True
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    round = models.CharField(
        max_length=100, choices=round_choices, null=True, blank=True
    )
    quantity = models.FloatField(null=True, blank=True)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    purity_percentage = models.FloatField(null=True, blank=True)
    germination_percentage = models.FloatField(null=True, blank=True)
    moisture_content = models.FloatField(null=True, blank=True)
    viable_seed_per_kilogram = models.FloatField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=TestResult)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    remark = models.TextField(null=True, blank=True)


class SurvivalCount(FormModelsBase):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, db_index=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, db_index=True)
    date = models.DateField()
    no_alive = models.IntegerField(default=0, help_text="Number of alive seedlings/trees")
    no_dead = models.IntegerField(default=0, help_text="Number of dead seedlings/trees")
    
    # Adding the missing fields that the view expects
    createdBy = models.ForeignKey(
        AfeUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="survival_counts",
        verbose_name="Created By"
    )
    
    # Optional: Add these for better tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Survival Count"
        verbose_name_plural = "Survival Counts"
        ordering = ['-date']
        unique_together = ['batch', 'location', 'date']  # Prevent duplicate entries for same batch/location/date
    
    def __str__(self):
        return f"{self.batch} - {self.location} - {self.date}"
    
    @property
    def total_survival(self):
        """Calculate total survival count"""
        return self.no_alive + self.no_dead
    
    @property
    def alive_percentage(self):
        """Calculate alive percentage"""
        total = self.no_alive + self.no_dead
        if total > 0:
            return (self.no_alive / total) * 100
        return 0.0
    
    @property
    def dead_percentage(self):
        """Calculate dead percentage"""
        total = self.no_alive + self.no_dead
        if total > 0:
            return (self.no_dead / total) * 100
        return 0.0


class SeedGrading(FormModelsBase):
    date = models.DateField()
    grade1_amount = models.FloatField()
    grade2_amount = models.FloatField()
    grade3_amount = models.FloatField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    decrease_log = models.ForeignKey(
        ItemInventoryLog,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="decrease_log",
    )
    increase_log = models.ForeignKey(
        ItemInventoryLog,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="increase_log",
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE)


class Handoff(FormModelsBase):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    amount = models.FloatField()
    date = models.DateField()
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True
    )


class Beatup(FormModelsBase):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    amount = models.FloatField()
    date = models.DateField()
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True
    )


class ThinningType(models.TextChoices):
    LOW = "LOW", "Low"
    HIGH = "HIGH", "High"
    PRE_COMMERCIAL = "PRE_COMMERCIAL", "Pre Commercial"
    COMMERCIAL = "COMMERCIAL", "Commercial"


class Thinning(FormModelsBase):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    amount = models.FloatField()
    date = models.DateField()
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True
    )
    product_category = models.CharField(max_length=200, choices=ProductName)
    thinning_type = models.CharField(max_length=100, choices=ThinningType)
    voucher_no = models.CharField(max_length=100, null=True, blank=True)


class ThinningSaleType(models.TextChoices):
    COPPICE = "COPPICE", "Coppice"
    THINNING = "THINNING", "Thinning"


class ThinningSale(FormModelsBase):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date = models.DateField()
    sold_to = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True
    )
    sold_by = models.CharField(max_length=100)
    sale_type = models.CharField(max_length=100, choices=ThinningSaleType)
    product_category = models.CharField(max_length=200, choices=ProductName)
    amount = models.FloatField()
    unit_price = models.FloatField()
    total_rev_before_vat = models.FloatField()
    voucher_no = models.CharField(max_length=100, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)


class ProductGiveAway(FormModelsBase):
    # Existing fields
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_index=True, verbose_name="Item")
    amount = models.FloatField(verbose_name="Amount", help_text="Quantity given away")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, db_index=True, verbose_name="Location")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, db_index=True, verbose_name="Batch")
    date = models.DateField(db_index=True, verbose_name="Giveaway Date")
    product_category = models.CharField(max_length=200, choices=ProductName, verbose_name="Product Category")
    unit_price = models.FloatField(verbose_name="Unit Price", help_text="Price per unit")
    total_price = models.FloatField(verbose_name="Total Price", help_text="Total price (amount × unit_price)")
    
    # Missing fields that the view expects
    createdBy = models.ForeignKey(
        AfeUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="product_giveaways",
        verbose_name="Created By"
    )
    unit = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="Unit",
        help_text="e.g., kg, liters, pieces, bags"
    )
    sender = models.CharField(
        max_length=200, 
        null=True, 
        blank=True, 
        verbose_name="Sender",
        help_text="Person/department sending the product"
    )
    receiver = models.CharField(
        max_length=200, 
        null=True, 
        blank=True, 
        verbose_name="Receiver",
        help_text="Person/department receiving the product"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Product Giveaway"
        verbose_name_plural = "Product Giveaways"
        ordering = ['-date', 'location']
        indexes = [
            models.Index(fields=['date', 'location']),
            models.Index(fields=['batch', 'date']),
            models.Index(fields=['sender', 'receiver']),
        ]
    
    def __str__(self):
        return f"{self.product_category} - {self.amount} {self.unit or 'units'} - {self.date}"
    
    # Properties for calculated fields
    @property
    def calculated_total_price(self):
        """Calculate total price (amount × unit_price)"""
        return self.amount * self.unit_price
    
    @property
    def formatted_total_price(self):
        """Return formatted total price"""
        return f"{self.total_price:,.2f}"
    
    # Validation
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure non-negative values
        if self.amount < 0:
            raise ValidationError({"amount": "Amount cannot be negative"})
        
        if self.unit_price < 0:
            raise ValidationError({"unit_price": "Unit price cannot be negative"})
        
        if self.total_price < 0:
            raise ValidationError({"total_price": "Total price cannot be negative"})
        
        # Validate total_price matches amount × unit_price
        calculated_total = self.amount * self.unit_price
        if abs(self.total_price - calculated_total) > 0.01:  # Allow small floating point difference
            raise ValidationError({
                "total_price": f"Total price ({self.total_price}) does not match amount × unit_price ({calculated_total})"
            })
        
        # Date cannot be in the future
        if self.date > timezone.now().date():
            raise ValidationError({"date": "Date cannot be in the future"})
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_price if not set correctly
        if self.total_price != self.amount * self.unit_price:
            self.total_price = self.amount * self.unit_price
        self.clean()
        super().save(*args, **kwargs)


class OperationalForestInventory(FormModelsBase):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    date = models.DateField()
    polygon_name = models.CharField(max_length=100)
    polygon_centroid_location = models.TextField()
    forest_volume_stand_level = models.FloatField()
    forest_volume_production = models.FloatField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE)


class HarvestingReport(FormModelsBase):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    date = models.DateField()
    polygon_name = models.CharField(max_length=100)
    polygon_centroid_location = models.TextField()
    product_type = models.CharField(max_length=200, choices=ProductName)
    amount = models.FloatField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    no_tree_fall = models.IntegerField()
    voucher_no = models.CharField(max_length=100)


class TimelyHarvestingReport(FormModelsBase):
    # Existing fields
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, db_index=True, verbose_name="Batch")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_index=True, verbose_name="Item")
    polygon_name = models.CharField(max_length=100, verbose_name="Polygon Name")
    polygon_centroid_location = models.TextField(verbose_name="Polygon Centroid Location")
    productive_area = models.FloatField(verbose_name="Productive Area (m³)", help_text="Volume in cubic meters")
    voucher_no = models.CharField(max_length=100, db_index=True, verbose_name="Voucher Number")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, db_index=True, verbose_name="Location")
    sold_to = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Sold To",
        db_index=True
    )
    total_volume = models.FloatField(
        verbose_name="Total Volume (m³)", 
        null=True, 
        blank=True,
        help_text="Total volume in cubic meters"
    )
    volume_in_hectare = models.FloatField(
        verbose_name="Volume per Hectare (m³/ha)", 
        null=True, 
        blank=True,
        help_text="Volume in cubic meters per hectare"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date", db_index=True)
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date", db_index=True)
    
    # Missing fields that the views expect (with corrected names - no trailing underscores)
    createdBy = models.ForeignKey(
        AfeUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="timely_harvesting_reports",
        verbose_name="Created By"
    )
    date = models.DateField(
        db_index=True, 
        verbose_name="Report Date",
        help_text="Date of the report",
        null=True,
        blank=True
    )
    
    # Performance fields (fixed - removed trailing underscore)
    performance_in_m3 = models.FloatField(  # Changed from performance_in_m3_
        null=True, 
        blank=True, 
        verbose_name="Performance (m³)",
        help_text="Performance in cubic meters"
    )
    performance_in_hectare = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="Performance (hectares)",
        help_text="Performance in hectares"
    )
    
    # Additional useful fields
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    harvesting_method = models.CharField(
        max_length=100,
        choices=[
            ('SELECTIVE', 'Selective'),
            ('CLEAR_CUT', 'Clear Cut'),
            ('THINNING', 'Thinning'),
        ],
        null=True,
        blank=True,
        verbose_name="Harvesting Method"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Timely Harvesting Report"
        verbose_name_plural = "Timely Harvesting Reports"
        ordering = ['-date', '-start_date']
        indexes = [
            models.Index(fields=['voucher_no', 'date']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['location', 'sold_to']),
            models.Index(fields=['batch', 'item']),
        ]
    
    def __str__(self):
        return f"{self.voucher_no} - {self.location} ({self.start_date} to {self.end_date})"
    
    # Properties for calculated fields
    @property
    def total_harvesting_days(self):
        """Calculate total harvesting days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0
    
    @property
    def daily_average_volume(self):
        """Calculate daily average volume"""
        days = self.total_harvesting_days
        if days > 0 and self.total_volume:
            return self.total_volume / days
        return 0.0
    
    @property
    def volume_performance_ratio(self):
        """Calculate volume performance ratio"""
        if self.productive_area > 0 and self.performance_in_m3:
            return self.performance_in_m3 / self.productive_area
        return 0.0
    
    @property
    def hectare_performance_ratio(self):
        """Calculate hectare performance ratio"""
        if self.productive_area > 0 and self.performance_in_hectare:
            return self.performance_in_hectare / self.productive_area
        return 0.0
    
    # Validation
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure dates are valid
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError({
                    "start_date": "Start date cannot be after end date"
                })
        
        # Ensure non-negative values
        if self.productive_area < 0:
            raise ValidationError({"productive_area": "Productive area cannot be negative"})
        
        if self.total_volume and self.total_volume < 0:
            raise ValidationError({"total_volume": "Total volume cannot be negative"})
        
        if self.volume_in_hectare and self.volume_in_hectare < 0:
            raise ValidationError({"volume_in_hectare": "Volume per hectare cannot be negative"})
        
        # Date cannot be in the future
        if self.date and self.date > timezone.now().date():
            raise ValidationError({"date": "Date cannot be in the future"})
    
    def save(self, *args, **kwargs):
        # Auto-calculate date if not set (use start_date or end_date)
        if not self.date:
            if self.start_date:
                self.date = self.start_date
            elif self.end_date:
                self.date = self.end_date
            else:
                self.date = timezone.now().date()
        
        # Auto-calculate performance fields if missing
        if not self.performance_in_m3 and self.total_volume:
            self.performance_in_m3 = self.total_volume
        
        if not self.performance_in_hectare and self.volume_in_hectare:
            self.performance_in_hectare = self.volume_in_hectare
        
        self.clean()
        super().save(*args, **kwargs)

class JobOportunity(FormModelsBase):
    no_groups_old = models.IntegerField()
    old_male_count = models.IntegerField()
    old_female_count = models.IntegerField()
    no_groups_new = models.IntegerField()
    new_male_count = models.IntegerField()
    new_female_count = models.IntegerField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()


class DownTime(FormModelsBase):
    start_date = models.DateField()
    end_date = models.DateField()
    downtime_hours = models.FloatField()
    reason = models.CharField(max_length=100)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)


class LumberStoredReport(FormModelsBase):
    daily_output = models.CharField(max_length=100)
    date = models.DateField()
    deliverer = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200, choices=ProductName)
    amount = models.FloatField()
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)


class ForestInventoryReport(FormModelsBase):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    amount = models.FloatField(verbose_name="Total Number of Trees")
    date = models.DateField()
    total_sample = models.IntegerField(verbose_name="Total Number of Sample")
    total_volume = models.FloatField(verbose_name="Total volume in m3")
    basal_area = models.FloatField(verbose_name="Basal Area in ha")


class FactoryProductionReport(FormModelsBase):
    product_category = models.CharField(max_length=200, choices=ProductName)
    product_name = models.CharField(max_length=200, choices=ProductName)
    amount = models.FloatField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()

class PlantationSiteSelectionReport(models.Model):
    site_code = models.CharField(max_length=50, unique=True)
    site_name = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    total_area = models.DecimalField(max_digits=10, decimal_places=2)
    
    SOIL_TYPES = [
        ('clay', 'Clay'),
        ('sandy', 'Sandy'),
        ('loamy', 'Loamy'),
        ('silt', 'Silt'),
    ]
    soil_type = models.CharField(max_length=20, choices=SOIL_TYPES)
    soil_ph = models.DecimalField(max_digits=4, decimal_places=2)
    drainage_rating = models.IntegerField()
    avg_temperature = models.DecimalField(max_digits=5, decimal_places=2)
    annual_rainfall = models.DecimalField(max_digits=7, decimal_places=2)
    suitability_score = models.IntegerField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'plantation_site_selection'
        verbose_name = 'Plantation Site Selection'
        verbose_name_plural = 'Plantation Site Selection'
class PlantedSeedlingReport(models.Model):
    plantation_site = models.ForeignKey(Location, on_delete=models.CASCADE)

    seedling_type = models.CharField(max_length=100)

    planted_quantity = models.PositiveIntegerField()

    survived_quantity = models.PositiveIntegerField(default=0)

    planting_date = models.DateField()

    planted_by = models.ForeignKey(
        AfeUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    rainfall_condition = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    remarks = models.TextField(blank=True, null=True)

    createdDate = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Planted Seedling Report"
        verbose_name_plural = "Planted Seedling Reports"

    def __str__(self):
        return f"{self.seedling_type} - {self.planted_quantity}"
class FormSubmission(AfeBaseModel):
    from core.attachable_forms.forms import get_form_choices

    name = models.CharField(
        max_length=50, null=False, blank=False, choices=get_form_choices()
    )
    detail_activity = models.ForeignKey(
        DetailActivity, on_delete=models.CASCADE, null=True
    )
    data = models.JSONField(null=False, blank=False)
    is_processed = models.BooleanField(default=False)
    actual_form_id = models.UUIDField(null=True, blank=True)


class DetailActivityType(AfeBaseModel):
    from core.attachable_forms.forms import get_form_choices

    name = models.CharField(max_length=500)
    activites = models.ManyToManyField(ActivityType)

    resource = models.BooleanField(default=True)
    input = models.BooleanField(default=True)
    tool = models.BooleanField(default=True)

    annual_resource_type = models.ForeignKey(
        ActivityResourceType,
        null=True,
        on_delete=models.SET_NULL,
        related_name="annual_activity_resource_type",
    )

    image_requirement = models.CharField(
        max_length=20,  # Added max_length
        choices=DOCUMENT_ATTACHMENT_CHOICES, 
        default="OPTIONAL"
    )
    document_requirement = models.CharField(
        max_length=20,  # Added max_length
        choices=DOCUMENT_ATTACHMENT_CHOICES, 
        default="OPTIONAL"
    )
    form = models.CharField(
        max_length=50,  # Added max_length
        null=True, 
        blank=True, 
        choices=get_form_choices()
    )

    def __str__(self) -> str:
        return self.name
class ImageSyncMeta(models.Model):
    model_id = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='sync_images/', null=True, blank=True)
    uploaded_date = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('synced', 'Synced'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Image Sync Metadata'
        verbose_name_plural = 'Image Sync Metadata'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.model_name} - {self.model_id} - {self.sync_status}"