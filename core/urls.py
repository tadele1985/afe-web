from django.conf.urls import include
from django.urls import path, re_path

from core import ajax
from core.views import (
    activity_plan_views,
    configuration_views,
    location_views,
    misc_views,
    operation_plan_views,
    user_management_views,
    additional_forms_views,
    item_views,
    report_views,
    general_report_views,
    role_permission_views,
    customer_management_views,
)

app_name = "core"

urlpatterns = [
    path(
        "api/edit_activity_plan/",
        activity_plan_views.edit_activity_plan,
        name="edit_activity_plan",
    ),
    path(
        "operation_plan_overview/",
        operation_plan_views.operation_plan_overview,
        name="operation_plan_overview",
    ),
    path(
        "operation_plan/", operation_plan_views.OperationPlanList.as_view(), name="home"
    ),
    path(
        "upload_operation_plans/",
        operation_plan_views.upload_operation_plans,
        name="upload_operation_plans",
    ),
    path(
        "upload_sub_activity_types/",
        operation_plan_views.upload_sub_activity_types,
        name="upload_sub_activity_types",
    ),
    path(
        "upload_location_tree/",
        operation_plan_views.upload_location_tree,
        name="upload_location_tree",
    ),
    path(
        "upload_resource_types/",
        operation_plan_views.upload_resource_types,
        name="upload_resource_types",
    ),
    path(
        "upload_annual_plan_metadata/",
        operation_plan_views.upload_annual_plan_metadata,
        name="upload_annual_plan_metadata",
    ),
    path(
        "api/add_activity_plan/",
        activity_plan_views.add_activity_plan,
        name="add_activity_plan",
    ),
    re_path(
        r"^operation_plan/(?P<uuid>[0-9a-fA-F-]+)/",
        operation_plan_views.OperationDetailView.as_view(),
        name="operation_plan_detail",
    ),
    re_path(
        r"^operation_plan/delete/(?P<uuid>[0-9a-fA-F-]+)/",
        operation_plan_views.delete_operation_plan,
        name="delete_operation_plan",
    ),
    re_path(
        r"^operation_plan/finalize/(?P<uuid>[0-9a-fA-F-]+)/",
        operation_plan_views.finalize_operation_plan,
        name="finalize_operation_plan",
    ),
    re_path(
        r"^activity_plan/(?P<uuid>[0-9a-fA-F-]+)/",
        activity_plan_views.DetailActivityDetailView.as_view(),
        name="activity_plan_detail",
    ),
    re_path(
        r"^detail_activity/(?P<uuid>[0-9a-fA-F-]+)/",
        activity_plan_views.detail_activity_detail,
        name="detail_activity_detail",
    ),
    path(
        "edit_detail_activity/",
        activity_plan_views.edit_detail_activity,
        name="edit_detail_activity",
    ),
    path(
        "edit_operation_plan/<slug:pk>/",
        operation_plan_views.OperationPlanUpdateView.as_view(),
        name="edit_operation_plan",
    ),
    path(
        "duplicate_operation_plan/<slug:pk>/",
        operation_plan_views.OperationPlanDuplicateView.as_view(),
        name="duplicate_operation_plan",
    ),
    path(
        "activity_resource_detail/<slug:pk>/",
        activity_plan_views.ActivityResourceDetail.as_view(),
        name="activity_resource_detail",
    ),
    path(
        "actual_activity_resources/",
        activity_plan_views.ActualActivityCreateView.as_view(),
        name="create_actual_activity_resource",
    ),
    path(
        "edit_actual_activity_resource/<slug:pk>/",
        activity_plan_views.EditActualActivityView.as_view(),
        name="edit_actual_activity_resource",
    ),
    path("", general_report_views.dashboard, name="dashboard"),
    path("permission_denied", misc_views.permission_denied, name="permission_denied"),
]

