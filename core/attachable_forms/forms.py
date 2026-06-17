import functools
import logging
import sys
from dataclasses import asdict
from enum import Enum
from typing import Dict
from core.attachable_forms.components import Components
from core.attachable_forms.form_models import FormField, AttachedForm, FormContext
from django.db.models import Q
from django.db.models.functions import Lower


from core.models import (
    SaleType,
    ActivityResourceType,
    AfeUser,
    Batch,
    Beatup,
    DownTime,
    FactoryProductionReport,
    ForestInventoryReport,
    Handoff,
    HarvestingReport,
    InventoryAffectorType,
    Item,
    ItemInventory,
    ItemRecieve,
    ItemTransportation,
    ItemType,
    JobOportunity,
    PlantationSiteSelectionReport,
    Location,
    LumberStoredReport,
    ProductName,
    ProductType,
    TestType,
    Thinning,
    ThinningSale,
    ThinningSaleType,
    TimelyHarvestingReport,
)
from core.utils import remove_empty

logger = logging.getLogger(__name__)


class Form(Enum):
    SeedPurchaseDetailsForm = AttachedForm(
        title="Tree Seed Purchase Details",
        version="1.0",
        fields=[
            FormField(
                label="Seed Source Site",
                name="location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {  # Double lambda for lazy evaluation
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
            ),
            FormField(
                label="Purchase Date",
                name="date",
                type="date",
                required=True,
            ),
            FormField(
                label="Expert Name",
                name="expert",
                type="string",
                required=True,
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
                multiple=True,
            ),
            FormField(
                label="Unit Cost",
                name="cost",
                type="float",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Amount in Kilogram",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Collection Date",
                name="collection_date",
                type="date",
                required=False,
                multiple=True,
            ),
            FormField(
                label="Collector Name",
                name="collector",
                type="string",
                required=False,
                multiple=True,
            ),
            FormField(
                label="Purity in Percentage",
                name="purity_percentage",
                type="float",
                required=False,
            ),
        ],
    )
    Test1 = AttachedForm(
        title="Internal Test Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_id",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.id): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SEED)
                },
                autofill_callable=lambda: lambda: {
                    "item_id": {
                        str(x.id): str(x.item.id)
                        for x in Batch.objects.filter(item__item_type=ItemType.SEED)
                    }
                },
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
            ),
            FormField(
                label="Result",
                name="result",
                type="select",
                required=True,
                options={"PASS": "Pass", "FAIL": "Fail"},
            ),
            FormField(label="Remark", name="remark", type="string", required=False),
            FormField(
                label="Start Date", name="start_date", type="date", required=True
            ),
            FormField(label="End Date", name="end_date", type="date", required=True),
            FormField(
                label="Round of Testing",
                name="round",
                type="select",
                required=True,
                options={"1": "Round 1", "2": "Round 2", "3": "Round 3"},
            ),
            FormField(
                label="Quantity in kg", name="quantity", type="float", required=True
            ),
            FormField(
                label="Purity in Percentage",
                name="purity_percentage",
                type="float",
                required=True,
            ),
            FormField(
                label="Germination in Percentage",
                name="germination_percentage",
                type="float",
                required=True,
            ),
            FormField(
                label="Moisture Content in Percentage",
                name="moisture_content",
                type="float",
                required=True,
            ),
            FormField(
                label="Viable Seed Per kilogram",
                name="viable_seed_per_kilogram",
                type="float",
                required=True,
            ),
            FormField(
                label="Tested By",
                name="tested_by_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
        ],
    )

    QuarantineTesting = AttachedForm(
        title="Quarantine Testing",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_id",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.id): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SEED)
                },
                autofill_callable=lambda: lambda: {
                    "item_id": {
                        str(x.id): str(x.item.id)
                        for x in Batch.objects.filter(item__item_type=ItemType.SEED)
                    },
                },
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
            ),
            FormField(
                label="Result",
                name="result",
                type="select",
                required=True,
                options={"PASS": "Pass", "FAIL": "Fail"},
            ),
            FormField(label="Remark", name="remark", type="string", required=False),
            FormField(
                label="Start Date", name="start_date", type="date", required=True
            ),
            FormField(label="End Date", name="end_date", type="date", required=True),
            FormField(
                label="Quantity in kg", name="quantity", type="float", required=True
            ),
            FormField(
                label="Purity in Percentage",
                name="purity_percentage",
                type="float",
                required=True,
            ),
            FormField(
                label="Germination in Percentage",
                name="germination_percentage",
                type="float",
                required=True,
            ),
            FormField(
                label="Moisture Content in Percentage",
                name="moisture_content",
                type="float",
                required=True,
            ),
            FormField(
                label="Viable Seed Per kilogram",
                name="viable_seed_per_kilogram",
                type="float",
                required=True,
            ),
            FormField(
                label="Tested By",
                name="tested_by_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
        ],
    )

    BranchHQTransportForm = AttachedForm(
        title="Branch to HQ Transportation",
        version="1.0",
        fields=[
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
                multiple=True,
            ),
            FormField(
                label="Seed Source Site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
                multiple=True,
            ),
            FormField(
                label="Amount in kg",
                name="amount",
                type="float",
                required=True,
                multiple=True,
            ),
            FormField(
                label="From",
                name="from_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="BRANCH").all().order_by("name")
                },
            ),
            FormField(
                label="To",
                name="to_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="HQ").all().order_by("name")
                },
            ),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Truck Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(
                label="Reciever",
                name="receiver_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
        ],
    )

    HQNurserySeedTransportationForm = AttachedForm(
        title="HQ to Nursery Seed Transportation",
        version="1.0",
        fields=[
            FormField(
                label="From",
                name="from_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="HQ").all().order_by("name")
                },
            ),
            FormField(
                label="To",
                name="to_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="NURSERY").all().order_by("name")
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="string",
                required=True,
            ),
              FormField(
                label="Unit",
                name="unit",
                type="string",
                required=True,
            ),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Truck Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(label="Date Sent", name="date", type="date", required=True),
            FormField(
                label="Batch",
                name="batch_id",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.id): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SEED)
                },
                multiple=True,
            ),
            FormField(
                label="Amount in Kilogram",
                name="amount",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    FirewoodCustomerTransportForm = AttachedForm(
        title="Transporting sold firewood to customer",
        version="1.0",
        fields=[
            Components.from_location("SUB_COMPARTMENT"),
            Components.date(),
            Components.driver_name(),
            Components.plate_number(),
            Components.voucher_no(),
            Components.unit(),
            Components.polygon_name(),
            Components.centroid_location(),
            FormField(
                label="Reciever",
                name="receiver_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
            Components.product(product_type=ProductType.FIREWOOD),
            Components.amount(),
        ],
    )

    LogProductionSawmillTransportForm = AttachedForm(
        title="Log Transportation from Production Site to Sawmill",
        version="1.0",
        fields=[
            Components.from_location("SUB_COMPARTMENT"),
            Components.date(),
            Components.driver_name(),
            Components.plate_number(),
            Components.to_location("SAWMILL"),
            Components.voucher_no(),
            Components.unit(),
            Components.polygon_name(),
            Components.centroid_location(),
            Components.batch_number(item__item_type=ItemType.PRODUCT),
            Components.product(),
            Components.product_category(),
            Components.amount(),
        ],
    )

    NurserySubCompartmentTransportForm = AttachedForm(
        title="Nursery Sub Compartment Transport",
        version="1.0",
        fields=[
            FormField(
                label="From",
                name="from_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="NURSERY").all().order_by("name")
                },
            ),
            FormField(
                label="To",
                name="to_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SUB_COMPARTMENT")
                    .all()
                    .order_by("name")
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
            Components.batch_number(multiple=True, item__item_type=ItemType.SEEDLING),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEEDLING").all()
                },
                multiple=True,
            ),
            FormField(
                label="Amount",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
        ],
    )

    SeedSourceBranchTransportForm = AttachedForm(
        title="Seed Source Branch Transport",
        version="1.0",
        fields=[
            FormField(
                label="Seed Source Site",
                name="from_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
            ),
            FormField(
                label="Branch",
                name="to_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="BRANCH").all().order_by("name")
                },
            ),
            FormField(
                label="Date",
                name="date",
                type="date",
                required=True,
            ),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Expert Name",
                name="expert_name",
                type="string",
                required=False,
            ),
            FormField(
                label="Truck Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                multiple=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
            ),
            FormField(
                label="Amount in kg",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
        ],
    )
    
    SeedBranchReceivingForm = AttachedForm(
        title="Seed Receiving Form",
        version="1.0",
        fields=[
            Components.incoming_transport(
                to_location__type="BRANCH",
                exclude_empty_batch=False,
                autofill_callable=lambda: lambda: {
                    "voucher_no": {
                        str(x.id): str(x.voucher_no)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="BRANCH",
                            itemrecieve__isnull=True,
                        )
                    },
                    "driver_name": {
                        str(x.id): str(x.driver_name)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="BRANCH",
                            itemrecieve__isnull=True,
                        )
                    },
                    "plate_number": {
                        str(x.id): str(x.plate_number)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="BRANCH",
                            itemrecieve__isnull=True,
                        )
                    },
                    "item_id": {
                        str(x.id): str(x.item.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="BRANCH",
                            itemrecieve__isnull=True,
                        )
                    },
                    "amount": {
                        str(x.id): str(x.amount)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="BRANCH",
                            itemrecieve__isnull=True,
                        )
                    },
                    "to_location_id": {
                        str(x.id): str(x.to_location.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="BRANCH",
                            itemrecieve__isnull=True,
                        )
                    },
                },
            ),
            FormField(
                label="Voucher Number",
                name="voucher_no",
                required=True,
                type="number",
            ),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Truck Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
                multiple=True,
            ),
            FormField(
                label="Amount in kg",
                name="amount",
                type="float",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Seed Source Site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
            ),
            FormField(
                label="Received Location",
                name="to_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="BRANCH").all().order_by("name")
                },
            ),
            FormField(label="Date", name="date", type="date", required=True),
        ],
    )

    NurserySeedReceivingForm = AttachedForm(
        title="Nursery Seed Receiving Details",
        version="1.0",
        fields=[
            Components.incoming_transport(
                to_location__type="NURSERY",
                autofill_callable=lambda: lambda: {
                    "voucher_no": {
                        str(x.id): str(x.voucher_no)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="NURSERY",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "from_location_id": {
                        str(x.id): str(x.from_location.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="NURSERY",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "to_location_id": {
                        str(x.id): str(x.to_location.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="NURSERY",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "amount": {
                        str(x.id): str(x.amount)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="NURSERY",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "driver_name": {
                        str(x.id): str(x.driver_name)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="NURSERY",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "plate_number": {
                        str(x.id): str(x.plate_number)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="NURSERY",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                },
            ),
            FormField(
                label="From HQ",
                name="from_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="HQ").all().order_by("name")
                },
            ),
            FormField(
                label="To Nursery",
                name="to_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="NURSERY").all().order_by("name")
                },
            ),
            FormField(
                label="Date",
                name="date",
                type="date",
                required=True,
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Truck Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(
                label="Batch",
                name="batch_no",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SEED)
                },
                multiple=True,
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
                multiple=True,
            ),
            FormField(
                label="Seed Source site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
                multiple=True,
            ),
            FormField(
                label="Amount in Kilogram",
                name="amount",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    LogReceivingForm = AttachedForm(
        title="Receiving logs/ approve sent logs",
        version="1.0",
        fields=[
            Components.from_location("SUB_COMPARTMENT"),
            Components.date(),
            Components.driver_name(),
            Components.plate_number(),
            Components.to_location("SAWMILL"),
            Components.voucher_no(),
            Components.polygon_name(),
            Components.centroid_location(),
            Components.batch_id(item__item_type=ItemType.TREE),
            Components.product_name(),
            Components.stock_code(),
            Components.code_single(),
            Components.length(),
            Components.bottom_diameter(),
            Components.top_diameter(),
            Components.middle_diameter(),
            Components.amount(),
        ],
    )

    SowingForm = AttachedForm(
        title="Sowing Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="string",
                option_callable=lambda: lambda: [
                    x.batch_number
                    for x in Batch.objects.filter(item__item_type="SEEDLING")
                ],
                autofill_callable=lambda: lambda: {
                    "item_id": {
                        str(x.batch_number): str(x.item.id)
                        for x in Batch.objects.filter(item__item_type="SEEDLING")
                    },
                    "source_site_id": {
                        str(x.batch_number): str(x.source_site.id)
                        for x in Batch.objects.filter(item__item_type="SEEDLING")
                    },
                },
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
            ),
            FormField(
                label="Seed Source site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
            ),
            FormField(
                label="Quantity in kg", name="quantity", type="float", required=True
            ),
            FormField(
                label="Started Date",
                name="start_date",
                type="date",
                required=True,
                allow_future_date=True,
            ),
            FormField(
                label="End Date",
                name="end_date",
                type="date",
                required=True,
                allow_future_date=True,
            ),
        ],
    )

    GerminatedSeedForm = AttachedForm(
        title="Germinated Seed Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SOWED_SEED)
                },
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type=ItemType.SOWED_SEED).all()
                },
            ),
            FormField(
                label="Seed Source site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
            ),
            FormField(label="Date", name="date", type="date", required=True),
            FormField(
                label="Total Germinated Seed number",
                name="amount",
                type="number",
                required=True,
            ),
        ],
    )

    SeedlingNurserySale = AttachedForm(
        title="Seedling Sale Form",
        version="1.0",
        fields=[
            FormField(label="Date Sold", name="date", type="date", required=True),
            FormField(
                label="Sold by",
                name="seller_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
            Components.sold_to(name="client"),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Batch",
                name="batch_id",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.id): x.batch_number
                    for x in Batch.objects.filter(
                        item__item_type=ItemType.SEEDLING
                    ).all()
                },
                multiple=True,
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type=ItemType.SEEDLING).all()
                },
                multiple=True,
            ),
            FormField(
                label="Amount of Seedling",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Unit Cost",
                name="unit_price",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    GradingSeedlingForm = AttachedForm(
        title="Grading Seedling Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(
                        item__item_type=ItemType.GERMINATED_SEED
                    )
                },
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(
                        item_type=ItemType.GERMINATED_SEED
                    ).all()
                },
            ),
            FormField(
                label="Seed Source site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
            ),
            FormField(label="Date", name="date", type="date", required=True),
        ],
    )

    HQSeedReceivingForm = AttachedForm(
        title="HQ Seed Receiving Details",
        version="1.0",
        fields=[
            Components.incoming_transport(
                exclude_empty_batch=False,
                to_location__type="HQ",
                autofill_callable=lambda: lambda: {
                    "voucher_no": {
                        str(x.id): str(x.voucher_no)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="HQ",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "item_id": {
                        str(x.id): str(x.item.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="HQ",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "amount": {
                        str(x.id): str(x.amount)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="HQ",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "from_location_id": {
                        str(x.id): str(x.from_location.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="HQ",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "to_location_id": {
                        str(x.id): str(x.to_location.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="HQ",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "driver_name": {
                        str(x.id): str(x.driver_name)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="HQ",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                    "plate_number": {
                        str(x.id): str(x.plate_number)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="HQ",
                            itemrecieve__isnull=True,
                        ).all()
                    },
                },
            ),
            FormField(
                label="From Branch",
                name="from_location_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="BRANCH").all().order_by("name")
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Expert Name",
                name="expert_name",
                type="string",
                required=False,
            ),
            FormField(
                label="Receiver",
                name="receiver_id",
                type="table_select",
                required=False,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
            FormField(
                label="Truck Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEED").all()
                },
                multiple=True,
            ),
            FormField(
                label="Collection Date",
                name="collection_date",
                type="date",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Amount in kg",
                name="amount",
                type="float",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Seed Source site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
                multiple=True,
            ),
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="string",
                multiple=True,
            ),
        ],
    )

    SeedlingReceivingForm = AttachedForm(
        title="Seedling Receiving Details",
        version="1.0",
        fields=[
            Components.incoming_transport(
                to_location__type="SUB_COMPARTMENT",
                autofill_callable=lambda: lambda: {
                    "voucher_no": {
                        str(x.id): str(x.voucher_no)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="SUB_COMPARTMENT",
                            itemrecieve__isnull=True,
                        )
                    },
                    "driver_name": {
                        str(x.id): str(x.driver_name)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="SUB_COMPARTMENT",
                            itemrecieve__isnull=True,
                        )
                    },
                    "plate_number": {
                        str(x.id): str(x.plate_number)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="SUB_COMPARTMENT",
                            itemrecieve__isnull=True,
                        )
                    },
                    "item_id": {
                        str(x.id): str(x.item.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="SUB_COMPARTMENT",
                            itemrecieve__isnull=True,
                        )
                    },
                    "amount": {
                        str(x.id): str(x.amount)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="SUB_COMPARTMENT",
                            itemrecieve__isnull=True,
                        )
                    },
                    "to_location_id": {
                        str(x.id): str(x.to_location.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="SUB_COMPARTMENT",
                            itemrecieve__isnull=True,
                        )
                    },
                    "batch_id": {
                        str(x.id): str(x.batch.id)
                        for x in ItemTransportation.get_by_distinct_voucher(
                            to_location__type="SUB_COMPARTMENT",
                            itemrecieve__isnull=True,
                        )
                    },
                },
            ),
            FormField(
                label="Nursery",
                name="location_id",
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="NURSERY").all()
                },
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
            FormField(
                label="Driver",
                name="driver_name",
                type="string",
                required=True,
            ),
            FormField(
                label="Truck Plate Number",
                name="plate_number",
                type="string",
                required=True,
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(item_type="SEEDLING").all()
                },
                multiple=True,
            ),
            FormField(
                label="Seed Source site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
                multiple=True,
            ),
            FormField(
                label="Batch",
                name="batch_id",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.id): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SEEDLING)
                },
                multiple=True,
            ),
            FormField(
                label="Amount in kilogram",
                name="amount",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    SeedSaleForm = AttachedForm(
        title="Seed Sale",
        version="1.0",
        fields=[
            FormField(label="Date Sold", name="date", type="date", required=True),
            FormField(
                label="Sold by",
                name="seller_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
            Components.sold_to(name="client"),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(
                label="Batch",
                name="batch_id",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.id): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SEED)
                },
                multiple=True,
            ),
            FormField(
                label="Quantity Sold",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Unit Price before VAT",
                name="unit_price",
                type="string",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Total Revenue before VAT",
                name="total_rev_before_vat",
                type="float",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Operational Cost by species/kg",
                name="operational_cost",
                type="float",
                required=True,
                multiple=True,
            ),
            FormField(
                label="Seed Collection Cost",
                name="seed_collection_cost",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    GradingForm = AttachedForm(
        title="Grading Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(
                        item__item_type=ItemType.GERMINATED_SEED
                    )
                },
            ),
            FormField(
                label="Species",
                name="item_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.species
                    for x in Item.objects.filter(
                        item_type=ItemType.GERMINATED_SEED
                    ).all()
                },
            ),
            FormField(
                label="Seed Source site",
                name="source_site_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.name
                    for x in Location.objects.filter(type="SEED_SOURCE")
                    .all()
                    .order_by(Lower("name"))
                },
            ),
            FormField(label="Date", name="date", type="date", required=True),
            FormField(
                label="Grade 1", name="grade1_amount", type="number", required=True
            ),
            FormField(
                label="Grade 2", name="grade2_amount", type="number", required=True
            ),
            FormField(
                label="Grade 3", name="grade3_amount", type="number", required=True
            ),
        ],
    )

    HandoffForm = AttachedForm(
        title="Handoff Planted Seedling Form",
        version="1.0",
        fields=[
            Components.batch_id(item__item_type=ItemType.SEEDLING),
            Components.amount(label="Number of Seedling Handoff", multiple=False),
            Components.date(),
        ],
    )

    BeatupForm = AttachedForm(
        title="Beatup Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.SEEDLING)
                },
            ),
            FormField(
                label="Number of Seedling Replaced",
                name="amount",
                type="number",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
        ],
    )

    GiveAwayForm = AttachedForm(
        title="Surplus by-products Giveaway",
        version="1.0",
        fields=[
            Components.batch_number(item__item_type=ItemType.PRODUCT),
            Components.date(),
            Components.product(),
            Components.amount(),
            Components.unit_price(),
            FormField(
                label="Total Price",
                name="total_price",
                type="number",
                required=True,
                multiple=True,
            ),
        ],
    )

    ForestInventoryForm = AttachedForm(
        title="Forest Inventory",
        version="1.0",
        fields=[
            Components.date(),
            Components.batch_id(item__item_type=ItemType.TREE),
            Components.amount("Total number of Trees", multiple=False),
            FormField(
                label="Total volume in m3",
                name="total_volume",
                type="float",
                required=True,
            ),
            FormField(
                label="Total number of sample",
                name="total_sample",
                type="float",
                required=True,
            ),
            FormField(
                label="Basal Area in ha", name="basal_area", type="float", required=True
            ),
        ],
    )

    SurvivalCountForm = AttachedForm(
        title="Survival Count Form",
        version="1.0",
        fields=[
            Components.batch_id(
                item__item_type=ItemType.SEEDLING,
                autofill_callable=lambda: lambda: {
                    "item_id": {
                        str(x.id): str(x.item.id)
                        for x in Batch.objects.filter(item__item_type=ItemType.SEEDLING)
                    }
                },
            ),
            Components.item(label="Species", item_type="SEEDLING"),
            FormField(
                label="Number of alive seedlings",
                name="no_alive",
                type="number",
                required=True,
            ),
            FormField(
                label="Number of dead seedlings",
                name="no_dead",
                type="number",
                required=True,
            ),
            Components.date(),
        ],
    )

    LowThinningForm = AttachedForm(
        title="Low Thinning Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.TREE).all()
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
            Components.product_name(),
            Components.product_category(),
            Components.stock_code(),
            Components.code_single(),
            Components.length(),
            Components.bottom_diameter(),
            Components.top_diameter(),
            Components.middle_diameter(),
            FormField(
                label="Amount in m3",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
        ],
    )

    HighThinningForm = AttachedForm(
        title="High Thinning Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="table_select",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.TREE).all()
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
            Components.product_name(),
            Components.product_category(),
            Components.stock_code(),
            Components.code_single(),
            Components.length(),
            Components.bottom_diameter(),
            Components.top_diameter(),
            Components.middle_diameter(),
            FormField(
                label="Amount",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
        ],
    )

    PreCommercialCoppiceSinglingForm = AttachedForm(
        title="Pre Commercial Coppice Singling Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="string",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.TREE)
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
            Components.product_name(),
            Components.product_category(),
            Components.stock_code(),
            Components.code_single(),
            Components.length(),
            Components.bottom_diameter(),
            Components.top_diameter(),
            Components.middle_diameter(),
            FormField(
                label="Amount",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
        ],
    )

    CommercialSinglingForm = AttachedForm(
        title="Commercial Coppice Singling Form",
        version="1.0",
        fields=[
            FormField(
                label="Batch",
                name="batch_no",
                required=True,
                type="string",
                option_callable=lambda: lambda: {
                    str(x.batch_number): x.batch_number
                    for x in Batch.objects.filter(item__item_type=ItemType.TREE)
                },
            ),
            FormField(
                label="Voucher number",
                name="voucher_no",
                type="number",
                required=True,
            ),
            FormField(label="Date", name="date", type="date", required=True),
            Components.product_name(),
            Components.product_category(),
            Components.stock_code(),
            Components.code_single(),
            Components.length(),
            Components.bottom_diameter(),
            Components.top_diameter(),
            Components.middle_diameter(),
            FormField(
                label="Amount",
                name="amount",
                type="number",
                required=True,
                multiple=True,
            ),
        ],
    )

    SaleCoppiceForm = AttachedForm(
        title="Coppice Sale Form",
        version="1.0",
        fields=[
            Components.date(),
            Components.batch_number(item__item_type=ItemType.PRODUCT),
            Components.voucher_no(),
            Components.sold_to(),
            Components.sold_by(),
            Components.product(),
            Components.product_category(),
            Components.amount(),
            Components.unit_price_before_vat(),
            FormField(
                label="Total Price before VAT",
                name="total_price_before_vat",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    SaleThinningForm = AttachedForm(
        title="Thinning Sale Form",
        version="1.0",
        fields=[
            Components.batch_number(item__item_type=ItemType.PRODUCT),
            Components.voucher_no(),
            Components.sold_to(),
            FormField(
                label="Sold By",
                name="sold_by",
                required=True,
                type="select",
                options=lambda: {  # Changed to lambda
                    user.username: f"{user.first_name} {user.last_name}"
                    for user in AfeUser.objects.all()
                },
            ),
            Components.date(),
            Components.unit(),
            Components.product(),
            Components.product_category(),
            Components.amount(),
            Components.unit_price_before_vat(),
            FormField(
                label="Total Price before VAT",
                name="total_price_before_vat",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    RegisterProductForm = AttachedForm(
        title="Register Products",
        version="1.0",
        fields=[
            Components.batch_id(item__item_type=ItemType.TREE),
            Components.item(label="Tree", item_type=ItemType.TREE),
            FormField(
                label="Number of fallen trees",
                name="no_tree_fall",
                required=True,
                type="number",
            ),
            Components.date(),
            Components.polygon_name(),
            Components.centroid_location(),
            Components.voucher_no(),
            Components.product_name(),
            Components.product_category(),
            Components.stock_code(),
            Components.code_single(),
            Components.length(),
            Components.bottom_diameter(),
            Components.top_diameter(),
            Components.middle_diameter(),
            Components.amount(),
        ],
    )

    TimelyHarvestingForm = AttachedForm(
        title="Timely Harvested Product",
        version="1.0",
        fields=[
            Components.batch_number(item__item_type=ItemType.TREE),
            Components.item(label="Species", item_type=ItemType.TREE),
            Components.start_date(required=False),
            Components.end_date(required=False),
            FormField(
                label="Polygon Name", name="polygon_name", type="string", required=True
            ),
            FormField(
                label="Centroid Location",
                name="polygon_centroid_location",
                type="float",
                required=True,
            ),
            Components.sold_to(required=False),
            Components.voucher_no(required=False),
            FormField(
                label="Production achievement in m3",
                name="productive_area_m3",
                type="float",
                required=True,
                multiple=True,
            ),
              FormField(
                label="Production achievement in ha",
                name="productive_area_ha",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    SaleEachProductForm = AttachedForm(
        title="Sale of each product",
        version="1.0",
        fields=[
            Components.date(),
            Components.sold_to(name="client"),
            FormField(
                label="Polygon Name", name="polygon_name", type="string", required=True
            ),
            FormField(
                label="Centroid Location",
                name="polygon_centroid_location",
                type="float",
                required=True,
            ),
            Components.voucher_no(),
            Components.batch_number(item__item_type=ItemType.PRODUCT),
            Components.product(),
            Components.product_category(),
            Components.amount(),
            Components.unit_price_before_vat(),
            FormField(
                label="Total Price before VAT",
                name="total_rev_before_vat",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    SaleDifferentProduct = AttachedForm(
        title="Sale of different product",
        version="1.0",
        fields=[
            Components.date(),
            Components.sold_to(name="client"),
            FormField(
                label="TIN Number", name="tin_number", type="number", required=True
            ),
            Components.voucher_no(),
            Components.batch_number(item__item_type=ItemType.PRODUCT),
            FormField(
                label="Sale Order Number",
                name="order_number",
                type="number",
                required=True,
            ),
            Components.product(),
            Components.product_category(),
            Components.amount(),
            Components.unit_price_before_vat(),
            FormField(
                label="Total Revenue before VAT",
                name="total_rev_before_vat",
                type="float",
                required=True,
                multiple=True,
            ),
        ],
    )

    StampageSaleForm = AttachedForm(
        title="Sale at Stampage",
        version="1.0",
        fields=[
            Components.batch_id(item__item_type=ItemType.TREE),
            Components.item(label="Tree", item_type=ItemType.TREE),
            Components.date(),
            Components.sold_to(name="client"),
            FormField(
                label="Polygon Name", name="polygon_name", type="string", required=True
            ),
            FormField(
                label="Centroid Location",
                name="polygon_centroid_location",
                type="float",
                required=True,
            ),
            Components.voucher_no(),
            Components.amount(label="Number of stand trees sold", multiple=False),
            FormField(
                label="Total Revenue before VAT",
                name="total_rev_before_vat",
                type="float",
                required=True,
            ),
            FormField(
                label="Start date of harvesting",
                name="harvesting_start_date",
                type="date",
                required=True,
            ),
            FormField(
                label="End date of harvesting",
                name="harvesting_end_date",
                type="date",
                required=True,
            ),
        ],
    )

    OperationalForestInventoryForm = AttachedForm(
        title="Operational Forest Inventory",
        version="1.0",
        fields=[
            Components.batch_id(),
            Components.item(label="Species"),
            Components.date(),
            FormField(
                label="Polygon Name", name="polygon_name", type="string", required=True
            ),
            FormField(
                label="Centroid Location",
                name="polygon_centroid_location",
                type="float",
                required=True,
            ),
            FormField(
                label="Forest Volume in ha for saling at stand level",
                name="forest_volume_stand_level",
                type="float",
                required=True,
            ),
            FormField(
                label="Forest Volume in ha for primary forest production",
                name="forest_volume_production",
                type="float",
                required=True,
            ),
        ],
    )

    DownTimeForm = AttachedForm(
        title="Recording Down Time Form",
        version="1.0",
        fields=[
            FormField(
                label="Start Date", name="start_date", type="date", required=True
            ),
            FormField(label="End Date", name="end_date", type="date", required=True),
            FormField(
                label="Total downtime in number of hours",
                name="downtime_hours",
                type="number",
                required=True,
            ),
            FormField(
                label="Down Time Reason",
                name="reason",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x): x
                    for x in [
                        "Electric problems",
                        "Log shortage",
                        "Lack of human power",
                        "Maintenance time",
                        "Shortages of machine spare part",
                        "Shortages of grease and oil and other major force",
                    ]
                },
            ),
        ],
    )

    JobOpportunityForm = AttachedForm(
        title="Record Created Job Opportunities",
        version="1.0",
        fields=[
            Components.date(),
            FormField(
                label="Number of new groups",
                name="no_groups_new",
                type="number",
                required=True,
            ),
            FormField(
                label="Total New Male",
                name="new_male_count",
                type="number",
                required=True,
            ),
            FormField(
                label="Total New Female",
                name="new_female_count",
                type="number",
                required=True,
            ),
            FormField(
                label="Number of old groups",
                name="no_groups_old",
                type="number",
                required=True,
            ),
            FormField(
                label="Total Previous Male",
                name="old_male_count",
                type="number",
                required=True,
            ),
            FormField(
                label="Total Previous Female",
                name="old_female_count",
                type="number",
                required=True,
            ),
        ],
    )

    DepoFactoryInputForm = AttachedForm(
        title="Depot To Factory Input Form",
        version="1.0",
        fields=[
            Components.from_location("SAWMILL"),
            Components.driver_name("Deliverer"),
            FormField(
                label="Reciever",
                name="receiver_id",
                type="table_select",
                required=True,
                option_callable=lambda: lambda: {
                    str(x.id): x.get_full_name() for x in AfeUser.objects.all()
                },
            ),
            Components.date(),
            Components.batch_number(item__item_type=ItemType.PRODUCT, multiple=True),
            Components.product(),
            Components.product_category(),
            Components.amount(),
        ],
    )

    FactoryDailyProductionForm = AttachedForm(
        version="1.0",
        title="Factory daily lumber production",
        fields=[
            Components.date(),
            Components.product_name(multiple=False),
            Components.product_category(multiple=False),
            Components.amount(multiple=False),
        ],
    )
    PlantationSiteSelectionForm = AttachedForm(
    version="1.0",
    title="Plantation Site Selection Report",
    fields=[

        FormField(
            label="Site Code",
            name="site_code",
            type="string",
            required=True,
        ),

        FormField(
            label="Site Name",
            name="site_name",
            type="string",
            required=True,
        ),

        FormField(
            label="Location",
            name="location",
            type="string",
            required=True,
        ),

        FormField(
            label="Total Area (Hectare)",
            name="total_area",
            type="number",
            required=True,
        ),

        FormField(
            label="Soil Type",
            name="soil_type",
            type="select",
            required=True,
            options=[
                ("clay", "Clay"),
                ("sandy", "Sandy"),
                ("loamy", "Loamy"),
                ("silt", "Silt"),
            ],
        ),

        FormField(
            label="Soil PH",
            name="soil_ph",
            type="number",
            required=True,
        ),

        FormField(
            label="Drainage Rating",
            name="drainage_rating",
            type="number",
            required=True,
        ),

        FormField(
            label="Average Temperature",
            name="avg_temperature",
            type="number",
            required=True,
        ),

        FormField(
            label="Annual Rainfall",
            name="annual_rainfall",
            type="number",
            required=True,
        ),

        FormField(
            label="Suitability Score",
            name="suitability_score",
            type="number",
            required=True,
        ),

        FormField(
            label="Available",
            name="is_available",
            type="boolean",
            required=False,
        ),
    ],
)
    LumberStoredForm = AttachedForm(
        version="1.0",
        title="Lumber Stored",
        fields=[
            FormField(
                label="Enter Daily Output",
                name="daily_output",
                type="string",
                required=True,
            ),
            Components.date(),
            Components.batch_id(
                item__item_type=ItemType.PRODUCT, item__product_type=ProductType.LUMBER
            ),
            Components.product_name(multiple=False),
            Components.stock_code(),
            Components.code_single(),
            Components.length(),
            Components.bottom_diameter(),
            Components.top_diameter(),
            Components.middle_diameter(),
            Components.amount(multiple=False),
        ],
    )

    def __init__(self, form: AttachedForm) -> None:
        self.title = form.title
        self.form_json = lambda: form.to_dict()
        self.form = form
        self.fields = form.fields
        self.fields_json = list(map(asdict, form.fields))


def get_form_choices():
    return [(form.name, form.title) for form in Form]


class FormCallbackMapper:
    @staticmethod
    def purchase(data: Dict, context: FormContext):
        from core.models import ItemPurchase

        purchase = ItemPurchase(**data)
        purchase.save()

    @staticmethod
    def empty_transportation(data: Dict, context: FormContext):
        transportation = ItemTransportation(**data)
        transportation.save()

    @staticmethod
    def transportation(data: Dict, context: FormContext):
        from core.models import ItemTransportation

        batch = Batch.get_batch_by_item(data.pop("batch_no"), data.get("item_id"))
        data["batch_id"] = batch.id
        transportation = ItemTransportation(**data)
        transportation.save()

        if transportation.batch:
            transportation.source_site = transportation.batch.source_site
            transportation.save()

        inventory = ItemInventory.get_inventory_by_batch(
            transportation.from_location, transportation.batch
        )
        if not inventory:
            raise ValueError("Inventory not found")
        inventory.decrease(
            transportation.amount,
            InventoryAffectorType.TRANSPORT,
            transportation.to_location,
            transportation.source_site,
        )
        inventory.save()

    @staticmethod
    def hq_nursery_transportation(data: Dict, context: FormContext):
        from core.models import ItemTransportation

        batch = Batch.objects.get(pk=data.get("batch_id"))
        item = batch.item
        transportation = ItemTransportation(**data, item=item)
        transportation.save()

        transportation.source_site = transportation.batch.source_site
        transportation.save()

        inventory = ItemInventory.get_inventory_by_batch(
            transportation.from_location, transportation.batch
        )
        if not inventory:
            raise ValueError("Inventory not found")
        inventory.decrease(
            transportation.amount,
            InventoryAffectorType.TRANSPORT,
            transportation.to_location,
            transportation.source_site,
        )
        inventory.save()

    @staticmethod
    def firewood_transportation(data: Dict, context: FormContext):
        from core.models import ItemTransportation

        transportation = ItemTransportation(**data)
        transportation.save()

        transportation.source_site = transportation.batch.source_site
        transportation.save()

    @staticmethod
    def sawmill_transportation(data: Dict, context: FormContext):
        from core.models import ItemTransportation

        batch = Batch.get_batch_by_item(data.pop("batch_no"), data.get("item_id"))
        transportation = ItemTransportation(**data, item=batch.item)
        transportation.save()

        transportation.source_site = transportation.batch.source_site
        transportation.save()

        inventory = ItemInventory.get_inventory_by_batch(
            context.location, transportation.batch
        )
        inventory.decrease(transportation.amount, InventoryAffectorType.TRANSPORT)
        inventory.save()

    @staticmethod
    def branch_hq_transportation(data: Dict, context: FormContext):
        from core.models import InventoryAffectorType, ItemTransportation

        transportation = ItemTransportation(**data)
        transportation.save()

        if transportation.batch:
            transportation.source_site = transportation.batch.source_site
            transportation.save()

        inventory = ItemInventory.get_inventory(
            transportation.item,
            transportation.from_location,
            transportation.source_site,
        )
        if not inventory:
            raise ValueError("Inventory not found")
        inventory.decrease(
            transportation.amount,
            InventoryAffectorType.TRANSPORT,
            transportation.from_location,
            transportation.source_site,
        )
        inventory.save()

    @staticmethod
    def test_form(data: Dict, form_name: str, context: FormContext):
        from core.models import Test

        test_type = None
        match form_name:
            case "Test1":
                test_type = TestType.TEST
            case "QuarantineTesting":
                test_type = TestType.QUARANTINE

        data["type"] = test_type
        data["location_id"] = str(context.location.id)
        test_form = Test(**data)
        test_form.save()

        if test_form.result == "FAIL":
            inventory = ItemInventory.get_inventory(
                test_form.item,
                context.location,
                test_form.batch.source_site,
            )
            inventory.decrease(test_form.quantity, InventoryAffectorType.TEST)
            inventory.save()

    @staticmethod
    def nursery_seedling_sale(data: Dict, context: FormContext):
        from core.models import ItemSale

        nursery = context.get_location_type("NURSERY")

        data["location_id"] = str(nursery.id)
        sale = ItemSale(**data)
        sale.save()

        inventory = ItemInventory.get_inventory_by_batch(nursery, sale.batch)
        inventory.decrease(sale.amount, InventoryAffectorType.SALE, nursery)
        inventory.save()

    @staticmethod
    def hq_seed_sale(data: Dict, context: FormContext):
        from core.models import ItemSale

        hq = context.get_location_type("HQ")
        if not hq:
            raise ValueError("HQ not found")

        item = Batch.objects.get(pk=data.get("batch_id")).item
        sale = ItemSale(**data, item=item, location=hq)
        sale.save()

        inventory = ItemInventory.get_inventory_by_batch(hq, sale.batch)
        inventory.decrease(
            sale.amount, InventoryAffectorType.SALE, hq, sale.batch.source_site
        )
        inventory.save()

    @staticmethod
    def harvesting_sale(data: Dict, context: FormContext):
        from core.models import ItemSale

        batch = Batch.get_batch_by_item(data.pop("batch_no"), data.get("item_id"))

        sale = ItemSale(**data, location=context.location, batch=batch)
        sale.save()

        inventory = ItemInventory.get_inventory_by_batch(context.location, batch)
        inventory.decrease(sale.amount, InventoryAffectorType.SALE)
        inventory.save()

    @staticmethod
    def sale_diff_product(data: Dict, context: FormContext):
        from core.models import ItemSale

        batch = Batch.get_batch_by_item(data.pop("batch_no"), data.get("item_id"))
        sale = ItemSale(**data, item=batch.item, location=context.location, batch=batch)
        sale.save()

        inventory = ItemInventory.get_inventory_by_batch(context.location, sale.batch)
        inventory.decrease(sale.amount, InventoryAffectorType.SALE)
        inventory.save()

    @staticmethod
    def stampage_sale(data: Dict, context: FormContext):
        from core.models import ItemSale

        batch = Batch.objects.get(pk=data.get("batch_id"))

        sale = ItemSale(**data, location=context.location, sale_type=SaleType.STAMPAGE)
        sale.save()

        inventory = ItemInventory.get_inventory_by_batch(context.location, batch)
        inventory.decrease(sale.no_stand_trees_sold, InventoryAffectorType.SALE)
        inventory.save()

    @staticmethod
    def grading(data: Dict, context: FormContext):
        from core.models import Batch, SeedGrading, InventoryAffectorType

        location = context.get_location_type("NURSERY")
        batch = Batch.get_batch(
            data.get("batch_no"), data.get("source_site_id"), data.get("item_id")
        )
        if batch.item.item_type != ItemType.GERMINATED_SEED:
            raise ValueError("Item is not germinated seed")

        inventory = ItemInventory.get_inventory_by_batch(location, batch)

        grade1 = data.get("grade1_amount")
        grade1 = float(grade1.strip()) if grade1 else 0

        grade2 = data.get("grade2_amount")
        grade2 = float(grade2.strip()) if grade2 else 0

        grade3 = data.get("grade3_amount")
        grade3 = float(grade3.strip()) if grade3 else 0

        decrease_log = inventory.decrease(
            grade1 + grade3,
            InventoryAffectorType.GRADING,
            source_site=batch.source_site,
        )
        inventory.save()

        new_item = Item.get_item(
            batch.item.title, batch.item.species, ItemType.SEEDLING
        )
        new_batch = Batch.get_batch(
            batch.batch_number, batch.source_site.id, new_item.id
        )
        new_inventory = ItemInventory.get_inventory_by_batch(location, new_batch)
        increase_log = new_inventory.increase(grade1, InventoryAffectorType.GRADING)
        new_inventory.save()

        seed_grading = SeedGrading(
            date=data.get("date"),
            grade1_amount=grade1,
            grade2_amount=grade2,
            grade3_amount=grade3,
            item=batch.item,
            decrease_log=decrease_log,
            increase_log=increase_log,
            location=location,
        )
        seed_grading.save()

    @staticmethod
    def hq_receive(data: Dict, context: FormContext):
        from core.models import Batch, InventoryAffectorType, ItemInventory, ItemRecieve

        batch_number = data.pop("batch_no")
        source_site_id = data.get("source_site_id")
        item_id = data.get("item_id")
        batch = Batch.get_batch(batch_number, source_site_id, item_id)

        location = context.get_location_type("HQ")
        data["to_location_id"] = str(location.id)
        data["batch_id"] = str(batch.id)
        receive = ItemRecieve(**data, location=location)
        receive.save()
        inventory = ItemInventory.get_inventory_by_batch(
            receive.to_location, receive.batch
        )
        if not inventory:
            raise ValueError("Inventory not found")
        inventory.increase(
            receive.amount,
            InventoryAffectorType.RECIEVE,
            receive.from_location,
            receive.source_site,
        )
        inventory.save()

    @staticmethod
    def branch_receive(data: Dict, context: FormContext):
        from core.models import InventoryAffectorType, ItemInventory, ItemRecieve

        data["from_location_id"] = data["source_site_id"]
        data["location_id"] = data["to_location_id"]
        recieve = ItemRecieve(**data)
        recieve.save()
        inventory = ItemInventory.get_inventory(
            recieve.item, recieve.to_location, recieve.source_site
        )
        if not inventory:
            raise ValueError("Inventory not found")
        inventory.increase(
            recieve.amount,
            InventoryAffectorType.RECIEVE,
            recieve.from_location,
            recieve.source_site,
        )
        inventory.save()

    @staticmethod
    def empty_receive(data: Dict, context: FormContext):
        from core.models import ItemRecieve

        receive = ItemRecieve(**data)
        receive.save()

    @staticmethod
    def log_receive(data: Dict, context: FormContext):
        product_category = ProductType.LOG
        product_name = data.pop("product_name")

        batch = Batch.objects.get(pk=data.pop("batch_id"))

        new_item = Item.get_product(product_name, batch.item.species, product_category)
        new_item.stock_code = data.pop("stock_code", None)
        new_item.code_single = data.pop("code_single", None)
        new_item.length = data.pop("length", None)
        new_item.bottom_diameter = data.pop("bottom_diameter", None)
        new_item.top_diameter = data.pop("top_diameter", None)
        new_item.middle_diameter = data.pop("middle_diameter", None)
        new_item.save()

        new_batch = Batch.get_batch(
            batch.batch_number, batch.source_site.id, new_item.id
        )
        receive = ItemRecieve(
            **data, item=new_item, batch=new_batch, location=context.location
        )
        receive.save()
        inventory = ItemInventory.get_inventory_by_batch(context.location, new_batch)
        inventory.increase(
            data.get("amount"),
            InventoryAffectorType.RECIEVE,
            source_site=batch.source_site,
        )
        inventory.save()

    @staticmethod
    def nursery_receive(data: Dict, context: FormContext):
        from core.models import InventoryAffectorType, ItemInventory, ItemRecieve

        batch_number = data.pop("batch_no")
        batch = Batch.get_batch(
            batch_number, data.get("source_site_id"), data.get("item_id")
        )
        data["batch_id"] = str(batch.id)
        data["item_id"] = str(batch.item.id)
        recieve = ItemRecieve(**data, location_id=data.get("to_location_id"))
        recieve.save()
        inventory = ItemInventory.get_inventory_by_batch(
            recieve.to_location, recieve.batch
        )
        if not inventory:
            raise ValueError("Inventory not found")
        inventory.increase(
            recieve.amount,
            InventoryAffectorType.RECIEVE,
            recieve.from_location,
            recieve.batch.source_site,
        )
        inventory.save()

    @staticmethod
    def giveaway(data: Dict, context: FormContext):
        from core.models import ItemInventory, ProductGiveAway

        batch = Batch.objects.filter(
            batch_number=data.pop("batch_no"), item__item_type=ItemType.PRODUCT
        )
        if not batch.exists():
            raise ValueError("Batch not found")
        else:
            batch = batch.first()

        product_giveaway = ProductGiveAway(
            **data,
            location=context.location,
            product_category=batch.item.title,
            batch=batch,
        )
        product_giveaway.save()

        inventory = ItemInventory.get_inventory_by_batch(context.location, batch)
        inventory.decrease(product_giveaway.amount, InventoryAffectorType.GIVE_AWAY)
        inventory.save()

    @staticmethod
    def register_product(data: Dict, context: FormContext):
        from core.models import Item

        batch = Batch.objects.get(pk=data.get("batch_id"))
        inventory = ItemInventory.get_inventory_by_batch(context.location, batch)
        inventory.decrease(
            data.get("no_tree_fall"), InventoryAffectorType.REGISTER_PRODUCT
        )
        inventory.save()

        new_item = Item.get_product(
            data.pop("product_name"), batch.item.species, data.pop("product_category")
        )
        new_item.stock_code = data.get("stock_code", None)
        new_item.code_single = data.get("code_single", None)
        new_item.length = data.get("length", None)
        new_item.bottom_diameter = data.get("bottom_diameter", None)
        new_item.top_diameter = data.get("top_diameter", None)
        new_item.middle_diameter = data.get("middle_diameter", None)
        new_item.save()

        new_batch = Batch.get_batch(
            batch.batch_number, batch.source_site.id, new_item.id
        )
        inventory = ItemInventory.get_inventory_by_batch(context.location, new_batch)
        inventory.increase(
            data.get("amount"),
            InventoryAffectorType.REGISTER_PRODUCT,
            source_site=batch.source_site,
        )
        inventory.save()

        harvesting_report = HarvestingReport(
            batch=new_batch,
            item=new_item,
            no_tree_fall=data.get("no_tree_fall"),
            date=data.get("date"),
            polygon_name=data.get("polygon_name"),
            polygon_centroid_location=data.get("polygon_centroid_location"),
            product_type=new_item.product_type,
            amount=data.get("amount"),
            location=context.location,
            voucher_no=data.get("voucher_no"),
        )
        harvesting_report.save()

    @staticmethod
    def timely_harvesting(data: Dict, context: FormContext):
        batch = Batch.get_batch_by_item(data.pop("batch_no"), data.get("item_id"))
        data["batch_id"] = str(batch.id)

        timely_harvesting = TimelyHarvestingReport(**data, location=context.location)
        timely_harvesting.save()

    @staticmethod
    def survival_count(data: Dict, context: FormContext):
        from core.models import SurvivalCount

        batch = Batch.objects.get(pk=data.get("batch_id"))

        new_item = Item.get_item(batch.item.title, batch.item.species, ItemType.TREE)
        new_batch = Batch.get_batch(
            batch.batch_number, batch.source_site.id, new_item.id
        )

        survival_count = SurvivalCount(
            batch_id=new_batch.id,
            location_id=context.location.id,
            date=data.get("date"),
            no_alive=data.get("no_alive"),
            no_dead=data.get("no_dead"),

        )
        survival_count.save()

        inventory = ItemInventory.get_inventory_by_batch(context.location, new_batch)
        inventory.increase(
            survival_count.no_alive, InventoryAffectorType.SURVIVAL_COUNT
        )
        inventory.save()

    @staticmethod
    def handoff(data: Dict, context: FormContext):
        location = context.get_location_type("SUB_COMPARTMENT")
        handoff = Handoff(
            batch_id=data.get("batch_id"),
            amount=data.get("amount"),
            date=data.get("date"),
            location=location,
        )
        handoff.save()

    @staticmethod
    def beatup(data: Dict, context: FormContext):
        batch_number = data.pop("batch_no")
        batch = Batch.objects.filter(
            batch_number=batch_number, item__item_type=ItemType.SEEDLING
        )

        if not batch.exists():
            raise ValueError("Batch not found")
        else:
            batch = batch.first()

        location = context.get_location_type("SUB_COMPARTMENT")
        beatup = Beatup(
            batch=batch,
            amount=data.get("amount"),
            date=data.get("date"),
            location=location,
        )
        beatup.save()

    @staticmethod
    def germinating(data: Dict, context: FormContext):
        from core.models import ItemInventory, ItemType, Item, InventoryAffectorType

        location = context.get_location_type("NURSERY")

        batch = Batch.get_batch(
            data.get("batch_no"), data.get("source_site_id"), data.get("item_id")
        )
        inventory = ItemInventory.get_inventory_by_batch(location, batch)
        inventory.decrease(
            data.get("amount"),
            InventoryAffectorType.GERMINATION,
            source_site=batch.source_site,
        )
        inventory.save()

        old_item = batch.item
        new_item = Item.get_item(
            old_item.title, old_item.species, ItemType.GERMINATED_SEED, old_item.unit
        )
        new_batch = Batch.get_batch(
            data.get("batch_no"), data.get("source_site_id"), new_item.id
        )
        new_inventory = ItemInventory.get_inventory_by_batch(location, new_batch)
        new_inventory.increase(data.get("amount"), InventoryAffectorType.GERMINATION)
        new_inventory.save()

    @staticmethod
    def sowing(data: Dict, context: FormContext):
        from core.models import ItemInventory, ItemType, Item, InventoryAffectorType

        location = context.get_location_type("NURSERY")

        batch = Batch.get_batch(
            data.get("batch_no"), data.get("source_site_id"), data.get("item_id")
        )
        inventory = ItemInventory.get_inventory_by_batch(location, batch)
        inventory.decrease(
            data.get("quantity"),
            InventoryAffectorType.SOWING,
            source_site=batch.source_site,
        )
        inventory.save()

        old_item = batch.item
        new_item = Item.get_item(
            old_item.title, old_item.species, ItemType.SOWED_SEED, old_item.unit
        )
        new_batch = Batch.get_batch(
            data.get("batch_no"), data.get("source_site_id"), new_item.id
        )
        new_inventory = ItemInventory.get_inventory_by_batch(location, new_batch)
        new_inventory.increase(data.get("quantity"), InventoryAffectorType.SOWING)
        new_inventory.save()

    @staticmethod
    def thinning(data: Dict, context: FormContext, thinning_type: str = "LOW"):
        from core.models import ItemInventory, ItemType, Item, InventoryAffectorType

        location = context.get_location_type("SUB_COMPARTMENT")

        if not location:
            raise ValueError("Location not found")

        batch = Batch.objects.filter(
            batch_number=data.get("batch_no"), item__item_type=ItemType.TREE
        )

        if not batch.exists():
            raise ValueError("Batch not found")
        else:
            batch = batch.first()

        product_category = data.pop("product_category")
        product_name = data.pop("product_name")

        new_item = Item.get_product(product_name, batch.item.species, product_category)
        new_item.stock_code = data.get("stock_code", None)
        new_item.code_single = data.get("code_single", None)
        new_item.length = data.get("length", None)
        new_item.bottom_diameter = data.get("bottom_diameter", None)
        new_item.top_diameter = data.get("top_diameter", None)
        new_item.middle_diameter = data.get("middle_diameter", None)
        new_item.save()

        new_batch = Batch.get_batch(
            batch.batch_number, batch.source_site.id, new_item.id
        )

        inventory = ItemInventory.get_inventory_by_batch(location, new_batch)
        inventory.increase(
            data.get("amount"),
            InventoryAffectorType.THINNING,
            source_site=batch.source_site,
        )
        inventory.save()

        thinning = Thinning(
            batch=new_batch,
            amount=data.get("amount"),
            location=location,
            product_category=product_category,
            thinning_type=thinning_type,
            voucher_no=data.get("voucher_no"),
            date=data.get("date"),
        )
        thinning.save()

    @staticmethod
    def sale_coppice(data: Dict, context: FormContext):
        location = context.get_location_type("SUB_COMPARTMENT")

        if not location:
            raise ValueError("Location not found")

        batch = Batch.get_batch_by_item(data.get("batch_no"), data.get("item_id"))

        inventory = ItemInventory.get_inventory_by_batch(location, batch)
        inventory.decrease(
            data.get("amount"),
            InventoryAffectorType.COPPICE_SALE,
            location,
            batch.source_site,
        )
        inventory.save()

        coppice_sale = ThinningSale(
            batch=batch,
            date=data.get("date"),
            sold_to_id=data.get("sold_to_id"),
            sold_by=data.get("sold_by"),
            amount=data.get("amount"),
            product_category=batch.item.product_type,
            voucher_no=data.get("voucher_no"),
            sale_type=ThinningSaleType.COPPICE,
            unit_price=data.get("unit_price"),
            location=context.location,
            total_rev_before_vat=data.get("total_price_before_vat"),
        )
        coppice_sale.save()

    @staticmethod
    def sale_thinning(data: Dict, context: FormContext):
        location = context.get_location_type("SUB_COMPARTMENT")

        if not location:
            raise ValueError("Location not found")

        batch = Batch.get_batch_by_item(data.get("batch_no"), data.get("item_id"))

        inventory = ItemInventory.get_inventory_by_batch(location, batch)
        inventory.decrease(
            data.get("amount"),
            InventoryAffectorType.THINNING_SALE,
            location,
            batch.source_site,
        )
        inventory.save()

        thinning_sale = ThinningSale(
            batch=batch,
            date=data.get("date"),
            sold_to_id=data.get("sold_to_id"),
            sold_by=data.get("sold_by"),
            amount=data.get("amount"),
            product_category=batch.item.product_type,
            voucher_no=data.get("voucher_no"),
            sale_type=ThinningSaleType.THINNING,
            unit_price=data.get("unit_price"),
            location=context.location,
            total_rev_before_vat=data.get("total_price_before_vat"),
        )
        thinning_sale.save()

    @staticmethod
    def operational_inventory(data: Dict, context: FormContext):
        from core.models import OperationalForestInventory

        inventory = OperationalForestInventory(**data, location=context.location)
        inventory.save()

    @staticmethod
    def dawn_time(data: Dict, context: FormContext):
        location = context.get_location_type("SUB_COMPARTMENT")
        down_time = DownTime(**data, location=location)
        down_time.save()

    @staticmethod
    def job_creation(data: Dict, context: FormContext):
        job_creation = JobOportunity(**data, location=context.location)
        job_creation.save()

    @staticmethod
    def depo_factory_input(data: Dict, context: FormContext):
        batch = Batch.get_batch_by_item(data.pop("batch_no"), data.get("item_id"))

        transportation = ItemTransportation(**data, to_location=context.location)
        transportation.save()

        inventory = ItemInventory.get_inventory_by_batch(context.location, batch)
        inventory.decrease(transportation.amount, InventoryAffectorType.TRANSPORT)
        inventory.save()

    @staticmethod
    def factory_daily_production(data: Dict, context: FormContext):
        report = FactoryProductionReport(**data, location=context.location)
        report.save()

    @staticmethod
    def lumber_stored(data: Dict, context: FormContext):
        batch = Batch.objects.get(pk=data.pop("batch_id"))

        new_item = Item.get_product(
            batch.item.title, batch.item.species, ProductType.LUMBER
        )
        new_item.stock_code = data.pop("stock_code", None)
        new_item.code_single = data.pop("code_single", None)
        new_item.length = data.pop("length", None)
        new_item.bottom_diameter = data.pop("bottom_diameter", None)
        new_item.top_diameter = data.pop("top_diameter", None)
        new_item.middle_diameter = data.pop("middle_diameter", None)
        new_item.save()

        new_batch = Batch.get_batch(
            batch.batch_number, batch.source_site.id, new_item.id
        )

        stored_lumber = LumberStoredReport(
            **data, batch=new_batch, location=context.location
        )
        stored_lumber.save()

        inventory = ItemInventory.get_inventory_by_batch(context.location, new_batch)
        inventory.increase(stored_lumber.amount, InventoryAffectorType.RECIEVE)
        inventory.save()

    @staticmethod
    def forest_inventory(data: Dict, context: FormContext):
        forest_inventory = ForestInventoryReport(**data, location=context.location)
        forest_inventory.save()

        batch = Batch.objects.get(pk=data.get("batch_id"))

        inventory = ItemInventory.get_inventory_by_batch(context.location, batch)
        inventory.set_amount(
            forest_inventory.amount, InventoryAffectorType.FOREST_INVENTORY
        )
        inventory.save()

    @staticmethod
    def get_callback(form_name: str):
        match form_name:
            case "SeedPurchaseDetailsForm" | "BranchPurchaseDetailsForm":
                return FormCallbackMapper().purchase
            case "SeedSourceBranchTransportForm":
                return FormCallbackMapper().empty_transportation
            case "TransportLogsForm" | "NurserySubCompartmentTransportForm":
                return FormCallbackMapper().transportation
            case "BranchHQTransportForm":
                return FormCallbackMapper().branch_hq_transportation
            case "HQNurserySeedTransportationForm":
                return FormCallbackMapper().hq_nursery_transportation
            case "FirewoodCustomerTransportForm":
                return FormCallbackMapper().firewood_transportation
            case "LogProductionSawmillTransportForm":
                return FormCallbackMapper().sawmill_transportation
            case "Test1" | "Test2" | "Test3" | "QuarantineTesting":
                return lambda d, ctx: FormCallbackMapper().test_form(d, form_name, ctx)
            case "SeedSaleForm":
                return FormCallbackMapper().hq_seed_sale
            case "SaleEachProductForm":
                return FormCallbackMapper().harvesting_sale
            case "SaleDifferentProduct":
                return FormCallbackMapper().sale_diff_product
            case "StampageSaleForm":
                return FormCallbackMapper().stampage_sale
            case "SeedlingNurserySale":
                return FormCallbackMapper().nursery_seedling_sale
            case "HQSeedReceivingForm":
                return FormCallbackMapper().hq_receive
            case "SeedBranchReceivingForm":
                return FormCallbackMapper().branch_receive
            case "SeedlingReceivingForm":
                return FormCallbackMapper().empty_receive
            case "NurserySeedReceivingForm":
                return FormCallbackMapper().nursery_receive
            case "LogReceivingForm":
                return FormCallbackMapper().log_receive
            case "GradingForm":
                return FormCallbackMapper().grading
            case "GiveAwayForm":
                return FormCallbackMapper().giveaway
            case "RegisterProductForm":
                return FormCallbackMapper().register_product
            case "TimelyHarvestingForm":
                return FormCallbackMapper().timely_harvesting
            case "SurvivalCountForm":
                return FormCallbackMapper().survival_count
            case "SowingForm":
                return FormCallbackMapper().sowing
            case "GerminatedSeedForm":
                return FormCallbackMapper().germinating
            case "HandoffForm":
                return FormCallbackMapper().handoff
            case "BeatupForm":
                return FormCallbackMapper().beatup
            case "LowThinningForm":
                return lambda d, ctx: FormCallbackMapper().thinning(d, ctx, "LOW")
            case "HighThinningForm":
                return lambda d, ctx: FormCallbackMapper().thinning(d, ctx, "HIGH")
            case "PreCommercialCoppiceSinglingForm":
                return lambda d, ctx: FormCallbackMapper().thinning(
                    d, ctx, "PRE_COMMERCIAL"
                )
            case "CommercialSinglingForm":
                return lambda d, ctx: FormCallbackMapper().thinning(
                    d, ctx, "COMMERCIAL"
                )
            case "SaleCoppiceForm":
                return FormCallbackMapper().sale_coppice
            case "SaleThinningForm":
                return FormCallbackMapper().sale_thinning
            case "OperationalForestInventoryForm":
                return FormCallbackMapper().operational_inventory
            case "DownTimeForm":
                return FormCallbackMapper().dawn_time
            case "JobOpportunityForm":
                return FormCallbackMapper().job_creation
            case "DepoFactoryInputForm":
                return FormCallbackMapper().depo_factory_input
            case "FactoryDailyProductionForm":
                return FormCallbackMapper().factory_daily_production
            case "LumberStoredForm":
                return FormCallbackMapper().lumber_stored
            case "ForestInventoryForm":
                return FormCallbackMapper().forest_inventory
            case _:
                return None

    @staticmethod
    def on_submit(form, user: AfeUser):
        callback = FormCallbackMapper.get_callback(form.name)

        if not callback:
            return None

        form_context = FormContext(form, user)
        form_data = remove_empty(form.data)
        form_data["createdBy_id"] = str(user.id)

        @functools.wraps(callback)
        def wrapper():
            try:
                callback(form_data, form_context)
            except Exception as e:
                logger.error(f"Error processing form {form.name}: {e}", exc_info=True)
                return False
            else:
                form.is_processed = True
                form.save()
                return True

        return wrapper
