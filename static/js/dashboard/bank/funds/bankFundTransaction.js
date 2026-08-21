import { BankFundAmountInputField } from "./bankFundAmountInputField.js";
import { getCsrfToken } from "../../../security/csrf.js";
import fetchData from "../../../fetch.js";



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
    const csrfToken = getCsrfToken();

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