ajax_urls = [
    path("api/get_resource_units", ajax.get_resource_units, name="get_resource_units"),
    path("api/operations/", ajax.get_operations, name="get_operations"),
    path("api/branches/", ajax.get_branches, name="get_branches"),
    path("api/forest_sites/", ajax.get_forest_sites, name="get_forest_sites"),
    path("api/blocks/", ajax.get_blocks, name="get_blocks"),
    path("api/compartments/", ajax.get_compartments, name="get_compartments"),
    path("api/get_locations/", ajax.get_locations, name="get_locations"),
    path(
        "api/get_multi_select_locations/",
        ajax.get_multi_select_locations,
        name="get_multi_select_locations",
    ),
    path(
        "api/sub_compartments/", ajax.get_sub_compartments, name="get_sub_compartments"
    ),
    path("api/operation_plans/", ajax.get_operation_plans, name="get_operation_plans"),
    path("api/get_resource_form/", ajax.get_resource_form, name="get_resource_form"),
    path("api/get_tool_form/", ajax.get_tool_form, name="get_tool_form"),
    path("api/get_input_form/", ajax.get_input_form, name="get_input_form"),
    path("api/get_cost/", ajax.get_cost, name="get_cost"),
    path("api/get_location_form/", ajax.get_location_form, name="get_location_form"),
    path(
        "api/get_multi_select_location_form/",
        ajax.get_multi_select_location_form,
        name="get_multi_select_location_form",
    ),
    path(
        "api/get_edit_activity_form/",
        ajax.get_edit_activity_form,
        name="get_edit_activity_form",
    ),
    path(
        "api/get_detailed_activity_form",
        ajax.get_detailed_activity_form,
        name="get_detailed_activity_form",
    ),
    path(
        "api/get_location_detail", ajax.get_location_detail, name="get_location_detail"
    ),
    path("api/get_resource_forms", ajax.get_resource_forms, name="get_resource_forms"),
    path(
        "api/get_operation_types", ajax.get_operation_types, name="get_operation_types"
    ),
    path(
        "api/get_resource_type_from_activity_type",
        ajax.get_resource_type_from_activity_type,
        name="get_annual_resource_types",
    ),
    path(
        "api/get_parent_locations_by_type",
        ajax.get_parent_locations_by_type,
        name="get_parent_locations_by_type",
    ),
    re_path(
        r"^api/get_edit_detailed_activity_form/(?P<id>[0-9a-fA-F-]+)/",
        ajax.get_edit_detailed_activity_form,
        name="get_edit_detailed_activity_form",
    ),
    path("api/v1/", include("core.api.urls")),
    # path("api/cache_formlist", ajax.get_formlist, name="formlist"),
    path("api/formlist", ajax.get_formlist, name="formlist"),
]

# user_management_urls = [path("users/", adminstration_views.users, name="users")]

location_urls = [
    path("location/", location_views.LocationListView.as_view(), name="location"),
    path(
        "location/<slug:pk>/",
        location_views.LocationDetailView.as_view(),
        name="location_detail",
    ),
]

item_urls = [
    path(
        "item_inventory/",
        item_views.FilteredInventoryListView.as_view(),
        name="item_inventory",
    ),
    path(
        "item_inventory/<slug:pk>/",
        item_views.InventoryDetailView.as_view(),
        name="item_inventory_detail",
    ),
    path(
        "hq_batch_info/",
        item_views.HQBatchInfoView.as_view(),
        name="hq_batch_info",
    ),
]

user_management_urls = [
    path("users/", user_management_views.UserListView.as_view(), name="users"),
    path("create/", user_management_views.user_create, name="user_create"),
    path("users/<uuid:pk>/", user_management_views.user_update, name="user_update"),
    path("delete/<uuid:uuid>/", user_management_views.user_delete, name="user_delete"),
    path(
        "user_enable/<uuid:pk>/", user_management_views.user_enable, name="user_enable"
    ),
    path(
        "user_disable/<uuid:pk>/",
        user_management_views.user_disable,
        name="user_disable",
    ),
]

customer_management_urls = [
    path(
        "customers/",
        customer_management_views.CustomerListView.as_view(),
        name="customers",
    ),
    path(
        "customers/create/",
        customer_management_views.customer_create,
        name="customer_create",
    ),
    path(
        "customers/users/<uuid:uuid>/",
        customer_management_views.customer_update,
        name="customer_update",
    ),
    path(
        "customers/delete/<uuid:uuid>/",
        customer_management_views.customer_delete,
        name="customer_delete",
    ),
]

additional_forms_urls = [
    path(
        "form_submissions/",
        additional_forms_views.FormSubmissionListView.as_view(),
        name="form_submissions",
    ),
    path(
        "form_submissions/<uuid:uuid>/",
        additional_forms_views.form_submission_detail,
        name="form_submission_detail",
    ),
]

