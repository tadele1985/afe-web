from dataclasses import dataclass
from typing import Dict
from django.contrib.auth.decorators import login_required
import re
from datetime import datetime, timedelta
from ethiopian_date import EthiopianDateConverter
from typing import Union
from django.db.models import F, QuerySet, Sum
from django import forms
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from render_block import render_block_to_string
import django_filters
from core.decorators import role_required


from core.forms import FilterForm
from core.models import (
    ActivityPlan,
    DetailActivity,
    ItemInventory,
    ItemInventoryLog,
    ItemSale,
    ItemType,
    Location,
    OperationType,
    ProductName,
    ProductType,
    LOCATION_TYPE_CHOICES,
    ThinningSale,
)


@role_required(["SYSTEM_ADMINISTRATOR", "DATA_ADMINISTRATOR", "DATA_ANALYST", "BRANCH_DATA_ADMINISTRATOR", "BRANCH_DATA_ANALYST"])
@login_required
def stock_report(request: HttpRequest):
    current_year = None
    try:
        current_year = int(request.GET.get("year", datetime.today().year))
    except Exception:
        current_year = datetime.today().year

    location = request.GET.get("location", None)
    if location == "":
        location = None

    months = [
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
        
    ]

    products = []
    for product in ProductType:
        month_data = []
        for i, month in enumerate(months):
            cur_month_data = {}
            current_datetime = datetime(current_year, i + 1, 1)
            if i < 11:
                end_of_month = datetime(current_year, i + 2, 1)
            else:
                end_of_month = datetime(current_year, 1, 1)

            beginning_balance_filters = dict(
                date__lt=current_datetime, inventory__item__product_type=product
            )
            if location is not None:
                beginning_balance_filters["inventory__location_id"] = location
            inventory_log = ItemInventoryLog.objects.filter(
                **beginning_balance_filters
            ).order_by("-date")

            if not inventory_log.exists():
                cur_month_data["beginning_balance"] = 0
            else:
                last_logs: Dict[str, ItemInventoryLog] = {}
                for log in inventory_log:
                    if (
                        log.inventory.id not in last_logs
                        or log.date > last_logs[log.inventory.id].date
                    ):
                        last_logs[log.inventory.id] = log

                cur_month_data["beginning_balance"] = sum(
                    log.amount_after_transaction for log in last_logs.values()
                )

            production_filters = {
                "date__gte": current_datetime,
                "date__lt": end_of_month,
                "inventory__item__product_type": product,
                "amount_before_transaction__lt": F("amount_after_transaction"),
            }
            if location is not None:
                production_filters["inventory__location_id"] = location

            if i == 10 and product == ProductType.TRANSMISSION_POLE:
                ps = ItemInventoryLog.objects.filter(**production_filters)
                print(list(map(lambda x: x.id, ps)))
                print("Length produced: ", len(ps))
                x = 0
                for p in ps:
                    x += p.amount_after_transaction - p.amount_before_transaction
                    print(
                        "Produced: ",
                        p.amount_after_transaction - p.amount_before_transaction,
                        p.id,
                        p.inventory.id,
                        p.amount_after_transaction,
                        p.date,
                    )
                print(x)
            production = ItemInventoryLog.objects.filter(
                **production_filters
            ).aggregate(
                production=Sum(
                    F("amount_after_transaction") - F("amount_before_transaction")
                )
            )["production"]
            if not production:
                production = 0

            sold_filters = dict(
                date__gte=current_datetime,
                date__lt=end_of_month,
                inventory__item__product_type=product,
                amount_before_transaction__gte=F("amount_after_transaction"),
            )
            if location is not None:
                sold_filters["inventory__location_id"] = location

            if i == 10 and product == ProductType.TRANSMISSION_POLE:
                ps = ItemInventoryLog.objects.filter(**sold_filters)
                print("Length sold: ", len(ps))
                print(list(map(lambda x: x.id, ps)))
                x = 0
                for p in ps:
                    x += p.amount_before_transaction - p.amount_after_transaction
                    print(
                        "Sold: ",
                        p.amount_before_transaction - p.amount_after_transaction,
                        p.id,
                        p.inventory.id,
                        p.amount_after_transaction,
                        p.date,
                    )
                print(x)
            sold = ItemInventoryLog.objects.filter(**sold_filters).aggregate(
                sold=Sum(F("amount_before_transaction") - F("amount_after_transaction"))
            )["sold"]
            if not sold:
                sold = 0
            cur_month_data["production"] = production
            cur_month_data["sold"] = sold
            cur_month_data["net_balance"] = production - sold
            if i == 10 and product == ProductType.TRANSMISSION_POLE:
                last_logs: Dict[str, ItemInventoryLog] = {}
                logs = ItemInventoryLog.objects.filter(
                    date__lt=datetime(current_year, i + 2, 1),
                    inventory__item__product_type=product,
                ).order_by("-date")
                print("Length after filter: ", len(logs))
                print(list(map(lambda x: x.id, logs)))
                for log in logs:
                    if log.inventory.id not in last_logs:
                        last_logs[log.inventory.id] = log
                print(last_logs)
                print(sum([log.amount_after_transaction for log in last_logs.values()]))
            month_data.append(cur_month_data)

        product_data = {"name": product.label, "month_data": month_data}
        products.append(product_data)

    total_by_product = []
    for product in products:
        total_by_product.append(
            {
                "name": product["name"],
                "beginning_balance": sum(
                    [x["beginning_balance"] for x in product["month_data"]]
                ),
                "production": sum([x["production"] for x in product["month_data"]]),
                "sold": sum([x["sold"] for x in product["month_data"]]),
                "net_balance": sum([x["net_balance"] for x in product["month_data"]]),
            }
        )

    for i, product in enumerate(products):
        product["total"] = total_by_product[i]

    total_by_product_by_month = []
    for i, _ in enumerate(months):
        total_begging_balance = 0
        total_production = 0
        total_sold = 0
        total_net_balance = 0
        for product in products:
            total_begging_balance += product["month_data"][i]["beginning_balance"]
            total_production += product["month_data"][i]["production"]
            total_sold += product["month_data"][i]["sold"]
            total_net_balance += product["month_data"][i]["net_balance"]

        total_by_product_by_month.append(
            {
                "beginning_balance": total_begging_balance,
                "production": total_production,
                "sold": total_sold,
                "net_balance": total_net_balance,
            }
        )
    total_by_product_by_month.append(
        {
            "beginning_balance": sum(
                [x["beginning_balance"] for x in total_by_product]
            ),
            "production": sum([x["production"] for x in total_by_product]),
            "sold": sum([x["sold"] for x in total_by_product]),
            "net_balance": sum([x["net_balance"] for x in total_by_product]),
        }
    )

    context_data = {
        "months": months,
        "products": products,
        "total_by_product": total_by_product,
        "total_by_product_by_month": total_by_product_by_month,
        "current_year": current_year,
        "locations": Location.objects.all(),
        "selected_location": location,
        "page": "Stock Balance Report",
    }
    if request.htmx:
        html = render_block_to_string(
            "core/stock_balance_report.html",
            "table",
            context_data,
            request,
        )
        return HttpResponse(html, content_type="text/html")

    return render(
        request,
        "core/stock_balance_report.html",
        context=context_data,
    )


