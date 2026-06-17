from django import template
from core.models import Item

register = template.Library()


@register.filter(name="test")
def get_operation_types(sectors):
    if sectors is None or len(sectors) == 0:
        return None

    sector = sectors[0]
    return sector.operationtype_set.all()


@register.filter
def next(some_list, current_index):
    """
    Returns the next element of the list using the current index if it exists.
    Otherwise returns an empty string.
    """
    try:
        return some_list[int(current_index) + 1]  # access the next element
    except:
        return ""  # return empty string in case of exception


@register.filter
def underscore(name):
    return name.replace(" ", "_")


@register.filter
def to_title(name):
    return name.replace("_", " ").title()


@register.simple_tag
def iterate_operation_plan_locations(location):
    if location is None:
        return []
    locations = [{"name": location.name, "type": location.get_type_display()}]

    while location.parent:
        locations.insert(
            0,
            {"name": location.parent.name, "type": location.parent.get_type_display()},
        )

        location = location.parent

    return locations


@register.simple_tag
def calculate_sector_rowspan(values):
    rowspan = 1
    rowspan += len(values)
    for year, values in values.items():
        rowspan += len(values) - 1
    
    return rowspan


@register.filter
def get_item(dict, key):
    if key not in ["selected", "options"]:
        key = key.upper().replace(" ", "_")
    return dict.get(key, None)


@register.filter
def get_item_name(id):
    return Item.objects.get(id=id).title

@register.filter
def add_class(label, css_class):
    return label.label_tag(attrs={"class": css_class})

@register.filter
def get_percentage(num1, num2):
    if num1 == 0 or num2 == 0:
        return 0
    return round((num2 / num1) * 100, 2)

@register.filter
def index(arr, idx):
    return arr[idx]
