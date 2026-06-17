import datetime

from django.utils.html import format_html
from django.utils import timezone
from core.utils import gregorian_year_to_ethiopian, ethiopian_year_to_gregorian
from ethiopian_date import EthiopianDateConverter

from django import forms
from django.urls import reverse_lazy
from django.forms.widgets import ChoiceWidget

from .models import (
    ActivityPlan,
    ActivityResource,
    ActivityResourceType,
    ActivityType,
    ActualActivityResource,
    AfeUser,
    DetailActivity,
    DetailActivityType,
    Item,
    Location,
    OperationPlan,
    OperationType,
    Sector,
    Role,
    UserRole,
    Customer,
)

from django.contrib.auth.models import Group, Permission
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.contrib.admin.widgets import FilteredSelectMultiple


def get_amharic_datestr(value):
    tmp = EthiopianDateConverter.date_to_ethiopian(value)
    date_str = f"{tmp[0]}-{tmp[1]}-{tmp[2]}"
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    print(f"Afe Date Input Widget2: {date_obj} for {value}")
    return date_obj.strftime("%d/%m/%Y")


class AfeDateInput(forms.DateInput):
    template_name = "components/date-input.html"

    class Media:
        css = {"all": ["css/calendar/jquery.calendars.picker.css"]}
        # js = ["datepicker.js"]
        js = [
            "js/jquery.min.js",
            "js/calendar/jquery.plugin.js",
            "js/calendar/jquery.calendars.js",
            "js/calendar/jquery.calendars.plus.js",
            "js/calendar/jquery.calendars.picker.js",
            "js/calendar/jquery.calendars.ethiopian.js",
            "js/calendar/jquery.calendars.ethiopian-am.js",
            "datepicker.js",
            "popupDatepicker.js",
        ]

    def __init__(self, attrs=None, format=None):
        if attrs is not None:
            if "class" in attrs:
                attrs["class"] += " popupDatepicker"
            else:
                attrs["class"] = "popupDatepicker"
        else:
            attrs = {"class": "popupDatepicker"}
        super().__init__(attrs, format)

    def format_value(self, value):
        print(f"Afe Date Input Widget: {value}, {type(value)}")
        if isinstance(value, datetime.datetime):
            return get_amharic_datestr(value)
        if isinstance(value, datetime.date):
            return get_amharic_datestr(value)
        return value

    def value_from_datadict(self, data, files, name: str):
        try:
            date, month, year = map(lambda x: int(x), data[name].split("/"))
            gregorian_date = EthiopianDateConverter.to_gregorian(year, month, date)
            return gregorian_date
        except Exception:
            return super().value_from_datadict(data, files, name)


