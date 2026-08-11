import { toggleElement } from "../../utils.js";
import { AlertUtils } from "../../alerts.js";
import { handleWalletStatusClick, handleWalletDisconnectInput } from "./WalletStatus.js";
import { WalletWizardIds } from "./walletWizard.js";


// ---------------------------------------------------------------------------
// Wallet DOM references
// ---------------------------------------------------------------------------

const walletAuthForm = document.getElementById("connect-wallet-form");
const linkAccountForm = document.getElementById("link-wallet-form");
const walletManualForm = document.getElementById( "manually-verification-wallet-form");
const walletManualFormSection = document.getElementById("link-wallet-verifcation");

const progressElement = document.getElementById("walletProgress");
const progressValue = document.getElementById("walletProgressValue");

const walletAuthInputFieldPanel = document.getElementById("connect-with-wallet-id");

const walletOptionAuthInputFields = document.querySelectorAll("#connect-wallet-auth-id-wrapper input");


// ---------------------------------------------------------------------------
// Wallet connection progress
// ---------------------------------------------------------------------------

function setWalletProgress(percent) {
    const completionPercentage = "100%";

    if (progressElement) {
        progressElement.style.setProperty("--progress", percent);
    }

    if (progressValue) {
        progressValue.textContent = `${percent}%`;
    }

    if (progressValue?.textContent === completionPercentage) {
        const innerProgressBar = document.querySelector(".wallet-progress");

        if (innerProgressBar) {
            innerProgressBar.style.background = "#16A34A";
            showWalletAuthCompletionMsg();
        }
    }
}

function startProgress() {
    let progress = 0;
    const MILLI_SECONDS = 25;

    setWalletProgress(0);

    const interval = setInterval(() => {
        progress += 1;
        setWalletProgress(progress);

        if (progress >= 100) {
            clearInterval(interval);
        }
    }, MILLI_SECONDS);
}

function showWalletAuthCompletionMsg() {
    const container = document.getElementById("wallet-auth-completion");

    if (!container) return;

    toggleElement({
        element: container,
        cSSSelector: "hide",
        show: false
    });
}

function removeAuthWalletVerifyBtn() {
    const button = document.getElementById("auth-verify-btn");

    if (!button) return;

    button.style.display = "none";
}

// ---------------------------------------------------------------------------
// Wallet authentication
// ---------------------------------------------------------------------------

function handleWalletAuthForm(event) {
    event.preventDefault();

    console.log(event.target.id);

    startProgress();
    removeAuthWalletVerifyBtn();
}

// ---------------------------------------------------------------------------
// Wallet linking
// ---------------------------------------------------------------------------

async function handleWalletLinkFormSubmission(event, WalletWizard) {
    event.preventDefault();

    const confirmed = await AlertUtils.showConfirmationAlert({
        title: "Link wallet to bank account?",
        text: "This will securely link your wallet so funds can move between accounts.",
        confirmButtonText: "Link account",
        messageToDisplayOnSuccess: "The accounts have been linked",
        denyButtonText: "Cancel",
        cancelMessage: "Wallet linking cancelled."
    });

    if (confirmed) {
        WalletWizard.closeModal();
    }
}

// ---------------------------------------------------------------------------
// Manual wallet verification
// ---------------------------------------------------------------------------

let walletModalStep2Button;

function disableStep2Button() {
    if (!walletModalStep2Button) {
        walletModalStep2Button = document.getElementById(
            WalletWizardIds.STEP2_BTN
        );
    }

    if (!walletModalStep2Button) return;

    walletModalStep2Button.disabled = true;
    walletModalStep2Button.textContent = "Disabled";
    walletModalStep2Button.style.opacity = "0.5";
}

function enableStep2Button() {
    if (!walletModalStep2Button) {
        walletModalStep2Button = document.getElementById(
            WalletWizardIds.STEP2_BTN
        );
    }

    if (!walletModalStep2Button) return;

    walletModalStep2Button.disabled = false;
    walletModalStep2Button.textContent = "Continue";
    walletModalStep2Button.style.opacity = "1";
}

function handleManualFormSubmission(event) {
    event.preventDefault();

    AlertUtils.showAlert({
        title: "Wallet verified",
        text: "Your wallet credentials have been successfully verified. You can now proceed with linking the wallet",
        icon: "success",
        confirmButtonText: "Continue"
    });

    toggleElement({
        element: walletManualFormSection,
        show: false
    });

    enableStep2Button();
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

/**
 * Initializes all wallet-related event listeners.
 *
 * WalletWizard is injected because its implementation was not present
 * in the uploaded source file.
 */
function initializeWallet({dashboard, WalletWizard}) {
    if (!dashboard) {
        throw new Error("initializeWallet: dashboard is required.");
    }

    if (!WalletWizard) {
        throw new Error("initializeWallet: WalletWizard is required.");
    }

    dashboard.addEventListener("click", (event) => {
        handleWalletWizardClick(event, WalletWizard);
        handleWalletStatusClick(event, WalletWizard);
    });

    dashboard.addEventListener("input", (event) => {
        handleWalletWizardInput(event, WalletWizard);
        handleWalletDisconnectInput(event);
    });

    dashboard.addEventListener("keydown", (event) => {
        handleWalletWizardKeydown(event, WalletWizard);
    });

    walletAuthForm?.addEventListener(
        "submit",
        handleWalletAuthForm
    );

    linkAccountForm?.addEventListener(
        "submit",
        (event) => handleWalletLinkFormSubmission(event, WalletWizard)
    );

    walletManualForm?.addEventListener(
        "submit",
        handleManualFormSubmission
    );
}

export {
    walletAuthForm,
    linkAccountForm,
    walletManualForm,
    walletManualFormSection,
    walletAuthInputFieldPanel,
    walletOptionAuthInputFields,
    progressElement,
    progressValue,

    setWalletProgress,
    startProgress,
    showWalletAuthCompletionMsg,
    removeAuthWalletVerifyBtn,

    handleWalletAuthForm,
    handleWalletLinkFormSubmission,

    disableStep2Button,
    enableStep2Button,
    handleManualFormSubmission,

    initializeWallet
};
