import { parseFormData } from "../../../formUtils.js";
import fetchData from "../../../fetch.js";
import { getCsrfToken } from "../../../security/csrf.js";
import { warnError } from "../../../logger.js";
import { toggleSpinner, clearElementField } from "../../../utils.js";
import { AlertUtils } from "../../../alerts.js";


const recentBankTransactionForm = document.getElementById("bank-transaction-form");
const transactionFilterBtn      = document.getElementById("bank-filter-btn");
const spinner                   = document.getElementById("transaction-report-spinner");
const transactionTable          = document.querySelector("#transaction-report-table tbody");
const transactionTitle          = document.getElementById("transactions-title");
const accountTotalBalance       = document.getElementById("total_account_balances");
const resetButton               = document.getElementById("bank-reset-btn");



recentBankTransactionForm?.addEventListener("submit", handleForm);
resetButton?.addEventListener("click", handleResetButton);




let recentTransactions = {};


function disableTransactionButton(disable) {
    transactionFilterBtn.disabled = disable ? true : false;
}



const PositiveAndNegativeClass = {
    POSITIVE : "positive",
    NEGATIVE: "negative"
}


async function getRecentTransactions() {

    // get request doesnn't require a csrf token since it is not a post
     return await fetchData({
         url: "/dashboard/get/recent_transactions/",
         body: {},
        method: "GET",

    })
}


export async function renderRecentTransactions() {
   const resp = await getRecentTransactions();

    const data = resp.data;

    recentTransactions = {
        transactions: data.TRANSACTIONS,
        numOfTransactions: data.NUMBER_RETURNED,
        totalBalance: data.TOTAL_BALANCE,
    }

    renderTransactions(data.TRANSACTIONS, data.NUMBER_RETURNED, data.TOTAL_BALANCE);


}


function handleData(data) {

    disableTransactionButton(false)

    if (!data.SUCCESS) {

        toggleSpinner(spinner, false);
        AlertUtils.showAlert({
            title: data.ACTION,
            text: data.ERROR_MSG,
            icon: "error",
            confirmButtonText: "Ok"
        })

        return;
    }

    renderTransactions(data.TRANSACTIONS, data.NUMBER_RETURNED, data.TOTAL_BALANCE)
}




/**

Validate the transaction search form and submit the search request.

Prevents the default form submission, validates the form data,
sends the search request to the backend, and handles the response.

*/
async function handleForm(e) {
    e.preventDefault();

    if (recentBankTransactionForm.checkValidity()) {

        const formData = new FormData(recentBankTransactionForm);
        const parsedData = parseFormData(formData, [
            "from_date",
            "to_date",
            "account_type",
            "movement",
            "status"

        ])

        if (!parsedData) {
            warnError("handleForm", {
                error: "Parsed data for the form data return none"
            });
            return;
        }

        disableTransactionButton(true);
        toggleSpinner(spinner)

        const resp = await fetchData({
            url: "/dashboard/search/recent_transactions/",
            csrfToken: getCsrfToken(),
            body: {
                from_date: parsedData.fromDate,
                to_date: parsedData.toDate,
                account_type: parsedData.accountType,
                movement: parsedData.movement,
                status: parsedData.status,
            },
            method: "POST",

        })

        handleData(resp.data);

    } else {
        recentBankTransactionForm.reportValidity();
    }
}




/**
 * Reset the transaction search UI after processing.
 */
function resetTransactionSearchUI() {
    disableTransactionButton(false);
    toggleSpinner(spinner, false);
}




/**

Return the positive or negative CSS class based on a condition.

@param {boolean} condition - Determines which CSS class to return.
@returns {string} The positive or negative CSS class.
*/
function getPositiveNegativeClass(condition) {
    return condition ? PositiveAndNegativeClass.POSITIVE : PositiveAndNegativeClass.NEGATIVE;
}




/**
 *  Reset the transaction search fields and restore the recent transactions.
 * */
function resetTransactionSearch() {

    recentBankTransactionForm.reset()
    const data = transactions.pop()
    renderTransactions(data.TRANSACTIONS, data.NUMBER_RETURNED, data.TOTAL_BALANCE);
}





function renderTransactions(transactions, numOfTransactions, totalBalance) {

    const fragment = document.createDocumentFragment();
    clearElementField(transactionTable)

    if (!Array.isArray(transactions)) {
        warnError("renderTransactions", {
            error: `Expected an array but got ${typeof transactions}`
        })
        return;
    }

    transactionTitle.textContent     = `Transaction History (${numOfTransactions})`;
    accountTotalBalance.textContent  =  totalBalance

    if (numOfTransactions === 0) {

        const tr = document.createElement("tr");

        tr.innerHTML = `<td colspan="9">No transactions found</td>`;

        transactionTable.appendChild(tr)

        resetTransactionSearchUI();
        return;
    }

    transactions.forEach((transaction) => {
        const tr = document.createElement("tr");

        const amountClass = getPositiveNegativeClass(transaction.movement.toLowerCase() === "credit");
        const statusClass = getPositiveNegativeClass(transaction.status.toLowerCase() === "completed");

        const amountPrefix = amountClass === PositiveAndNegativeClass.POSITIVE ? "+" : "-"

        tr.innerHTML = `
            <td class="transaction-id">${transaction.id}</td>
            <td class="transaction-type">${transaction.transaction_type}</td>
            <td class="movement">${transaction.movement}</td>
            <td class="amount ${amountClass}">${amountPrefix}${transaction.amount}</td>
            <td class="opening-balance">${transaction.opening_balance}</td>
            <td class="closing-balance">${transaction.closing_balance}</td>
            <td class="account-type">${transaction.account_type}</td>
            <td class="status ${statusClass}">${transaction.status}</td>
            <td class="created-on">${transaction.created_on}</td>
        `;

        fragment.appendChild(tr);
    });

    transactionTable.appendChild(fragment);
    resetTransactionSearchUI();

}



function handleResetButton() {

    recentBankTransactionForm.reset();

    renderTransactions(recentTransactions.transactions,
                        recentTransactions.numOfTransactions,
                        recentTransactions.totalBalance
                      );
}
