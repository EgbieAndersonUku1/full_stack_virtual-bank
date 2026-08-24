import { warnError } from "../../logger.js";
import { formatCurrency } from "../../utils.js";

const currentAccountBalance = document.getElementById("current_account_balance");
const savingAccountBalance  = document.getElementById("saving_account_balance");
const pendingBalance        = document.getElementById("account_pending_amount");
const totalAccountsBalance  = document.getElementById("total_balance_accross_accounts");
const navBankBalance        = document.getElementById("nav-bank-balance");
const currencySymbol        = document.getElementById("pending-amount-currency-symbol")



export const DashboardBankPanel = (() => {

    /**
     * Validates that the provided account balance is a number.
     *
     * @param {*} amount - The account balance to validate.
     * @returns {boolean} `true` when the amount is a number; otherwise `false`.
     */
    function validateAmount(amount) {
        if (typeof amount !== "string") {
            warnError("validateAmount", {
               error: `The amount has an incorrect type. Expected a number, got type ${typeof amount}`
            })
            return false;
        }

        return true;
    }

    /**
     * Sets the text content of a balance element after validating the amount.
     *
     * If the amount is invalid, the element displays "N/A".
     *
     * @param {number} amount - The account balance to display.
     * @param {HTMLElement} element - The element that displays the balance.
     * @returns {void}
     */
    function setBalance(amount, element) {
        if (!validateAmount(amount)) {
            element.textContent = "N/A";
            return;
        }

        element.textContent = amount;
    }

    /**
     * Updates the current account balance displayed in the dashboard.
     *
     * @param {number} amount - The current account balance.
     * @returns {void}
     */
    function setCurrentAccountBalance(amount) {
        setBalance(amount, currentAccountBalance);
    }

    /**
     * Updates the savings account balance displayed in the dashboard.
     *
     * @param {number} amount - The savings account balance.
     * @returns {void}
     */
    function setSavingAccountBalance(amount) {
        setBalance(amount, savingAccountBalance);
    }

    /**
     * Updates the pending balance displayed in the dashboard.
     *
     * @param {number} amount - The pending balance.
     * @returns {void}
     */
    function setPendingBalance(amount) {

        // Hide the static currency symbol in the HTML first because `formatCurrency`
        // includes the currency symbol in the formatted amount.
        currencySymbol.style.display = "none";
        setBalance(formatCurrency(amount), pendingBalance);
    }

    /**
     * Updates the total account balance displayed in the dashboard.
     *
     * @param {number} amount - The combined account balance.
     * @returns {void}
     */
    function setTotalAccountBalance(amount) {
        setBalance(amount, totalAccountsBalance);
    }

    /**
     * Updates the bank balance displayed in the dashboard navigation.
     *
     * @param {number} amount - The bank balance to display.
     * @returns {void}
     */
    function setNavBankBalance(amount) {
        setBalance(amount, navBankBalance);
    }

    return {
        setCurrentAccountBalance,
        setSavingAccountBalance,
        setPendingBalance,
        setTotalAccountBalance,
        setNavBankBalance,
    }

})()
