const numOfTransactions = document.getElementById("num-of-transactions");

import { warnError } from "../../logger.js";
import { formatDate, formatCurrency } from "../../utils.js";



/**
 * Creates a transaction card element from a transaction object.
 *
 * @param {Object} transaction - The transaction data used to populate the card.
 * @param {string} transaction.title - The transaction title.
 * @param {string} transaction.description - A description of the transaction.
 * @param {number} transaction.amount - The transaction amount.
 * @param {string} transaction.date - The transaction date.
 *
 * @returns {HTMLElement} The generated transaction card element.
 *
 * @example
 * const card = createTransactionCard({
 *     title: "Card Request Fee",
 *     description: "Card Request Transaction",
 *     amount: 0,
 *     date: "2026-06-01"
 * });
 */
function createTransactionCard(transaction) {

    const element = document.createElement("div")
    element.innerHTML = `
        <div class="recent-transaction_card flex-grid pl-12">
           
             <div class="transaction-card__icon">
                    <i class="fa-solid fa-credit-card mt-8"></i>
                </div>

                <div class="transaction-card__info flex-grid">
                    <small class="capitalise light-bold">${transaction.title}</small>
                    <small class="text-muted">${transaction.description.slice(0, 100)} </small>
                </div>

            <div class="transaction-card__meta flex-grid text-align-right pr-8">
                <small class="transaction-card__amount">${formatCurrency(transaction.amount)}</small>
                <small class="transaction-card__date text-muted">${formatDate(transaction.date)}</small>
            </div>
        </div>
        `;
    return element.firstElementChild
}



/**
 * Renders a collection of valid transactions into the recent transactions
 * container and updates the displayed transaction count.
 *
 * Invalid transactions are skipped and returned in the summary object.
 *
 * @param {Object[]} transactions - Array of transaction objects to render.
 *
 * @returns {Object|undefined} A summary object containing the number of
 * rendered transactions and any invalid transactions encountered, or
 * undefined if the supplied value is not an array.
 *
 * @property {number} rendered - Total number of successfully rendered transactions.
 * @property {Object[]} invalid - Collection of invalid transaction objects.
 *
 * @example
 * const result = renderTransactions(transactionList);
 *
 * console.log(result.rendered); // 10
 * console.log(result.invalid);  // []
 */
export const TransactionRenderer = (() => {


    /**
     * Updates the displayed number of rendered transactions in the UI.
     *
     * @param {number} count - The total number of transactions rendered.
     *
     * @returns {void}
     *
     * @example
     * updateTransactionCount(5);
     */
    function updateTransactionCount(count) {
        numOfTransactions.textContent = count;
    }

    /**
     * Validates a transaction object before rendering.
     *
     * @param {Object} transaction
     * @returns {boolean}
     */
    function isTransactionValid(transaction) {
        return (
            transaction &&
            typeof transaction.title === "string" &&
            typeof transaction.description === "string" &&
            typeof transaction.amount === "number" &&
            typeof transaction.date === "string"
        );
    }


    /**
     * Renders a single transaction into a container.
     *
     * @param {Object} transaction
     * @param {HTMLElement} container
     */
    function renderSingleTransaction(transaction, container) {
        const card = createTransactionCard(transaction);
        container.appendChild(card);
    }

    /**
     * Renders multiple transactions into the DOM.
     *
     * @param {Array<Object>} transactions
     * @returns {Object} summary of render result
     */
    function renderTransactions(transactions) {

        const container = document.querySelector(".recent-transaction__cards");

        if (!container) {
            warnError("renderTransactions", {
                error: "The container needed to contain the recent transactions return an incorrect value",
                returned: container
            });

            return;
        }


        const fragment = document.createDocumentFragment()
        const invalidTransactions = [];

        if (!Array.isArray(transactions)) {
            warnError("TransactionRenderer.renderTransactions", {
                error: "Transactions must be an array",
                received: typeof transactions
            });
            return;
        }

        transactions.forEach(transaction => {

            if (!isTransactionValid(transaction)) {
                invalidTransactions.push(transaction);
                return;
            }

            renderSingleTransaction(transaction, fragment) // add it to fragment
        });


        // add the fragmment to container
        container.appendChild(fragment);
        const renderedCount = transactions.length - invalidTransactions.length

        updateTransactionCount(renderedCount)

        return {
            rendered: renderedCount,
            invalid: invalidTransactions
        };
    }

    // public API
    return {
        renderTransactions
    };

})();

export default TransactionRenderer;