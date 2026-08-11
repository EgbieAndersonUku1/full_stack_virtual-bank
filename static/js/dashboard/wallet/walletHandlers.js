import { AlertUtils } from "../../alerts.js";
import { WalletWizard } from "./walletWizard.js";


/**
 * Handles the confirmation process for disconnecting a wallet.
 * @async
 * @returns {Promise<void>}
 */
async function handleDisconnecectionConfirmationButton() {
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



export function handleWalletStatusClick(event, WalletWizard) {
    if (event.target.id === "disconnect-wallet-status") {
        statusWalletDisconnectPanel?.classList.add("show");
        return;
    }

    const buttonID = event.target.closest("button")?.id;

    switch (buttonID) {
        case "disconnect-btn":
            toggleElement({
                element: disconnectConfirmaionPanel
            });

            disconnectInputFieldElement?.focus();
            break;

        case "confirm-disconnect-btn":
            handleWalletDisconnect();
            break;

        case "cancel-disconnect-btn":
            toggleElement({
                element: disconnectConfirmaionPanel,
                show: false
            });
            break;

        case "disconnection-modal-close-btn":
            closeConfirmationPanel();
            break;

        case "dashboard-status-modal-close-btn":
            closeStatusPanels();
            break;

        case "refresh-connection-btn":
            handleRefreshConnection();
            break;

        case "test-connection-btn":
            handleTestConnection();
            break;

        case "connect-modal-close-btn":
            WalletWizard.closeModal();
            break;
    }
}