def get_income_by_month(sales: QuerySet):
    pass


class ItemSaleFilter(django_filters.FilterSet):
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
        model = ItemSale
        fields = ["location"]
        form = FilterForm


class ThinningSaleFilter(django_filters.FilterSet):
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
        model = ThinningSale
        fields = ["location"]
        form = FilterForm


@dataclass
class TaskDataRow:
    name: str
    todo_tasks: int
    in_progress_tasks: int
    done_tasks: int
    completion_percentage: int
    children: list

    @property
    def codified_name(self):
        snake_case = re.sub(r"[^a-zA-Z0-9_]+", "_", self.name)
        snake_case = snake_case.lower()
        return snake_case


def get_task_data(location_type=None, location=None, sector=None):
    filters = {}
    activity_plan_filters = {}
    if location_type:
        filters["activity_plan__operation_plan__location__type"] = location_type
        activity_plan_filters["operation_plan__location__type"] = location_type

    if location:
        filters["activity_plan__operation_plan__location_id"] = location
        activity_plan_filters["operation_plan__location_id"] = location

    operation_types: Union[OperationType, None] = None
    if sector:
        operation_types = OperationType.objects.filter(sectors__in=[sector])
    else:
        operation_types = OperationType.objects.all()

    final_data: list[TaskDataRow] = []
    aggregate_info = {
        "Total detail activities": 0,
        "In To do": 0,
        "In Progress": 0,
        "Done": 0,
    }
    month_data_aggregate_info = {"in_todo": 0, "in_progress": 0, "done": 0}

    month_data = {
        "January": month_data_aggregate_info.copy(),
        "February": month_data_aggregate_info.copy(),
        "March": month_data_aggregate_info.copy(),
        "April": month_data_aggregate_info.copy(),
        "May": month_data_aggregate_info.copy(),
        "June": month_data_aggregate_info.copy(),
        "July": month_data_aggregate_info.copy(),
        "August": month_data_aggregate_info.copy(),
        "September": month_data_aggregate_info.copy(),
        "October": month_data_aggregate_info.copy(),
        "November": month_data_aggregate_info.copy(),
        "December": month_data_aggregate_info.copy(),
    }
    for operation_type in operation_types:
        data = TaskDataRow(
            name=operation_type.name,
            todo_tasks=0,
            in_progress_tasks=0,
            done_tasks=0,
            completion_percentage=0,
            children=[],
        )

        tasks = DetailActivity.objects.filter(
            **filters, activity_plan__operation_plan__operation_type=operation_type
        )
        aggregate_info["Total detail activities"] += tasks.count()
        data.todo_tasks = tasks.filter(status="TODO").count()
        aggregate_info["In To do"] += data.todo_tasks
        data.in_progress_tasks = tasks.filter(status="STARTED").count()
        aggregate_info["In Progress"] += data.in_progress_tasks
        data.done_tasks = tasks.filter(status="COMPLETED").count()
        aggregate_info["Done"] += data.done_tasks
        if data.todo_tasks == 0:
            data.completion_percentage = 0
        else:
            percentage = (data.done_tasks / data.todo_tasks) * 100
            data.completion_percentage = round(percentage, 2)

        for task in tasks:
            month = task.start_date.strftime("%B")
            if task.status == "TODO":
                month_data[month]["in_todo"] += 1
            if task.status == "STARTED":
                month_data[month]["in_progress"] += 1
            if task.status == "COMPLETED":
                month_data[month]["done"] += 1

        activity_plans = ActivityPlan.objects.filter(
            operation_plan__operation_type=operation_type,
            **activity_plan_filters,
            type__isnull=False,
        )
        distinct_activity_types = activity_plans.values_list(
            "type__id", "type__name"
        ).distinct()
        for activity_type in distinct_activity_types:
            activity_id = activity_type[0]
            activity_name = activity_type[1]

            activity_data = TaskDataRow(
                name=activity_name,
                todo_tasks=0,
                in_progress_tasks=0,
                done_tasks=0,
                completion_percentage=0,
                children=[],
            )

            for activity_plan in activity_plans.filter(type_id=activity_id):
                tasks = activity_plan.activity_detail
                activity_data.todo_tasks = activity_data.todo_tasks + tasks.count()
                activity_data.in_progress_tasks = (
                    activity_data.in_progress_tasks
                    + tasks.filter(status="STARTED").count()
                )
                activity_data.done_tasks = (
                    activity_data.done_tasks + tasks.filter(status="COMPLETED").count()
                )
            activity_data.completion_percentage = (
                (activity_data.done_tasks / activity_data.todo_tasks) * 100
                if activity_data.todo_tasks > 0
                else 0
            )
            data.children.append(activity_data)
        final_data.append(data)

    aggregate_info["Completion rate"] = (
        round((aggregate_info["Done"] / aggregate_info["In To do"]) * 100, 2)
        if aggregate_info["In To do"] > 0
        else 0
    )
    return {
        "aggregate_info": aggregate_info,
        "month_aggregate_info": month_data,
        "activity_performance": final_data,
    }


