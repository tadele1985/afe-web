from urllib.parse import urlencode
from django.http import HttpRequest
from django import forms
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django_filters import FilterSet
import django_filters
import django_tables2 as tables
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from django_filters.views import FilterView
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta


from core.decorators import role_required
from core.forms import FilterForm
from core.models import (
    Beatup,
    DownTime,
    FactoryProductionReport,
    ForestInventoryReport,
    Handoff,
    HarvestingReport,
    ItemPurchase,
    ItemRecieve,
    ItemSale,
    ItemTransportation,
    ItemType,
    JobOportunity,
    Location,
    LumberStoredReport,
    PlantationSiteSelectionReport,
    OperationalForestInventory,
    PlantedSeedlingReport,
    ProductGiveAway,
    SurvivalCount,
    Test,
    Thinning,
    ThinningSale,
    ThinningType,
    TimelyHarvestingReport,
    DetailActivityType,
    DetailActivity,
    LOCATION_TYPE_CHOICES,
    Sector,
    OperationType,
    ActualActivityResource,
)
from django.utils.translation import gettext as _


class ItemReceiveTable(tables.Table):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )
    item_species = tables.Column(accessor="id", verbose_name="Species")
    amount = tables.Column(
        verbose_name="Amount",
        footer=lambda table: sum(
            sum(
                ItemRecieve.objects.filter(voucher_no=x._record.voucher_no).values_list(
                    "amount", flat=True
                )
            )
            for x in table.page
        ),
    )

    class Meta:
        model = ItemRecieve
        fields = [
            "date",
            "amount",
            "voucher_no",
            "location",
            "driver_name",
            "createdBy",
        ]
        sequence = [
            "voucher_no",
            "item_species",
            "location",
            "amount",
            "date",
            "driver_name",
            "create"
            "dBy",
            "actions",
        ]
        template_name = "base-table.html"

    def render_item_species(self, record):
        all_species = ItemRecieve.objects.filter(voucher_no=record.voucher_no)
        species_list = ""
        for i, species in enumerate(all_species):
            if i != len(all_species) - 1:
                if i > 3:
                    species_list += "..."
                    break
                species_list += species.item.species + ", "
            else:
                species_list += species.item.species
        return species_list

    def render_amount(self, record):
        amounts = ItemRecieve.objects.filter(voucher_no=record.voucher_no).values_list(
            "amount", flat=True
        )
        return sum(amounts)

    def render_actions(self, value):
        return render_to_string("partials/item-receive-actions.html", {"id": value})


class ItemReceiveFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )
    location_type = django_filters.ChoiceFilter(
        choices=LOCATION_TYPE_CHOICES,
        label="Location Type",
        field_name="location__type",
    )

    class Meta:
        model = ItemRecieve
        fields = ["date", "batch", "source_site", "location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        receives = ItemRecieve.objects.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for receive in receives:
            if receive["voucher_no"] not in found_vouchers:
                found_vouchers.append(receive["voucher_no"])
                ids.append(receive["id"])
        return parent.filter(id__in=ids)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemReceiveListView(ExportMixin, SingleTableMixin, FilterView):
    model = ItemRecieve
    table_class = ItemReceiveTable
    template_name = "core/item_receive_list.html"
    filterset_class = ItemReceiveFilter
    export_name = "Receive Report"
    dataset_kwargs = {"title": "Receive Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Receive Report")
        return context


class FullItemRecieveTable(tables.Table):
    item_species = tables.Column(accessor="item__species", verbose_name="Species")
    item_name = tables.Column(accessor="item__title", verbose_name="Item Name")

    class Meta:
        model = ItemRecieve
        fields = [
            "item_name",
            "item_species",
            "batch",
            "date",
            "amount",
            "voucher_no",
            "source_site",
            "driver_name",
            "plate_number",
        ]
        sequence = [
            "voucher_no",
            "source_site",
            "item_name",
            "item_species",
            "batch",
            "driver_name",
            "plate_number",
            "amount",
            "date",
        ]
        template_name = "base-table.html"


class FullItemReceiveFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )

    class Meta:
        model = ItemRecieve
        fields = ["batch", "source_site"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        receive = get_object_or_404(ItemRecieve, pk=uuid)
        return parent.filter(voucher_no=receive.voucher_no)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemReceiveDetailView(SingleTableMixin, FilterView):
    model = ItemRecieve
    table_class = FullItemRecieveTable
    template_name = "core/item_receive_detail.html"
    filterset_class = FullItemReceiveFilter

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get("pk")
        context = super().get_context_data(**kwargs)
        context["page"] = _("Receive Report")
        context["id"] = pk
        context["breadcrumbs"] = [
            {"name": _("Receive Reports"), "url": reverse_lazy("core:reports_receive")},
            {"name": _("Recieve Report"), "url": "#"},
        ]
        return context


class TransportTable(tables.Table):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )
    item_species = tables.Column(accessor="id", verbose_name="Species")
    amount = tables.Column(
        verbose_name="Amount",
        footer=lambda table: sum(table.render_amount(x) for x in table.data),
    )

    class Meta:
        model = ItemTransportation
        fields = [
            "date",
            "from_location",
            "to_location",
            "amount",
            "voucher_no",
            "createdBy",
            "unit",
        ]
        sequence = [
            "voucher_no",
            "createdBy",
            "item_species",
            "from_location",
            "to_location",
            "unit",
            "date",
            "amount",
            "actions",
        ]
        template_name = "base-table.html"

    def render_item_species(self, record):
        all_species = ItemTransportation.objects.filter(voucher_no=record.voucher_no)
        species_list = ""
        for i, species in enumerate(all_species):
            if not species.item.species:
                continue
            if i != len(all_species) - 1:
                if i > 3:
                    species_list += "..."
                    break
                species_list += species.item.species + ", "
            else:
                species_list += species.item.species
        return species_list

    def render_amount(self, record):
        amounts = ItemTransportation.objects.filter(
            voucher_no=record.voucher_no
        ).values_list("amount", flat=True)
        return sum(amounts)

    def render_actions(self, value):
        return render_to_string("partials/item-transport-actions.html", {"id": value})


class FullTransportTable(tables.Table):
    item_name = tables.Column(accessor="item__title", verbose_name="Item Name")
    item_species = tables.Column(accessor="item__species", verbose_name="Species")

    class Meta:
        model = ItemTransportation
        fields = [
            "driver_name",
            "from_location",
            "to_location",
            "voucher_no",
            "amount",
            "plate_number",
        ]
        sequence = [
            "voucher_no",
            "item_name",
            "item_species",
            "driver_name",
            "plate_number",
            "from_location",
            "to_location",
            "amount",
        ]
        template_name = "base-table.html"


class TransportationFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )
    from_location = django_filters.ModelChoiceFilter(
        field_name="from_location", label="From", queryset=Location.objects.all()
    )
    to_location = django_filters.ModelChoiceFilter(
        field_name="to_location", label="To", queryset=Location.objects.all()
    )

    from_location_type = django_filters.ChoiceFilter(
        choices=LOCATION_TYPE_CHOICES,
        label="From Location Type",
        field_name="from_location__type",
    )

    to_location_type = django_filters.ChoiceFilter(
        choices=LOCATION_TYPE_CHOICES,
        label="To Location Type",
        field_name="to_location__type",
    )

    class Meta:
        model = ItemTransportation
        fields = ["date", "from_location", "to_location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        transports = ItemTransportation.objects.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for transport in transports:
            if transport["voucher_no"] not in found_vouchers:
                found_vouchers.append(transport["voucher_no"])
                ids.append(transport["id"])
        return parent.filter(id__in=ids)


class FullTransportationFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )
    from_location = django_filters.ModelChoiceFilter(
        field_name="from_location", label="From", queryset=Location.objects.all()
    )
    to_location = django_filters.ModelChoiceFilter(
        field_name="to_location", label="To", queryset=Location.objects.all()
    )

    class Meta:
        model = ItemTransportation
        fields = ["date", "from_location", "to_location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        transport = get_object_or_404(ItemTransportation, pk=uuid)
        return parent.filter(voucher_no=transport.voucher_no)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemTransportListView(ExportMixin, SingleTableMixin, FilterView):
    model = ItemTransportation
    table_class = TransportTable
    template_name = "core/item_transport_list.html"
    filterset_class = TransportationFilter
    export_name = "Transportation Report"
    dataset_kwargs = {"title": "Transportation Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Transportation Report")
        return context


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemTransportDetailView(SingleTableMixin, FilterView):
    model = ItemTransportation
    table_class = FullTransportTable
    template_name = "core/item_transport_detail.html"
    filterset_class = FullTransportationFilter

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get("pk")
        context = super().get_context_data(**kwargs)
        context["page"] = _("Transportation Report")
        context["id"] = pk
        context["breadcrumbs"] = [
            {
                "name": _("Transportation Reports"),
                "url": reverse_lazy("core:reports_transportation"),
            },
            {"name": _("Transportation Report"), "url": "#"},
        ]
        return context


class PurchaseTable(tables.Table):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )
    amount = tables.Column(
        verbose_name="Amount",
        footer=lambda table: sum(
            sum(
                ItemPurchase.objects.filter(
                    voucher_no=x._record.voucher_no
                ).values_list("amount", flat=True)
            )
            for x in table.page
        ),
    )

    class Meta:
        model = ItemPurchase
        fields = ["voucher_no", "date", "location", "amount", "createdBy", "actions"]
        template_name = "base-table.html"

    def render_amount(self, record):
        amounts = ItemPurchase.objects.filter(voucher_no=record.voucher_no).values_list(
            "amount", flat=True
        )
        return sum(amounts)

    def render_actions(self, value):
        return render_to_string("partials/item-purchase-actions.html", {"id": value})


class FullPurchaseTable(tables.Table):
    total_cost = tables.Column(accessor="id", verbose_name="Total Cost")

    class Meta:
        model = ItemPurchase
        fields = [
            "voucher_no",
            "date",
            "location",
            "item__species",
            "expert",
            "cost",
            "amount",
        ]
        template_name = "base-table.html"

    def render_total_cost(self, record):
        return record.cost * record.amount


class PurchaseFilter(FilterSet):
    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    location_type = django_filters.ChoiceFilter(
        choices=LOCATION_TYPE_CHOICES,
        label="Location Type",
        field_name="location__type",
    )

    class Meta:
        model = ItemPurchase
        fields = ["location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        purchases = ItemPurchase.objects.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for purchase in purchases:
            if purchase["voucher_no"] not in found_vouchers:
                found_vouchers.append(purchase["voucher_no"])
                ids.append(purchase["id"])
        return parent.filter(id__in=ids)


class FullPurchaseFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )

    class Meta:
        model = ItemPurchase
        fields = ["location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        purchase = get_object_or_404(ItemPurchase, pk=uuid)
        return parent.filter(voucher_no=purchase.voucher_no)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemPurchaseListView(ExportMixin, SingleTableMixin, FilterView):
    model = ItemPurchase
    table_class = PurchaseTable
    template_name = "core/item_purchase_list.html"
    filterset_class = PurchaseFilter
    export_name = "Purchase Report"
    dataset_kwargs = {"title": "Purchase Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Purchase Report")
        return context


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemPurchaseDetailView(SingleTableMixin, FilterView):
    model = ItemPurchase
    table_class = FullPurchaseTable
    template_name = "core/item_purchase_detail.html"
    filterset_class = FullPurchaseFilter

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get("pk")
        context = super().get_context_data(**kwargs)
        context["page"] = _("Purchase Report")
        context["id"] = pk
        context["breadcrumbs"] = [
            {
                "name": _("Purchase Reports"),
                "url": reverse_lazy("core:reports_purchase"),
            },
            {"name": _("Purchase Report"), "url": "#"},
        ]
        return context


class ItemSaleTable(tables.Table):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )

    class Meta:
        model = ItemSale
        fields = ("product_type", "unit", "amount", "unit_price", "total_price", "date", "createdBy", "location", "seller", "client", "voucher_no")
        exclude = ("id", "item")
        sequence = ("voucher_no",)
        template_name = "base-table.html"

    def render_actions(self, value):
        return render_to_string("partials/item-sale-actions.html", {"id": value})


class ItemSaleFilter(FilterSet):
    location_type = django_filters.ChoiceFilter(
        choices=LOCATION_TYPE_CHOICES,
        label="Location Type",
        field_name="location__type",
    )

    class Meta:
        model = ItemSale
        fields = ["date", "location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        sales = ItemSale.objects.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for sale in sales:
            if sale["voucher_no"] not in found_vouchers:
                found_vouchers.append(sale["voucher_no"])
                ids.append(sale["id"])
        return parent.filter(id__in=ids)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemSaleListView(ExportMixin, SingleTableMixin, FilterView):
    model = ItemSale
    table_class = ItemSaleTable
    template_name = "core/item_sale_list.html"
    filterset_class = ItemSaleFilter
    export_name = "Sale Report"
    dataset_kwargs = {"title": "Sale Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Sale Report")
        return context


class FullItemSaleFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )

    item__item_type = django_filters.ChoiceFilter(
        choices=ItemType,
        label="Sale Type",
        field_name="item__item_type",
    )

    branch = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(type="BRANCH").all(),
        label="Branch",
        method="branch_filter",
    )

    class Meta:
        model = ItemSale
        fields = ["batch"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        sale = get_object_or_404(ItemSale, pk=uuid)
        return parent.filter(voucher_no=sale.voucher_no)

    def branch_filter(self, queryset, name, value):
        children = value.get_all_children()
        children_ids = [child.id for child in children]
        return queryset.filter(location_id__in=children_ids)


class FullItemSaleTable(tables.Table):
    item_species = tables.Column(accessor="item__species", verbose_name="Species")
    total_price = tables.Column(verbose_name="Total Price")

    class Meta:
        model = ItemSale
        exclude = ("id", "item", "createdDate", "updatedDate")
        sequence = [
            "voucher_no",
            "date",
            "batch",
            "item_species",
            "unit_price",
            "amount",
            "total_price",
        ]
        template_name = "base-table.html"

@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ItemSaleDetailView(SingleTableMixin, FilterView):
    model = ItemSale
    table_class = FullItemSaleTable
    template_name = "core/item_sale_detail.html"
    filterset_class = FullItemSaleFilter

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get("pk")
        context = super().get_context_data(**kwargs)
        context["page"] = _("Sale Report")
        context["id"] = pk
        context["breadcrumbs"] = [
            {"name": _("Sale Reports"), "url": reverse_lazy("core:reports_sale")},
            {"name": _("Sale Report"), "url": "#"},
        ]
        return context


class ThinningSaleTable(tables.Table):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )

    class Meta:
        model = ThinningSale
        fields = [
            "product_type",
            "unit",
            "amount",
            "unit_price",
            "total_price",
            "sale_type",
            "location",
            "voucher_no",
            "batch",
            "batch__item__species",
            "batch__source_site",
            "date",
            "sold_to",
            "sold_by",
        ]
        template_name = "base-table.html"

    def render_actions(self, value):
        link = reverse_lazy("core:reports_thinning_sale_detail", kwargs={"pk": value})
        return render_to_string("partials/base-actions-partial.html", {"url": link})


