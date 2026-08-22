import { BankFundAmountInputField } from "./bankFundAmountInputField.js";
import { getCsrfToken } from "../../../security/csrf.js";
import fetchData from "../../../fetch.js";
import { AlertUtils } from "../../../alerts.js";
import { DashboardBankPanel } from "../../panel/dasboardPanel.js";


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

    return await fetchData({
        url: "/dashboard/quick_fund/current_account/",
        method: "POST",
        csrfToken: getCsrfToken(),
        body: {
            amount:amount,
            pin: pin
        }

    });
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

    updateFrontendBalance(data.BALANCE);

    return true;
}



/**
 * Updates the displayed current account and navigation balances
 * using the balance returned by the bank-funding transaction.
 *
 * @param {Object} balance- The updated bank balance to be rendered to the frontend.
 * @returns {void}
 */
function updateFrontendBalance(balance) {

    DashboardBankPanel.setCurrentAccountBalance(balance);
    DashboardBankPanel.setNavBankBalance(balance);
}
