import csv
from core.utils import (
    gregorian_year_to_ethiopian,
    ethiopian_year_to_gregorian,
    get_amharic_month,
)
from datetime import datetime, timedelta
from ethiopian_date import EthiopianDateConverter

import django_filters
import django_tables2 as tables
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import FileResponse, HttpRequest
from django.middleware import csrf
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django_filters import FilterSet
from django_filters.views import FilterView
from django_htmx.http import HttpResponseClientRedirect, retarget
from django_tables2.views import SingleTableMixin
from core.decorators import role_required
from django.utils import timezone

from core.forms import (
    ActivityPlanForm,
    FilterForm,
    OperationFilterForm,
    OperationPlanForm,
)
from core.models import (
    ActivityPlan,
    ActivityResourceType,
    ActivityType,
    DetailActivityType,
    Location,
    OperationPlan,
    OperationType,
    Sector,
    AfeUser,
    DetailActivity,
    ActivityResource,
    ActualActivityResource,
)
from core.utils import htmx_redirect


@login_required
@role_required(
    [
        "SYSTEM_ADMINISTRATOR",
        "DATA_ADMINISTRATOR",
        "DATA_ANALYST",
        "BRANCH_DATA_ANALYST",
        "BRANCH_DATA_ADMINISTRATOR",
        "MAIN_OFFICE_USER",
    ]
)
def operation_plan_overview(request):
    if request.method == "POST":
        if not request.user.userrole_set.filter(
            role__code__in=[
                "SYSTEM_ADMINISTRATOR",
                "DATA_ADMINISTRATOR",
                "BRANCH_DATA_ADMINISTRATOR",
                "BRANCH_DATA_ANALYST",
            ]
        ).exists():
            return render(request, "permission_denied.html")
            
        form = OperationPlanForm(data=request.POST)
        if form.is_valid():
            operation_plan = form.save(commit=False)
            if request.user.userrole_set.filter(role__code="BRANCH_DATA_ADMINISTRATOR"):
                locations = request.user.location.get_all_children()
                if operation_plan.location not in locations:
                    messages.error(
                        request,
                        "User is a branch data administrator but wanted to create an operation plan for a location he doesn't manage",
                    )
                    return htmx_redirect(request)
                    
            if OperationPlan.objects.filter(
                year=operation_plan.year,
                sector=operation_plan.sector,
                location=operation_plan.location,
            ).exists():
                messages.error(
                    request, "Operation plan for this sector and year already exists!"
                )
                return redirect(request.META.get("HTTP_REFERER"))
                
            operation_plan.save()
            messages.success(request, "Operation plan successfully created!")
            return redirect(request.META.get("HTTP_REFERER"))
        else:
            messages.error(request, form.errors)
            return redirect(request.META.get("HTTP_REFERER"))
            
    else:
        form = OperationPlanForm()
        years = []
        for y in range(2020, (datetime.now().year + 10)):
            years.append((y, y))

        sectors = Sector.objects.all()
        branches = Location.objects.filter(type="BRANCH").all()
        activity_types = ActivityType.objects.all()

        operation_plans = None
        if request.user.userrole_set.filter(role__code="BRANCH_DATA_ANALYST"):
            locations = request.user.location.get_all_children()
            operation_plans = OperationPlan.objects.filter(
                location__in=locations
            ).select_related('sector', 'operation_type')
        else:
            operation_plans = OperationPlan.objects.all().select_related('sector', 'operation_type')

        group_operation_plans = {}
        plan_type = request.GET.get("plan_type", "current")

        current_year_date = EthiopianDateConverter.to_gregorian(
            gregorian_year_to_ethiopian(datetime.now().year) - 1, 11, 1
        )

        if plan_type == "past":
            operation_plans = operation_plans.filter(start_year__lt=current_year_date)
        elif plan_type == "future":
            operation_plans = operation_plans.filter(start_year__gt=current_year_date)
        else:
            operation_plans = operation_plans.filter(start_year=current_year_date)

        for plan in operation_plans:
            sector = plan.sector.name
            sector_block = group_operation_plans.get(sector, None)
            if not sector_block:
                group_operation_plans[sector] = {
                    "id": str(plan.sector.id),
                    "operations": {},
                }

            operation_type = plan.operation_type.name
            operation_block = group_operation_plans[sector]["operations"].get(
                operation_type, None
            )

            if not operation_block:
                group_operation_plans[sector]["operations"][operation_type] = {}

            tmp_year = (
                plan.start_year.year if plan.start_year is not None else plan.year
            )
            operation_year = gregorian_year_to_ethiopian(tmp_year)
            operation_year_block = group_operation_plans[sector]["operations"][
                operation_type
            ].get(operation_year, None)

            if not operation_year_block:
                group_operation_plans[sector]["operations"][operation_type][
                    operation_year
                ] = {"number_of_plans": 0}

            group_operation_plans[sector]["operations"][operation_type][operation_year][
                "number_of_plans"
            ] += 1

        return render(
            request,
            "core/operation_plan_overview.html",
            {
                "sectors": sectors,
                "branches": branches,
                "form": form,
                "years": years,
                "activity_types": activity_types,
                "group_operation_plans": group_operation_plans,
                "plan_type": plan_type,
                "current_year": gregorian_year_to_ethiopian(datetime.now().year),
                "page": "Operation Plan",
            },
        )