class ThinningSaleFilter(FilterSet):
    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = ThinningSale
        fields = [
            "batch__source_site",
            "batch__item__species",
            "location",
            "location__type",
        ]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        sales = ThinningSale.objects.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for sale in sales:
            if sale["voucher_no"] not in found_vouchers:
                found_vouchers.append(sale["voucher_no"])
                ids.append(sale["id"])
        return parent.filter(id__in=ids)


class FullThinningSaleTable(tables.Table):
    amount = tables.Column(
        verbose_name="Amount", footer=lambda table: sum(x.amount for x in table.data)
    )

    class Meta:
        model = ThinningSale
        fields = [
            "batch",
            "batch__item__species",
            "product_category",
            "amount",
            "unit_price",
            "total_rev_before_vat",
        ]
        template_name = "base-table.html"


class FullThinningSaleFilter(FilterSet):
    class Meta:
        model = ThinningSale
        fields = ["batch", "batch__item__species", "product_category"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        sale = get_object_or_404(ThinningSale, pk=uuid)
        return parent.filter(voucher_no=sale.voucher_no)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ThinningSaleListView(ExportMixin, SingleTableMixin, FilterView):
    model = ThinningSale
    table_class = ThinningSaleTable
    template_name = "core/base_report.html"
    filterset_class = ThinningSaleFilter
    export_name = "Thinning Sale Report"
    dataset_kwargs = {"title": "Thinning Sale Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Thinning Sale Report")
        context["report_name"] = _("Thinning Sale Report")
        context["clear_url"] = reverse_lazy("core:reports_thinning_sale")
        return context


class ThinningSaleDetailView(SingleTableMixin, FilterView):
    model = ThinningSale
    table_class = FullThinningSaleTable
    template_name = "core/base_report.html"
    filterset_class = FullThinningSaleFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        context["page"] = _("Thinning Sale Report")
        context["report_name"] = _("Thinning Sale Report")
        context["clear_url"] = reverse_lazy(
            "core:reports_thinning_sale_detail", kwargs={"pk": pk}
        )
        context["breadcrumbs"] = [
            {
                "name": _("Thinning Sale Reports"),
                "url": reverse_lazy("core:reports_thinning_sale"),
            },
            {"name": _("Thinning Sale Report"), "url": "#"},
        ]
        return context


class SeedTestTable(tables.Table):
    item_species = tables.Column(accessor="item__species", verbose_name="Species")
    quantity = tables.Column(
        verbose_name="Quantity",
        footer=lambda table: sum(x._record.quantity for x in table.page),
    )

    class Meta:
        model = Test
        exclude = ("id", "item")
        template_name = "base-table.html"


class SeedTestFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )

    class Meta:
        model = Test
        fields = [
            "start_date",
            "end_date",
            "result",
            "batch",
            "round",
            "location",
            "type",
        ]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class SeedTestListView(ExportMixin, SingleTableMixin, FilterView):
    model = Test
    table_class = SeedTestTable
    template_name = "core/seed_test_list.html"
    filterset_class = SeedTestFilter
    export_name = "Tree Seed Testing Report"
    dataset_kwargs = {"title": "Tree Seed Testing Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Tree Seed Testing Report")
        return context


class HandoffTable(tables.Table):
    item_species = tables.Column(
        accessor="batch__item__species", verbose_name="Species"
    )

    seed_source = tables.Column(accessor="batch__source_site")
    amount = tables.Column(
        verbose_name="Amount", footer=lambda table: sum(x.amount for x in table.data)
    )

    class Meta:
        model = Handoff
        fields = ["createdBy", "batch", "item_species", "seed_source", "date", "amount"]
        template_name = "base-table.html"


class HandoffFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="batch__item__species", label="Species"
    )

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = Handoff
        fields = ["date", "batch__source_site", "location"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class HandoffListView(ExportMixin, SingleTableMixin, FilterView):
    model = Handoff
    table_class = HandoffTable
    template_name = "core/base_report.html"
    filterset_class = HandoffFilter
    export_name = "Handoff Report"
    dataset_kwargs = {"title": "Handoff Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Handoff Report")
        context["report_name"] = _("Handoff Report")
        context["clear_url"] = reverse_lazy("core:reports_handoff")
        return context
    
class BeatupTable(tables.Table):
    item_species = tables.Column(
        accessor="batch__item__species", verbose_name="Species"
    )

    seed_source = tables.Column(accessor="batch__source_site")
    amount = tables.Column(
        verbose_name="Amount", footer=lambda table: sum(x.amount for x in table.data)
    )

    class Meta:
        model = Beatup
        fields = [
            "createdBy",
            "batch",
            "item_species",
            "seed_source",
            "location",
            "date",
            "amount",
        ]
        template_name = "base-table.html"


class BeatupFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="batch__item__species", label="Species"
    )

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = Beatup
        fields = ["date", "batch__source_site", "location"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class BeatupListView(ExportMixin, SingleTableMixin, FilterView):
    model = Beatup
    table_class = BeatupTable
    template_name = "core/base_report.html"
    filterset_class = BeatupFilter
    export_name = "Beatup Report"
    dataset_kwargs = {"title": "Beatup Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Beatup Report")
        context["report_name"] = _("Beatup Report")
        context["clear_url"] = reverse_lazy("core:reports_beatup")
        return context


class SurvivalCountTable(tables.Table):
    item_species = tables.Column(
        accessor="batch__item__species", verbose_name="Species"
    )

    seed_source = tables.Column(accessor="batch__source_site")

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )
    
    no_alive = tables.Column(
        verbose_name="No alive",
        footer=lambda table: sum(x.no_alive for x in table.data if hasattr(x, 'no_alive')),
    )
    
    no_dead = tables.Column(
        verbose_name="No dead", 
        footer=lambda table: sum(x.no_dead for x in table.data if hasattr(x, 'no_dead')),
    )
    
    total_survival = tables.Column(
        verbose_name="Total Survival Count",
        footer=lambda table: sum((x.no_alive + x.no_dead) for x in table.data if hasattr(x, 'no_alive') and hasattr(x, 'no_dead')),
    )
    
    no_alive_percentage = tables.Column(
        verbose_name="Total Alive in (%)",
        attrs={'td': {'class': 'text-success fw-bold'}},
        footer=lambda table: calculate_alive_percentage(table.data)
    )
    
    no_dead_percentage = tables.Column(
        verbose_name="Total Dead in (%)",
        attrs={'td': {'class': 'text-danger fw-bold'}},
        footer=lambda table: calculate_dead_percentage(table.data)
    )
    
    class Meta:
        model = SurvivalCount
        fields = [
            "createdBy",
            "batch",
            "item_species",
            "seed_source",
            "location",
            "date",
            "no_alive",
            "no_dead",
            "total_survival",
            "no_alive_percentage",
            "no_dead_percentage",
        ]
        template_name = "base-table.html"

    def render_total_survival(self, value, record):
        """Calculate total survival count for each row"""
        return record.no_alive + record.no_dead
    
    def render_no_alive_percentage(self, value, record):
        """Calculate and render alive percentage for each row"""
        total = record.no_alive + record.no_dead
        if total > 0:
            percentage = (record.no_alive / total) * 100
            return f"{percentage:.1f}%"
        return "0%"
    
    def render_no_dead_percentage(self, value, record):
        """Calculate and render dead percentage for each row"""
        total = record.no_alive + record.no_dead
        if total > 0:
            percentage = (record.no_dead / total) * 100
            return f"{percentage:.1f}%"
        return "0%"


