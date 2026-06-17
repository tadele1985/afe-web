from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.http.request import HttpRequest
from django.middleware import csrf
from django.shortcuts import get_object_or_404, render
from django.db.models import Q

import json

from core.attachable_forms.forms import Form
from core.forms import (
    ActivityInputForm,
    ActivityPlanForm,
    ActivityResourceForm,
    ActivityToolForm,
    DetailActivityForm,
    EditActivityPlanForm,
    EditDetailActivityForm,
)
from core.models import (
    ActivityPlan,
    ActivityResource,
    ActivityResourceType,
    ActivityType,
    DetailActivity,
    DetailActivityType,
    Location,
    OperationPlan,
    OperationType,
    Sector,
    get_parent_location_types,
    location_type_to_reference_field_map,
)


def get_option_html(objs, name):
    if len(objs) == 0:
        return f'<option disabled selected value="">Select {name}</option>'

    html = f'<option disabled selected value="">Select {name}</option>'
    for obj in objs:
        html += f'<option value="{obj.id}">{obj.name}</option>'

    return html


@login_required
def get_operations(request: HttpRequest):
    sector = get_object_or_404(Sector, pk=request.GET.get("sector"))
    html = get_option_html(sector.operationtype_set.all(), "Operation")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_branches(request: HttpRequest):
    branches = Location.objects.filter(type="BRANCH").all()
    html = get_option_html(branches, "Branch")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_forest_sites(request: HttpRequest):
    forest_sites = Location.objects.filter(
        type="FOREST_SITE", parent__id=request.GET.get("branch")
    ).all()
    html = get_option_html(forest_sites, name="Forest Site")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_blocks(request: HttpRequest):
    blocks = Location.objects.filter(
        type="BLOCK", parent__id=request.GET.get("forest_site")
    ).all()
    html = get_option_html(blocks, name="Block")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_compartments(request: HttpRequest):
    compartments = Location.objects.filter(
        type="COMPARTMENT", parent__id=request.GET.get("block")
    ).all()
    html = get_option_html(compartments, name="Compartment")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_sub_compartments(request: HttpRequest):
    sub_compartments = Location.objects.filter(
        type="SUB_COMPARTMENT", parent__id=request.GET.get("comparment")
    ).all()
    html = get_option_html(sub_compartments, name="Sub Compartment")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_locations(request: HttpRequest):
    location_type = request.GET.get("type")
    end_location = request.GET.get("end_location")
    locations = Location.objects.filter(
        parent__id=request.GET.get(location_type.lower())
    )

    location_type_name = ""
    if end_location in ["Forest site", "Block", "Compartment", "Sub compartment"]:
        location_type_name = "FOREST_SITE"
    elif end_location == "Nursery":
        location_type_name = "NURSERY"
    elif end_location == "Sawmill":
        location_type_name == "SAWMILL"
    elif end_location == "Seed source":
        location_type_name = "SEED_SOURCE"
    elif end_location == "Forest establishment":
        location_type_name = "FOREST_ESTABLISTMENT"

    if location_type == "Branch":
        locations = locations.filter(type=location_type_name)

    html = get_option_html(locations, name="Select location")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_multi_select_locations(request: HttpRequest):
    location_type = request.GET.get("type")
    end_location = request.GET.get("end_location")
    locations = Location.objects.filter(
        parent__id__in=request.GET.getlist(location_type.lower())
    )

    location_type_name = ""
    if end_location in ["Forest site", "Block", "Compartment", "Sub compartment"]:
        location_type_name = "FOREST_SITE"
    elif end_location == "Nursery":
        location_type_name = "NURSERY"
    elif end_location == "Sawmill":
        location_type_name = "SAWMILL"
    elif end_location == "Seed source":
        location_type_name = "SEED_SOURCE"
    elif end_location == "Forest establishment":
        location_type_name = "FOREST_ESTABLISTMENT"

    if location_type == "HQ" and end_location != "Branch":
        children = Location.objects.filter(type=location_type_name)
        locations = locations.filter(Q(children__in=children)).distinct()
    elif location_type == "Branch":
        locations = locations.filter(type=location_type_name)

    html = get_option_html(locations, name="Select location")
    response = HttpResponse(html, content_type="text/html")
    return response