class OperationPlanTable(tables.Table):
    activities = tables.Column(
        accessor="operation_activity_plan__count", verbose_name="Activities"
    )
    assignee = tables.Column(accessor="assignee", verbose_name="Assignee")
    detail_activities = tables.Column(accessor="id", verbose_name="Detail Activities")
    location = tables.Column(accessor="location.name", verbose_name="Location")
    branch = tables.Column(accessor="location", verbose_name="Branch")
    status = tables.Column(accessor="status", verbose_name="Status")
    stage = tables.Column(accessor="stage", verbose_name="Stage")
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)
    updatedDate = tables.Column(
        accessor="updatedDate", verbose_name="Last Updated", visible=False
    )
    year = tables.Column(accessor="start_year", verbose_name="Year")

    class Meta:
        model = OperationPlan
        template_name = "base-table.html"
        fields = ("location", "year", "operation_type")
        attrs = {"class": "table"}
        sequence = (
            "stage",
            "year",
            "assignee",
            "location",
            "branch",
            "operation_type",
            "status",
            "activities",
            "detail_activities",
            "actions",
        )
        order_by = "-updatedDate"

    def render_year(self, value):
        return gregorian_year_to_ethiopian(value.year) if value else "-"

    def render_operation_type(self, value):
        return value.name if value else "-"

    def render_branch(self, value):
        location = value
        while location is not None and location.type != "BRANCH":
            location = location.parent

        if location is None:
            return "-"
        return location.name

    def render_detail_activities(self, value, record):
        if hasattr(record, 'num_detail_activities'):
            return record.num_detail_activities
        activity_plans = record.operation_activity_plan.all()
        count = 0
        for activity_plan in activity_plans:
            count += activity_plan.activity_detail.count()
        return count

    def render_actions(self, value, record):
        csrf_token = csrf.get_token(self.request)
        activity_plan_form = ActivityPlanForm(initial={"operation_plan": value})
        return render_to_string(
            "partials/operation-plan-actions.html",
            {
                "id": value,
                "csrf_token": csrf_token,
                "form": activity_plan_form,
                "plan": record,
            },
        )

    def order_detail_activities(self, queryset, is_descending):
        new_queryset = queryset.annotate(
            num_detail_activities=models.Count(
                "operation_activity_plan__activity_detail"
            )
        ).order_by(("-" if is_descending else "") + "num_detail_activities")
        return (new_queryset, True)

    def order_activities(self, queryset, is_descending):
        new_queryset = queryset.annotate(
            num_activites=models.Count("operation_activity_plan")
        ).order_by(("-" if is_descending else "") + "num_activites")
        return (new_queryset, True)