# Helper functions for footer calculations
def calculate_alive_percentage(data):
    """Calculate overall alive percentage for footer"""
    total_alive = sum(x.no_alive for x in data if hasattr(x, 'no_alive'))
    total_dead = sum(x.no_dead for x in data if hasattr(x, 'no_dead'))
    total = total_alive + total_dead
    if total > 0:
        return f"{ (total_alive / total) * 100:.1f}%"
    return "0%"


def calculate_dead_percentage(data):
    """Calculate overall dead percentage for footer"""
    total_alive = sum(x.no_alive for x in data if hasattr(x, 'no_alive'))
    total_dead = sum(x.no_dead for x in data if hasattr(x, 'no_dead'))
    total = total_alive + total_dead
    if total > 0:
        return f"{ (total_dead / total) * 100:.1f}%"
    return "0%"


class SurvivalCountFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="batch__item__species", label="Species"
    )

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = SurvivalCount
        fields = ["date", "batch__source_site", "location"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class SurvivalCountListView(ExportMixin, SingleTableMixin, FilterView):
    model = SurvivalCount
    table_class = SurvivalCountTable
    template_name = "core/base_report.html"
    filterset_class = SurvivalCountFilter
    export_name = "Survival Count Report"
    dataset_kwargs = {"title": "Survival Count Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Survival Count Report")
        context["report_name"] = _("Survival Count Report")
        context["clear_url"] = reverse_lazy("core:reports_survival")
        return context


class ThinningTable(tables.Table):
    item_species = tables.Column(
        accessor="batch__item__species", verbose_name="Species"
    )

    seed_source = tables.Column(accessor="batch__source_site")
    amount = tables.Column(
        verbose_name="Amount",
        footer=lambda table: sum(
            sum(
                Thinning.objects.filter(voucher_no=x._record.voucher_no).values_list(
                    "amount", flat=True
                )
            )
            for x in table.page
        ),
    )
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )

    class Meta:
        model = Thinning
        fields = [
            "createdBy",
            "batch",
            "item_species",
            "seed_source",
            "location",
            "date",
            "product_category",
            "voucher_no",
        ]
        sequence = [
            "voucher_no",
            "createdBy",
            "date",
            "batch",
            "product_category",
            "item_species",
            "seed_source",
        ]
        template_name = "base-table.html"

    def render_amount(self, record):
        amounts = Thinning.objects.filter(voucher_no=record.voucher_no).values_list(
            "amount", flat=True
        )
        return sum(amounts)

    def render_actions(self, value, record):
        link = reverse_lazy("core:reports_thinning_detail", kwargs={"pk": value})
        query_params = {"thinning_type": record.thinning_type}
        encoded_param = urlencode(query_params)

        final_url = f"{link}?{encoded_param}"

        return render_to_string(
            "partials/base-actions-partial.html", {"url": final_url}
        )


class ThinningFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="batch__item__species", label="Species"
    )

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    thinning_type = django_filters.CharFilter(
        field_name="thinning_type", widget=forms.HiddenInput()
    )

    class Meta:
        model = Thinning
        fields = ["date", "batch__source_site", "thinning_type", "location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        thinnings = Thinning.objects.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for receive in thinnings:
            if receive["voucher_no"] not in found_vouchers:
                found_vouchers.append(receive["voucher_no"])
                ids.append(receive["id"])
        return parent.filter(id__in=ids)


class FullThinningFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="batch__item__species", label="Species"
    )

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    thinning_type = django_filters.CharFilter(
        field_name="thinning_type", widget=forms.HiddenInput()
    )

    class Meta:
        model = Thinning
        fields = ["date", "batch__source_site", "thinning_type"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        thinning = get_object_or_404(Thinning, pk=uuid)
        return parent.filter(voucher_no=thinning.voucher_no)


class FullThinningTable(tables.Table):
    item_species = tables.Column(
        accessor="batch__item__species", verbose_name="Species"
    )

    seed_source = tables.Column(accessor="batch__source_site")
    amount = tables.Column(
        verbose_name="Amount",
        footer=lambda table: sum(x._record.amount for x in table.page),
    )

    class Meta:
        model = Thinning
        fields = [
            "batch",
            "item_species",
            "seed_source",
            "date",
            "product_category",
            "voucher_no",
        ]
        sequence = [
            "voucher_no",
            "date",
            "batch",
            "product_category",
            "item_species",
            "seed_source",
        ]
        template_name = "base-table.html"


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ThinningListView(ExportMixin, SingleTableMixin, FilterView):
    model = Thinning
    table_class = ThinningTable
    template_name = "core/base_report.html"
    filterset_class = ThinningFilter
    export_name = "Thinnning Report"
    dataset_kwargs = {"title": "Thinnning Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thinning_type = self.request.GET.get("thinning_type")
        friendly_name = ThinningType(thinning_type).label
        context["page"] = _(f"{friendly_name} Thinning Report")
        context["report_name"] = _(f"{friendly_name} Thinning Report")
        context["clear_url"] = (
            reverse_lazy("core:reports_thinning") + f"?thinning_type={thinning_type}"
        )
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class ThinningDetailView(SingleTableMixin, FilterView):
    model = Thinning
    table_class = FullThinningTable
    template_name = "core/base_report.html"
    filterset_class = FullThinningFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thinning_type = self.request.GET.get("thinning_type")
        pk = self.kwargs.get("pk")
        friendly_name = ThinningType(thinning_type).label
        context["page"] = _(f"{friendly_name} Thinning Report")
        context["report_name"] = _(f"{friendly_name} Thinning Report")
        context["clear_url"] = (
            reverse_lazy("core:reports_thinning_detail", kwargs={"pk": pk})
            + f"?thinning_type={thinning_type}"
        )
        context["breadcrumbs"] = [
            {
                "name": f"{friendly_name} Thinning Reports",
                "url": reverse_lazy("core:reports_thinning")
                + f"?thinning_type={thinning_type}",
            },
            {"name": _("Thinning Report"), "url": "#"},
        ]
        return context


class HarvestingReportBaseTable(tables.Table):
    no_tree_fall = tables.Column(
        verbose_name="No tree fall",
        footer=lambda table: sum(x.no_tree_fall for x in table.data),
    )
    amount = tables.Column(
        verbose_name="Amount", footer=lambda table: sum(x.amount for x in table.data)
    )

    class Meta:
        model = HarvestingReport
        template_name = "base-table.html"
        fields = [
            "createdBy",
            "batch",
            "item__species",
            "batch__source_site",
            "location",
            "polygon_name",
            "polygon_centroid_location",
            "no_tree_fall",
            "amount",
            "date",
        ]
        sequence = [
            "createdBy",
            "date",
            "batch",
            "item__species",
            "batch__source_site",
            "location",
            "polygon_name",
            "polygon_centroid_location",
            "no_tree_fall",
            "amount",
        ]
        template_name = "base-table.html"


class HarvestingBaseFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = HarvestingReport
        fields = ["date", "batch__source_site", "location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        harvestings = HarvestingReport.objects.values("id", "voucher_no").distinct()
        found_vouchers = []
        ids = []
        for receive in harvestings:
            if receive["voucher_no"] not in found_vouchers:
                found_vouchers.append(receive["voucher_no"])
                ids.append(receive["id"])
        return parent.filter(id__in=ids)


class HarvestingDetailFilter(FilterSet):
    species = django_filters.CharFilter(
        lookup_expr="icontains", field_name="item__species", label="Species"
    )

    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = HarvestingReport
        fields = ["date", "batch__source_site", "location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        harvest = get_object_or_404(HarvestingReport, pk=uuid)
        return parent.filter(voucher_no=harvest.voucher_no)


class HarvestingReportListTable(HarvestingReportBaseTable):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )
    amount = tables.Column(
        verbose_name="Amount", footer=lambda table: sum(x.amount for x in table.data)
    )

    class Meta:
        model = HarvestingReport
        template_name = "base-table.html"
        fields = [
            "voucher_no",
            "batch",
            "item__species",
            "batch__source_site",
            "location",
            "polygon_name",
            "polygon_centroid_location",
            "no_tree_fall",
            "amount",
            "date",
        ]
        sequence = [
            "voucher_no",
            "date",
            "batch",
            "item__species",
            "batch__source_site",
            "location",
            "polygon_name",
            "polygon_centroid_location",
            "no_tree_fall",
            "amount",
            "actions",
        ]
        template_name = "base-table.html"

    def render_actions(self, value):
        return render_to_string(
            "partials/base-actions-partial.html",
            {
                "url": reverse_lazy(
                    "core:reports_harvesting_detail", kwargs={"pk": value}
                )
            },
        )

    def render_amount(self, record):
        amounts = HarvestingReport.objects.filter(
            voucher_no=record.voucher_no
        ).values_list("amount", flat=True)
        return sum(amounts)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class HarvestingReportListView(ExportMixin, SingleTableMixin, FilterView):
    model = HarvestingReport
    table_class = HarvestingReportListTable
    template_name = "core/base_report.html"
    filterset_class = HarvestingBaseFilter
    export_name = "Harvesting Report"
    dataset_kwargs = {"title": "Harvesting Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Harvesting Report")
        context["report_name"] = _("Harvesting Reports")
        context["clear_url"] = reverse_lazy("core:reports_harvesting")
        return context


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class HarvestingReportDetailView(SingleTableMixin, FilterView):
    model = HarvestingReport
    table_class = HarvestingReportBaseTable
    template_name = "core/base_report.html"
    filterset_class = HarvestingDetailFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        context["page"] = _("Harvesting Report")
        context["report_name"] = _("Harvesting Report")
        context["clear_url"] = reverse_lazy(
            "core:reports_harvesting_detail", kwargs={"pk": pk}
        )
        context["breadcrumbs"] = [
            {
                "name": _("Harvesting Reports"),
                "url": reverse_lazy("core:reports_harvesting"),
            },
            {"name": _("Harvesting Report"), "url": "#"},
        ]
        return context


class TimelyHarvestingReportBaseTable(tables.Table):
    productive_area = tables.Column(
        footer=lambda table: sum(x.productive_area for x in table.data)
    )

    class Meta:
        model = TimelyHarvestingReport
        template_name = "base-table.html"
        fields = [
            "createdBy",
            "voucher_no",
            "batch",
            "start_date",
            "end_date",
            "performance_in m3_",
            "performance_in_hectare",
            "item__species",
            "batch__source_site",
            "location",
            "sold_to",
            "polygon_name",
            "polygon_centroid_location",
        ]
        template_name = "base-table.html"


class TimelyHarvestingBaseFilter(FilterSet):
    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = TimelyHarvestingReport
        fields = ["sold_to", "location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        harvestings = TimelyHarvestingReport.objects.values(
            "id", "voucher_no"
        ).distinct()
        found_vouchers = []
        ids = []
        for receive in harvestings:
            if receive["voucher_no"] not in found_vouchers:
                found_vouchers.append(receive["voucher_no"])
                ids.append(receive["id"])
        return parent.filter(id__in=ids)


class TimelyHarvestingDetailFilter(FilterSet):
    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = TimelyHarvestingReport
        fields = ["sold_to", "location"]
        form = FilterForm

    @property
    def qs(self):
        parent = super().qs
        uuid = self.request.resolver_match.kwargs.get("pk")
        harvest = get_object_or_404(TimelyHarvestingReport, pk=uuid)
        return parent.filter(voucher_no=harvest.voucher_no)


class TimelyHarvestingReportListTable(TimelyHarvestingReportBaseTable):
    actions = tables.Column(
        accessor="id", verbose_name="Actions", orderable=False, exclude_from_export=True
    )

    class Meta(TimelyHarvestingReportBaseTable.Meta):
        fields = ["date", "productive_area", "location"]

    def render_actions(self, value):
        return render_to_string(
            "partials/base-actions-partial.html",
            {
                "url": reverse_lazy(
                    "core:reports_timely_harvesting_detail", kwargs={"pk": value}
                )
            },
        )


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class TimelyHarvestingListView(ExportMixin, SingleTableMixin, FilterView):
    model = TimelyHarvestingReport
    table_class = TimelyHarvestingReportListTable
    template_name = "core/base_report.html"
    filterset_class = TimelyHarvestingBaseFilter
    export_name = "Timley Harvesting Report"
    dataset_kwargs = {"title": "Timley Harvesting Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Timely Harvesting Report")
        context["report_name"] = _("Timely Harvesting Reports")
        context["clear_url"] = reverse_lazy("core:reports_timely_harvesting")
        return context


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class TimelyHarvestingDetailView(SingleTableMixin, FilterView):
    model = TimelyHarvestingReport
    table_class = TimelyHarvestingReportBaseTable
    template_name = "core/base_report.html"
    filterset_class = TimelyHarvestingDetailFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        context["page"] = _("Timely Harvesting Report")
        context["report_name"] = _("Timely Harvesting Report")
        context["clear_url"] = reverse_lazy(
            "core:reports_timely_harvesting_detail", kwargs={"pk": pk}
        )
        context["breadcrumbs"] = [
            {
                "name": _("Timely Harvesting Reports"),
                "url": reverse_lazy("core:reports_timely_harvesting"),
            },
            {"name": _("Timely Harvesting Report"), "url": "#"},
        ]
        return context


class DownTimeTable(tables.Table):
    class Meta:
        model = DownTime
        fields = ["date", "createdBy", "reason", "location"]
        template_name = "base-table.html"


class DownTimeFilter(FilterSet):
    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = DownTime
        fields = ["location"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
@method_decorator(login_required, name="dispatch")
class DownTimeListView(ExportMixin, SingleTableMixin, FilterView):
    model = DownTime
    table_class = DownTimeTable
    template_name = "core/base_report.html"
    filterset_class = DownTimeFilter
    export_name = "Downtime Report"
    dataset_kwargs = {"title": "Downtime Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Downtime Report")
        context["report_name"] = _("Downtime Report")
        context["clear_url"] = reverse_lazy("core:reports_downtime")
        return context


class OperationalForestInventoryTable(tables.Table):
    forest_volume_stand_level = tables.Column(
        footer=lambda table: sum(x.forest_volume_stand_level for x in table.data)
    )
    forest_volume_production = tables.Column(
        footer=lambda table: sum(x.forest_volume_production for x in table.data)
    )

    class Meta:
        model = OperationalForestInventory
        template_name = "base-table.html"
        fields = [
            "createdBy",
            "location",
            "batch",
            "item__species",
            "batch__source_site",
            "date",
            "hectare",
            "total_volume",
            "polygon_name",
            "polygon_centroid_location",
            "forest_volume_stand_level",
            "forest_volume_production",
        ]


class OperationalForestInventoryFilter(FilterSet):
    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = OperationalForestInventory
        fields = ["location", "batch__item__species"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class OperationalForestInventoryListView(ExportMixin, SingleTableMixin, FilterView):
    model = OperationalForestInventory
    table_class = OperationalForestInventoryTable
    template_name = "core/base_report.html"
    filterset_class = OperationalForestInventoryFilter
    export_name = "Operational Forest Inventory Report"
    dataset_kwargs = {"title": "Operational Forest Inventory Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Operational Forest Inventory")
        context["report_name"] = _("Operational Forest Inventory")
        context["clear_url"] = reverse_lazy("core:reports_op_forest_inventory")
        return context


class LumberStoredTable(tables.Table):
    amount = tables.Column(footer=lambda table: sum(x.amount for x in table.data))

    class Meta:
        model = LumberStoredReport
        fields = [
            "location",
            "date",
            "createdBy",
            "product_category",
            "batch__batch_number",
            "amount",
        ]
        template_name = "base-table.html"


class LumberStoredFilter(FilterSet):
    class Meta:
        model = LumberStoredReport
        fields = ["date", "location", "createdBy"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class LumberStoredReportView(ExportMixin, SingleTableMixin, FilterView):
    model = LumberStoredReport
    table_class = LumberStoredTable
    template_name = "core/base_report.html"
    filterset_class = LumberStoredFilter
    export_name = "Lumber Stored Report"
    dataset_kwargs = {"title": "Lumber Stored Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Lumber Stored Report")
        context["report_name"] = _("Lumber Stored Report")
        context["clear_url"] = reverse_lazy("core:reports_lumber_stored")
        return context


class FactoryProductionTable(tables.Table):
    amount = tables.Column(footer=lambda table: sum(x.amount for x in table.data))

    class Meta:
        model = FactoryProductionReport
        fields = ["location", "date", "createdBy", "product_category", "amount"]
        template_name = "base-table.html"


class FactoryProductionFilter(FilterSet):
    class Meta:
        model = FactoryProductionReport
        fields = ["date", "location", "createdBy"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class FactoryProductionView(ExportMixin, SingleTableMixin, FilterView):
    model = FactoryProductionReport
    table_class = FactoryProductionTable
    template_name = "core/base_report.html"
    filterset_class = FactoryProductionFilter
    export_name = "Factory Production Report"
    dataset_kwargs = {"title": "Factory Production Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Factory Production Report")
        context["report_name"] = _("Factory Production Report")
        context["clear_url"] = reverse_lazy("core:reports_factory_production")
        return context
class PlantationSiteSelectionTable(tables.Table):
    suitability_score = tables.Column(footer=lambda table: f"Avg: {sum(x.suitability_score for x in table.data) // len(table.data) if table.data else 0}")
    total_area = tables.Column(footer=lambda table: f"Total: {sum(x.total_area for x in table.data):.2f} ha" if table.data else "Total: 0 ha")

    class Meta:
        model = PlantationSiteSelectionReport
        fields = ["site_code", "site_name", "location", "total_area", "soil_type", "soil_ph", "drainage_rating", "avg_temperature", "annual_rainfall", "suitability_score"]
        template_name = "base-table.html"
    
class PlantationSiteSelectionFilter(FilterSet):
    class Meta:
        model = PlantationSiteSelectionReport
        fields = ["soil_type",
                  "is_available", 
                  "location"]
        form = FilterForm
@method_decorator(
 role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class PlantationSiteSelectionView(ExportMixin, SingleTableMixin, FilterView):
    model = PlantationSiteSelectionReport
    table_class = PlantationSiteSelectionTable
    template_name = "core/base_report.html"
    filterset_class = PlantationSiteSelectionFilter
    export_name = "Plantation Site Selection Report"
    dataset_kwargs = {"title": "Plantation Site Selection Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Plantation Site Selection")
        context["report_name"] = _("Plantation Site Selection Report")
        context["clear_url"] = reverse_lazy( "core:reports_plantation_site_selection"
)
        return context
    
class PlantedSeedlingTable(tables.Table):

    planted_quantity = tables.Column(
        footer=lambda table:
        f"Total: {sum(x.planted_quantity for x in table.data)}"
        if table.data else "0"
    )

    survived_quantity = tables.Column(
        footer=lambda table:
        f"Total: {sum(x.survived_quantity for x in table.data)}"
        if table.data else "0"
    )

    class Meta:
        model = PlantedSeedlingReport
        fields = [
            "plantation_site",
            "seedling_type",
            "planted_quantity",
            "survived_quantity",
            "planting_date",
        ]
        template_name = "base-table.html"


class PlantedSeedlingFilter(FilterSet):

    class Meta:
        model = PlantedSeedlingReport
        fields = [
            "plantation_site",
            "seedling_type",
            "planting_date",
        ]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class PlantedSeedlingView(ExportMixin, SingleTableMixin, FilterView):

    model = PlantedSeedlingReport
    table_class = PlantedSeedlingTable
    template_name = "core/base_report.html"
    filterset_class = PlantedSeedlingFilter
    export_name = "Planted Seedling Report"
    dataset_kwargs = {"title": "Planted Seedling Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page"] = _("Planted Seedling Report")
        context["report_name"] = _("Planted Seedling Report")
        context["clear_url"] = reverse_lazy(
            "core:reports_planted_seedling"
        )

        return context
    
class GiveAwayTable(tables.Table):
    total_price = tables.Column(
        footer=lambda table: sum(x.total_price for x in table.data)
    )
    amount = tables.Column(footer=lambda table: sum(x.amount for x in table.data))

    class Meta:
        model = ProductGiveAway
        fields = [
            "location",
            "date",
            "createdBy",
            "batch",
            "unit",
            "sender",
            "receiver",
            "batch__item__species",
            "batch__source_site",
            "product_category",
            "unit_price",
            "total_price",
            "amount",
        ]
        template_name = "base-table.html"


class GiveAwayFilter(FilterSet):
    class Meta:
        model = ProductGiveAway
        fields = ["date", "batch__item__species", "batch__source_site"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class GiveAwayReportView(ExportMixin, SingleTableMixin, FilterView):
    model = ProductGiveAway
    table_class = GiveAwayTable
    template_name = "core/base_report.html"
    filterset_class = GiveAwayFilter
    export_name = "Product Giveaway Report"
    dataset_kwargs = {"title": "Product Giveaway Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Product Giveaway Report")
        context["report_name"] = _("Product Giveaway Report")
        context["clear_url"] = reverse_lazy("core:reports_product_giveaway")
        return context


class JobOpportunityTable(tables.Table):
    old_male_count = tables.Column(
        footer=lambda table: sum(x.old_male_count for x in table.data)
    )
    old_female_count = tables.Column(
        footer=lambda table: sum(x.old_female_count for x in table.data)
    )
    new_male_count = tables.Column(
        footer=lambda table: sum(x.new_male_count for x in table.data)
    )
    new_female_count = tables.Column(
        footer=lambda table: sum(x.new_female_count for x in table.data)
    )
    
    # New columns for totals
    total_male_count = tables.Column(
        verbose_name="Total Male",
        footer=lambda table: sum(x.old_male_count + x.new_male_count for x in table.data)
    )
    total_female_count = tables.Column(
        verbose_name="Total Female",
        footer=lambda table: sum(x.old_female_count + x.new_female_count for x in table.data)
    )
    total_all_beneficiaries = tables.Column(
        verbose_name="Total Beneficiaries",
        footer=lambda table: sum(
            x.old_male_count + x.old_female_count + x.new_male_count + x.new_female_count 
            for x in table.data
        )
    )
    
    no_groups_old = tables.Column(
        footer=lambda table: sum(x.no_groups_old for x in table.data)
    )
    no_groups_new = tables.Column(
        footer=lambda table: sum(x.no_groups_new for x in table.data)
    )
    no_total_old_new = tables.Column(
        accessor="id",
        verbose_name="Total Old and New Groups",
        footer=lambda table: sum(x.no_groups_old for x in table.data)
        + sum(x.no_groups_new for x in table.data),
    )

    class Meta:
        model = JobOportunity
        fields = [
            "location",
            "date",
            "no_groups_old",
            "no_groups_new",
            "no_total_old_new",
            "old_male_count",
            "old_female_count",
            "new_male_count",
            "new_female_count",
            
        ]
        template_name = "base-table.html"

    def render_no_total_old_new(self, record):
        return record.no_groups_old + record.no_groups_new
    
    def render_total_male_count(self, record):
        """Calculate total male (old + new) for each row"""
        return record.old_male_count + record.new_male_count
    
    def render_total_female_count(self, record):
        """Calculate total female (old + new) for each row"""
        return record.old_female_count + record.new_female_count
    
    def render_total_all_beneficiaries(self, record):
        """Calculate total beneficiaries (all male + all female) for each row"""
        return (record.old_male_count + record.old_female_count + 
                record.new_male_count + record.new_female_count)


class JobOportunityFilter(FilterSet):
    branch = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(type="BRANCH").all(),
        label="Branch",
        method="branch_filter",
    )

    class Meta:
        model = JobOportunity
        fields = ["date", "location", "location__type"]
        form = FilterForm

    def branch_filter(self, queryset, name, value):
        children = value.get_all_children()
        children_ids = [child.id for child in children]
        return queryset.filter(location_id__in=children_ids)


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class JobOportunityReportView(ExportMixin, SingleTableMixin, FilterView):
    model = JobOportunity
    table_class = JobOpportunityTable
    template_name = "core/base_report.html"
    filterset_class = JobOportunityFilter
    export_name = "Job Creation Report"
    dataset_kwargs = {"title": "Job Creation Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Job Creation Report")
        context["report_name"] = _("Job Creation Report")
        context["clear_url"] = reverse_lazy("core:reports_job_creation")
        return context

class ForestInventoryTable(tables.Table):
    amount = tables.Column(footer=lambda table: sum(x.amount for x in table.data))
    total_volume = tables.Column(
        footer=lambda table: sum(x.total_volume for x in table.data)
    )
    total_sample = tables.Column(
        footer=lambda table: sum(x.total_sample for x in table.data)
    )
    basal_area = tables.Column(
        footer=lambda table: sum(x.basal_area for x in table.data)
    )

    class Meta:
        model = ForestInventoryReport
        fields = [
            "location",
            "date",
            "batch",
            "batch__item__species",
            "amount",
            "total_volume",
            "total_sample",
            "basal_area",
        ]
        template_name = "base-table.html"


class ForestInventoryFilter(FilterSet):
    date__gt = django_filters.DateFilter(
        field_name="date", lookup_expr="gte", label="From Date"
    )
    date__lt = django_filters.DateFilter(
        field_name="date", lookup_expr="lte", label="To Date"
    )

    class Meta:
        model = ForestInventoryReport
        fields = ["location", "batch"]
        form = FilterForm


@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR",
            "DATA_ANALYST",
            "MAIN_OFFICE_USER",
            "BRANCH_DATA_ADMINISTRATOR",
            "BRANCH_DATA_ANALYST",
        ]
    ),
    name="dispatch",
)
class ForestInventoryReportView(ExportMixin, SingleTableMixin, FilterView):
    model = ForestInventoryReport
    table_class = ForestInventoryTable
    template_name = "core/base_report.html"
    filterset_class = ForestInventoryFilter
    export_name = "Forest Inventory Report"
    dataset_kwargs = {"title": "Forest Inventory Report"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Forest Inventory Report")
        context["report_name"] = _("Forest Inventory Report")
        context["clear_url"] = reverse_lazy("core:reports_forest_inventory")
        return context


def get_year_month_day_dict(start, end):
    year_month_day_dict = {}
    date_generated = [
        start + timedelta(days=x) for x in range(0, (end - start).days + 1)
    ]

    for date in date_generated:
        year = date.strftime("%Y")
        month = date.strftime("%B")
        if year not in year_month_day_dict:
            year_month_day_dict[year] = {}
        if month not in year_month_day_dict[year]:
            year_month_day_dict[year][month] = 0
        year_month_day_dict[year][month] += 1

    return year_month_day_dict


def distribute_value(start_date, end_date, value):
    year_month_day_dict = get_year_month_day_dict(start_date, end_date)
    total_days = sum([sum(months.values()) for months in year_month_day_dict.values()])
    for year, months in year_month_day_dict.items():
        for month, days in months.items():
            year_month_day_dict[year][month] = (days / total_days) * value
    return year_month_day_dict


@login_required
@role_required(
    [
        "SYSTEM_ADMINISTRATOR",
        "DATA_ADMINISTRATOR",
        "DATA_ANALYST",
        "BRANCH_DATA_ANALYST",
        "BRANCH_DATA_ADMINISTRATOR",
        "MAIN_OFFICE_USER",
        "BRANCH_DATA_ADMINISTRATOR",
        "BRANCH_DATA_ANALYST",
    ]
)
def annual_plan_report(request: HttpRequest):
    current_year = request.GET.get("year", datetime.today().year)

    detail_activity_types = DetailActivityType.objects.exclude(
        annual_resource_type=None
    )
    report_data = {}

    for detail_type in detail_activity_types:
        report_data[detail_type] = {
            "months": {
                "January": {"planned": 0, "value": 0},
                "February": {"planned": 0, "value": 0},
                "March": {"planned": 0, "value": 0},
                "April": {"planned": 0, "value": 0},
                "May": {"planned": 0, "value": 0},
                "June": {"planned": 0, "value": 0},
                "July": {"planned": 0, "value": 0},
                "August": {"planned": 0, "value": 0},
                "September": {"planned": 0, "value": 0},
                "October": {"planned": 0, "value": 0},
                "November": {"planned": 0, "value": 0},
                "December": {"planned": 0, "value": 0},
            }
        }
        detail_activites = DetailActivity.objects.filter(detail_type=detail_type)

        annual_sum = 0
        for task in detail_activites:
            planned_sum_distributed = distribute_value(
                task.start_date, task.end_date, task.planned_sum
            )
            annual_sum_distributed = {current_year: {}}

            actual_activity_resources = ActualActivityResource.objects.filter(
                activity_resource__detail_activity=task, createdDate__year=current_year
            )
            for actual_activity_resource in actual_activity_resources:
                actual_month = actual_activity_resource.createdDate.strftime("%B")
                if not annual_sum_distributed[current_year].get(actual_month, None):
                    annual_sum_distributed[current_year][actual_month] = 0

                annual_sum_distributed[current_year][actual_month] += (
                    actual_activity_resource.achievement
                )

            annual_sum += round(
                sum(
                    [
                        value
                        for month, value in planned_sum_distributed.get(
                            current_year, {}
                        ).items()
                    ]
                ),
                2,
            )

            for month, value in annual_sum_distributed.get(current_year, {}).items():
                report_data[detail_type]["months"][month]["value"] = round(
                    report_data[detail_type]["months"][month]["value"] + value, 2
                )

            for month, value in planned_sum_distributed.get(current_year, {}).items():
                report_data[detail_type]["months"][month]["planned"] = round(
                    report_data[detail_type]["months"][month]["planned"]
                    + planned_sum_distributed[current_year][month],
                    2,
                )

        report_data[detail_type]["annual_sum"] = annual_sum
    return render(
        request,
        "core/annual_plan_list.html",
        {
            "selected_year": current_year,
            "years": [
                str(x)
                for x in range(datetime.today().year - 5, datetime.today().year + 5)
            ],
            "report_data": report_data,
            "current_year": current_year,
            "months": [
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
            ],
            "page": "Annual Plan Report",
        },
    )


@login_required
@role_required(
    [
        "SYSTEM_ADMINISTRATOR",
        "DATA_ADMINISTRATOR",
        "DATA_ANALYST",
        "BRANCH_DATA_ANALYST",
        "BRANCH_DATA_ADMINISTRATOR",
        "MAIN_OFFICE_USER",
        "BRANCH_DATA_ADMINISTRATOR",
        "BRANCH_DATA_ANALYST",
    ]
)
def performance_report(request):
    current_year = str(datetime.today().year)
    sector = request.GET.get("sector", None)
    operation = request.GET.get("operation", None)
    location = request.GET.get("location", None)
    report_type = request.GET.get("report_type", None)
    detail_activity_type = request.GET.get("detail_activity_type", None)

    detail_activity_types_all = DetailActivityType.objects.exclude(
        annual_resource_type=None
    )

    detail_activity_types = detail_activity_types_all
    if detail_activity_type:
        detail_activity_types = detail_activity_types_all.filter(
            id=detail_activity_type
        )

    report_data = {
        "months": {
            "January": {"planned": 0, "value": 0},
            "February": {"planned": 0, "value": 0},
            "March": {"planned": 0, "value": 0},
            "April": {"planned": 0, "value": 0},
            "May": {"planned": 0, "value": 0},
            "June": {"planned": 0, "value": 0},
            "July": {"planned": 0, "value": 0},
            "August": {"planned": 0, "value": 0},
            "September": {"planned": 0, "value": 0},
            "October": {"planned": 0, "value": 0},
            "November": {"planned": 0, "value": 0},
            "December": {"planned": 0, "value": 0},
        }
    }

    for detail_type in detail_activity_types:
        detail_activites = DetailActivity.objects.filter(detail_type=detail_type)
        if sector:
            detail_activites = detail_activites.filter(
                activity_plan__operation_plan__sector__id=sector
            )

        if operation:
            detail_activites = detail_activites.filter(
                activity_plan__operation_plan__operation_type__id=operation
            )

        if location:
            detail_activites = detail_activites.filter(
                activity_plan__operation_plan__location__id=location
            )

        annual_sum = 0
        for task in detail_activites:
            planned_sum_distributed = distribute_value(
                task.start_date, task.end_date, task.planned_sum
            )
            annual_sum_distributed = {current_year: {}}

            actual_activity_resources = ActualActivityResource.objects.filter(
                activity_resource__detail_activity=task, createdDate__year=current_year
            )
            for actual_activity_resource in actual_activity_resources:
                actual_month = actual_activity_resource.createdDate.strftime("%B")
                if not annual_sum_distributed[current_year].get(actual_month, None):
                    annual_sum_distributed[current_year][actual_month] = 0

                annual_sum_distributed[current_year][actual_month] += (
                    actual_activity_resource.achievement
                )

            annual_sum += round(
                sum(
                    [
                        value
                        for month, value in planned_sum_distributed.get(
                            current_year, {}
                        ).items()
                    ]
                ),
                2,
            )

            for month, value in annual_sum_distributed.get(current_year, {}).items():
                report_data["months"][month]["value"] = round(
                    report_data["months"][month]["value"] + value, 2
                )

            for month, value in planned_sum_distributed.get(current_year, {}).items():
                report_data["months"][month]["planned"] = round(
                    report_data["months"][month]["planned"]
                    + planned_sum_distributed[current_year][month],
                    2,
                )

        report_data["annual_sum"] = annual_sum

    if report_type == "quarterly":
        report_data["months"] = {
            "Quarter 1": {
                "planned": report_data["months"]["January"]["planned"]
                + report_data["months"]["February"]["planned"]
                + report_data["months"]["March"]["planned"],
                "value": report_data["months"]["January"]["value"]
                + report_data["months"]["February"]["value"]
                + report_data["months"]["March"]["value"],
            },
            "Quarter 2": {
                "planned": report_data["months"]["April"]["planned"]
                + report_data["months"]["May"]["planned"]
                + report_data["months"]["June"]["planned"],
                "value": report_data["months"]["April"]["value"]
                + report_data["months"]["May"]["value"]
                + report_data["months"]["June"]["value"],
            },
            "Quarter 3": {
                "planned": report_data["months"]["July"]["planned"]
                + report_data["months"]["August"]["planned"]
                + report_data["months"]["September"]["planned"],
                "value": report_data["months"]["July"]["value"]
                + report_data["months"]["August"]["value"]
                + report_data["months"]["September"]["value"],
            },
            "Quarter 4": {
                "planned": report_data["months"]["October"]["planned"]
                + report_data["months"]["November"]["planned"]
                + report_data["months"]["December"]["planned"],
                "value": report_data["months"]["October"]["value"]
                + report_data["months"]["November"]["value"]
                + report_data["months"]["December"]["value"],
            },
        }
    elif report_type == "yearly":
        report_data["months"] = {
            str(current_year): {
                "planned": sum(
                    [item["planned"] for key, item in report_data["months"].items()]
                ),
                "value": sum(
                    [item["value"] for key, item in report_data["months"].items()]
                ),
            }
        }

    return render(
        request,
        "core/performance_report.html",
        {
            "report_data": report_data,
            "current_year": current_year,
            "page": "Performance Report",
            "detail_types": detail_activity_types_all,
            "sectors": Sector.objects.all(),
            "operations": OperationType.objects.all(),
            "locations": Location.objects.all(),
            "sector": sector,
            "operation": operation,
            "location": location,
            "report_type": report_type,
            "detail_activity_type": detail_activity_type,
        },
    )