@login_required
def get_location_form(request):
    options = Location.objects.filter(type="HQ")
    opertaion_type = OperationType.objects.get(id=request.GET.get("operation_type"))
    parent_locations_types = get_parent_location_types(opertaion_type.hierarchy_type)

    location_id = request.GET.get("location_id", None)

    selected_location_list = None

    def add_location_options_and_selected(location):
        captialized_type = location.type.upper().replace(" ", "_")
        selected_location_list[captialized_type] = {
            "selected": location.id,
            "options": Location.objects.filter(type=captialized_type),
        }
        if location.parent:
            add_location_options_and_selected(location.parent)

    if location_id:
        selected_location_list = {}
        selected_location = Location.objects.get(id=location_id)
        captialized_type = selected_location.type.upper().replace(" ", "_")
        selected_location_list[captialized_type] = {
            "selected": selected_location.id,
            "options": [selected_location],
        }
        add_location_options_and_selected(selected_location.parent)

    return render(
        request,
        "core/location_form.html",
        {
            "locations": get_parent_location_types(opertaion_type.hierarchy_type),
            "end_location": opertaion_type.hierarchy_type,
            "options": options,
            "selected_location_list": selected_location_list,
        },
    )


@login_required
def get_multi_select_location_form(request):
    options = Location.objects.filter(type="HQ")
    opertaion_type = OperationType.objects.get(id=request.GET.get("operation_type"))
    parent_locations_types = get_parent_location_types(opertaion_type.hierarchy_type)

    location_id = request.GET.get("location_id", None)

    selected_location_list = None

    def add_location_options_and_selected(location):
        captialized_type = location.type.upper().replace(" ", "_")
        selected_location_list[captialized_type] = {
            "selected": location.id,
            "options": Location.objects.filter(type=captialized_type),
        }
        if location.parent:
            add_location_options_and_selected(location.parent)

    if location_id:
        selected_location_list = {}
        selected_location = Location.objects.get(id=location_id)
        captialized_type = selected_location.type.upper().replace(" ", "_")
        selected_location_list[captialized_type] = {
            "selected": selected_location.id,
            "options": [selected_location],
        }
        add_location_options_and_selected(selected_location.parent)

    return render(
        request,
        "core/muti_select_location_form.html",
        {
            "locations": get_parent_location_types(opertaion_type.hierarchy_type),
            "end_location": opertaion_type.hierarchy_type,
            "options": options,
            "selected_location_list": selected_location_list,
        },
    )


@login_required
def get_operation_plans(request: HttpRequest):
    operation_plans = OperationPlan.objects.all()

    plan_type = request.GET.get("plan_type", "current")

    if plan_type == "past":
        operation_plans = operation_plans.filter(year__lt=datetime.now().year)
    elif plan_type == "future":
        operation_plans = operation_plans.filter(year__gt=datetime.now().year)
    elif plan_type == "current":
        operation_plans = operation_plans.filter(year=datetime.now().year)
    else:
        operation_plans = operation_plans.all()

    tmp_plans = []
    for operation in operation_plans:
        tmp_plans.append(
            {
                "id": operation.id,
                "Year": operation.year,
                "Sector": operation.sector.name if operation.sector else None,
                "Operation Type": (
                    operation.operation_type.name
                    if operation.operation_type is not None
                    else None
                ),
                "Activity Count": operation.operation_activity_plan.count(),
            }
        )
    return JsonResponse(tmp_plans, safe=False)


def get_resource_form(request):
    activity_plan_id = request.GET.get("activity_plan")
    activity_plan = get_object_or_404(ActivityPlan, pk=activity_plan_id)
    form = ActivityResourceForm(prefix="resource", activity_plan=activity_plan)
    return render(request, form.template_name, {"form": form})