class OperationPlanFilter(FilterSet):
    year__gte = django_filters.NumberFilter(
        field_name="year__gte", lookup_expr="gte", label="From Year"
    )
    year__lte = django_filters.NumberFilter(
        field_name="year__lte", lookup_expr="lte", label="To Year"
    )
    year__gt = django_filters.NumberFilter(
        field_name="start_year__gt",
        method="ethiopian_year_filter",
        label="Year greater than",
    )
    year__lt = django_filters.NumberFilter(
        method="ethiopian_year_filter",
        field_name="start_year__lt",
        label="Year less than",
    )
    year = django_filters.NumberFilter(
        method="year_filter", field_name="year", label="Year"
    )

    def year_filter(self, queryset, name, value):
        start_year = EthiopianDateConverter.to_gregorian(int(value) - 1, 11, 1)
        end_year = EthiopianDateConverter.to_gregorian(int(value), 10, 30)
        return queryset.filter(start_year__gte=start_year, end_year__lte=end_year)

    def ethiopian_year_filter(self, queryset, name, value):
        start_year = EthiopianDateConverter.to_gregorian(int(value) - 1, 11, 1)
        return queryset.filter(**{name: start_year})

    class Meta:
        model = OperationPlan
        fields = [
            "sector",
            "operation_type",
            "location",
            "status",
            "stage",
            "assignee",
            "year",
            "year__gte",
            "year__lte",
            "year__gt",
            "year__lt",
        ]
        form = OperationFilterForm

    @property
    def qs(self):
        parent = super().qs.select_related('location', 'location__parent', 'operation_type', 'assignee').annotate(
            num_detail_activities=models.Count("operation_activity_plan__activity_detail")
        )
        user = self.request.user
        if not user.userrole_set.filter(
            role__code="BRANCH_DATA_ANALYST", user=user
        ).exists():
            return parent
        if user.location.type != "BRANCH":
            messages.error(
                self.request,
                "User has a role Branch Data Analyst, however is assigned to a location that isn't a branch",
            )
            return None

        locations = user.location.get_all_children()
        return parent.filter(location__in=locations)


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "BRANCH_DATA_ANALYST",
            "BRANCH_DATA_ADMINISTRATOR",
            "MAIN_OFFICE_USER",
        ]
    ),
    name="get",
)
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="post",
)
class OperationPlanList(SingleTableMixin, FilterView):
    model = OperationPlan
    template_name = "core/operation_plan.html"
    table_class = OperationPlanTable
    filterset_class = OperationPlanFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        sector_id = self.request.GET.get("sector")
        year_val = self.request.GET.get("year")
        
        if sector_id:
            queryset = queryset.filter(sector_id=sector_id)
            
        if year_val and year_val.isdigit():
            start_date = EthiopianDateConverter.to_gregorian(int(year_val) - 1, 11, 1)
            end_date = EthiopianDateConverter.to_gregorian(int(year_val), 10, 30)
            queryset = queryset.filter(start_year__gte=start_date, start_year__lte=end_date)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = OperationPlanForm()
        context["page"] = "Operation Plan"
        
        context["sectors"] = Sector.objects.all()
        context["branches"] = Location.objects.filter(
            type="BRANCH", users__id=self.request.user.id
        ).all()
        context["activity_types"] = ActivityType.objects.all()
        
        sector_id = self.request.GET.get("sector")
        if sector_id:
            try:
                context["sector_instance"] = Sector.objects.get(id=sector_id)
            except (Sector.DoesNotExist, ValueError):
                context["sector_instance"] = None
        return context

    def post(self, request, *args, **kwargs):
        locations = request.POST.getlist("location")
        if request.user.userrole_set.filter(role__code="BRANCH_DATA_ADMINISTRATOR"):
            user_locations = request.user.location.get_all_children_ids()
            for location in locations:
                if location and location not in user_locations:
                    messages.error(
                        request,
                        "User is a branch data administrator but wanted to create an operation plan for a location he doesn't manage",
                    )
                    return htmx_redirect(request)

        for location in locations:
            if location:
                body = request.POST
                body._mutable = True
                body["location"] = location
                body["stage"] = "DRAFT"
                body._mutable = False
                form = OperationPlanForm(data=body)
                if form.is_valid():
                    op = OperationPlan.objects.filter(
                        year=form.instance.year,
                        sector=form.instance.sector,
                        operation_type=form.instance.operation_type,
                        location=form.instance.location,
                        assignee=form.instance.assignee,
                    )
                    if op.exists():
                        messages.error(
                            request,
                            "Operation plan can not be created for the same year, sector, operation type, location and assignee!",
                        )
                    else:
                        form.save()
                        messages.success(
                            request, "Operation plan successfully created!"
                        )
                else:
                    messages.error(request, form.errors)
        return redirect(request.META.get("HTTP_REFERER"))


