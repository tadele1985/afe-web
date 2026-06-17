from django.views.generic import UpdateView
from django_tables2 import SingleTableMixin, SingleTableView, Column
from core.models import AfeUser, Role, UserRole
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages import success
from core.forms import FilterForm, UserForm
from django_filters import FilterSet
from django_filters.views import FilterView
import django_tables2 as tables
from django.middleware import csrf
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.http import JsonResponse
from core.decorators import role_required
from django.utils.decorators import method_decorator

from core.utils import htmx_redirect


class UserTable(tables.Table):
    username = tables.Column(accessor="username", verbose_name="Username")
    first_name = tables.Column(accessor="first_name", verbose_name="First Name")
    middle_name = tables.Column(accessor="middle_name", verbose_name="Middle Name")
    last_name = tables.Column(accessor="last_name", verbose_name="Last Name")
    user_role = tables.Column(accessor="id", verbose_name="Role")
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = AfeUser
        template_name = "base-table.html"
        fields = ["username", "first_name", "middle_name", "last_name", "location"]
        exclude = ["password"]
        attrs = {"class": "table"}
        sequence = ("username", "first_name", "middle_name", "last_name", "location")
        order_by = 'username'

    def render_user_role(self, value):
        try:
            return UserRole.objects.get(user__id=value).role.name
        except Exception:
            return "—"

    def render_actions(self, value):
        csrf_token = csrf.get_token(self.request)
        user_form = UserForm(initial={"id": value})
        user = AfeUser.objects.get(id=value)
        return render_to_string(
            "partials/users-action.html",
            {"id": value, "csrf_token": csrf_token, "form": user_form, "user": user},
        )


class UserFilter(FilterSet):
    class Meta:
        model = AfeUser
        fields = {
            "username": ["exact"],
        }
        fields = ["username"]
        form = FilterForm


@method_decorator(login_required, name="dispatch")
@method_decorator(role_required(["SYSTEM_ADMINISTRATOR"]), name="dispatch")
class UserListView(SingleTableMixin, FilterView):
    model = AfeUser
    table_class = UserTable
    template_name = "core/user_management/user_list.html"
    filterset_class = UserFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = UserForm()
        context["page"] = "User/staff management"
        return context


@login_required
@role_required(["SYSTEM_ADMINISTRATOR"])
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User created successfully.")
            response = JsonResponse({})
            response["HX-Redirect"] = reverse_lazy("core:users")
            return response
    else:
        form = UserForm()
    return render(request, "core/user_management/user_create.html", {"form": form})


@method_decorator(role_required(["SYSTEM_ADMINISTRATOR"]), name="dispatch")
class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = AfeUser
    form = UserForm
    template_name = "core/user_management/user_update.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "User updated successfully")
        return htmx_redirect(self.request, reverse_lazy("core:users"))


@login_required
@role_required(["SYSTEM_ADMINISTRATOR"])
def user_update(request, pk):
    user = AfeUser.objects.get(id=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User updated successfully.")
            response = JsonResponse({})
            response["HX-Redirect"] = reverse_lazy("core:users")
            return response
    else:
        form = UserForm(None, instance=user)
    return render(request, "core/user_management/user_update.html", {"form": form})


@login_required
@role_required(["SYSTEM_ADMINISTRATOR"])
def user_delete(request, pk):
    user = AfeUser.objects.get(pk=pk)
    if request.method == "POST":
        user.delete()
        success(request, f'User "{user.username}" deleted successfully.')
        return redirect("users:user_list")
    return render(request, "users/user_delete.html", {"user": user})


@login_required
@role_required(["SYSTEM_ADMINISTRATOR"])
def user_disable(request, pk):
    user = AfeUser.objects.get(id=pk)
    if request.method == "POST":
        user.is_active = False
        user.save()
        messages.success(request, f"User successfully disabled.")
        return redirect("core:users")


@login_required
@role_required(["SYSTEM_ADMINISTRATOR"])
def user_enable(request, pk):
    user = AfeUser.objects.get(id=pk)
    if request.method == "POST":
        user.is_active = True
        user.save()
        messages.success(request, f"User successfully enabled.")
        return redirect("core:users")
