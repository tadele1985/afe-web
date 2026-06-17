from dataclasses import asdict, dataclass, field
from typing import Callable, Dict, Literal, Optional
import logging

logger = logging.getLogger(__name__)


class FormFieldMeta(type):
    def __call__(cls, *args, **kwargs):
        obj = super().__call__(*args, **kwargs)
        obj.__post_init__()
        return obj


@dataclass(slots=True)
class FormField:
    name: str
    label: str
    type: Literal[
        "string",
        "number",
        "float",
        "date",
        "select",
        "table_select",
        "table_autocomplete",
    ]
    required: bool
    options: Optional[str | list[str] | list[dict]] = None
    autofill: Optional[str | list[str] | list[dict]] = None
    filters: Optional[Dict] = None
    option_callable: Optional[Callable] = field(default=None, repr=False)
    autofill_callable: Optional[Callable] = field(default=None, repr=False)
    multiple: bool = False
    allow_future_date: bool = None


@dataclass(slots=True)
class AttachedForm:
    title: str
    version: str
    fields: list[FormField] = field(default_factory=list)
    is_inventory: bool = False
    detail_activity_id: Optional[int] = None

    @staticmethod
    def dict_factory(cls):
        exclude_fields = (
            "option_callable",
            "autofill_callable",
        )
        return {
            k: v for (k, v) in cls if ((v is not None) and (k not in exclude_fields))
        }

    def to_dict(self):
        for form_field in self.fields:
            try:
                if form_field.type == "table_select":
                    form_field.options = form_field.option_callable()

                if form_field.autofill_callable:
                    form_field.autofill = form_field.autofill_callable()
            except Exception as e:
                logger.error("Error in callable: %s", exc_info=e)

        return asdict(self, dict_factory=AttachedForm.dict_factory)


class FormContext:
    def __init__(self, form, user):
        self.detail_activity = form.detail_activity
        self.location = self.detail_activity.activity_plan.operation_plan.location
        self.form_id = str(form.actual_form_id)
        self.user = user

    def get_location_type(self, location_type: str):
        return self.location.get_location_type(location_type)