configuration_urls = [
    path("configuration/", configuration_views.configuration, name="configuration"),
    path(
        "configuration/sectors/",
        configuration_views.SectorListView.as_view(),
        name="sectors",
    ),
    path(
        "configuration/sectors/update/<slug:pk>/",
        configuration_views.SectorUpdateView.as_view(),
        name="edit_sector",
    ),
    path(
        "configuration/sectors/delete/<slug:pk>",
        configuration_views.SectorDeleteView.as_view(),
        name="delete_sector",
    ),
    path(
        "configuration/sectors/create/",
        configuration_views.SectorCreateView.as_view(),
        name="create_sector",
    ),
    path(
        "configuration/sector/<slug:pk>/",
        configuration_views.SectorDetailView.as_view(),
        name="sector",
    ),
    path(
        "configuration/resources/",
        configuration_views.ResourcesListView.as_view(),
        name="resources",
    ),
    path(
        "configuration/resources/create/",
        configuration_views.ResourceCreateView.as_view(),
        name="create_resource",
    ),
    path(
        "configuration/resources/update/<slug:pk>/",
        configuration_views.ResourceUpdateView.as_view(),
        name="edit_resource",
    ),
    path(
        "configuration/resources/delete/<slug:pk>",
        configuration_views.ResourceDeleteView.as_view(),
        name="delete_resource",
    ),
    path(
        "configuration/resource/<slug:pk>/",
        configuration_views.ResourceDetailView.as_view(),
        name="resource",
    ),
    path(
        "configuration/detail_activity/",
        configuration_views.DetailActivityTypeListView.as_view(),
        name="detail_activity_types",
    ),
    path(
        "configuration/detail_activity/create/",
        configuration_views.DetailActivityTypeCreateView.as_view(),
        name="create_detail_activity_type",
    ),
    path(
        "configuration/detail_activity/update/<slug:pk>/",
        configuration_views.DetailActivityTypeUpdateView.as_view(),
        name="update_detail_activity_type",
    ),
    path(
        "configuration/operation_type/",
        configuration_views.OperationTypeListView.as_view(),
        name="operation_types",
    ),
    path(
        "configuration/operation_type/create/",
        configuration_views.OperationTypeCreateView.as_view(),
        name="create_operation_type",
    ),
    path(
        "configuration/operation_type/update/<slug:pk>/",
        configuration_views.OperationTypeUpdateView.as_view(),
        name="update_operation_type",
    ),
    path(
        "configuration/activity_type/",
        configuration_views.ActivityTypeListView.as_view(),
        name="activity_types",
    ),
    path(
        "configuration/activity_type/create/",
        configuration_views.ActivityTypeCreateView.as_view(),
        name="create_activity_type",
    ),
    path(
        "configuration/activity_type/update/<slug:pk>/",
        configuration_views.ActivityTypeUpdateView.as_view(),
        name="update_activity_type",
    ),
    path(
        "configuration/items/",
        configuration_views.ItemListView.as_view(),
        name="items",
    ),
    path(
        "configuration/items/create/",
        configuration_views.ItemCreateView.as_view(),
        name="create_item",
    ),
    path(
        "configuration/location/",
        configuration_views.LocationListView.as_view(),
        name="locations",
    ),
    path(
        "configuration/location/create/",
        configuration_views.LocationCreateView.as_view(),
        name="create_location",
    ),
    path(
        "configuration/location/update/<slug:pk>/",
        configuration_views.LocationUpdateView.as_view(),
        name="update_location",
    ),
    path(
        "export/locations",
        configuration_views.export_locations,
        name="export_locations",
    ),
]