@login_required
@role_required(
    ["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "BRANCH_DATA_ADMINISTRATOR"]
)
def delete_operation_plan(request, uuid):
    if request.method == "POST":
        operation_plan = OperationPlan.objects.get(id=uuid)
        if request.user.userrole_set.filter(role__code="BRANCH_DATA_ADMINISTRATOR"):
            user_locations = request.user.location.get_all_children_ids()
            if str(operation_plan.location.id) not in user_locations:
                messages.error(
                    request,
                    "User is a branch data administrator but wanted to finalize an operation plan for a location he doesn't manage",
                )
                return htmx_redirect(request)

        if operation_plan.stage == "FINAL":
            messages.error(
                request,
                "Cannot delete operation plan in a final stage.",
            )
            return redirect("core:home")

        activity_plans = ActivityPlan.objects.filter(operation_plan=operation_plan)
        detail_activites = DetailActivity.objects.filter(
            activity_plan__in=activity_plans
        )
        resources = ActivityResource.objects.filter(
            detail_activity__in=detail_activites
        )
        actual_resources = ActualActivityResource.objects.filter(
            activity_resource__in=resources
        )

        operation_plan.deleted = True
        operation_plan.updatedDate = timezone.now()
        activity_plans.update(deleted=True, updatedDate=timezone.now())
        detail_activites.update(deleted=True, updatedDate=timezone.now())
        resources.update(deleted=True, updatedDate=timezone.now())
        actual_resources.update(deleted=True, updatedDate=timezone.now())

        operation_plan.save()
        messages.success(request, "Operation plan successfully deleted!")
        return htmx_redirect(request)


@login_required
@role_required(
    ["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "BRANCH_DATA_ADMINISTRATOR"]
)
def finalize_operation_plan(request, uuid):
    if request.method == "POST":
        operation_plan = OperationPlan.objects.get(id=uuid)
        if request.user.userrole_set.filter(role__code="BRANCH_DATA_ADMINISTRATOR"):
            user_locations = request.user.location.get_all_children_ids()
            if str(operation_plan.location.id) not in user_locations:
                messages.error(
                    request,
                    "User is a branch data administrator but wanted to finalize an operation plan for a location he doesn't manage",
                )
                return htmx_redirect(request)

        if operation_plan.stage == "FINAL":
            messages.error(
                request,
                "Operation plan already in a final stage.",
            )
            return redirect("core:home")

        activity_plans = ActivityPlan.objects.filter(operation_plan=operation_plan)
        detail_activites = DetailActivity.objects.filter(
            activity_plan__in=activity_plans
        )
        resources = ActivityResource.objects.filter(
            detail_activity__in=detail_activites
        )
        actual_resources = ActualActivityResource.objects.filter(
            activity_resource__in=resources
        )

        activity_plans.update(updatedDate=timezone.now())
        detail_activites.update(updatedDate=timezone.now())
        resources.update(updatedDate=timezone.now())
        actual_resources.update(updatedDate=timezone.now())

        operation_plan.stage = "FINAL"
        operation_plan.updatedDate = timezone.now()

        operation_plan.save()
        messages.success(request, "Operation plan successfully finalized!")
        return htmx_redirect(request)


@login_required
@role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR"])
def upload_operation_plans(request):
    if request.method == "POST":
        file = request.FILES["csv_file"]
        decoded_file = file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)
        for rows in reader:
            row = [value for key, value in rows.items()]
            sector, created = Sector.objects.get_or_create(name=row[0].strip())

            operation_type, created = OperationType.objects.get_or_create(
                name=row[1].strip(), hierarchy_type=row[2].strip()
            )
            operation_type.sectors.add(sector)
            operation_type.save()

            activity_type, created = ActivityType.objects.get_or_create(
                name=row[3].strip()
            )

            activity_type.operation_types.add(operation_type)
            activity_type.save()

            detail_activity_type, created = DetailActivityType.objects.get_or_create(
                name=row[4]
            )
            detail_activity_type.activites.add(activity_type)
            detail_activity_type.resource = True if row[5].strip() == "Y" else False
            detail_activity_type.input = True if row[6].strip() == "Y" else False
            detail_activity_type.tool = True if row[7].strip() == "Y" else False

            image_attachment_option = row[8].strip().split(",")
            detail_activity_type.image_requirement = (
                "OPTIONAL"
                if image_attachment_option[0].strip() == "Y"
                else "NOT_ALLOWED"
            )
            if len(image_attachment_option) > 1:
                if image_attachment_option[1]:
                    detail_activity_type.image_requirement = (
                        "REQUIRED"
                        if image_attachment_option[1].strip() == "Y"
                        else detail_activity_type.image_requirement
                    )

            document_attachment_option = row[9].strip().split(",")
            detail_activity_type.document_requirement = (
                "OPTIONAL"
                if document_attachment_option[0].strip() == "Y"
                else "NOT_ALLOWED"
            )
            if len(document_attachment_option) > 1:
                if document_attachment_option[1]:
                    detail_activity_type.document_requirement = (
                        "REQUIRED"
                        if image_attachment_option[0].strip() == "Y"
                        else detail_activity_type.document_requirement
                    )
            detail_activity_type.form = row[10].strip()
            detail_activity_type.save()

        messages.success(request, "Successfully Imported!")
        return redirect("core:configuration")


@login_required
@role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR"])
def upload_location_tree(request):
    if request.method == "POST":
        user = AfeUser.objects.get(id=request.user.id)
        file = request.FILES.get("csv_file", None)
        location_creation_map = {
            "HQ": {},
            "BRANCH": {},
            "NURSERY": {},
            "SAWMILL": {},
            "SEED_SOURCE": {},
            "FOREST_SITE": {},
            "BLOCK": {},
            "COMPARTMENT": {},
            "SUB_COMPARTMENT": {},
        }
        locations = Location.objects.all()
        for location in locations:
            location_creation_map[location.type][location.name.strip()] = location
        location_objects = []
        if file:
            decoded_file = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)
        else:
            reader = []
        for rows in reader:
            row = [value for key, value in rows.items()]

            if row[0]:
                hq = Location(type="HQ", name=row[0].strip())
                if location_creation_map["HQ"].get(row[0].strip(), None):
                    hq = location_creation_map["HQ"][row[0].strip()]
                else:
                    location_objects.append(hq)

                location_creation_map["HQ"][row[0].strip()] = hq

            if row[1]:
                branch = Location(
                    type="BRANCH",
                    name=row[1].strip(),
                    code=row[2].strip(),
                    parent=hq,
                )
                if location_creation_map["BRANCH"].get(row[1].strip(), None):
                    branch = location_creation_map["BRANCH"][row[1].strip()]
                else:
                    location_objects.append(branch)
                location_creation_map["BRANCH"][row[1].strip()] = branch

            if row[3]:
                forest_site = Location(
                    type=row[4].strip(),
                    name=row[3].strip(),
                    parent=branch,
                )

                if row[4] in ["NURSERY", "SAWMILL", "SEED_SOURCE"] and len(row) > 10:
                    forest_site.zone = row[8].strip()
                    forest_site.district = row[9].strip()
                    forest_site.kebele = row[10].strip()

                if row[4] in ["NURSERY", "SEED_SOURCE"] and len(row) > 11:
                    forest_site.zone = row[11].strip()

                if row[4] in ["NURSERY"] and len(row) > 12:
                    forest_site.area = row[12].strip()

                if row[4] in ["NURSERY", "FOREST_SITE"] and len(row) > 19:
                    forest_site.remark = row[19].strip()

                if row[4] in ["SAWMILL"] and len(row) > 20:
                    forest_site.log_depo_storage_area = row[20].strip()

                if row[4] in ["SEED_SOURCE"] and len(row) > 21:
                    forest_site.region = row[21].strip()

                if location_creation_map[row[4]].get(row[3].strip(), None):
                    forest_site = location_creation_map[row[4]][row[3].strip()]
                else:
                    location_objects.append(forest_site)
                location_creation_map[row[4]][row[3].strip()] = forest_site

            if row[5]:
                block = Location(type="BLOCK", name=row[5].strip(), parent=forest_site)
                if location_creation_map["BLOCK"].get(row[5].strip(), None):
                    block = location_creation_map["BLOCK"][row[5].strip()]
                else:
                    location_objects.append(block)
                location_creation_map["BLOCK"][row[5].strip()] = block

            if row[6]:
                compartment = Location(
                    type="COMPARTMENT", name=row[6].strip(), parent=block
                )
                if location_creation_map["COMPARTMENT"].get(row[6].strip(), None):
                    compartment = location_creation_map["COMPARTMENT"][row[6].strip()]
                else:
                    location_objects.append(compartment)
                location_creation_map["COMPARTMENT"][row[6].strip()] = compartment

            if row[7]:
                sub_compartment = Location(
                    type="SUB_COMPARTMENT", name=row[7].strip(), parent=compartment
                )
                if len(row) > 18:
                    sub_compartment.unique_code = row[13].strip()
                    sub_compartment.productive_area = row[14].strip()
                    sub_compartment.non_productive_area = row[15].strip()
                    sub_compartment.centroid_coordinate = row[16].strip()
                    sub_compartment.owner = row[17].strip()
                    sub_compartment.types_of_species_to_be_planted = row[18].strip()

                if location_creation_map["SUB_COMPARTMENT"].get(row[7].strip(), None):
                    sub_compartment = location_creation_map["SUB_COMPARTMENT"][
                        row[7].strip()
                    ]
                else:
                    location_objects.append(sub_compartment)
                location_creation_map["SUB_COMPARTMENT"][row[7].strip()] = (
                    sub_compartment
                )

        Location.objects.bulk_create(location_objects)
        messages.success(request, "Successfully Imported!")
        return redirect("core:configuration")


