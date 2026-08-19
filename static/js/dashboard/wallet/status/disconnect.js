import { toggleElement } from "../../../utils.js";
import { AlertUtils } from "../../../alerts.js";
import { WalletWizard } from "../walletWizard.js";

const statusWalletDisconnectPanel = document.getElementById("dashboard__status");
const disconnectInputFieldElement = document.getElementById("wallet-disconnect-inputfield");



/**
 * Handles the confirmation process for disconnecting a wallet.
 * @async
 * @returns {Promise<void>}
 */
export async function handleDisconnecectionConfirmationButton() {
    const expectedWord = "disconnect";

    if (!disconnectInputFieldElement) return;
    if (disconnectInputFieldElement.value.length < expectedWord.length) return;
    if (disconnectInputFieldElement.value.toLowerCase() !== expectedWord) return;

    const confirmed = await AlertUtils.showConfirmationAlert({
        title: "Are you sure you want to disconnect wallet?",
        text: "This action will disconnect your wallet from your bank, and stop all information.",
        confirmButtonText: "Disconnect wallet",
        messageToDisplayOnSuccess: "The wallet has been disconnected",
        denyButtonText: "Cancel Disconnect",
        cancelMessage: "No action taken."
    });

    if (confirmed) {
        closeStatusPanels();
        WalletWizard.closeModal();
    }
}


/**
 * Closes all wallet-related status panels and clears input fields.
 * @returns {void}
 */
function closeStatusPanels() {
    toggleElement({ element: statusWalletDisconnectPanel, show: false })
    closeConfirmationPanel();
    clearDisconnectInputField();
}


/**
 * Closes the disconnect confirmation panel.
 * @returns {void}
 */
function closeConfirmationPanel() {
    toggleElement({ element: disconnectConfirmaionPanel, show: false })
}


/**
 * Clears the input field used for confirming wallet disconnection.
 * @returns {void}
 */
function clearDisconnectInputField() {
    disconnectInputFieldElement.value = "";
}

