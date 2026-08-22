import { BankFundAmountInputField } from "./bankFundAmountInputField.js";
import { getCsrfToken } from "../../../security/csrf.js";
import fetchData from "../../../fetch.js";
import { AlertUtils } from "../../../alerts.js";



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



export function handleBankFundRespData(data) {

     if (!data.SUCCESS) {
        AlertUtils.showAlert({
            title: data.ACTION,
            text: data.MSG,
            icon: "error",
            confirmButtonText: "Ok!",
        })
        return false;
    }

    AlertUtils.showAlert({
        title: data.ACTION,
        text: data.MSG,
        icon: "success",
        confirmButtonText: "Ok!",
    })

    updateFrontendAmount(data)
    return true;


}


function updateFrontendAmount(data) {
   
    console.log(data);
}