class UserForm(BaseUserCreationForm):
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput, required=True
    )

    role = forms.ModelChoiceField(
        label="Role",
        widget=forms.Select(),
        queryset=Role.objects.all(),
        required=True,
    )

    class Meta:
        model = AfeUser
        fields = [
            "username",
            "email",
            "first_name",
            "middle_name",
            "last_name",
            "role",
            "location",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["location"].queryset = Location.objects.filter(
            type__in=["HQ", "BRANCH"]
        )

        if self.instance.createdDate:
            self.fields["password1"].required = False
            self.fields["password2"].required = False
        else:
            self.fields["password1"].required = True
            self.fields["password2"].required = True

        for field in self.fields:
            if self.fields.get(field).required:
                self.fields.get(field).label = f"{self.fields.get(field).label} *"

        if self.instance:
            user_role = UserRole.objects.filter(user=self.instance).first()
            if user_role:
                self.fields["role"].initial = user_role.role

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        password1 = self.cleaned_data.get("password1")
        role = self.cleaned_data.get("role")

        if password1:
            user.set_password(password1)

        try:
            user_role = UserRole.objects.get(user=user)
            user_role.role = role
        except UserRole.DoesNotExist:
            user_role = UserRole(user=user, role=role)

        if commit:
            user.save()
            user_role.save()

        return user


def generate_year_groups():
    today = timezone.now()
    year_groups = []
    for year in range(today.year - 6, today.year + 5):
        cur_ethiopian_year = gregorian_year_to_ethiopian(year)
        year_groups.append((cur_ethiopian_year, cur_ethiopian_year + 1))

    return year_groups


class OperationPlanForm(forms.ModelForm):
    location = forms.ModelChoiceField(
        widget=forms.Select(attrs={"class": "hidden"}),
        queryset=Location.objects.all(),
        required=False,
    )
    year = forms.ChoiceField(
        initial=gregorian_year_to_ethiopian(datetime.datetime.now().year),
        choices=[
            (year, f"{year - 1}/{year}")
            for year in range(
                gregorian_year_to_ethiopian(2020),
                gregorian_year_to_ethiopian(datetime.datetime.now().year + 10),
            )
        ],
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
                "id": "year_id",
                "hx-swap": "innerHTML",
                "hx-trigger": "change",
                "hx-target": "#operations",
                "hx-get": reverse_lazy("core:get_operations"),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if kwargs.get("instance"):
            year = kwargs.get("instance").start_year.year
            ethiopian_year = gregorian_year_to_ethiopian(int(year))
            choices = [
                (year, year) for year in range(ethiopian_year, ethiopian_year + 5)
            ]
            self.fields["year"].choices = choices
            self.fields["year"].initial = ethiopian_year

        if not self.instance.createdDate:
            self.fields["operation_type"].widget.attrs.update(
                {"hx-get": reverse_lazy("core:get_multi_select_location_form")}
            )
        else:
            self.fields["operation_type"].widget.attrs.update(
                {
                    "hx-get": reverse_lazy("core:get_multi_select_location_form"),
                    "hx-target": "#duplicate_location_form",
                    "hx-trigger": "load",
                }
            )
        self.fields["location"].required = False

    class Meta:
        model = OperationPlan
        fields = ["assignee", "year", "sector", "operation_type", "status", "location"]
        labels = {
            "operation_type": "Operation",
        }
        widgets = {
            # "location": forms.HiddenInput(),
            "location": forms.Select(attrs={"class": "hidden"}),
            "status": forms.Select(attrs={"class": "select select-bordered"}),
            "stage": forms.HiddenInput(),
            "sector": forms.Select(
                attrs={
                    "id": "sector_id",
                    "hx-swap": "innerHTML",
                    "hx-trigger": "change",
                    "hx-target": "#operations",
                    "hx-get": reverse_lazy("core:get_operations"),
                    "class": "select select-bordered w-full",
                }
            ),
            "operation_type": forms.Select(
                attrs={
                    "id": "operations",
                    "class": "select select-bordered w-full",
                    "hx-swap": "innerHTML",
                    "hx-trigger": "change",
                    "hx-target": "#location_form",
                    "hx-get": reverse_lazy("core:get_location_form"),
                }
            ),
            "assignee": forms.Select(
                attrs={
                    "class": "select select-bordered w-full",
                }
            ),
        }

    def save(self, commit=True):
        operation_plan = super().save(commit=False)
        chosen_year = operation_plan.year
        start_of_year = EthiopianDateConverter.to_gregorian(chosen_year - 1, 11, 1)
        end_of_year = EthiopianDateConverter.to_gregorian(chosen_year, 10, 30)
        operation_plan.year = start_of_year.year
        operation_plan.start_year = start_of_year
        operation_plan.end_year = end_of_year
        if commit:
            operation_plan.save()
        return operation_plan


class ActivityPlanForm(forms.ModelForm):
    template_name = "core/activity_plan_form.html"

    class Meta:
        model = ActivityPlan
        fields = ["id", "type", "assignee", "start_date", "end_date", "status"]
        widgets = {
            "id": forms.HiddenInput,
            "start_date": AfeDateInput(
                attrs={
                    "x-model": "start",
                    "x-on:change": "end = $event.target.value",
                }
            ),
            "end_date": AfeDateInput(
                attrs={"type": "date", "x-model": "end", "x-bind:min": "start"}
            ),
        }
        labels = {
            "type": "Select Activity",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not kwargs.get("instance"):
            self.operation_plan = OperationPlan.objects.get(
                pk=self.initial.get("operation_plan")
            )
        else:
            self.operation_plan = kwargs.get("instance").operation_plan

        self.fields["type"].queryset = ActivityType.objects.filter(
            operation_types__in=[self.operation_plan.operation_type]
        ).all()
        operation_plan_time = datetime.datetime(self.operation_plan.year, 1, 1)
        if not kwargs.get("instance"):
            self.fields["start_date"].initial = get_amharic_datestr(
                self.operation_plan.start_year
            )

        self.fields["start_date"].widget.attrs["min"] = get_amharic_datestr(
            operation_plan_time
        )
        # self.fields["start_date"].widget.attrs["min"] = operation_plan_time.strftime(
        #     "%Y-%m-%d"
        # )
        if not kwargs.get("instance"):
            self.fields["end_date"].initial = datetime.datetime(
                self.operation_plan.year, 1, 1
            )
        self.fields["end_date"].widget.attrs["min"] = get_amharic_datestr(
            operation_plan_time
        )
        # self.fields["end_date"].widget.attrs["min"] = operation_plan_time.strftime(
        #     "%Y-%m-%d"
        # )
        for visible in self.visible_fields():
            class_str = " field bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-2.5"

            if "class" in visible.field.widget.attrs:
                visible.field.widget.attrs["class"] += class_str
            else:
                visible.field.widget.attrs["class"] = class_str

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(
                    "Start date must be less than or equal to end date."
                )
        return cleaned_data

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        converted_start_date = EthiopianDateConverter.date_to_ethiopian(
            self.operation_plan.start_year
        )
        if start_date < self.operation_plan.start_year:
            raise forms.ValidationError(
                f"Start Date must be in the year of operation plan({converted_start_date[0]}/{converted_start_date[1]}/{converted_start_date[2]})"
            )
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        converted_end_date = EthiopianDateConverter.date_to_ethiopian(
            self.operation_plan.end_year
        )
        if end_date > self.operation_plan.end_year:
            raise forms.ValidationError(
                f"End Date must be in the year of operation plan({converted_end_date[0]}/{converted_end_date[1]}/{converted_end_date[2]})"
            )
        return end_date


class EditActivityPlanForm(ActivityPlanForm):
    class Meta:
        model = ActivityPlan
        fields = ["id", "type", "assignee", "start_date", "end_date", "status"]
        widgets = {
            "id": forms.HiddenInput,
            "start_date": AfeDateInput(),
            "end_date": AfeDateInput(),
        }
        labels = {
            "type": "Select Activity",
        }


class ActivityResourceForm(forms.ModelForm):
    template_name = "core/resource_form.html"

    class Meta:
        model = ActivityResource
        fields = [
            "id",
            "detail_activity",
            "resource_type",
            "work_norm",
            "achievement",
            "payment",
        ]
        widgets = {
            "id": forms.HiddenInput,
            "detail_activity": forms.HiddenInput,
            "resource_type": forms.Select(
                attrs={
                    "hx-trigger": "change",
                    "hx-swap": "outerHTML",
                    "hx-params": "*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        activity_plan = kwargs.pop("activity_plan", None)
        super().__init__(*args, **kwargs)
        if activity_plan:
            resource_types = activity_plan.operation_plan.operation_type.activityresourcetype_set.all()
            self.fields["resource_type"].queryset = resource_types.filter(
                type="RESOURCE"
            )
        else:
            self.fields["resource_type"].queryset = ActivityResourceType.objects.filter(
                type="RESOURCE"
            )

        self.fields["resource_type"].label = "Resource type:"
        self.fields["resource_type"].widget.attrs["hx-target"] = (
            f"#resource-forms-{self.instance.id}"
        )

        self.fields["resource_type"].widget.attrs["hx-get"] = (
            reverse_lazy("core:get_resource_units")
            + f"?id={self.instance.id}&activity_plan={activity_plan.id if activity_plan else ''}"
        )

        for field_name in ("work_norm", "achievement", "payment"):
            self.fields[field_name].widget.attrs["hx-get"] = reverse_lazy(
                "core:get_cost"
            )
            self.fields[field_name].widget.attrs["hx-target"] = (
                f"#resource-forms-{self.instance.id} #calculated_label"
            )
            self.fields[field_name].widget.attrs["hx-swap"] = "innerHTML"
            self.fields[field_name].widget.attrs["hx-include"] = (
                f"#resource-forms-{self.instance.id} input, #resource-forms-{self.instance.id} select"
            )

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )


class ActivityToolForm(forms.ModelForm):
    template_name = "core/resource_form.html"

    class Meta:
        model = ActivityResource
        fields = [
            "id",
            "detail_activity",
            "resource_type",
            "work_norm",
            "achievement",
            "payment",
        ]
        widgets = {
            "id": forms.HiddenInput,
            "detail_activity": forms.HiddenInput,
            "activity_plan": forms.HiddenInput,
            "resource_type": forms.Select(
                attrs={
                    "hx-trigger": "change",
                    "hx-swap": "outerHTML",
                    "hx-params": "*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        activity_plan = kwargs.pop("activity_plan", None)
        super().__init__(*args, **kwargs)
        if activity_plan:
            resource_types = activity_plan.operation_plan.operation_type.activityresourcetype_set.all()
            self.fields["resource_type"].queryset = resource_types.filter(type="TOOL")
        else:
            self.fields["resource_type"].queryset = ActivityResourceType.objects.filter(
                type="TOOL"
            )
        self.fields["resource_type"].label = "Tool type:"
        self.fields["resource_type"].widget.attrs["hx-target"] = (
            f"#resource-forms-{self.instance.id}"
        )

        self.fields["resource_type"].widget.attrs["hx-get"] = (
            reverse_lazy("core:get_resource_units")
            + f"?id={self.instance.id}&activity_plan={activity_plan.id if activity_plan else ''}"
        )
        for field_name in ("work_norm", "achievement", "payment"):
            self.fields[field_name].widget.attrs["hx-get"] = reverse_lazy(
                "core:get_cost"
            )
            self.fields[field_name].widget.attrs["hx-target"] = (
                f"#resource-forms-{self.instance.id} #calculated_label"
            )
            self.fields[field_name].widget.attrs["hx-swap"] = "innerHTML"
            self.fields[field_name].widget.attrs["hx-include"] = (
                f"#resource-forms-{self.instance.id} input, #resource-forms-{self.instance.id} select"
            )
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )


class ActivityInputForm(forms.ModelForm):
    template_name = "core/resource_form.html"

    class Meta:
        model = ActivityResource
        fields = [
            "id",
            "detail_activity",
            "resource_type",
            "work_norm",
            "achievement",
            "payment",
        ]
        widgets = {
            "id": forms.HiddenInput,
            "detail_activity": forms.HiddenInput,
            "activity_plan": forms.HiddenInput,
            "resource_type": forms.Select(
                attrs={
                    "hx-trigger": "change",
                    "hx-swap": "outerHTML",
                    "hx-params": "*",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        activity_plan = kwargs.pop("activity_plan", None)
        super().__init__(*args, **kwargs)
        if activity_plan:
            resource_types = activity_plan.operation_plan.operation_type.activityresourcetype_set.all()
            self.fields["resource_type"].queryset = resource_types.filter(type="INPUT")
        else:
            self.fields["resource_type"].queryset = ActivityResourceType.objects.filter(
                type="INPUT"
            )
        self.fields["resource_type"].label = "Input type:"
        self.fields["resource_type"].widget.attrs["hx-target"] = (
            f"#resource-forms-{self.instance.id}"
        )

        self.fields["resource_type"].widget.attrs["hx-get"] = (
            reverse_lazy("core:get_resource_units")
            + f"?id={self.instance.id}&activity_plan={activity_plan.id if activity_plan else ''}"
        )
        for field_name in ("work_norm", "achievement", "payment"):
            self.fields[field_name].widget.attrs["hx-get"] = reverse_lazy(
                "core:get_cost"
            )
            self.fields[field_name].widget.attrs["hx-target"] = (
                f"#resource-forms-{self.instance.id} #calculated_label"
            )
            self.fields[field_name].widget.attrs["hx-swap"] = "innerHTML"
            self.fields[field_name].widget.attrs["hx-include"] = (
                f"#resource-forms-{self.instance.id} input, #resource-forms-{self.instance.id} select"
            )
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )


class OperationTypeForm(forms.ModelForm):
    class Meta:
        model = OperationType
        fields = ["name", "sectors", "hierarchy_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str


class ActivityTypeForm(forms.ModelForm):
    class Meta:
        model = ActivityType
        fields = ["name", "operation_types"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str


class DetailActivityTypeForm(forms.ModelForm):
    class Meta:
        model = DetailActivityType
        fields = [
            "name",
            "activites",
            "resource",
            "input",
            "tool",
            "annual_resource_type",
            "form",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str
            if visible.name == "activites":
                new_attrs = {
                    "hx-trigger": "load,change",
                    "hx-get": reverse_lazy("core:get_annual_resource_types"),
                    "hx-include": "#id_activites",
                    "hx-target": 'next select[name="annual_resource_type"]',
                    "hx-swap": "innerHTML",
                }
                visible.field.widget.attrs.update(new_attrs)


class DetailActivityForm(forms.ModelForm):
    template_name = "core/detail_activity_form.html"

    class Meta:
        model = DetailActivity
        fields = [
            "activity_plan",
            "detail_type",
            "assignee",
            "start_date",
            "end_date",
            "status",
        ]
        widgets = {
            "activity_plan": forms.HiddenInput,
            "start_date": AfeDateInput(),
            "end_date": AfeDateInput(),
            "detail_type": forms.Select(
                attrs={
                    "hx-target": "#resource-forms",
                    "hx-trigger": "load,change",
                    "hx-swap": "innerHTML",
                    "hx-get": reverse_lazy("core:get_resource_forms"),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activity_plan = ActivityPlan.objects.get(
            id=self.initial.get("activity_plan")
        )
        self.plan = ActivityPlan.objects.get(id=self.initial.get("activity_plan"))
        self.fields["detail_type"].widget.attrs["hx-get"] = (
            reverse_lazy("core:get_resource_forms")
            + f"?activity_plan={self.activity_plan.id}"
        )
        self.fields["detail_type"].queryset = DetailActivityType.objects.filter(
            activites=self.activity_plan.type
        )
        if not kwargs.get("instance"):
            self.fields["start_date"].initial = get_amharic_datestr(
                self.activity_plan.start_date
            )
            self.fields["end_date"].initial = get_amharic_datestr(
                self.activity_plan.start_date
            )

        class_str = " field bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-2.5 "

        for visible in self.visible_fields():
            if "class" in visible.field.widget.attrs:
                visible.field.widget.attrs["class"] += class_str
            else:
                visible.field.widget.attrs["class"] = class_str

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if not (
            start_date >= self.activity_plan.start_date
            and start_date <= self.activity_plan.end_date
        ):
            raise forms.ValidationError(
                f"Start date must be in the range of the main activity({self.activity_plan.start_date.strftime('%B %d, %Y')} to {self.activity_plan.end_date.strftime('%B %d, %Y')})"
            )
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        if not (
            end_date >= self.activity_plan.start_date
            and end_date <= self.activity_plan.end_date
        ):
            raise forms.ValidationError(
                f"End date must be in the range of the main activity({self.activity_plan.start_date.strftime('%B %d, %Y')} to {self.activity_plan.end_date.strftime('%B %d, %Y')})"
            )
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(
                    "Start date must be less than or equal to end date."
                )
        # detail_type = cleaned_data.get("detail_type")
        # if detail_type.image_requirement == "REQUIRED" and not cleaned_data.get(
        #     "image"
        # ):
        #     raise forms.ValidationError("Image is required.")
        # if detail_type.image_requirement == "NOT_ALLOWED" and cleaned_data.get("image"):
        #     raise forms.ValidationError("Image is not allowed.")
        # if detail_type.document_requirement == "REQUIRED" and not cleaned_data.get(
        #     "document"
        # ):
        #     raise forms.ValidationError("Document is required.")
        # if detail_type.document_requirement == "NOT_ALLOWED" and cleaned_data.get(
        #     "document"
        # ):
        #     raise forms.ValidationError("Document is not allowed.")


class EditDetailActivityForm(DetailActivityForm):
    template_name = "core/edit_detail_activity_form.html"

    class Meta:
        model = DetailActivity
        fields = [
            "id",
            "activity_plan",
            "detail_type",
            "assignee",
            "start_date",
            "end_date",
            "status",
        ]
        widgets = {
            "id": forms.HiddenInput,
            "activity_plan": forms.HiddenInput,
            "start_date": AfeDateInput(),
            "end_date": AfeDateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        activity_plan = self.instance.activity_plan
        self.fields["detail_type"].queryset = DetailActivityType.objects.filter(
            activites=activity_plan.type
        )
        self.fields["detail_type"].widget.attrs = {
            "hx-target": "#edit-resource-forms",
            "hx-trigger": "change",
            "hx-swap": "innerHTML",
            "hx-get": reverse_lazy("core:get_resource_forms")
            + f"?activity_plan={activity_plan.id}",
        }
        class_str = " field bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-2.5"
        for visible in self.visible_fields():
            if "class" in visible.field.widget.attrs:
                visible.field.widget.attrs["class"] += class_str
            else:
                visible.field.widget.attrs["class"] = class_str


class FilterForm(forms.Form):
    template_name = "partials/filter-form.html"

    def __init__(self, *args, **kwargs):
        print(f"Args: {args}, Kwargs: {kwargs}")
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            match visible.widget_type:
                case "text" | "number":
                    visible.field.widget.attrs["class"] = (
                        "input input-bordered input-sm"
                    )
                case "select" | "selectmultiple":
                    visible.field.widget.attrs["class"] = (
                        "select select-bordered select-sm"
                    )
                case "date":
                    visible.field.widget = AfeDateInput(
                        attrs={"class": "input input-bordered input-sm"}
                    )


class InventoryFilterForm(forms.Form):
    template_name = "partials/filter-form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )

        if "item" in self.fields:
            self.fields["item"].queryset = Item.objects.filter(
                iteminventory__isnull=False
            ).distinct()

        self.fields["location"].queryset = Location.objects.filter(
            inventories__isnull=False
        ).distinct()

        if "source_site" in self.fields:
            self.fields["source_site"].queryset = Location.objects.filter(
                source_site_inventories__isnull=False
            ).distinct()


class OperationFilterForm(forms.Form):
    template_name = "partials/operation-filter-form.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            match visible.name:
                case "sector":
                    visible.field.widget.attrs = {
                        "name": "sector",
                        "id": "sector_filter",
                        "class": "select select-sm select-bordered",
                        "hx-trigger": "change",
                        "hx-get": reverse_lazy("core:get_operation_types"),
                        "hx-include": "#sector_filter",
                        "hx-target": "#operation_type_filter",
                        "hx-swap": "innerHTML",
                    }
                case "operation_type":
                    visible.field.widget.attrs = {
                        "id": "operation_type_filter",
                        "class": "select select-bordered select-sm",
                        "hx-trigger": "change",
                        "hx-get": reverse_lazy("core:get_operations"),
                        "hx-target": "#operations",
                        "hx-swap": "innerHTML",
                    }
                case "location" | "status" | "stage":
                    visible.field.widget.attrs = {
                        "class": "select select-sm select-bordered",
                    }
                case _:
                    visible.field.widget.attrs["class"] = (
                        "input input-bordered input-sm"
                    )


class ActualActivityForm(forms.ModelForm):
    class Meta:
        model = ActualActivityResource
        fields = ["activity_resource", "work_norm", "achievement", "payment"]
        widgets = {
            "activity_resource": forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )


class SectorForm(forms.ModelForm):
    class Meta:
        model = Sector
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )


class ResourceTypeForm(forms.ModelForm):
    class Meta:
        model = ActivityResourceType
        exclude = [
            "id",
            "type",
            "createdBy",
            "updatedBy",
            "deleted",
            "syncWoredaContext",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ["metadata", "date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str


class UserGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = "__all__"
        widgets = {
            "permissions": FilteredSelectMultiple(
                "Permission", False, attrs={"rows": "2"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["permissions"].queryset = Permission.objects.filter(
            # UserGroup related permissions
            content_type_id=10
        )
        self.fields["permissions"].widget.attrs.update({"style": "height: 200px;"})

        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "field bg-gray-50 border border-gray-300 text-gray-900 text-sm focus:ring-blue-500 focus:border-blue-500 p-2.5"
            )


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "email", "phone_number", "address", "tin_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number" | "email":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = [
            "name",
            "type",
            "parent",
            "code",
            "zone",
            "district",
            "kebele",
            "location_on_map",
            "area",
            "unique_code",
            "productive_area",
            "non_productive_area",
            "centroid_coordinate",
            "owner",
            "types_of_species_to_be_planted",
            "remark",
            "log_depo_storage_area",
            "region",
        ]
        widgets = {
            "zone": forms.TextInput,
            "district": forms.TextInput,
            "kebele": forms.TextInput,
            "location_on_map": forms.TextInput,
            "area": forms.NumberInput,
            "unique_code": forms.TextInput,
            "productive_area": forms.NumberInput,
            "non_productive_area": forms.NumberInput,
            "centroid_coordinate": forms.TextInput,
            "owner": forms.TextInput,
            "types_of_species_to_be_planted": forms.TextInput,
            "remark": forms.TextInput,
            "log_depo_storage_area": forms.NumberInput,
            "region": forms.TextInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["type"].required = True
        self.fields["type"].widget.attrs.update(
            {
                "class": "select select-bordered w-full",
                "hx-swap": "innerHTML",
                "hx-trigger": "change",
                "hx-target": "#id_parent",
                "hx-get": reverse_lazy("core:get_parent_locations_by_type"),
            }
        )

        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number" | "email":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str

    def clean(self):
        cleaned_data = super().clean()
        location_type = cleaned_data.get("type")
        if location_type != "HQ" and cleaned_data.get("parent") is None:
            raise forms.ValidationError("Parent location is required.")
        return cleaned_data


class LocationUpdateForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = [
            "name",
            "code",
            "zone",
            "district",
            "kebele",
            "location_on_map",
            "area",
            "unique_code",
            "productive_area",
            "non_productive_area",
            "centroid_coordinate",
            "owner",
            "types_of_species_to_be_planted",
            "remark",
            "log_depo_storage_area",
            "region",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number" | "email":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"
                case "textarea":
                    class_str = "textarea textarea-bordered"

            visible.field.widget.attrs["class"] = class_str


class OperationTypeUpdateForm(forms.ModelForm):
    class Meta:
        model = OperationType
        fields = [
            "name",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True

        for visible in self.visible_fields():
            class_str = None
            match visible.widget_type:
                case "text" | "number" | "email":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"

            visible.field.widget.attrs["class"] = class_str
