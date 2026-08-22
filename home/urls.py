from django.urls import path

from . import views



urlpatterns = [

    path('', view=views.bank_home, name="bank_home"),
    path('bank/', view=views.bank_home, name="bank_home"),
    path("dashboard/", view=views.dashboard, name="dashboard"),
    path("dashboard/money/transfer/", view=views.money_transfer, name="money_transfer"),
    path("dashboard/money/cards/", view=views.manage_credit_cards, name="manage_cards"),
    path("dashboard/admin/system_tools/", view=views.manage_admin, name="manage_admin"),
    path("dashboard/settings/", view=views.manage_settings, name="manage_settings"),
    path("dashboard/money_management/", view=views.money_management_portal, name="money_management"),
    path("dashboard/quick_fund/current_account/", view=views.quick_fund_current_account, name="quick_fund_current_account"),

]
