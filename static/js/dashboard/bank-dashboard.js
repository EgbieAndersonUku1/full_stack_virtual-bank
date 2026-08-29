import { BankFundInput } from "./bank/funds/addFunds.js";

import { DashboardCardSidePanel } from "./bank/sidePanel/panel.js";
import { ViewTransactionsModal } from "./bank/viewTransactions/transactionModal.js";
import { handleWalletStatusClick } from "./wallet/WalletStatus.js";
import { handleDisconnecectionConfirmationButton } from "./wallet/status/disconnect.js";
import { handleWalletAuthForm, walletAuthForm } from "./wallet/wallet.js";
import { WalletWizard, handleWalletLinkFormSubmission } from "./wallet/walletWizard.js";


const dashboard = document.getElementById("dashboard");
const linkAccountForm = document.getElementById("link-wallet-form");
const walletManualForm = document.getElementById("manually-verification-wallet-form");


const excludeFields = new Set(["username", "email", "wallet-disconnect-inputfield",
    "transfer-type", "from", "to", "transaction-type", "transfer-amount"]);
const excludeTypes = new Set(["checkbox", "radio", "password", "email", "textarea"]);



dashboard.addEventListener("click", handleDelegation);
dashboard.addEventListener("change", handleDelegation)
walletAuthForm.addEventListener("submit", handleWalletAuthForm);




/**
 * Sets up dashboard and wallet form event delegation.
 * - Handles input in dashboard fields for wallet auth.
 * - Handles Backspace/Delete key navigation.
 * - Handles wallet linking and manual form submissions.
 */
dashboard.addEventListener("input", (e) => {
    const target = e.target;

    // Skip excluded types or IDs
    if (excludeTypes.has(target.type) || excludeFields.has(target.id)) return;
    WalletWizard.handleWalletConnectAuthInputFields(e);
    handleDisconnecectionConfirmationButton(e)
});


dashboard.addEventListener("keydown", (e) => {
    WalletWizard.handleBackspaceOrDelete(e);
});


/**
 * Events listeners
 */
linkAccountForm.addEventListener("submit", handleWalletLinkFormSubmission);
walletManualForm.addEventListener("submit", WalletWizard.handleManualFormSubmission);




/**
 * Delegates wallet connection UI events to WalletWizard.
 * @param {Event} e Click or submit event.
 */
async function handleDelegation(e) {

    WalletWizard.handleWalletConnectionSteps(e);
    handleWalletStatusClick(e);

    BankFundInput.handleEvents(e);
    DashboardCardSidePanel.handleEvents(e);

    ViewTransactionsModal.handleEvent(e);

}




















