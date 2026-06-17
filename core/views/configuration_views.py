from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
import django_tables2 as tables
from django.template.loader import render_to_string
from django_htmx.http import HttpResponseClientRedirect, retarget
from core.forms import (
    ActivityTypeForm,
    DetailActivityTypeForm,
    ItemForm,
    OperationTypeForm,
    ResourceTypeForm,
    SectorForm,
    LocationForm,
    LocationUpdateForm,
    OperationTypeUpdateForm,
)

from core.models import (
    ActivityResourceType,
    ActivityType,
    DetailActivityType,
    Item,
    OperationType,
    Sector,
    Location,
)
from core.decorators import role_required
from core.utils import htmx_redirect
from django.middleware import csrf
from django.http import HttpResponse
import csv
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
import django_tables2 as tables
from ethiopian_date import EthiopianDateConverter



@login_required
@role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR"])
def configuration(request):
    return render(request, "core/configuration.html", {"page": "CSV Configuration"})


class SectorTable(tables.Table):
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)
    createdDate = tables.Column(accessor="createdDate", verbose_name="Created Date")

    class Meta:
        model = Sector
        fields = ["name", "description", "createdDate"]
        template_name = "base-table.html"

    def render_createdDate(self, value):
        """Render created date in Ethiopian calendar"""
        if not value:
            return "-"
        
        # Convert Gregorian to Ethiopian calendar
        converter = EthiopianDateConverter()
        ethiopian_date = converter.to_ethiopian(value.year, value.month, value.day)
        year = ethiopian_date[0]
        month = ethiopian_date[1]
        day = ethiopian_date[2]
        months = [
            "መስከረም", "ጥቅምት", "ህዳር", "ታህሳስ", "ጥር", "የካቲት",
            "መጋቢት", "ሚያዚያ", "ግንቦት", "ሰኔ", "ሐምሌ", "ነሃሴ", "ጳጉሜ"
        ]
        
        month_name = months[month - 1] if 1 <= month <= 13 else "Unknown"
        return f"{month_name} {day}, {year}"

    def render_actions(self, value):
        return render_to_string("partials/sector-table-actions.html", {"id": value})
@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class SectorListView(tables.SingleTableView):
    model = Sector
    table_class = SectorTable
    template_name = "core/sector_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Sectors")
        context["form"] = SectorForm()
        return context    

    def get_table_data(self):
        name_filter = self.request.GET.get("name", "").strip()
        queryset = Sector.objects.all()
        
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        return queryset.all()


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class SectorUpdateView(UpdateView):
    model = Sector
    template_name = "partials/configuration-update.html"
    form_class = SectorForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        context["title"] = _("Sector")
        context["href"] = "core:edit_sector"
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Sector updated successfully")
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class SectorCreateView(CreateView):
    model = Sector
    form_class = SectorForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = Sector.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Sector with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))
        else:
            form.save()
            messages.success(self.request, _("Sector created successfully"))

        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class SectorDeleteView(DeleteView):
    model = Sector

    def get_success_url(self) -> str:
        messages.success(self.request, _("Sector deleted successfully"))
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class SectorDetailView(DetailView):
    model = Sector
    template_name = "core/sector_detail.html"
    context_object_name = "sector"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {
                "name": _("Sectors"),
                "url": reverse_lazy("core:sectors"),
            },
            {"name": self.object.name, "url": "#"},
        ]
        return context