report_urls = [
    path(
        "reports/receive/",
        report_views.ItemReceiveListView.as_view(),
        name="reports_receive",
    ),
    path(
        "reports/receive/detail/<slug:pk>/",
        report_views.ItemReceiveDetailView.as_view(),
        name="reports_receive_detail",
    ),
    path(
        "reports/transportation/",
        report_views.ItemTransportListView.as_view(),
        name="reports_transportation",
    ),
    path(
        "reports/transportation/detail/<slug:pk>/",
        report_views.ItemTransportDetailView.as_view(),
        name="reports_transportation_detail",
    ),
    path(
        "reports/purchase/",
        report_views.ItemPurchaseListView.as_view(),
        name="reports_purchase",
    ),
    path(
        "reports/purchase/detail/<slug:pk>/",
        report_views.ItemPurchaseDetailView.as_view(),
        name="reports_purchase_detail",
    ),
    path(
        "reports/sale/",
        report_views.ItemSaleListView.as_view(),
        name="reports_sale",
    ),
    path(
        "reports/thinning_sale/",
        report_views.ThinningSaleListView.as_view(),
        name="reports_thinning_sale",
    ),
    path(
        "reports/thinning_sale/detail/<slug:pk>/",
        report_views.ThinningSaleDetailView.as_view(),
        name="reports_thinning_sale_detail",
    ),
    path(
        "reports/sale/detail/<slug:pk>/",
        report_views.ItemSaleDetailView.as_view(),
        name="reports_sale_detail",
    ),
    path(
        "reports/testing/",
        report_views.SeedTestListView.as_view(),
        name="reports_testing",
    ),
    path(
        "reports/handoff/",
        report_views.HandoffListView.as_view(),
        name="reports_handoff",
    ),
    path(
        "reports/beatup/",
        report_views.BeatupListView.as_view(),
        name="reports_beatup",
    ),
    path(
        "reports/survival_count/",
        report_views.SurvivalCountListView.as_view(),
        name="reports_survival",
    ),
    path(
        "reports/thinning/",
        report_views.ThinningListView.as_view(),
        name="reports_thinning",
    ),
    path(
        "reports/thinning/detail/<slug:pk>/",
        report_views.ThinningDetailView.as_view(),
        name="reports_thinning_detail",
    ),
    path(
        "reports/harvesting/",
        report_views.HarvestingReportListView.as_view(),
        name="reports_harvesting",
    ),
    path(
        "reports/harvesting/detail/<slug:pk>/",
        report_views.HarvestingReportDetailView.as_view(),
        name="reports_harvesting_detail",
    ),
    path(
        "reports/downtime/",
        report_views.DownTimeListView.as_view(),
        name="reports_downtime",
    ),
    path(
        "reports/op_forest_inventory/",
        report_views.OperationalForestInventoryListView.as_view(),
        name="reports_op_forest_inventory",
    ),
    path(
        "reports/forest_inventory/",
        report_views.ForestInventoryReportView.as_view(),
        name="reports_forest_inventory",
    ),
    path(
        "reports/timely_harvesting/",
        report_views.TimelyHarvestingListView.as_view(),
        name="reports_timely_harvesting",
    ),
    path(
        "reports/timely_harvesting/detail/<slug:pk>/",
        report_views.TimelyHarvestingDetailView.as_view(),
        name="reports_timely_harvesting_detail",
    ),
    path(
        "reports/lumber_stored/",
        report_views.LumberStoredReportView.as_view(),
        name="reports_lumber_stored",
    ),
    path(
        "reports/factory_production/",
        report_views.FactoryProductionView.as_view(),
        name="reports_factory_production",
    ),
    path(
        "reports/plantation_site_selection/",
        report_views.PlantationSiteSelectionView.as_view(),
        name="reports_plantation_site_selection",
    ),
    path(
        "reports/planted_seedling/",
        report_views.PlantedSeedlingView.as_view(),
        name="reports_planted_seedling",
    ),
    path(
        "reports/product_giveaway",
        report_views.GiveAwayReportView.as_view(),
        name="reports_product_giveaway",
    ),
    path(
        "reports/job_creation",
        report_views.JobOportunityReportView.as_view(),
        name="reports_job_creation",
    ),
    path(
        "reports/annual_plan/",
        report_views.annual_plan_report,
        name="annual_plan_report",
    ),
    path(
        "reports/performance/",
        report_views.performance_report,
        name="performance_report",
    ),
]

general_report_urls = [
    path(
        "reports/stock_balance_report/",
        general_report_views.stock_report,
        name="stock_report",
    ),
    path("dashboard/", general_report_views.dashboard, name="dashboard"),
]

role_permission_vies = [
    path(
        "role_permission/",
        role_permission_views.role_permission,
        name="role_permission",
    ),
    path(
        "edit_role_permissions/<slug:id>/",
        role_permission_views.edit_role_permissions,
        name="edit_role_permissions",
    ),
    path(
        "fetch_permission/",
        role_permission_views.fetch_permission,
        name="fetch_permission",
    ),
    path(
        "add_permissions_to_group/",
        role_permission_views.add_permissions_to_group,
        name="add_permissions_to_group",
    ),
    path(
        "remove_permissions_to_group/",
        role_permission_views.remove_permissions_to_group,
        name="remove_permissions_to_group",
    ),
    path(
        "add_group_modal/",
        role_permission_views.add_group_modal,
        name="add_group_modal",
    ),
    path("add_group/", role_permission_views.add_group, name="add_group"),
    path(
        "delete_group/<slug:id>/",
        role_permission_views.delete_group,
        name="delete_group",
    ),
]

urlpatterns += ajax_urls
urlpatterns += user_management_urls
urlpatterns += location_urls
urlpatterns += item_urls
urlpatterns += additional_forms_urls
urlpatterns += configuration_urls
urlpatterns += report_urls
urlpatterns += general_report_urls
urlpatterns += role_permission_vies
urlpatterns += customer_management_urls