def get_resource_units(request):
    resource_type_id = request.GET.get("resource-resource_type") or request.GET.get(
        "resource_type"
    )
    activity_plan_id = request.GET.get("activity_plan")

    try:
        activity_plan = ActivityPlan.objects.get(id=activity_plan_id)
    except ActivityPlan.DoesNotExist:
        activity_plan = None

    request_type = "resource"
    if not resource_type_id:
        resource_type_id = request.GET.get("tool-resource_type")
        request_type = "tool"
    if not resource_type_id:
        resource_type_id = request.GET.get("input-resource_type")
        request_type = "input"

    resource_type = get_object_or_404(ActivityResourceType, pk=resource_type_id)
    form_mapper = {
        "resource": ActivityResourceForm,
        "tool": ActivityToolForm,
        "input": ActivityInputForm,
    }
    form = form_mapper[request_type](
        prefix=request_type,
        initial={"resource_type": resource_type},
        activity_plan=activity_plan,
    )
    return render(
        request,
        form.template_name,
        {
            "form": form,
            "units": [
                resource_type.norm_unit,
                resource_type.achievment_unit,
                resource_type.payment_unit,
            ],
            "formula_type": resource_type.formula_type,
        },
    )


def get_tool_form(request):
    activity_plan_id = request.GET.get("activity_plan")
    activity_plan = get_object_or_404(ActivityPlan, pk=activity_plan_id)
    form = ActivityToolForm(prefix="tool", activity_plan=activity_plan)
    return render(request, "core/resource_form.html", {"form": form})


def get_input_form(request):
    activity_plan_id = request.GET.get("activity_plan")
    activity_plan = get_object_or_404(ActivityPlan, pk=activity_plan_id)
    form = ActivityInputForm(prefix="input", activity_plan=activity_plan)
    return render(request, "core/resource_form.html", {"form": form})


def get_cost(request):
    get_dict = {}
    for key, value in request.GET.items():
        if (
            key.startswith("resource-")
            or key.startswith("tool-")
            or key.startswith("input-")
        ):
            new_key = key.split("-")[1]
            get_dict[new_key] = value
    work_norm = 0
    achievement = 0
    payment = 0
    for key, value in get_dict.items():
        if value == "":
            continue

        if key == "resource-work_norm" or key == "work_norm":
            work_norm = float(value)
        elif key == "resource-achievement" or key == "achievement":
            achievement = float(value)
        elif key == "resource-payment" or key == "payment":
            payment = float(value)

    resource_type_id = get_dict.get("resource_type", None)
    if resource_type_id is None:
        return JsonResponse({"error": "Invalid resource type"}, status=400)

    resource_type = get_object_or_404(ActivityResourceType, pk=resource_type_id)
    cost = ActivityResource.calculate_cost(
        work_norm, achievement, payment, resource_type.formula_type
    )

    return HttpResponse(cost, content_type="text/html")


def get_edit_activity_form(request):
    uuid = request.GET.get("uuid")
    if not uuid:
        return JsonResponse({"error": "Invalid uuid"}, status=400)
    instance = get_object_or_404(ActivityPlan, pk=uuid)
    form = EditActivityPlanForm(instance=instance)
    csrf_token = csrf.get_token(request)
    return render(request, form.template_name, {"form": form, "csrf_token": csrf_token})


def get_detailed_activity_form(request):
    uuid = request.GET.get("uuid")
    form = None
    if uuid is not None:
        form = DetailActivityForm(prefix="detail", initial={"activity_plan": uuid})
    else:
        form = DetailActivityForm(prefix="detail")

    return render(request, form.template_name, {"form": form})


def get_edit_detailed_activity_form(request, id=None):
    instance = DetailActivity.objects.get(id=id)
    resources = instance.activityresource_set.filter(
        resource_type__type="RESOURCE"
    ).all()
    tools = instance.activityresource_set.filter(resource_type__type="TOOL").all()
    inputs = instance.activityresource_set.filter(resource_type__type="INPUT").all()

    resources = [
        ActivityResourceForm(
            instance=resource, prefix="resource", activity_plan=instance.activity_plan
        )
        for resource in resources
    ]
    tools = [
        ActivityToolForm(
            instance=tool, prefix="tool", activity_plan=instance.activity_plan
        )
        for tool in tools
    ]
    inputs = [
        ActivityInputForm(
            instance=input, prefix="input", activity_plan=instance.activity_plan
        )
        for input in inputs
    ]

    form = EditDetailActivityForm(instance=instance)
    return render(
        request,
        "core/edit_detail_activity_form.html",
        {
            "form": form,
            "resources": resources,
            "inputs": inputs,
            "tools": tools,
            "detail_type": instance.detail_type,
            "activity_plan": instance.activity_plan.id,
        },
    )


