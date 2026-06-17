from urllib.parse import urlencode
import re
from django.urls import reverse_lazy
from django.http import HttpResponse
from django import forms
from django.views.generic import DetailView
import django_filters
from django_filters import widgets
import django_tables2 as tables
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from django_filters import FilterSet
from render_block import render_block_to_string
from core.decorators import role_required
from core.forms import FilterForm, InventoryFilterForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.db.models import Q

from core.models import (
    Batch,
    ItemInventory,
    ItemInventoryLog,
    ItemPurchase,
    ItemRecieve,
    ItemSale,
    ItemTransportation,
    Location,
    ProductName,
    ProductType,
    Test,
)


class ItemInventoryTable(tables.Table):
    species = tables.Column(accessor="item__species", verbose_name="Species")
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)
    item_type = tables.Column(accessor="item__item_type", verbose_name="Item Type")

    class Meta:
        model = ItemInventory
        template_name = "base-table.html"
        fields = [
            "item__title",
            "item_type",
            "location",
            "source_site",
            "species",
            "amount",
            "updated_at",
            "batch",
        ]
        sequence = [
            "location",
            "batch",
            "item_type",
            "item__title",
            "species",
            "source_site",
            "amount",
            "updated_at",
        ]
        order_by = "location"

    def render_item_type(self, value, record):
        if record.item.item_type == "PRODUCT":
            # try:
            #     return ProductName(record.item.product_type).label
            # except Exception:
            #     return ProductType(record.item.product_type).label
            return record.item.product_type
        if record.item.item_type == "SEEDLING" and record.location.type == "HQ":
            return "Grade 1"
        return value

    def render_actions(self, value):
        return render_to_string(
            "partials/item-inventory-table-actions.html", {"id": value}
        )

    def render_updated_at(self, value):
        return value.strftime("%d-%m-%Y")

    def render_amount(self, value):
        return round(value, 2)


class ItemTransportationTable(tables.Table):
    item = tables.Column(accessor="item__title", verbose_name="Item")

    class Meta:
        model = ItemTransportation
        attrs = {"class": "table"}


class ItemRecieveTable(tables.Table):
    item = tables.Column(accessor="item__title", verbose_name="Item")

    class Meta:
        model = ItemRecieve
        attrs = {"class": "table"}


class ItemSaleTable(tables.Table):
    item = tables.Column(accessor="item__title", verbose_name="Item")

    class Meta:
        model = ItemSale
        attrs = {"class": "table"}


class ItemPurchaseTable(tables.Table):
    item = tables.Column(accessor="item__title", verbose_name="Item")

    class Meta:
        model = ItemPurchase
        attrs = {"class": "table"}


class ItemInventoryFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )

    class Meta:
        model = ItemInventory
        fields = ["item", "location", "source_site", "item__item_type"]
        form = InventoryFilterForm


class ReducedInventoryFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains",
        field_name="item__species",
        label="Species",
        widget=forms.HiddenInput,
    )

    class Meta:
        model = ItemInventory
        fields = ["location", "item__item_type"]
        form = InventoryFilterForm


@method_decorator(
    role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "DATA_ANALYST", "BRANCH_DATA_ADMINISTRATOR", "BRANCH_DATA_ANALYST"]), name="dispatch"
)
@method_decorator(login_required, name="dispatch")
class FilteredInventoryListView(SingleTableMixin, FilterView):
    table_class = ItemInventoryTable
    model = ItemInventory
    template_name = "core/item_inventory_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.exclude(
            Q(amount=0) & Q(iteminventorylog__isnull=True)
        )

    def get_filterset_class(self):
        if self.request.htmx and not self.request.META.get("HTTP_REFERER").endswith(str(reverse_lazy(
            "core:item_inventory"
        ))):
            print("ININ")
            return ReducedInventoryFilter
        return ItemInventoryFilter

    def get(self, request, *args, **kwargs):
        if self.request.htmx:
            filterset_class = self.get_filterset_class()
            self.filterset = self.get_filterset(filterset_class)

            if (
                not self.filterset.is_bound
                or self.filterset.is_valid()
                or not self.get_strict()
            ):
                self.object_list = self.filterset.qs
            else:
                self.object_list = self.filterset.queryset.none()

            context = self.get_context_data(
                filter=self.filterset, object_list=self.object_list
            )
            content_html = render_block_to_string(
                self.template_name, "content", context=context, request=self.request
            )
            return HttpResponse(content_html, content_type="text/html")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Item Inventory")
        context["tab"] = _("Item Inventory")
        return context


class InventoryLogTable(tables.Table):
    amount = tables.Column(accessor="id", verbose_name="Amount")

    class Meta:
        model = ItemInventoryLog
        template_name = "base-table.html"
        exclude = (
            "id",
            "inventory",
            "cost",
            "amount_before_transaction",
            "amount_after_transaction",
        )
        sequence = (
            "date",
            "affector_location",
            "affector_source_site",
            "amount",
            "reason",
        )

    def render_amount(self, record):
        if record.amount < 0:
            return f'{_("Removed")} {abs(record.amount)}'
        elif record.amount == 0:
            return _("Empty transaction")
        else:
            return f'{_("Received")} {record.amount}'


