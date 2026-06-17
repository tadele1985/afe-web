from core.attachable_forms.form_models import FormField
from core.models import (
    Batch,
    Customer,
    Item,
    ItemTransportation,
    ItemType,
    Location,
    ProductName,
    ProductType,
)


class Components:
    @staticmethod
    def batch_number(multiple=False, **filters):
        def option_callable():
            if not filters:
                return {
                    str(x.batch_number): x.batch_number for x in Batch.objects.all()
                }
            return {
                str(x.batch_number): x.batch_number
                for x in Batch.objects.filter(**filters)
            }

        return FormField(
            label="Batch",
            name="batch_no",
            required=True,
            type="table_select",
            option_callable=option_callable,
            multiple=multiple,
        )

    @staticmethod
    def batch_id(autofill_callable=None, multiple=False, **filters):
        def option_callable():
            if not filters:
                return {str(x.id): x.batch_number for x in Batch.objects.all()}
            return {str(x.id): x.batch_number for x in Batch.objects.filter(**filters)}

        return FormField(
            label="Batch",
            name="batch_id",
            required=True,
            type="table_select",
            option_callable=option_callable,
            autofill_callable=autofill_callable,
            multiple=multiple,
        )

    @staticmethod
    def source_site(multiple=True):
        return FormField(
            label="Seed Source site",
            name="source_site_id",
            type="table_select",
            required=True,
            option_callable=lambda: {
                str(x.id): x.name
                for x in Location.objects.filter(type="SEED_SOURCE")
                .all()
                .order_by("name")
            },
            multiple=multiple,
        )

    @staticmethod
    def voucher_no(required=True):
        return FormField(
            label="Voucher Number",
            name="voucher_no",
            required=required,
            type="number",
        )

    @staticmethod
    def date(multiple=False):
        return FormField(
            label="Date", name="date", required=True, type="date", multiple=multiple
        )

    @staticmethod
    def sold_to(name="sold_to", required=True):
        return FormField(
            label="Sold To",
            name=name + "_id",
            required=required,
            type="table_select",
            option_callable=lambda: {str(x.id): x.name for x in Customer.objects.all()},
        )

    @staticmethod
    def sold_by():
        return FormField(
            label="Sold By",
            name="sold_by",
            required=True,
            type="string",
        )

    @staticmethod
    def amount(label="Amount", multiple=True):
        return FormField(
            label=label,
            name="amount",
            required=True,
            type="float",
            multiple=multiple,
        )

    @staticmethod
    def unit_price_before_vat(multiple=True):
        return FormField(
            label="Unit Price before VAT",
            name="unit_price",
            type="string",
            required=True,
            multiple=multiple,
        )

    @staticmethod
    def unit_price(multiple=True):
        return FormField(
            label="Unit Price",
            name="unit_price",
            type="string",
            required=True,
            multiple=multiple,
        )
    @staticmethod
    def unit():
        return FormField(
            name="unit",
            label="Unit",
            type="string",
            required=True,
            multiple=True
        )
    @staticmethod
    def product(multiple=True, **filters):
        def option_callable():
            if not filters:
                return {
                    str(x.id): str(x.title)
                    for x in Item.objects.filter(item_type=ItemType.PRODUCT)
                }

            return {
                str(x.id): str(x.title)
                for x in Item.objects.filter(item_type=ItemType.PRODUCT).filter(
                    **filters
                )
            }

        return FormField(
            label="Pick Product",
            name="item_id",
            type="table_select",
            required=True,
            option_callable=option_callable,
            multiple=multiple,
        )

    @staticmethod
    def product_name(multiple=True):
        return FormField(
            label="Select Product",
            name="product_name",
            type="select",
            required=True,
            multiple=multiple,
            options={str(x[0]): str(x[1]) for x in ProductName.choices},
        )

    @staticmethod
    def product_category(multiple=True):
        return FormField(
            label="Select Product Category",
            name="product_category",
            type="select",
            required=True,
            multiple=multiple,
            options={str(x[0]): str(x[1]) for x in ProductType.choices},
        )

    @staticmethod
    def item(label="Item", multiple=False, **filters):
        def option_callable():
            if not filters:
                return {str(x.id): str(x.species) for x in Item.objects.all()}

            return {str(x.id): str(x.species) for x in Item.objects.filter(**filters)}

        return FormField(
            label=label,
            name="item_id",
            type="table_select",
            required=True,
            option_callable=option_callable,
            multiple=multiple,
        )

    @staticmethod
    def incoming_transport(
        autofill_callable, required=False, exclude_empty_batch=True, **filters
    ):
        return FormField(
            label="Incoming Transport",
            name="received_transportation_id",
            required=required,
            type="table_select",
            option_callable=lambda: {
                str(
                    x.id
                ): f"{x.voucher_no} - {x.from_location.name} -> {x.to_location.name}: {x.amount}"
                for x in ItemTransportation.get_by_distinct_voucher(
                    **filters,
                    itemrecieve__isnull=True,
                    exclude_empty_batch=exclude_empty_batch,
                )
            },
            autofill_callable=autofill_callable,
        )

    @staticmethod
    def polygon_name():
        return FormField(
            label="Polygon Name", name="polygon_name", type="string", required=True
        )

    @staticmethod
    def centroid_location():
        return FormField(
            label="Centroid Location",
            name="polygon_centroid_location",
            type="float",
            required=True,
        )

    @staticmethod
    def from_location(location_type):
        return FormField(
            label="From",
            name="from_location_id",
            type="table_select",
            required=True,
            option_callable=lambda: {
                str(x.id): x.name
                for x in Location.objects.filter(type=location_type)
                .all()
                .order_by("name")
            },
        )

    @staticmethod
    def to_location(location_type):
        return FormField(
            label="To",
            name="to_location_id",
            type="table_select",
            required=True,
            option_callable=lambda: {
                str(x.id): x.name
                for x in Location.objects.filter(type=location_type)
                .all()
                .order_by("name")
            },
        )

    @staticmethod
    def driver_name(label="Driver"):
        return FormField(
            label=label,
            name="driver_name",
            type="string",
            required=True,
        )

    @staticmethod
    def plate_number(label="Truck Plate Number"):
        return FormField(
            label=label,
            name="plate_number",
            type="string",
            required=True,
        )

    @staticmethod
    def stock_code(multiple=True):
        return FormField(
            label="Stock Code",
            name="stock_code",
            type="string",
            required=False,
            multiple=multiple,
        )

    @staticmethod
    def code_single(multiple=True):
        return FormField(
            label="Code Single",
            name="code_single",
            type="string",
            required=False,
            multiple=multiple,
        )

    @staticmethod
    def length(multiple=True):
        return FormField(
            label="Length",
            name="length",
            type="float",
            required=False,
            multiple=multiple,
        )

    @staticmethod
    def bottom_diameter(multiple=True):
        return FormField(
            label="Bottom Diameter",
            name="bottom_diameter",
            type="float",
            required=False,
            multiple=multiple,
        )

    @staticmethod
    def top_diameter(multiple=True):
        return FormField(
            label="Top Diameter",
            name="top_diameter",
            type="float",
            required=False,
            multiple=multiple,
        )

    @staticmethod
    def middle_diameter(multiple=True):
        return FormField(
            label="Middle Diameter",
            name="middle_diameter",
            type="float",
            required=False,
            multiple=multiple,
        )

    @staticmethod
    def start_date(required=True):
        return FormField(
            label="Start Date", name="start_date", type="date", required=required
        )

    @staticmethod
    def end_date(required=True):
        return FormField(
            label="End Date", name="end_date", type="date", required=required
        )
