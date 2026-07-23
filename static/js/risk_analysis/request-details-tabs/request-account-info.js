
import { ApplicationValidators } from "./validator.js";
import { toTitle } from "../../utils.js";



export class RequestBankAccountDetails extends ApplicationValidators {

    constructor(applicationData) {
        super(applicationData)

        this.validateResponse(applicationData);

        this.data = applicationData;

        this.elements = {

           sortNumberLastFourDigits: document.getElementById("request-sortcode"),
           accountNumberLastFourDigits: document.getElementById("request-accountNumber"),
           accountType: document.getElementById("request__account-type"),
           balance: document.getElementById("account-balance"),
           bankName: document.getElementById("bank-account-heading"),
           sortCode: document.getElementById("bank-details__sortcode-value"),
           accountNumber: document.getElementById("bank-details__account-num-value"),
           balanceForCard: document.getElementById("bank-details__balance-value"),
           bankStatus: document.getElementById("bank-details__status"),
           totalUserApplications: document.getElementById("total-user-applications"),
           address1: document.getElementById("branch-address-line1"),
           address2: document.getElementById("branch-address-line2"),
           city: document.getElementById("branch-city"),
           country: document.getElementById("branch-country"),
           postCode: document.getElementById("branch-postcode"),
           phoneNumber: document.getElementById("branch-phone"),
           accountTypeCard: document.getElementById("account-information__type"),
           currencySymbol: document.getElementById("account-information__currency-symbol"),
           currency: document.getElementById("account-information__currency"),
           accountStatus: document.getElementById("account-information__status"),
           canRequestLoan: document.getElementById("can-request-loan"),
           overdraft: document.getElementById("account-information__overdraft"),
           bankName: document.getElementById("account-information__bank-name"),
           branch: document.getElementById("account-information__bank-branch"),

        };

        this.validateElements(this.elements);

        this.balance = this.data.ACCOUNT_DETAILS.BALANCE;
    }

    #setSortNumberLastFourDigits() {
        this.elements.sortNumberLastFourDigits.textContent = this.data.ACCOUNT_DETAILS.SORT_CODE_LAST_FOUR_DIGITS;
    }

    #setAccountNumberLastFourDigits() {
        this.elements.accountNumberLastFourDigits.textContent = this.data.ACCOUNT_DETAILS.ACCOUNT_LAST_FOUR_DIGITS
    }

    #setAccountType() {
        this.elements.accountType.textContent = this.data.ACCOUNT_DETAILS.TYPE.toUpperCase();
    }

    #setAccountBalance() {
        this.elements.balance.textContent = this.balance
    }

    #setBankName() {
        this.elements.bankName.textContent = this.data.BANK_DETAILS.NAME;
    }

    #setSortCode() {
        this.elements.sortCode.textContent = this.data.ACCOUNT_DETAILS.SORT_CODE;

    }

    #setAccountNumber() {
        this.elements.accountNumber.textContent = this.data.ACCOUNT_DETAILS.ACCOUNT_NUMBER;
    }

    #setCardBalance() {
        this.elements.balanceForCard.textContent = this.balance;
    }

    #setBankStatus() {
        const bankElement  =  this.elements.bankStatus;
        const bankStatus      = this.data.BANK_DETAILS.STATUS;

        const cssStatus =  bankStatus && bankStatus.toLowerCase() === "active" ? "approved" : "rejected";

        bankElement.className = `status status--${cssStatus} ml-4`;
        bankElement.textContent = bankStatus
    }

    #totalUserApplications() {
        this.elements.totalUserApplications.textContent = this.data.USER_STATS.TOTAL_APPLICATIONS;
    }

    #setFullAddress() {
        this.elements.address1.textContent = this.data.BANK_DETAILS.ADDRESS_LINE_1;

        if (this.data.BANK_DETAILS.ADDRESS_LINE_2) {
             this.elements.address2.textContent = this.data.BANK_DETAILS.ADDRESS_LINE_2
        }

        this.elements.postCode.textContent = this.data.BANK_DETAILS.POSTCODE;
        this.elements.country.textContent  = this.data.BANK_DETAILS.COUNTRY;


    }

    #setBranchPhoneNumber() {

        const countryCode = this.data.BANK_DETAILS.COUNTRY_PHONE_NUMBER_CODE;
        const nationalNumber = this.data.BANK_DETAILS.NATIONAL_NUMBER;
        const ext            = this.data.BANK_DETAILS.EXT === null ? "None" : this.data.BANK_DETAILS.EXT;

        this.elements.phoneNumber.textContent = `Ext (${ext}), Country code (${countryCode}), Phone number (${nationalNumber})`;
    }

    #setAccountInformation() {
        this.elements.accountTypeCard.textContent = toTitle(this.data.ACCOUNT_DETAILS.TYPE);
        this.elements.currencySymbol.textContent  = this.data.ACCOUNT_DETAILS.CURRENCY_CODE;
        this.elements.currency.textContent        = this.data.ACCOUNT_DETAILS.CURRENCY;
        this.elements.accountStatus.textContent   = toTitle(this.data.ACCOUNT_DETAILS.STATUS);
        this.elements.canRequestLoan.textContent  = toTitle(this.data.ACCOUNT_DETAILS.CAN_REQUEST_OVERDRAFT);
        this.elements.overdraft.textContent       = toTitle(this.data.ACCOUNT_DETAILS.CAN_REQUEST_OVERDRAFT);
        this.elements.bankName.textContent        = toTitle(this.data.BANK_DETAILS.NAME);
        this.elements.branch.textContent          = toTitle(this.data.BANK_DETAILS.BRANCH_NAME)

    }


    render() {
        this.#setSortNumberLastFourDigits();
        this.#setAccountNumberLastFourDigits();
        this.#setAccountType();
        this.#setAccountBalance();
        this.#setBankName();
        this.#setSortCode();
        this.#setAccountNumber();
        this.#setCardBalance();
        this.#setBankStatus();
        this.#totalUserApplications();
        this.#setFullAddress();
        this.#setBranchPhoneNumber();
        this.#setAccountInformation();

    }

}
