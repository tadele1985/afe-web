from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django_htmx.http import HttpResponseClientRedirect, retarget
from django.contrib.messages import success
from django.urls import reverse_lazy
from core.forms import UserGroupForm


@login_required
def role_permission(request):
    groups = Group.objects.all().order_by("id")
    return render(
        request,
        "core/role_permissions/role_permission.html",
        context={"groups": groups, "page": "Role/Permisssions management"},
    )


@login_required
def edit_role_permissions(request, id):
    group = Group.objects.get(id=id)
    if request.method == "POST":
        form = UserGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            success(request, f"Group updated successfully.")
        return redirect("core:role_permission")
    else:
        return render(
            request,
            "core/role_permissions/edit_role_permissions.html",
            {"group": group, "form": UserGroupForm(instance=group)},
        )


@login_required()
def fetch_permission(request):
    search = request.GET.get("search", "")
    selected_permissions = request.GET.get("permissions", "")
    content_type_id = Permission.objects.get(codename="admin").content_type_id
    if selected_permissions != "":
        permissions = [
            model_to_dict(permission)
            for permission in Permission.objects.filter(
                name__icontains=search, content_type_id=content_type_id
            ).exclude(id__in=selected_permissions.split(";"))[0:9]
        ]
    else:
        permissions = [
            model_to_dict(permission)
            for permission in Permission.objects.filter(
                name__icontains=search, content_type_id=content_type_id
            )[0:9]
        ]

    return JsonResponse(permissions, safe=False)


@login_required
def add_permissions_to_group(request):
    group = Group.objects.get(id=request.GET.get("group", ""))
    permissions = request.GET.get("permissions", "").split(";")
    for permission in permissions:
        group.permissions.add(Permission.objects.get(id=permission))

    return JsonResponse({}, safe=False)


@login_required
def remove_permissions_to_group(request):
    group = Group.objects.get(id=request.GET.get("group", ""))
    permission = request.GET.get("permission", "")
    group.permissions.remove(Permission.objects.get(id=permission))

    return JsonResponse({}, safe=False)


@login_required
def add_group_modal(request):
    return render(request, "core/role_permissions/add_group_modal.html")


@login_required
def add_group(request):
    name = request.POST.get("name", "")
    group = Group.objects.create(name=name)
    success(request, f'Group "{group.name}" created successfully.')
    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def delete_group(request, id):
    group = Group.objects.get(id=id)
    group.delete()
    success(request, f'Group "{group.name}" deleted successfully.')
    return redirect(request.META.get("HTTP_REFERER"))