class ResourceTable(tables.Table):
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = ActivityResourceType
        fields = ["name", "sectors", "operation_types", "norm_unit"]
        template_name = "base-table.html"

    def render_actions(self, value):
        return render_to_string("partials/resource-table-actions.html", {"id": value})


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ResourcesListView(tables.SingleTableView):
    model = ActivityResourceType
    table_class = ResourceTable
    template_name = "core/resource_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.resource_type = request.GET.get("type", "RESOURCE")
        if self.resource_type not in ["RESOURCE", "TOOL", "INPUT"]:
            return HttpResponseBadRequest()

        response = super().dispatch(request, *args, **kwargs)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match self.resource_type:
            case "RESOURCE":
                context["page"] = _("Resources")
                context["title"] = _("Resource")
                context["action"] = reverse_lazy("core:create_resource")
            case "TOOL":
                context["page"] = _("Tools")
                context["title"] = _("Tool")
                context["action"] = reverse_lazy("core:create_resource") + "?type=TOOL"
            case "INPUT":
                context["page"] = _("Inputs")
                context["title"] = _("Input")
                context["action"] = reverse_lazy("core:create_resource") + "?type=INPUT"

        context["form"] = ResourceTypeForm()
        return context

    def get_table_data(self):
        name_filter = self.request.GET.get("name", "").strip()
        queryset = ActivityResourceType.objects.filter(type=self.resource_type)
        
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        return queryset


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ResourceCreateView(CreateView):
    model = ActivityResourceType
    form_class = ResourceTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        resource_type = self.request.GET.get("type", "RESOURCE")
        obj = ActivityResourceType.objects.filter(name=name, type=resource_type).exclude(id=id)

        if obj:
            messages.error(self.request, _('Resource with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))
        
        self.object = form.save(commit=False)
        if resource_type not in ["RESOURCE", "TOOL", "INPUT"]:
            return HttpResponseBadRequest()
        self.object.type = resource_type
        selected_sectors = form.cleaned_data.get("sectors", [])
        selected_operation_types = form.cleaned_data.get("operation_types", [])
        self.object.save()
        self.object.sectors.set(selected_sectors)
        self.object.operation_types.set(selected_operation_types)
        self.object.save()
        messages.success(
            self.request,
            _(f"{resource_type.lower().capitalize()} created successfully"),
        )
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ResourceUpdateView(UpdateView):
    model = ActivityResourceType
    template_name = "partials/configuration-update.html"
    form_class = ResourceTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        context["title"] = _("Resource")
        context["form_action"] = reverse_lazy(
            "core:edit_resource", kwargs={"pk": self.object.id}
        )
        context["href"] = "core:edit_resource"
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        selected_sectors = form.cleaned_data.get("sectors", [])
        selected_operation_types = form.cleaned_data.get("operation_types", [])
        self.object.save()
        self.object.sectors.set(selected_sectors)
        self.object.operation_types.set(selected_operation_types)
        self.object.save()

        messages.success(
            self.request,
            _(f"{self.object.type.lower().capitalize()} updated successfully"),
        )
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ResourceDeleteView(DeleteView):
    model = ActivityResourceType

    def get_success_url(self) -> str:
        messages.success(
            self.request,
            _(f"{self.object.type.lower().capitalize()} deleted successfully"),
        )
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ResourceDetailView(DetailView):
    model = ActivityResourceType
    template_name = "core/resource_detail.html"
    context_object_name = "resource"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match self.object.type:
            case "RESOURCE":
                context["page"] = _("Resources")
            case "TOOL":
                context["page"] = _("Tools")
            case "INPUT":
                context["page"] = _("Inputs")

        context["breadcrumbs"] = [
            {
                "name": _("Resources"),
                "url": reverse_lazy("core:resources"),
            },
            {"name": self.object.name, "url": "#"},
        ]
        return context


class ItemTable(tables.Table):
    class Meta:
        model = Item
        fields = [
            "title",
            "species",
            "product_type",
            "date",
            "item_type",
            "batch",
          
        ]
        template_name = "base-table.html"

    def render_date(self, value):
        return value.strftime("%d-%m-%Y")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ItemListView(tables.SingleTableView):
    model = Item
    table_class = ItemTable
    template_name = "core/item_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Items")
        context["form"] = ItemForm()
        return context

    def get_table_data(self):
        name_filter = self.request.GET.get("name", "").strip()
        queryset = Item.objects.all()
        
        if name_filter:
            queryset = queryset.filter(species__icontains=name_filter)

        return queryset.all()


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ItemCreateView(CreateView):
    model = Item
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Item created successfully"))
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class OperationTypeCreateView(CreateView):
    model = OperationType
    form_class = OperationTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = OperationType.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Operation type with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))

        form.save()
        messages.success(self.request, _("Operation Type created successfully"))
        return htmx_redirect(self.request)

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class OperationTypeUpdateView(UpdateView):
    model = OperationType
    template_name = "partials/configuration-update.html"
    form_class = OperationTypeUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        context["title"] = _("Operation Type")
        context["href"] = "core:update_operation_type"
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = OperationType.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Operation type with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))

        form.save()
        messages.success(self.request, _("Operation type updated successfully"))
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


