import { toggleElement } from "../../utils.js";
import { AlertUtils } from "../../alerts.js";
import { WalletWizard } from "./walletWizard.js";

// ---------------------------------------------------------------------------
// Wallet status DOM references
// ---------------------------------------------------------------------------

const statusWalletDisconnectPanel =
    document.getElementById("dashboard__status");

const disconnectInputFieldElement = document.getElementById(
    "wallet-disconnect-inputfield"
);

const disconnectConfirmaionPanel = document.getElementById(
    "wallet-disconnection-confirmation"
);






/**
 * Updates the wallet connection progress UI.
 * - Sets the CSS progress value
 * - Updates the visible percentage
 * - Handles completion state at 100%
 *
 * @param {number} percent - Progress percentage (0–100)
 */
function setWalletProgress(percent) {
    const completionPercentage = "100%";

    progressElement.style.setProperty("--progress", percent);
    progressValue.textContent = percent + "%";

    if (progressValue.textContent === completionPercentage) {
        const innerProgressBar = document.querySelector(".wallet-progress");

        if (innerProgressBar) {
            innerProgressBar.style.background = "#16A34A";
            showWalletAuthCompletionMsg();

        }
    }
}



/**
 * Starts the wallet authentication progress animation.
 * Increments progress until completion is reached.
 */
function startProgress() {
    let progress = 0;
    setWalletProgress(0);
    const MILLI_SECONDS = 25

    const interval = setInterval(() => {
        progress += 1;
        setWalletProgress(progress);

        if (progress >= 100) {
            clearInterval(interval);
        }
    }, MILLI_SECONDS);
}

// ---------------------------------------------------------------------------
// Wallet disconnect
// ---------------------------------------------------------------------------

async function handleWalletDisconnect() {
    const expectedWord = "disconnect";

    if (!disconnectInputFieldElement) return;

    if (
        disconnectInputFieldElement.value.length <
        expectedWord.length
    ) {
        return;
    }

    if (
        disconnectInputFieldElement.value.toLowerCase() !==
        expectedWord
    ) {
        return;
    }

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
    }
}

function handleWalletDisconnectInput() {
    handleWalletDisconnect();
}

// ---------------------------------------------------------------------------
// Wallet connection status actions
// ---------------------------------------------------------------------------

async function handleRefreshConnection() {
    await AlertUtils.showConfirmationAlert({
        title: "Refresh wallet connection?",
        text: "This will refresh your current wallet connection.",
        confirmButtonText: "Refresh connection",
        messageToDisplayOnSuccess: "Wallet connection refreshed successfully.",
        denyButtonText: "Cancel",
        cancelMessage: "No changes were made."
    });
}

async function handleTestConnection() {
    await AlertUtils.showConfirmationAlert({
        title: "Test wallet connection?",
        text: "This will test if your wallet connection is working properly.",
        confirmButtonText: "Run test",
        messageToDisplayOnSuccess: "Wallet connection is working!",
        denyButtonText: "Cancel",
        cancelMessage: "No changes were made."
    });
}

// ---------------------------------------------------------------------------
// Wallet status panels
// ---------------------------------------------------------------------------

function handleWalletStatusClick(event, WalletWizard) {
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


function closeStatusPanels() {
    toggleElement({
        element: statusWalletDisconnectPanel,
        show: false
    });

    closeConfirmationPanel();
    clearDisconnectInputField();
}

function closeConfirmationPanel() {
    toggleElement({
        element: disconnectConfirmaionPanel,
        show: false
    });
}

function clearDisconnectInputField() {
    if (disconnectInputFieldElement) {
        disconnectInputFieldElement.value = "";
    }
}




/**
 * Toggles visibility of various status and confirmation panels
 * based on which button was clicked.
 * @param {MouseEvent} e - The click event.
 * @returns {void}
 */
function toggleStatusPanel(e) {

    if (e.target.id === "disconnect-wallet-status") {
        statusWalletDisconnectPanel.classList.add("show");
        return;
    }

    const buttonID = e.target.closest("button")?.id;

    switch (buttonID) {
        case "disconnect-btn":

            toggleElement({ element: disconnectConfirmaionPanel });
            disconnectInputFieldElement.focus()
            break;
        case "confirm-disconnect-btn":
            handleDisconnecectionConfirmationButton();
            break;
        case "cancel-disconnect-btn":
            toggleElement({ element: disconnectConfirmaionPanel, show: false });
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


/**
 * Handles clicks on status buttons.
 * Delegates the click to toggleStatusPanel.
 * @param {MouseEvent} e - The click event.
 * @returns {void}
 */
export function handleStatusButtonClick(e) {
    toggleStatusPanel(e)
}


export {
    statusWalletDisconnectPanel,
    disconnectInputFieldElement,
    disconnectConfirmaionPanel,

    handleWalletDisconnect,
    handleWalletDisconnectInput,

    handleRefreshConnection,
    handleTestConnection,

    handleWalletStatusClick,
    closeStatusPanels,
    closeConfirmationPanel,
    clearDisconnectInputField
};