@method_decorator(
    role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "DATA_ANALYST"]), name="dispatch"
)
@method_decorator(login_required, name="dispatch")
class InventoryDetailView(tables.SingleTableView):
    model = ItemInventoryLog
    template_name = "core/item_inventory_detail.html"
    context_object_name = "inventory"
    table_class = InventoryLogTable

    def get_table_data(self):
        return ItemInventoryLog.objects.filter(inventory_id=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["inventory"] = ItemInventory.objects.get(pk=self.kwargs.get("pk"))
        context["tab"] = _("Item Inventory")
        context["page"] = _("Item Inventory")
        context["breadcrumbs"] = [
            {
                "name": _("Inventory List"),
                "url": reverse_lazy("core:item_inventory"),
            },
            {"name": _("Inventory Detail"), "url": "#"},
        ]
        return context


class HQBatchInfoTable(tables.Table):
    amount = tables.Column(accessor="id", verbose_name="Amount")
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = Batch
        fields = ["batch_number", "item__species"]
        template_name = "base-table.html"

    def __init__(self, *args, **kwargs):
        self.location: Location = kwargs.pop("location")
        super().__init__(*args, **kwargs)

    def render_amount(self, record):
        inventory = ItemInventory.get_inventory_by_batch(self.location, record)
        return inventory.amount

    def render_actions(self, record):
        filters = {"location": self.location.id, "batch": record.id}
        encoded_param = urlencode(filters)
        url = f"{reverse_lazy('core:reports_testing')}?{encoded_param}"

        return render_to_string("partials/base-actions-partial.html", {"url": url})


class HQBatchInfoFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )
    round = django_filters.CharFilter(method="filter_round", label="Round")
    test_type = django_filters.CharFilter(
        method="filter_test_type",
        label="Test Type",
        widget=forms.HiddenInput,
    )
    untested = django_filters.BooleanFilter(
        method="filter_untested", label="Untested", widget=forms.HiddenInput
    )

    class Meta:
        model = Batch
        fields = []
        form = FilterForm

    def filter_untested(self, queryset, name, value):
        if value is False:
            return queryset

        tested_batches = Test.objects.filter(
            location_id=self.request.GET.get("location"),
        ).values_list("batch_id", flat=True)
        return queryset.exclude(id__in=tested_batches)

    def filter_round(self, queryset, name, value):
        test_type = self.request.GET.get("test_type")
        if test_type:
            tested_batches = Test.objects.filter(
                location_id=self.request.GET.get("location"),
                type=self.request.GET.get("test_type"),
                round=value,
            ).values_list("batch_id", flat=True)
        else:
            tested_batches = Test.objects.filter(
                location_id=self.request.GET.get("location"),
                round=value,
            ).values_list("batch_id", flat=True)
        if value == "1":
            round2_batches = Test.objects.filter(
                location_id=self.request.GET.get("location"),
                type=self.request.GET.get("test_type"),
                round="2",
            ).values_list("batch_id", flat=True)
            round3_batches = Test.objects.filter(
                location_id=self.request.GET.get("location"),
                type=self.request.GET.get("test_type"),
                round="3",
            ).values_list("batch_id", flat=True)
            return queryset.filter(
                id__in=tested_batches.exclude(batch_id__in=round2_batches).exclude(
                    batch_id__in=round3_batches
                )
            )
        elif value == "2":
            round3_batches = Test.objects.filter(
                location_id=self.request.GET.get("location"),
                type=self.request.GET.get("test_type"),
                round="3",
            ).values_list("batch_id", flat=True)
            return queryset.filter(
                id__in=tested_batches.exclude(batch_id__in=round3_batches)
            )
        return queryset.filter(id__in=tested_batches)

    def filter_test_type(self, queryset, name, value):
        if value:
            tested_batches = Test.objects.filter(
                location_id=self.request.GET.get("location"),
                type=value,
            ).values_list("batch_id", flat=True)
        else:
            tested_batches = Test.objects.filter(
                location_id=self.request.GET.get("location"),
                type=value,
            ).values_list("batch_id", flat=True)
        return queryset.filter(id__in=tested_batches)

    @property
    def qs(self):
        parent = super().qs
        location = self.request.GET.get("location")
        batch_ids = ItemInventory.objects.filter(location_id=location).values_list(
            "batch_id", flat=True
        )
        return parent.filter(id__in=batch_ids)


class HQBatchInfoView(SingleTableMixin, FilterView):
    table_class = HQBatchInfoTable
    model = Batch
    template_name = "partials/hq-batch-info.html"
    filterset_class = HQBatchInfoFilter

    def get_table(self, **kwargs):
        pk = self.request.GET.get("location")
        location = Location.objects.get(pk=pk)
        kwargs["location"] = location
        table = super().get_table(**kwargs)
        untested = bool(self.request.GET.get("untested"))
        if untested:
            table.exclude = ("actions",)
        return table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["location"] = self.request.GET.get("location")
        return context