class OperationTypeTable(tables.Table):
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = OperationType
        fields = ["createdDate", "name", "sectors", "hierarchy_type"]
        template_name = "base-table.html"

    def render_actions(self, value):
        csrf_token = csrf.get_token(self.request)
        user_form = LocationUpdateForm(initial={"id": value})
        return render_to_string(
            "partials/operation-type-action.html",
            {"id": value, "csrf_token": csrf_token, "form": user_form},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class OperationTypeListView(tables.SingleTableView):
    model = OperationType
    table_class = OperationTypeTable
    template_name = "core/configuration_base_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Operation Types")
        context["title"] = _("Operation Types")
        context["entity_name"] = "Operation Type"
        context["form"] = OperationTypeForm()
        context["action"] = reverse_lazy("core:create_operation_type")
        return context

    def get_table_data(self):
        name_filter = self.request.GET.get("name", "").strip()
        queryset = OperationType.objects.all()
        
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        return queryset.all()


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ActivityTypeCreateView(CreateView):
    model = ActivityType
    form_class = ActivityTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = ActivityType.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Activity type with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))

        form.save()
        messages.success(self.request, _("Activity Type created successfully"))
        return htmx_redirect(self.request)

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ActivityTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ActivityType
    form_class = ActivityTypeForm
    template_name = "partials/configuration-update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        context["title"] = _("Activity Type")
        context["href"] = "core:update_activity_type"
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = ActivityType.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Activity type with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))

        form.save()
        messages.success(self.request, _("Activity Type updated successfully"))
        return htmx_redirect(self.request)

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


class ActivityTypeTable(tables.Table):
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = ActivityType
        fields = ["createdDate", "name", "operation_types"]
        template_name = "base-table.html"

    def render_actions(self, value):
        return render_to_string(
            "partials/base-configuration-action.html",
            {"url": reverse_lazy("core:update_activity_type", kwargs={"pk": value})},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class ActivityTypeListView(tables.SingleTableView):
    model = ActivityType
    table_class = ActivityTypeTable
    template_name = "core/configuration_base_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Activity Types")
        context["title"] = _("Activity Types")
        context["entity_name"] = "Activity Type"
        context["form"] = ActivityTypeForm()
        context["action"] = reverse_lazy("core:create_activity_type")
        return context

    def get_table_data(self):
        name_filter = self.request.GET.get("name", "").strip()
        queryset = ActivityType.objects.all()
        
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        return queryset.all()


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class DetailActivityTypeCreateView(CreateView):
    model = DetailActivityType
    form_class = DetailActivityTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = DetailActivityType.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Detail Activity type with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))

        form.save()
        messages.success(self.request, _("Detail Activity Type created successfully"))
        return htmx_redirect(self.request)

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class DetailActivityTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = DetailActivityType
    form_class = DetailActivityTypeForm
    template_name = "partials/configuration-update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        context["title"] = _("Detail Activity Type")
        context["href"] = "core:update_detail_activity_type"
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = DetailActivityType.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Detail Activity type with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))

        form.save()
        messages.success(self.request, _("Detail Activity Type updated successfully"))
        return htmx_redirect(self.request)

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


class DetailActivityTypeTable(tables.Table):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, localize=True
    )

    class Meta:
        model = DetailActivityType
        fields = [
            "createdDate",
            "name",
            "activites",
            "resource",
            "input",
            "tool",
            "annual_resource_type",
            "form",
        ]
        localize = (
            "createdDate",
            "name",
            "activities",
            "resource",
            "input",
            "tool",
            "annual_resource_type",
            "form",
        )
        template_name = "base-table.html"

    def render_actions(self, value):
        return render_to_string(
            "partials/base-configuration-action.html",
            {
                "url": reverse_lazy(
                    "core:update_detail_activity_type", kwargs={"pk": value}
                )
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class DetailActivityTypeListView(tables.SingleTableView):
    model = DetailActivityType
    table_class = DetailActivityTypeTable
    template_name = "core/configuration_base_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Detail Activity Types")
        context["title"] = _("Detail Activity Types")
        context["entity_name"] = "Detail Activity Type"
        context["form"] = DetailActivityTypeForm()
        context["action"] = reverse_lazy("core:create_detail_activity_type")
        return context

    def get_table_data(self):
        name_filter = self.request.GET.get("name", "").strip()
        queryset = DetailActivityType.objects.all()
        
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        return queryset.all()


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class LocationCreateView(CreateView):
    model = Location
    form_class = LocationForm
    template_name = "base-form.html"

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = Location.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Location with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))

        form.save()
        messages.success(self.request, _("Location created successfully"))
        return htmx_redirect(self.request)

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class LocationUpdateView(UpdateView):
    model = Location
    template_name = "partials/location-update.html"
    form_class = LocationUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.object.id
        context["title"] = _("Location")
        context["href"] = "core:update_location"
        return context

    def form_valid(self, form):
        id = form.instance.id
        name = form.cleaned_data['name']
        obj = Location.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(self.request, _('Location with that name already exists'))
            return redirect(self.request.META.get("HTTP_REFERER"))
        
        form.save()
        messages.success(self.request, _("Location updated successfully"))
        if not self.request.htmx:
            return redirect(self.request.META.get("HTTP_REFERER"))

        response = HttpResponseClientRedirect(self.request.META.get("HTTP_REFERER"))
        response = retarget(response, "body")
        return response

    def get_success_url(self) -> str:
        return self.request.META.get("HTTP_REFERER")