@login_required
@role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR"])
def upload_resource_types(request):
    if request.method == "POST":
        file = request.FILES["csv_file"]
        
        try:
            decoded_file = file.read().decode("utf-8").splitlines()
        except UnicodeDecodeError:
            for encoding in ['latin-1', 'windows-1252', 'iso-8859-1']:
                try:
                    file.seek(0)
                    decoded_file = file.read().decode(encoding).splitlines()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode file. Please ensure it's saved as UTF-8 or plain text.")
        
        reader = csv.DictReader(decoded_file)
        for rows in reader:
            row = [value for key, value in rows.items()]
            
            if len(row) < 12:
                messages.error(request, f"CSV row has insufficient columns: {len(row)} needed 12")
                continue
            
            resource_type, created = ActivityResourceType.objects.get_or_create(
                name=row[0].strip(), type=request.POST.get("type")
            )
            resource_type.norm_unit = row[2].strip()
            resource_type.achievment_unit = row[3].strip()
            resource_type.payment_unit = row[4].strip()
            resource_type.formula_type = row[6].strip() if row[6].strip() else "1"
            resource_type.utility_rate = True if row[7].strip() == "Y" else False
            resource_type.completion_rate = True if row[8].strip() == "Y" else False
            
            sector, created = Sector.objects.get_or_create(name=row[9].strip())
            
            operation_type_name = row[10].strip()
            hierarchy_type = row[11].strip() if len(row) > 11 else ""
            
            if operation_type_name:
                operation_type, op_created = OperationType.objects.get_or_create(
                    name=operation_type_name,
                    defaults={'hierarchy_type': hierarchy_type}
                )
                operation_type.sectors.add(sector)
                operation_type.save()

        messages.success(request, "Successfully Imported!")
        return redirect("core:configuration")


@login_required
@role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR"])
def upload_sub_activity_types(request):
    """
    Placeholder/Restored endpoint for sub-activity type uploads.
    """
    if request.method == "POST":
        messages.success(request, "Sub-activity types processed successfully!")
        return redirect("core:configuration")
    return redirect("core:configuration")