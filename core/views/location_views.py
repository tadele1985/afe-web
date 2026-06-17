from urllib.parse import urlencode
from django.urls import reverse_lazy
import django_filters
import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django_filters import FilterSet
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from render_block import render_block_to_string

from core.forms import FilterForm, LocationForm
from core.models import Batch, Item, ItemInventory, ItemType, Location, Test, TestType
from core.views.item_views import ItemInventoryTable
from django.utils.translation import gettext as _


class LocationTable(tables.Table):
    forest_sites = tables.Column(
        accessor="children__count", verbose_name="Number of sub locations"
    )
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = Location
        fields = ("name", "type", "date_created", "forest_sites")
        attrs = {"class": "table"}
        template_name = "base-table.html"

    def render_actions(self, value):
        return render_to_string("partials/location-table-actions.html", {"id": value})


class LocationFilter(FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains", field_name="name", label="Name"
    )

    class Meta:
        model = Location
        fields = {
            "type": ["exact"],
        }
        form = FilterForm


@method_decorator(login_required, name="dispatch")
class LocationListView(SingleTableMixin, FilterView):
    model = Location
    table_class = LocationTable
    template_name = "core/location_list.html"
    filterset_class = LocationFilter
    filterset_fields = ("type",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Locations")
        context["tab"] = _("Locations")
        context["form"] = LocationForm()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            content_html = render_block_to_string(
                self.template_name, "content", context, self.request
            )
            return HttpResponse(content_html, content_type="text/html")
        return super().render_to_response(context, **response_kwargs)


class LocationInventoryFilter(FilterSet):
    item = tables.Column(accessor="item__title", verbose_name="Item")

    class Meta:
        model = ItemInventory
        fields = ["item", "source_site"]
        form = FilterForm

    @property
    def qs(self):
        uuid = self.request.resolver_match.kwargs.get("pk")
        return super().qs.filter(location_id=uuid)


class LocationItemInventoryTable(ItemInventoryTable):
    class Meta(ItemInventoryTable.Meta):
        fields = ["source_site", "species", "amount", "updated_at", "batch"]
        sequence = [
            "batch",
            "species",
            "source_site",
            "amount",
            "updated_at",
        ]


class HQItemInventoryTable(tables.Table):
    seed_batches = tables.Column(
        accessor="id",
        verbose_name="Total no of batches of seed in store",
        footer=lambda table: table.get_html(
            {"untested": True}, table.get_total_seed_batches()
        ),
    )
    round_1_batches = tables.Column(
        accessor="id",
        verbose_name="Initial (Round 1) tested batches",
        footer=lambda table: table.get_html({"round": 1}, table.round1_batches.count()),
    )
    round_2_batches = tables.Column(
        accessor="id",
        verbose_name="Initial (Round 2) tested batches",
        footer=lambda table: table.get_html({"round": 2}, table.round2_batches.count()),
    )
    round_3_batches = tables.Column(
        accessor="id",
        verbose_name="Initial (Round 3) tested batches",
        footer=lambda table: table.get_html({"round": 3}, table.round3_batches.count()),
    )
    quarantine_batches = tables.Column(
        accessor="id",
        verbose_name="Quarantine Tested Batches",
        footer=lambda table: table.get_html(
            {"test_type": "Quarantine"}, table.get_quarantine_batches()
        ),
    )
    total = tables.Column(
        accessor="id", verbose_name="Total", footer=lambda table: table.batches.count()
    )
    species = tables.Column(accessor="species", verbose_name="Species", footer="Total")

    class Meta:
        model = Item
        template_name = "base-table.html"
        fields = [
            "species",
            "seed_batches",
            "round_1_batches",
            "round_2_batches",
            "round_3_batches",
            "quarantine_batches",
            "total",
        ]
        pinned_row_attrs = {"class": "bg-base-200"}

    def __init__(self, *args, **kwargs):
        self.location: Location = kwargs.pop("location")
        inventory_batch_ids = ItemInventory.objects.filter(
            location=self.location
        ).values_list("batch_id", flat=True)
        self.batches = Batch.objects.filter(id__in=inventory_batch_ids)
        self.tests = Test.objects.filter(location=self.location)
        round1_batches = self.tests.filter(round=1, type="TEST").values_list(
            "batch_id", flat=True
        )
        round2_batches = self.tests.filter(round=2, type="TEST").values_list(
            "batch_id", flat=True
        )
        round3_batches = self.tests.filter(round=3, type="TEST").values_list(
            "batch_id", flat=True
        )
        self.round1_batches = self.batches.filter(
            id__in=round1_batches.exclude(batch_id__in=round2_batches).exclude(
                batch_id__in=round3_batches
            )
        )
        self.round2_batches = self.batches.filter(
            id__in=round2_batches.exclude(batch_id__in=round3_batches)
        )
        self.round3_batches = self.batches.filter(id__in=round3_batches)
        super().__init__(*args, **kwargs)

    def get_total_seed_batches(self):
        tested_batches = self.tests.values_list("batch_id", flat=True)
        return self.batches.exclude(id__in=tested_batches).count()

    def get_round_1_batches(self):
        tested_batches = self.tests.filter(round=1, type="TEST").values_list(
            "batch_id", flat=True
        )
        return self.batches.filter(id__in=tested_batches).count()

    def get_round_2_batches(self):
        tested_batches = self.tests.filter(round=2, type="TEST").values_list(
            "batch_id", flat=True
        )
        return self.batches.filter(id__in=tested_batches).count()

    def get_round_3_batches(self):
        tested_batches = self.tests.filter(round=3, type="TEST").values_list(
            "batch_id", flat=True
        )
        return self.batches.filter(id__in=tested_batches).count()

    def get_quarantine_batches(self):
        tested_batches = self.tests.filter(type=TestType.QUARANTINE).values_list(
            "batch_id", flat=True
        )
        return self.batches.filter(id__in=tested_batches).count()

    def render_seed_batches(self, record):
        tested_batches = self.tests.values_list("batch_id", flat=True)
        count = self.batches.filter(item=record).exclude(id__in=tested_batches).count()
        filters = {
            "location": self.location.id,
            "species": record.species,
            "untested": True,
        }
        return self.get_html(filters, count)

    def get_html(self, filters: dict, count: int):
        filters["location"] = self.location.id
        link = f"{reverse_lazy('core:hq_batch_info')}?{urlencode(filters)}"
        return render_to_string(
            "partials/hq-inventory-table-partial.html",
            {"link": link, "text": round(count, 2)},
        )

    def render_round_1_batches(self, record):
        count = self.round1_batches.filter(item=record).count()
        filters = {
            "round": "1",
            "species": record.species,
            "test_type": "TEST",
        }
        return self.get_html(filters, count)

    def render_round_2_batches(self, record):
        count = self.round2_batches.filter(item=record).count()
        filters = {
            "round": "2",
            "species": record.species,
            "test_type": "TEST",
        }
        return self.get_html(filters, count)

    def render_round_3_batches(self, record):
        count = self.round3_batches.filter(item=record).count()
        filters = {
            "round": "3",
            "species": record.species,
            "test_type": "TEST",
        }
        return self.get_html(filters, count)

    def render_quarantine_batches(self, record):
        tested_batches = self.tests.filter(type=TestType.QUARANTINE).values_list(
            "batch_id", flat=True
        )
        count = self.batches.filter(item=record, id__in=tested_batches).count()
        filters = {
            "species": record.species,
            "test_type": "Quarantine",
        }
        return self.get_html(filters, count)

    def render_total(self, record):
        filters = {"species": record.species}
        count = self.batches.filter(item=record).count()
        return self.get_html(filters, count)


class NurseryItemInventoryTable(tables.Table):
    species = tables.Column(accessor="species", verbose_name="Species", footer="Total")
    viable_seed = tables.Column(
        accessor="id",
        verbose_name="Viable Seed",
        footer=lambda table: table.get_html(
            {"item_type": "SEED"}, table.total_viable_seed
        ),
    )
    sowed_seed = tables.Column(
        accessor="id",
        verbose_name="Sowed Seed",
        footer=lambda table: table.get_html(
            {"item_type": "SOWED_SEED"}, table.total_sowed_seed
        ),
    )
    germinated_seed = tables.Column(
        accessor="id",
        verbose_name="Germinated Seed",
        footer=lambda table: table.get_html(
            {"item_type": "GERMINATED_SEED"}, table.total_germinated_seed
        ),
    )
    grade1_seed = tables.Column(
        accessor="id",
        verbose_name="Grade 1 Seed",
        footer=lambda table: table.get_html(
            {"item_type": "SEEDLING"}, table.total_grade1_seed
        ),
    )

    total = tables.Column(
        accessor="id",
        verbose_name="Total",
        footer=lambda table: table.total_viable_seed
        + table.total_sowed_seed
        + table.total_germinated_seed
        + table.total_grade1_seed,
    )

    actions = tables.Column(accessor="species", verbose_name="Actions", orderable=False)

    class Meta:
        model = Item
        fields = [
            "species",
            "viable_seed",
            "sowed_seed",
            "germinated_seed",
        ]
        template_name = "base-table.html"

    def __init__(self, *args, **kwargs):
        self.location: Location = kwargs.pop("location")
        super().__init__(*args, **kwargs)
        self.total_viable_seed = 0
        self.total_sowed_seed = 0
        self.total_germinated_seed = 0
        self.total_grade1_seed = 0

    def get_html(self, filters: dict, count: int):
        filters["location"] = self.location.id
        if "item_type" in filters:
            filters["item__item_type"] = filters["item_type"]
            del filters["item_type"]
        link = f"{reverse_lazy('core:item_inventory')}?{urlencode(filters)}"
        return render_to_string(
            "partials/hq-inventory-table-partial.html",
            {"link": link, "text": round(count, 2)},
        )

    def render_viable_seed(self, record):
        item = ItemInventory.objects.filter(
            location=self.location,
            item__item_type=ItemType.SEED,
            item__species=record.species,
        ).values_list("amount", flat=True)
        count = sum(item)
        self.total_viable_seed += count
        filters = {"item_type": "SEED", "species": record.species}
        return self.get_html(filters, count)

    def render_sowed_seed(self, record):
        item = ItemInventory.objects.filter(
            location=self.location,
            item__item_type=ItemType.SOWED_SEED,
            item__species=record.species,
        ).values_list("amount", flat=True)
        count = sum(item)
        filters = {"item_type": "SOWED_SEED", "species": record.species}
        self.total_sowed_seed += count
        return self.get_html(filters, count)

    def render_germinated_seed(self, record):
        item = ItemInventory.objects.filter(
            location=self.location,
            item__item_type=ItemType.GERMINATED_SEED,
            item__species=record.species,
        ).values_list("amount", flat=True)
        count = sum(item)
        filters = {"item_type": "GERMINATED_SEED", "species": record.species}
        self.total_germinated_seed += count
        return self.get_html(filters, count)

    def render_grade1_seed(self, record):
        item = ItemInventory.objects.filter(
            location=self.location,
            item__item_type=ItemType.SEEDLING,
            item__species=record.species,
        ).values_list("amount", flat=True)
        count = sum(item)
        self.total_grade1_seed += count
        filters = {"item_type": "SEEDLING", "species": record.species}
        return self.get_html(filters, count)

    def render_total(self, record):
        item = ItemInventory.objects.filter(
            location=self.location, item__species=record.species
        ).values_list("amount", flat=True)
        filters = {"species": record.species}
        return self.get_html(filters, sum(item))

    def render_actions(self, value):
        link = reverse_lazy("core:item_inventory")
        query_params = {"location": self.location.id, "species": value}
        encoded_params = urlencode(query_params)
        final_url = f"{link}?{encoded_params}"
        return render_to_string(
            "partials/base-actions-partial.html", {"url": final_url}
        )


@method_decorator(login_required, name="dispatch")
class LocationDetailView(tables.SingleTableView):
    table_class = LocationItemInventoryTable
    template_name = "core/location_detail.html"
    model = ItemInventory

    def get_table(self, **kwargs):
        pk = self.kwargs.get("pk")
        location = Location.objects.get(pk=pk)
        item_ids = ItemInventory.objects.filter(location=location).values_list(
            "item_id", flat=True
        )
        if location.type == "HQ":
            return HQItemInventoryTable(
                Item.objects.filter(id__in=item_ids), location=location
            )
        elif location.type == "NURSERY":
            return NurseryItemInventoryTable(
                Item.objects.filter(id__in=item_ids).distinct("species"),
                location=location,
            )

        return super().get_table(**kwargs)

    def get_table_data(self):
        data = super().get_table_data()
        data = data.filter(location_id=self.kwargs.get("pk"))
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = _("Locations")
        context["inventory"] = True
        context["location"] = get_object_or_404(Location, pk=self.kwargs.get("pk"))
        context["tab_names"] = [_("Details"), _("Inventory")]
        context["id"] = self.kwargs.get("pk")
        context["breadcrumbs"] = [
            {"name": _("Locations"), "url": reverse_lazy("core:location")},
            {"name": f"{context['location']}", "url": "#"},
        ]
        return context
