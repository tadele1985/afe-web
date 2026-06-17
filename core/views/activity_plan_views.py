from typing import Union

from core.utils import get_amharic_month
from ethiopian_date import EthiopianDateConverter
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
import django_tables2 as tables
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, UpdateView
from django_htmx.http import HttpResponseClientRedirect, retarget
from django_filters import FilterSet
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from core.decorators import role_required

from core.forms import (
    ActivityInputForm,
    ActivityPlanForm,
    ActivityResourceForm,
    ActivityToolForm,
    ActualActivityForm,
    DetailActivityForm,
    EditDetailActivityForm,
    FilterForm,
)
from core.models import (
    ActivityPlan,
    ActivityResource,
    ActivityResourceType,
    ActualActivityResource,
    DetailActivity,
    DetailActivityType,
    RoleCode,
)
from core.utils import htmx_redirect


class DetailActivityTable(tables.Table):
    name = tables.Column(accessor="detail_type__name", verbose_name="Name")
    date_range = tables.Column(accessor="id", verbose_name="Date Range")
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = DetailActivity
        fields = ("assignee", "status")
        sequence = (
            "name",
            "date_range",
            "assignee",
            "status",
            "actions",
        )
        template_name = "base-table.html"

    # def render_date_range(self, record):
    #     date_range = (
    #         record.start_date.strftime("%d %b %Y")
    #         + " - "
    #         + record.end_date.strftime("%d %b %Y")
    #     )
    #     return date_range

    def render_date_range(self, record):
        start_date = EthiopianDateConverter.date_to_ethiopian(record.start_date)
        end_date = EthiopianDateConverter.date_to_ethiopian(record.end_date)
        return f"{start_date[2]} {get_amharic_month(start_date[1])} {start_date[0]} - {end_date[2]} {get_amharic_month(end_date[1])} {end_date[0]}"

    def render_actions(self, value):
        return render_to_string(
            "partials/detail-activity-actions.html",
            {"id": value},
        )


class DetailActivityFilter(FilterSet):
    class Meta:
        model = DetailActivity
        fields = ["detail_type", "assignee", "status", "start_date", "end_date"]
        # form = FilterForm

    def get_form_class(self):
        return FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("uuid")
        return parent.filter(activity_plan_id=uuid)