def get_income_data(
    start_date,
    end_date,
    location_type=None,
    location=None,
    time_interval="week",
):
    filters = {
        "date__gte": start_date,
        "date__lte": end_date,
    }
    filters = {}
    if location_type:
        filters["location__type"] = location_type

    if location:
        filters["location_id"] = location

    product_sales_data = {}
    sales = ItemSale.objects.filter(**filters)
    thinning_sales = ThinningSale.objects.filter(**filters)
    for product_category in ProductType:
        product_sales = sales.filter(item__product_type=product_category)
        product_thinning_sales = thinning_sales.filter(
            product_category=product_category
        )
        month_income = {
            "January": 0,
            "February": 0,
            "March": 0,
            "April": 0,
            "May": 0,
            "June": 0,
            "July": 0,
            "August": 0,
            "September": 0,
            "October": 0,
            "November": 0,
            "December": 0,
        }
        for sale in product_sales:
            if sale.date:
                month = sale.date.strftime("%B")
            else:
                month = sale.updatedDate.strftime("%B")
            if month not in month_income:
                month_income[month] = 0
            if not sale.amount:
                continue
            price = None
            if sale.unit_price:
                try:
                    price = float(sale.unit_price)
                except ValueError:
                    continue
            elif sale.sale_price:
                price = sale.sale_price
            else:
                continue
            month_income[month] += sale.amount * price

        for sale in product_thinning_sales:
            if sale.date:
                month = sale.date.strftime("%B")
            else:
                month = sale.updatedDate.strftime("%B")
            if month not in month_income:
                month_income[month] = 0
            if not sale.amount:
                continue
            price = None
            if sale.unit_price:
                try:
                    price = float(sale.unit_price)
                except ValueError:
                    continue
            else:
                continue
            month_income[month] += sale.amount * price

        product_sales_data[product_category] = month_income

    return product_sales_data


class DashboardTopForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label="Location",
        widget=forms.Select(attrs={"class": "select select-bordered select-sm"}),
    )
    start_date = forms.CharField(  # ← CharField, not DateField
        label="Start Date",
        widget=forms.TextInput(attrs={
            "class": "input input-bordered",
            "placeholder": "YYYY-MM-DD (Ethiopian)",
        }),
    )
    end_date = forms.CharField(  # ← CharField, not DateField
        label="End Date",
        widget=forms.TextInput(attrs={
            "class": "input input-bordered",
            "placeholder": "YYYY-MM-DD (Ethiopian)",
        }),
    )
    location_type = forms.ChoiceField(
        choices=LOCATION_TYPE_CHOICES,
        required=False,
        label="Location Type",
        widget=forms.Select(attrs={"class": "select select-bordered select-sm"}),
    )
def to_ethiopian(gregorian_date):
    """Convert a Gregorian date to Ethiopian calendar."""
    if isinstance(gregorian_date, str):
        gregorian_date = datetime.strptime(gregorian_date, "%Y-%m-%d")
    
    eth = EthiopianDateConverter.to_ethiopian(
        gregorian_date.year,
        gregorian_date.month,
        gregorian_date.day
    )
    # Returns (year, month, day) tuple
    return f"{eth[0]}-{eth[1]:02d}-{eth[2]:02d}"

def to_gregorian(ethiopian_date_str):
    """Convert an Ethiopian calendar date string to Gregorian."""
    year, month, day = map(int, ethiopian_date_str.split("-"))
    greg = EthiopianDateConverter.to_gregorian(year, month, day)
    # greg is already a datetime.date object, just wrap it in datetime
    return datetime(greg.year, greg.month, greg.day)
def get_ethiopian_today():
    today = datetime.now()
    eth = EthiopianDateConverter.to_ethiopian(today.year, today.month, today.day)
    return f"{eth[0]}-{eth[1]:02d}-{eth[2]:02d}"


@login_required
def dashboard(request: HttpRequest):
    product_name = request.GET.get("product_name", ProductName.LUMBER_1)
    sector = request.GET.get("sector", None)
    location_type = request.GET.get("location_type", None)
    location = request.GET.get("location", None)

    default_start_eth = to_ethiopian(datetime.now() - timedelta(days=365))
    default_end_eth = get_ethiopian_today()  # ← Always Ethiopian today

    start_date_eth = request.GET.get("start_date", default_start_eth)
    end_date_eth = request.GET.get("end_date", default_end_eth)

    # Fallback if empty string is passed
    if not start_date_eth:
        start_date_eth = default_start_eth
    if not end_date_eth:
        end_date_eth = default_end_eth

    try:
        start_date = to_gregorian(start_date_eth)
    except Exception:
        start_date_eth = default_start_eth
        start_date = to_gregorian(start_date_eth)

    try:
        end_date = to_gregorian(end_date_eth)
    except Exception:
        end_date_eth = default_end_eth
        end_date = to_gregorian(end_date_eth)

    income_data = get_income_data(start_date, end_date, location_type, location)

    form = DashboardTopForm(
        initial={
            "start_date": start_date_eth,
            "end_date": end_date_eth,
            "location": location,
            "location_type": location_type,
        }
    )

    inventories = ItemInventory.objects.filter(
        item__item_type=ItemType.PRODUCT, item__title=product_name
    )

    # prepare some data
    location_names = [
        f"{inventory.location.name} - {inventory.location.type}"
        for inventory in inventories
    ]
    inventory_amounts = [inventory.amount for inventory in inventories]

    sales = []
    for inventory in inventories:
        sale = ItemSale.objects.filter(
            item=inventory.item, location=inventory.location, batch=inventory.batch
        ).aggregate(total=Sum("amount"))["total"]
        sales.append(sale)
        thinning_sale = ThinningSale.objects.filter(
            batch__item=inventory.item,
            location=inventory.location,
            batch=inventory.batch,
        ).aggregate(total=Sum("amount"))["total"]
        sales.append(thinning_sale)

    tmp = get_task_data(location_type, location, sector)
    performance_aggregate_info = tmp["aggregate_info"]
    month_aggregate_info = tmp["month_aggregate_info"]
    activity_performance = tmp["activity_performance"]

    context = {
        "page": "Dashboard",
        "location_names": location_names,
        "inventory_amounts": inventory_amounts,
        "sales": sales,
        "selected_product_name": product_name,
        "product_names": [x.label for x in ProductName],
        "activity_performance": activity_performance,
        "aggregate_performance": performance_aggregate_info,
        "income_data": income_data,
        "months": [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        "start_date": start_date,
        "end_date": end_date,
        "form": form,
        "month_aggregate_info": month_aggregate_info,
    }

    return render(request, "core/dashboard.html", context=context)
