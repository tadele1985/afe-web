from dataclasses import dataclass
from django.utils.translation import gettext as _

from core.models import RoleCode


@dataclass
class SidebarItem:
    name: str
    url: str
    sub_menu: list = None
    query_params: str = None
    roles: list[RoleCode] = None

    def get_dict(self, roles: list[RoleCode]):
        if self.roles and roles.filter(role__code__in=self.roles).count() == 0:
            return None

        final_dict = {
            "name": _(self.name),
            "url": self.url,
        }
        if self.sub_menu:
            new_sub_menu = []
            for menu in self.sub_menu:
                new_sub_menu.append(menu.get_dict(roles))
            final_dict["sub_menu"] = new_sub_menu

        if self.query_params:
            final_dict["query_params"] = self.query_params

        return final_dict


links = [
    SidebarItem(name="Dashboard", url="core:dashboard"),
    SidebarItem(
        name="Configuration",
        url="core:configuration",
        sub_menu=[
            SidebarItem(name="CSV Configuration", url="core:configuration"),
            SidebarItem(name="Resources", url="core:resources"),
            SidebarItem(name="Tools", url="core:resources", query_params="?type=TOOL"),
            SidebarItem(
                name="Inputs", url="core:resources", query_params="?type=INPUT"
            ),
            SidebarItem(name="Operation Types", url="core:operation_types"),
            SidebarItem(name="Activity Types", url="core:activity_types"),
            SidebarItem(name="Detail Activity Types", url="core:detail_activity_types"),
            SidebarItem(name="Items", url="core:items"),
            SidebarItem(name="Sectors", url="core:sectors"),
            SidebarItem(name="Customers", url="core:customers"),
            SidebarItem(name="Location", url="core:locations"),
        ],
        roles=[RoleCode.SYSTEM_ADMINISTRATOR, RoleCode.DATA_ADMINISTRATOR],
    ),
    SidebarItem(name="Operation Plan", url="core:operation_plan_overview"),
    SidebarItem(name="Locations", url="core:location"),
    SidebarItem(name="Item Inventory", url="core:item_inventory"),
    SidebarItem(
        name="User/staff management",
        url="core:users",
        roles=[RoleCode.SYSTEM_ADMINISTRATOR],
    ),
    SidebarItem(
        name="Reports",
        url="core:home",
        sub_menu=[
            SidebarItem(name="Annual Plan Report", url="core:annual_plan_report"),
            SidebarItem(name="Stock Balance Report", url="core:stock_report"),
            SidebarItem(name="Performance Report", url="core:performance_report"),
            SidebarItem(name="Receive Report", url="core:reports_receive"),
            SidebarItem(
                name="Transportation Report", url="core:reports_transportation"
            ),
            SidebarItem(name="Purchase Report", url="core:reports_purchase"),
            SidebarItem(name="Sale Report", url="core:reports_sale"),
            SidebarItem(name="Thinning Sale Report", url="core:reports_thinning_sale"),
            SidebarItem(name="Tree Seed Testing Report", url="core:reports_testing"),
            SidebarItem(name="Handoff Report", url="core:reports_handoff"),
            SidebarItem(name="Beatup Report", url="core:reports_beatup"),
            SidebarItem(name="Survival Count Report", url="core:reports_survival"),
            SidebarItem(
                name="Low Thinning Report",
                url="core:reports_thinning",
                query_params="?thinning_type=LOW",
            ),
            SidebarItem(
                name="High Thinning Report",
                url="core:reports_thinning",
                query_params="?thinning_type=HIGH",
            ),
            SidebarItem(
                name="Pre Commercial Thinning Report",
                url="core:reports_thinning",
                query_params="?thinning_type=PRE_COMMERCIAL",
            ),
            SidebarItem(
                name="Commercial Thinning Report",
                url="core:reports_thinning",
                query_params="?thinning_type=COMMERCIAL",
            ),
            SidebarItem(name="Harvesting Report", url="core:reports_harvesting"),
            SidebarItem(
                name="Timely Harvesting Report", url="core:reports_timely_harvesting"
            ),
            SidebarItem(name="Job Creation Report", url="core:reports_job_creation"),
            SidebarItem(name="Downtime Report", url="core:reports_downtime"),
            SidebarItem(
                name="Product Giveaway Report", url="core:reports_product_giveaway"
            ),
            SidebarItem(
                name="Operational Forest Inventory",
                url="core:reports_op_forest_inventory",
            ),
            SidebarItem(
                name="Forest Inventory Report", url="core:reports_forest_inventory"
            ),
            SidebarItem(name="Lumber Stored Report", url="core:reports_lumber_stored"),
            SidebarItem(
                name="Factory Production Report", url="core:reports_factory_production"
            ),
            SidebarItem(
                name="Plantation Site Selection Report", url="core:reports_plantation_site_selection"
            ),
            SidebarItem(
                name="Planted Seedling Report", url="core:reports_planted_seedling"
            ),
        ],
    ),
]


def sidebar_content(request):
    user = request.user
    if not user.is_authenticated:
        return {}

    roles = user.userrole_set.all()
    return {
        "sidebar_content": [
            link.get_dict(roles) for link in links if link.get_dict(roles) is not None
        ]
    }
