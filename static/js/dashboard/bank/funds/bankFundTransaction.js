import { BankFundAmountInputField } from "./bankFundAmountInputField.js";
import { getCsrfToken } from "../../../security/csrf.js";
import fetchData from "../../../fetch.js";
import { AlertUtils } from "../../../alerts.js";
import { DashboardBankPanel } from "../../panel/dasboardPanel.js";
import { formatCurrency } from "../../../utils.js";




async function submitBankFund(pin, url, amount) {
    return await fetchData({
        url: url,
        method: "POST",
        csrfToken: getCsrfToken(),
        body: {
            amount:amount,
            pin: pin
        }

    });
}


/**
 * Submits a bank-fund transaction using the entered PIN and
 * the amount provided by the bank-fund amount input field.
 *
 * Retrieves the current CSRF token from the page and sends the transaction
 * data to the bank-funding endpoint.
 *
 * @param {string} pin - The PIN entered by the user for the transaction.
 * @returns {Promise<*>} The response returned by the transaction request.
 */
export async function submitBankFundTransaction(pin) {

    const amount = BankFundAmountInputField.getAmountInputFieldValue();
    const url    =  "/dashboard/quick_fund/current_account/";

    return await submitBankFund(pin, url, amount);
}



export async function submitBankFundSavingTransaction(pin) {
    const amount = BankFundAmountInputField.getAmountInputFieldValue();
    const url    =  "/dashboard/quick_fund/saving_account/";
    return await submitBankFund(pin, url, amount);

}



/**
 * Handles the response from a bank-funding transaction.
 *
 * Displays a success or error alert based on the transaction result and,
 * when successful, updates the displayed account balances.
 *
 * @param {Object} data - The bank-funding transaction response.
 * @returns {boolean} `true` when the transaction was successful, otherwise `false`.
 */
export function handleBankFundRespData(data) {

    if (!data.SUCCESS) {
        AlertUtils.showAlert({
            title: data.ACTION,
            text: data.MSG,
            icon: "error",
            confirmButtonText: "Ok!",
        });

        return false;
    }

    AlertUtils.showAlert({
        title: data.ACTION,
        text: data.MSG,
        icon: "success",
        confirmButtonText: "Ok!",
    });

    updateFrontendBalance(data);

    return true;
}



/**
 * Updates the displayed current account and navigation balances
 * using the balance returned by the bank-funding transaction.
 *
 * @param {Object} balance- The updated bank balance to be rendered to the frontend.
 * @returns {void}
 */
function updateFrontendBalance(data) {

    DashboardBankPanel.setCurrentAccountBalance(data.CURRENT_ACCOUNT_BALANCE);
    DashboardBankPanel.setNavBankBalance(data.TOTAL_BALANCE);
    DashboardBankPanel.setSavingAccountBalance(data.SAVINGS_ACCOUNT_BALANCE);
    DashboardBankPanel.setTotalAccountBalance(data.TOTAL_BALANCE);
    DashboardBankPanel.setPendingBalance(data.PENDING_AMOUNT);
  
}
