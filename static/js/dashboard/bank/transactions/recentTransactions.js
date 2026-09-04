import { parseFormData } from "../../../formUtils.js";
import fetchData from "../../../fetch.js";
import { getCsrfToken } from "../../../security/csrf.js";
import { warnError } from "../../../logger.js";
import { toggleSpinner, clearElementField } from "../../../utils.js";
import { AlertUtils } from "../../../alerts.js";


const recentBankTransactionForm = document.getElementById("bank-transaction-form");
const transactionFilterBtn = document.getElementById("bank-filter-btn");
const spinner = document.getElementById("transaction-report-spinner");
const transactionTable = document.querySelector("#transaction-report-table tbody");
const transactionTitle = document.getElementById("transactions-title");



recentBankTransactionForm?.addEventListener("submit", handleForm);


function disableTransactionButton(disable) {
    transactionFilterBtn.disabled = disable ? true : false;
}


const PositiveAndNegativeClass = {
    POSITIVE : "positive",
    NEGATIVE: "negative"
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

    renderTableTransactions(data.TRANSACTIONS, data.NUMBER_RETURNED)
}




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


function getPositiveNegativeClass(condition) {
    return condition ? PositiveAndNegativeClass.POSITIVE : PositiveAndNegativeClass.NEGATIVE;
}



function renderTableTransactions(transactions, numOfTransactions) {

    const fragment = document.createDocumentFragment();
    clearElementField(transactionTable)

    if (!Array.isArray(transactions)) {
        warnError("renderTableTransactions", {
            error: `Expected an array but got ${typeof transactions}`
        })
        return;
    }

    transactionTitle.textContent = `Transaction History (${numOfTransactions})`

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