@method_decorator(login_required, name="get")
@method_decorator(
    role_required(
        [
            RoleCode.SYSTEM_ADMINISTRATOR,
            RoleCode.DATA_ADMINISTRATOR,
            RoleCode.BRANCH_USER,
            RoleCode.BRANCH_DATA_ADMINISTRATOR,
        ]
    ),
    name="post",
)
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "BRANCH_USER",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="get",
)
class DetailActivityDetailView(SingleTableMixin, FilterView):
    model = DetailActivity
    table_class = DetailActivityTable
    filterset_class = DetailActivityFilter
    template_name = "core/activity_plan_detail.html"

    def get_context_data(self, **kwargs):
        uuid = self.kwargs.get("uuid")
        context = super().get_context_data(**kwargs)
        plan = ActivityPlan.objects.get(id=uuid)
        detail_activity_form = DetailActivityForm(
            prefix="detail", initial={"activity_plan": uuid}
        )
        render_args = {
            "id": uuid,
            "page": "Operation Plan",
            "plan": plan,
            "detail_activity_form": detail_activity_form,
            "breadcrumbs": [
                {
                    "name": "Operation Overview",
                    "url": reverse_lazy("core:operation_plan_overview"),
                },
                {"name": "Operation Plans", "url": reverse_lazy("core:home")},
                {
                    "name": plan.operation_plan.operation_type.name,
                    "url": reverse_lazy(
                        "core:operation_plan_detail",
                        kwargs={"uuid": plan.operation_plan.id},
                    ),
                },
                {"name": plan.type.name, "url": "#"},
            ],
            "tab_names": ["Detail", "Detail Activities"],
        }
        context.update(render_args)
        return context

    def post(self, request, *args, **kwargs):
        uuid = self.kwargs.get("uuid")
        detail_activity_form = DetailActivityForm(
            request.POST,
            request.FILES,
            prefix="detail",
            initial={"activity_plan": uuid},
        )
        if request.user.userrole_set.filter(
            role__code="BRANCH_DATA_ADMINISTRATOR"
        ).exists():
            locations = request.user.location.get_all_children()
            activity_plan = ActivityPlan.objects.get(pk=uuid)
            if activity_plan.operation_plan.location not in locations:
                messages.error(
                    request,
                    "User is a branch data adminstrator but wanted to create an detail activity for a location he doesn't manage",
                )
                return htmx_redirect(request)
        if not detail_activity_form.is_valid():
            return render(
                request,
                detail_activity_form.template_name,
                {"form": detail_activity_form},
            )

        new_detail_activity = detail_activity_form.save(commit=False)
        detail_activity_form.save()

        holder = {
            "resource": [],
            "tool": [],
            "input": [],
        }
        for key, item_list in request.POST.items():
            tmp = key.split("-")
            if tmp[0] == "initial":
                tmp = tmp[1:]
            if len(tmp) <= 1:
                continue
            item_type, val = tmp
            if item_type not in ["resource", "tool", "input"]:
                continue

            item_list = request.POST.getlist(key)
            for i, item in enumerate(item_list):
                if i >= len(holder[item_type]):
                    holder[item_type].append({val: item})
                else:
                    holder[item_type][i][val] = item

        form_mapper: dict[
            str, Union[ActivityResourceForm, ActivityToolForm, ActivityInputForm]
        ] = {
            "resource": ActivityResourceForm,
            "tool": ActivityToolForm,
            "input": ActivityInputForm,
        }

        for resource_type, type_list in holder.items():
            if len(type_list) == 0:
                continue

            for data in type_list:
                form = form_mapper.get(resource_type)
                data["detail_activity"] = new_detail_activity
                my_form = form(data=data)
                if not my_form.is_valid():
                    messages.error(request, my_form.errors)
                    return render(
                        request,
                        my_form.template_name,
                        {"form": detail_activity_form},
                    )

        for resource_type, type_list in holder.items():
            for resource in type_list:
                resource["detail_activity"] = new_detail_activity
                rt = ActivityResourceType.objects.get(pk=resource["resource_type"])
                if not rt:
                    continue

                activity_resource = ActivityResource(
                    detail_activity=new_detail_activity,
                    resource_type=rt,
                    work_norm=resource["work_norm"],
                    achievement=resource["achievement"],
                    payment=resource["payment"],
                )
                activity_resource.save()

        messages.success(request, "Detail activity successfully added!")
        if not request.htmx:
            return redirect(request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(request.META.get("HTTP_REFERER"))
        return retarget(response, "body")


@login_required
@role_required(
    [
        "SYSTEM_ADMINISTRATOR",
        "DATA_ADMINISTRATOR",
        "BRANCH_USER",
        "BRANCH_DATA_ADMINISTRATOR",
    ]
)
def edit_detail_activity(request):
    if request.method == "POST":
        if not request.user.userrole_set.filter(
            role__code__in=[
                "SYSTEM_ADMINISTRATOR",
                "DATA_ADMINISTRATOR",
                "BRANCH_DATA_ADMINISTRATOR",
            ]
        ).exists():
            return render(request, "permission_denied.html")
        detail_activity = DetailActivity.objects.get(pk=request.POST.get("id"))
        if request.user.userrole_set.filter(role__code="BRANCH_DATA_ADMINISTRATOR"):
            locations = request.user.location.get_all_children()
            if detail_activity.activity_plan.operation_plan.location not in locations:
                messages.error(
                    request,
                    "User is a branch data adminstrator but wanted to create an detail activity for a location he doesn't manage",
                )
                return htmx_redirect(request)
        form = EditDetailActivityForm(
            request.POST, request.FILES, instance=detail_activity
        )
        if not form.is_valid():
            resources = detail_activity.activityresource_set.filter(
                resource_type__type="RESOURCE"
            ).all()
            tools = detail_activity.activityresource_set.filter(
                resource_type__type="TOOL"
            ).all()
            inputs = detail_activity.activityresource_set.filter(
                resource_type__type="INPUT"
            ).all()

            resources = [
                ActivityResourceForm(instance=resource, prefix="resource")
                for resource in resources
            ]
            tools = [ActivityToolForm(instance=tool, prefix="tool") for tool in tools]
            inputs = [
                ActivityInputForm(instance=input, prefix="input") for input in inputs
            ]
            return render(
                request,
                form.template_name,
                {
                    "form": form,
                    "resources": resources,
                    "inputs": inputs,
                    "tools": tools,
                    "detail_type": detail_activity.detail_type,
                },
            )

        form.save()
        messages.success(request, "Detail activity successfully edited!")

        holder = {
            "resource": [],
            "tool": [],
            "input": [],
        }
        for key, item_list in request.POST.items():
            tmp = key.split("-")
            if tmp[0] == "initial":
                tmp = tmp[1:]
            if len(tmp) <= 1:
                continue

            item_type, val = tmp
            if item_type not in ["resource", "tool", "input"]:
                continue

            item_list = request.POST.getlist(key)
            for i, item in enumerate(item_list):
                if i >= len(holder[item_type]):
                    holder[item_type].append({val: item})
                else:
                    holder[item_type][i][val] = item

        form_mapper: dict[
            str, Union[ActivityResourceForm, ActivityToolForm, ActivityInputForm]
        ] = {
            "resource": ActivityResourceForm,
            "tool": ActivityToolForm,
            "input": ActivityInputForm,
        }

        for resource_type, type_list in holder.items():
            if len(type_list) == 0:
                continue

            for data in type_list:
                form = form_mapper.get(resource_type)
                if data.get("detail_activity"):
                    data["update"] = True
                else:
                    data["detail_activity"] = detail_activity.id
                    my_form = form(data=data)
                    if not my_form.is_valid():
                        messages.error(request, my_form.errors)
                        if not request.htmx:
                            return redirect(request.META.get("HTTP_REFERER"))

                        response = HttpResponseClientRedirect(
                            request.META.get("HTTP_REFERER")
                        )
                        return retarget(response, "body")

        all_ids = [x.get("id") for data in holder.values() for x in data]
        for resource in detail_activity.activityresource_set.all():
            if str(resource.id) not in all_ids:
                resource.deleted = True
                resource.updatedDate = timezone.now()
                resource.save()

        for resource_type, type_list in holder.items():
            for resource in type_list:
                if resource.get("update"):
                    form = form_mapper.get(resource_type)
                    ar = ActivityResource.objects.get(pk=resource.get("id"))
                    my_form = form(instance=ar, data=resource)
                    if my_form.is_valid():
                        my_form.save()
                    else:
                        messages.error(request, my_form.errors)
                        return redirect(request.META.get("HTTP_REFERER"))
                else:
                    resource["detail_activity"] = detail_activity
                    rt = ActivityResourceType.objects.get(pk=resource["resource_type"])
                    if not rt:
                        continue

                    activity_resource = ActivityResource(
                        detail_activity=detail_activity,
                        resource_type=rt,
                        work_norm=resource["work_norm"],
                        achievement=resource["achievement"],
                        payment=resource["payment"],
                    )
                    activity_resource.save()

        if not request.htmx:
            return redirect(request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(request.META.get("HTTP_REFERER"))
        return retarget(response, "body")


@login_required
@role_required(
    [
        "SYSTEM_ADMINISTRATOR",
        "DATA_ADMINISTRATOR",
        "BRANCH_USER",
        "BRANCH_DATA_ADMINISTRATOR",
    ]
)
def add_activity_plan(request):
    if request.method == "POST":
        form = ActivityPlanForm(data=request.POST)
        if form.is_valid():
            activity_plan = form.save(commit=False)
            if request.user.userrole_set.filter(role__code="BRANCH_DATA_ADMINISTRATOR"):
                locations = request.user.location.get_all_children()
                if activity_plan.operation_plan.location not in locations:
                    messages.error(
                        request,
                        "User is a branch data adminstrator but wanted to create an detail activity for a location he doesn't manage",
                    )
                    return htmx_redirect(request)
            activity_plan.save()
            messages.success(request, "Activity successfully added to the plan!")
        else:
            messages.error(request, form.errors)
        return redirect(request.META.get("HTTP_REFERER"))


@login_required
@role_required(
    [
        "SYSTEM_ADMINISTRATOR",
        "DATA_ADMINISTRATOR",
        "DATA_ANALYST",
        "BRANCH_USER",
        "BRANCH_DATA_ADMINISTRATOR",
        "BRANCH_DATA_ANALYST",
    ]
)
def detail_activity_detail(request, uuid=None):
    if request.method == "GET":
        detail_activity = DetailActivity.objects.get(id=uuid)
        resources = (
            ActivityResource.objects.filter(detail_activity=detail_activity)
            .filter(resource_type__type="RESOURCE")
            .all()
        )
        inputs = (
            ActivityResource.objects.filter(detail_activity=detail_activity)
            .filter(resource_type__type="INPUT")
            .all()
        )
        tools = (
            ActivityResource.objects.filter(detail_activity=detail_activity)
            .filter(resource_type__type="TOOL")
            .all()
        )
        detail_activity_form = DetailActivityForm(instance=detail_activity)
        data_names = []
        if len(resources) > 0:
            data_names.append("resources")
        if len(inputs) > 0:
            data_names.append("inputs")
        if len(tools) > 0:
            data_names.append("tools")

        ethio_start_date = EthiopianDateConverter.date_to_ethiopian(
            detail_activity.start_date
        )
        ethio_end_date = EthiopianDateConverter.date_to_ethiopian(
            detail_activity.end_date
        )
        detail_activity_date_range = f"{get_amharic_month(ethio_start_date[1])} {ethio_start_date[2]} - {get_amharic_month(ethio_end_date[1])} {ethio_end_date[2]}"

        return render(
            request,
            "core/detail_activity_detail.html",
            {
                "detail_activity": detail_activity,
                "detail_date_range": detail_activity_date_range,
                "resources": resources,
                "inputs": inputs,
                "tools": tools,
                "data_names": data_names,
                "breadcrumbs": [
                    {
                        "name": "Operation Overview",
                        "url": reverse_lazy("core:operation_plan_overview"),
                    },
                    {"name": "Operation Plans", "url": reverse_lazy("core:home")},
                    {
                        "name": detail_activity.activity_plan.operation_plan.operation_type.name,
                        "url": f"/operation_plan/{detail_activity.activity_plan.operation_plan.id}",
                        "ur": reverse_lazy(
                            "core:operation_plan_detail",
                            kwargs={
                                "uuid": detail_activity.activity_plan.operation_plan.id
                            },
                        ),
                    },
                    {
                        "name": detail_activity.activity_plan.type.name,
                        "url": f"/activity_plan/{detail_activity.activity_plan.id}",
                    },
                    {"name": detail_activity.detail_type.name, "url": f"#"},
                ],
                "page": "Operation Plan",
            },
        )
    elif request.method == "POST":
        if not request.user.userrole_set.filter(
            role__code__in=[
                "SYSTEM_ADMINISTRATOR",
                "DATA_ADMINISTRATOR",
                "BRANCH_DATA_ADMINISTRATOR",
            ]
        ).exists():
            return render(request, "permission_denied.html")
        detail_activity_form = DetailActivityForm(
            request.POST, request.FILES, prefix="detail"
        )
        if not detail_activity_form.is_valid():
            messages.error(request, detail_activity_form.errors)
            return redirect(request.META.get("HTTP_REFERER"))

        new_detail_activity = detail_activity_form.save(commit=False)
        if request.user.userrole_set.filter(
            role__code="BRANCH_DATA_ADMINISTRATOR"
        ).exists():
            locations = request.user.location.get_all_children()
            if (
                new_detail_activity.activity_plan.operation_plan.location
                not in locations
            ):
                messages.error(
                    request,
                    "User is a branch data adminstrator but wanted to create a detail activity for a location he doesn't manage",
                )
                return htmx_redirect(request)

        activity_plan = ActivityPlan.objects.get(pk=uuid)
        if not activity_plan:
            messages.error(request, "Invalid Activity Plan")
            return redirect(request.META.get("HTTP_REFERER"))

        new_detail_activity.activity_plan = activity_plan
        new_detail_activity.save()

        holder = {
            "resource": [],
            "tool": [],
            "input": [],
        }
        for key, item_list in request.POST.items():
            tmp = key.split("-")
            if len(tmp) <= 1:
                continue
            item_type, val = tmp
            if item_type not in ["resource", "tool", "input"]:
                continue

            item_list = request.POST.getlist(key)
            for i, item in enumerate(item_list):
                if i >= len(holder[item_type]):
                    holder[item_type].append({val: item})
                else:
                    holder[item_type][i][val] = item

        form_mapper: dict[
            str, Union[ActivityResourceForm, ActivityToolForm, ActivityInputForm]
        ] = {
            "resource": ActivityResourceForm,
            "tool": ActivityToolForm,
            "input": ActivityInputForm,
        }

        for resource_type, type_list in holder.items():
            if len(type_list) == 0:
                continue

            for data in type_list:
                form = form_mapper.get(resource_type)
                my_form = form(data=data)
                if not my_form.is_valid():
                    messages.error(request, my_form.errors)
                    return redirect(request.META.get("HTTP_REFERER"))

        for resource_type, type_list in holder.items():
            for resource in type_list:
                resource["detail_activity"] = new_detail_activity
                rt = ActivityResourceType.objects.get(pk=resource["resource_type"])
                if not rt:
                    continue

                activity_resource = ActivityResource(
                    detail_activity=new_detail_activity,
                    resource_type=rt,
                    work_norm=resource["work_norm"],
                    achievement=resource["achievement"],
                    payment=resource["payment"],
                )
                activity_resource.save()

        return redirect(request.META.get("HTTP_REFERER"))


@login_required
@role_required(
    [
        "SYSTEM_ADMINISTRATOR",
        "DATA_ADMINISTRATOR",
        "BRANCH_USER",
        "BRANCH_DATA_ADMINISTRATOR",
    ]
)
def edit_activity_plan(request):
    if request.method == "POST":
        activity_plan = get_object_or_404(ActivityPlan, pk=request.POST.get("id"))
        if request.user.userrole_set.filter(
            role__code="BRANCH_DATA_ADMINISTRATOR"
        ).exists():
            locations = request.user.location.get_all_children()
            if activity_plan.operation_plan.location not in locations:
                messages.error(
                    request,
                    "User is a branch data adminstrator but wanted to edit an activity plan for a location he doesn't manage",
                )
                return htmx_redirect(request)
        form = ActivityPlanForm(instance=activity_plan, data=request.POST)
        if not form.is_valid():
            return render(request, form.template_name, {"form": form})

        form.save()
        messages.success(request, "Activity successfully edited!")

        if not request.htmx:
            return redirect(request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(request.META.get("HTTP_REFERER"))
        return retarget(response, "body")


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "BRANCH_USER",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class ActivityResourceDetail(DetailView):
    model = ActivityResource
    template_name = "core/activity_resource.html"
    context_object_name = "resource"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail_activity = self.object.detail_activity
        context["breadcrumbs"] = [
            {
                "name": "Operation Overview",
                "url": reverse_lazy("core:operation_plan_overview"),
            },
            {"name": "Operation Plans", "url": reverse_lazy("core:home")},
            {
                "name": detail_activity.activity_plan.operation_plan.operation_type.name,
                "url": f"/operation_plan/{detail_activity.activity_plan.operation_plan.id}",
                "ur": reverse_lazy(
                    "core:operation_plan_detail",
                    kwargs={"uuid": detail_activity.activity_plan.operation_plan.id},
                ),
            },
            {
                "name": detail_activity.activity_plan.type.name,
                "url": f"/activity_plan/{detail_activity.activity_plan.id}",
            },
            {
                "name": detail_activity.detail_type.name,
                "url": f"/detail_activity/{detail_activity.id}",
            },
            {"name": self.object.resource_type.name, "url": "#"},
        ]
        return context


@method_decorator(
    role_required(
        ["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "DATA_ANALYST", "BRANCH_USER"]
    ),
    name="get",
)
@method_decorator(
    role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "BRANCH_USER"]),
    name="post",
)
class ActualActivityCreateView(CreateView):
    template_name = "partials/actual_activity_form.html"
    form_class = ActualActivityForm

    def get_initial(self):
        initial = super().get_initial()
        if self.request.method == "GET":
            activity_resource_id = self.request.GET.get("activity_resource_id")
            activity_resource = ActivityResource.objects.get(pk=activity_resource_id)
            initial["activity_resource"] = activity_resource
        return initial

    def form_valid(self, form):
        if self.request.user.userrole_set.filter(
            role__code="BRANCH_DATA_ADMINISTRATOR"
        ).exists():
            locations = self.request.user.location.get_all_children()
            activity_resource = ActivityResource.objects.get(
                self.request.GET.get("activity_resource_id")
            )
            if (
                activity_resource.detail_activity.activity_plan.operation_plan.location
                not in locations
            ):
                messages.error(
                    self.request,
                    "User is a branch data adminstrator but wanted to create an actual activity for a location he doesn't manage",
                )
                return htmx_redirect(self.request)
        form.save()
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(
    role_required(
        ["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "DATA_ANALYST", "BRANCH_USER"]
    ),
    name="get",
)
@method_decorator(
    role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "BRANCH_USER"]),
    name="post",
)
class EditActualActivityView(UpdateView):
    model = ActualActivityResource
    template_name = "partials/actual-activity-update.html"
    form_class = ActualActivityForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        return context

    def form_valid(self, form):
        if self.request.user.userrole_set.filter(
            role__code="BRANCH_DATA_ADMINISTRATOR"
        ).exists():
            locations = self.request.user.location.get_all_children()
            activity_resource = ActivityResource.objects.get(
                self.request.GET.get("activity_resource_id")
            )
            if (
                activity_resource.detail_activity.activity_plan.operation_plan.location
                not in locations
            ):
                messages.error(
                    self.request,
                    "User is a branch data adminstrator but wanted to create an actual activity for a location he doesn't manage",
                )
                return htmx_redirect(self.request)

        form.save()
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")
