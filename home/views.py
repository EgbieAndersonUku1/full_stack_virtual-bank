from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from bank.services.services import BankAccountCacheService
from bank.utils import get_account_context
from card.services import CardDashboardServiceCache
from utils.decorators import is_email_verified, go_to_staff_page
from card.models import BankCard
from user_profile.services import ProfileCacheService
from authentication.view_helper import handle_json_post_request
from setup.decorators import onboarding_required
from bank.services.quick_funding_service import QuickFundingService

# Create your views here.

@go_to_staff_page
@is_email_verified
def bank_home(request):

    uncompleted_on_boarding_step = request.session.get("next_step")

    context = {
        "on_boarding_step": uncompleted_on_boarding_step
    }
    return render(request, "home/bank/virtual-bank.html", context=context)


@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def dashboard(request):

    bank_account = BankAccountCacheService.get_accounts(user = request.user)

    current_account = bank_account.first()
    dashboard_cards = CardDashboardServiceCache.get_user_cards(bank_account=current_account,
                                                               session_key_id=request.user.id
                                                               )

    context = {
        "number_of_accounts": 0,
        "current_account": None,
        "saving_account": None,
        "dashboard_cards": dashboard_cards,
        "has_wallet": False,

    }


    if bank_account:

        context.update(get_account_context(bank_account))

        bank                           = context["current_account"].sort_code.bank
        context["minimum_deposit"]     = bank.minimum_opening_deposit
        context["monthly_deposit"]     = bank.monthly_deposit
        context["met_conditions"]      = context["current_account"].has_met_minimum_deposit_conditions
        context["offer_loans"]         = bank.offer_loans
        context["has_overdraft"]       = bank.offer_overdraft
        context["interest_rates"]      = bank.interest_rate_percent
        context["has_saving_account"]  = bank.offer_saving_account
        context["bank_name"]           = bank.name


    return render(request, "home/dashboard/dashboard.html", context=context)


@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def money_transfer(request):
    return render(request, "home/dashboard/money_transfer.html")


@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def manage_credit_cards(request):
    bank_account    = BankAccountCacheService.get_current_account(user=request.user)
    cards           = BankCard.get_by_bank_account(bank_account=bank_account)
    dashboard_cards = CardDashboardServiceCache.get_user_cards(bank_account=bank_account,
                                                               session_key_id=request.user.id
                                                               )

    context = {
        "cards": cards,
        "num_of_cards": cards.count(),
        "num_of_dashboard_cards_selected": len(dashboard_cards)
    }


    return render(request, "home/dashboard/manage_cards.html", context=context)



@onboarding_required
@is_email_verified
@login_required
def manage_admin(request):

    return render(request, "home/dashboard/admin/system_tools.html")


@onboarding_required
@is_email_verified
@login_required
def manage_settings(request):

    user         = request.user
    profile      = ProfileCacheService.get_user_profile(user=user)
    bank_account = BankAccountCacheService.get_accounts(user = request.user)

    context = {
        "profile": profile,

    }
    context.update(get_account_context(bank_account))

    return render(request,  "home/dashboard/settings.html", context=context)


@onboarding_required
@is_email_verified
@login_required
def money_management_portal(request):
    return render(request, "home//dashboard/money_management.html")



@login_required
@onboarding_required
@is_email_verified
def quick_fund_current_account(request):

    def fund_current_account(request_body):
        pin = request_body.get("pin")["values"]
        return QuickFundingService.quick_fund_current_account(pin=pin,
                                                          amount=request_body.get("amount"),
                                                          user=request.user)


    return handle_json_post_request(request, func=fund_current_account)