class EthiopianDateColumn(tables.Column):
    """Custom column for Ethiopian calendar dates"""
    
    def render(self, value):
        if not value:
            return "-"
        
        converter = EthiopianDateConverter()
        
        # Pass as positional arguments: year, month, day
        ethiopian_date = converter.to_ethiopian(value.year, value.month, value.day)
        
        # ethiopian_date is a tuple (year, month, day)
        year, month, day = ethiopian_date
        
        # Ethiopian month names in Amharic
        months = [
            "መስከረም", "ጥቅምት", "ህዳር", "ታህሳስ", "ጥር", "የካቲት",
            "መጋቢት", "ሚያዚያ", "ግንቦት", "ሰኔ", "ሐምሌ", "ነሃሴ", "ጳጉሜ"
        ]
        
        month_name = months[month - 1] if 1 <= month <= 13 else "Unknown"
        
        return f"{month_name} {day}, {year}"

class LocationTable(tables.Table):
    createdDate = EthiopianDateColumn(verbose_name="Created Date")  # Ethiopian calendar
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = Location
        fields = [
            "createdDate",
            "name",
            "parent",
        ]
        attrs = {"class": "table"}
        template_name = "base-table.html"
    def render_actions(self, value):
        csrf_token = csrf.get_token(self.request)
        user_form = LocationUpdateForm(initial={"id": value})
        return render_to_string(
            "partials/location-action.html",
            {"id": value, "csrf_token": csrf_token, "form": user_form},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
class LocationListView(tables.SingleTableView):
    model = Location
    table_class = LocationTable
    template_name = "core/configuration_base_list.html"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        name_param = self.request.GET.get("name")

        if name_param:
            queryset = queryset.filter(name__icontains=name_param)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Location")
        context["title"] = _("Locations")
        context["entity_name"] = "Location"
        context["form"] = LocationForm()
        context["action"] = reverse_lazy("core:create_location")
        return context


@login_required
def export_locations(request):
    location_type_to_reference_field_map = {
        "HQ": [],
        "BRANCH": [],
        "FOREST_SITE": ["remark"],
        "FOREST_ESTABLISTMENT": ["remark"],
        "NURSERY": ["zone", "district", "kebele", "location_on_map", "area", "remark"],
        "SAWMILL": [
            "zone",
            "district",
            "kebele",
            "location_on_map",
            "log_depo_storage_area",
        ],
        "SEED_SOURCE": ["region", "zone", "district", "kebele", "location_on_map"],
        "BLOCK": [],
        "COMPARTMENT": [],
        "SUB_COMPARTMENT": [
            "unique_code",
            "productive_area",
            "non_productive_area",
            "centroid_coordinate",
            "owner",
            "types_of_species_to_be_planted",
        ],
    }

    location_type = request.GET.get("location_type")
    locations = Location.objects.filter(type=location_type)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="location_list.csv"'

    current_location_fields = location_type_to_reference_field_map[location_type]

    headers = ["Name", "Parent", "Location Type"] + current_location_fields

    writer = csv.writer(response)
    writer.writerow(headers)

    for location in locations:
        row = [
            location.name,
            location.parent.__dict__.get("name", "") if location.parent else "",
            location.type,
        ] + [location.__dict__.get(field, "") for field in current_location_fields]

        writer.writerow(row)

    return response
