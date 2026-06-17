from django_tables2 import SingleTableMixin, SingleTableView, Column
from tomlkit import value
from core.models import AfeUser, Role, UserRole, Customer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.messages import success
from core.forms import FilterForm, CustomerForm
import django_filters
from django_filters import FilterSet
from django_filters.views import FilterView
import django_tables2 as tables
from django.middleware import csrf
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from core.decorators import role_required
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from ethiopian_date import EthiopianDateConverter


class CustomerTable(tables.Table):
    name = tables.Column(accessor="name", verbose_name="Name")
    createdDate = tables.Column(accessor="createdDate", verbose_name="Created At")
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = Customer
        fields = [
            "name",
            "phone_number",
            "createdDate",
            "email",
            "address",
            "tin_number",
        ]
        attrs = {"class": "table"}
        sequence = ("name", "createdDate")

    def render_createdDate(self, value):
     csrf_token = csrf.get_token(self.request)
     customer_form = CustomerForm(initial={"id": value})
     if value:
        year, month, day = EthiopianDateConverter.to_ethiopian(
            value.year,
            value.month,
            value.day
        )

        return f"{day}/{month}/{year}"

     return render_to_string(
            "partials/customer-actions.html",
            {"id": value, "csrf_token": csrf_token, "form": customer_form},
        )
class CustomerFilter(FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains", field_name="name", label="Name"
    )

    class Meta:
        model = Customer
        fields = ["name"]
        form = FilterForm


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
class CustomerListView(SingleTableMixin, FilterView):
    model = Customer
    table_class = CustomerTable  # To be defined later
    template_name = "core/customer_management/customer_list.html"
    filterset_class = CustomerFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CustomerForm()
        context["page"] = "Customers"
        return context


@login_required
@role_required([
    "SYSTEM_ADMINISTRATOR",
    "DATA_ADMINISTRATOR"
  ])
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        id = form.instance.id
        name = request.POST.get('name')
        obj = Customer.objects.filter(name=name).exclude(id=id)

        if obj:
            messages.error(request, _('Customer with that name already exists'))
        elif form.is_valid():
            customer = form.save()
            messages.success(request, "Customer created successfully.")

        response = JsonResponse({})
        response["HX-Redirect"] = reverse_lazy("core:customers")
        return response
    else:
        form = CustomerForm()
    return render(
        request, "core/customer_management/customer_create.html", {"form": form}
    )


@login_required
@method_decorator(
    role_required(
        [
            "SYSTEM_ADMINISTRATOR",
            "DATA_ADMINISTRATOR"
        ]
    ),
    name="dispatch",
)
def customer_update(request, uuid):
    customer = Customer.objects.get(id=uuid)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated successfully.")
            response = JsonResponse({})
            response["HX-Redirect"] = reverse_lazy("core:customers")
            return response
    else:
        form = CustomerForm(None, instance=customer)
    return render(
        request, "core/customer_management/customer_update.html", {"form": form}
    )

@login_required
@role_required([
    "SYSTEM_ADMINISTRATOR",
    "DATA_ADMINISTRATOR"
])
def customer_detail(request, uuid):
    customer = Customer.objects.get(id=uuid)

    context = {
        "customer": customer
    }

    return render(
        request,
        "core/customer_management/customer_list.html",
        context
    )
def render_actions(self, value):
    view_url = reverse("core:customer-detail", args=[value])
    edit_url = reverse("core:customer-update", args=[value])
    delete_url = reverse("core:customer-delete", args=[value])

    return format_html(
        """
        <div class="btn-group">

            <a href="{}" class="btn btn-info btn-sm">View</a>

            <a href="{}" class="btn btn-warning btn-sm">Edit</a>

            <a href="{}" class="btn btn-danger btn-sm">Delete</a>

        </div>
        """,
        view_url,
        edit_url,
        delete_url,
    )
@login_required
@role_required(["SYSTEM_ADMINISTRATOR"])
def customer_delete(request, pk):
    customer = Customer.objects.get(pk=pk)
    if request.method == "POST":
        customer.delete()
        success(request, f'Customer "{customer.name}" deleted successfully.')
        return redirect("core:customers")
    return render(request, "users/customer_delete.html", {"customer": customer})