def get_location_detail(request):
    id = request.GET.get("id", None)
    if id:
        location = Location.objects.get(id=id)
        location_detail_types = location_type_to_reference_field_map.get(
            location.type, []
        )
        result = {}
        for detail_type in location_detail_types:
            result[detail_type] = getattr(location, detail_type)
        return JsonResponse(result)


def get_resource_forms(request):
    detail_type_id = request.GET.get("detail-detail_type") or request.GET.get(
        "detail_type"
    )
    activity_plan = request.GET.get("activity_plan") or None
    if not detail_type_id:
        return JsonResponse({"error": "Invalid detail_type id"}, status=400)
    detail_type = get_object_or_404(DetailActivityType, pk=detail_type_id)
    return render(
        request,
        "partials/resource-form.html",
        {
            "resource": detail_type.resource,
            "input": detail_type.input,
            "tool": detail_type.tool,
            "activity_plan": activity_plan,
        },
    )


def get_activity_types(request):
    uuid = request.GET.get("uuid")
    if not uuid:
        return JsonResponse({"error": "Invalid uuid"}, status=400)
    operation_plan = get_object_or_404(OperationPlan, pk=uuid)
    activity_types = ActivityType.objects.filter(
        operation_types__in=[operation_plan.operation_type]
    ).all()
    html = ""
    for activity_type in activity_types:
        html += f'<option value="{activity_type.id}">{activity_type.name}</option>'
    return HttpResponse(html, content_type="text/html")


def get_resource_type_from_activity_type(request):
    activity_types = request.GET.getlist("activites")
    operation_types = OperationType.objects.filter(
        activitytype__id__in=activity_types
    ).distinct()
    activity_resource_types = ActivityResourceType.objects.filter(
        operation_types__in=operation_types
    )
    html = ""
    for activity_resource_type in activity_resource_types:
        html += f'<option value="{activity_resource_type.id}">{activity_resource_type.name}</option>'
    return HttpResponse(html, content_type="text/html")


def get_operation_types(request):
    uuid = request.GET.get("sector")
    if not uuid:
        return JsonResponse({"error": "Invalid uuid"}, status=400)
    operation_types = OperationType.objects.filter(sector_id=uuid).all()
    html = ""
    for operation_type in operation_types:
        html += f'<option value="{operation_type.id}">{operation_type.name}</option>'
    return HttpResponse(html, content_type="text/html")


def get_parent_locations_by_type(request):
    location_type = request.GET.get("type")

    locations = []

    if location_type == "BRANCH":
        locations = Location.objects.filter(type="HQ")
    elif location_type in [
        "NURSERY",
        "SAWMIL",
        "FOREST_SITE",
        "SEED_SOURCE",
        "FOREST_ESTABLISHMENT",
    ]:
        locations = Location.objects.filter(type="BRANCH")
    elif location_type == "BLOCK":
        locations = Location.objects.filter(
            type__in=["FOREST_SITE", "FOREST_ESTABLISTMENT"]
        )
    elif location_type == "COMPARTMENT":
        locations = Location.objects.filter(type="BLOCK")
    elif location_type == "SUB_COMPARTMENT":
        locations = Location.objects.filter(type="COMPARTMENT")

    html = get_option_html(locations, "Location")
    response = HttpResponse(html, content_type="text/html")

    return response


def get_formlist(request):
    form_list = []
    for form in Form:
        new_json = form.form_json()
        new_json["type"] = form.name
        form_list.append(new_json)

    # json_object = json.dumps(form_list, indent=4)
    # with open("core/attachable_forms/formlist_cache.json", "w") as outfile:
    #     outfile.write(json_object)

    return JsonResponse(form_list, safe=False)


def get_cached_formlist(request):
    with open("core/attachable_forms/formlist_cache.json", "r") as formlist_file:
        data = formlist_file.read()

    response = HttpResponse(content=data)
    response["Content-Type"] = "application/json"

    return response
