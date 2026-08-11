import { toggleElement, sanitizeText } from "../../utils.js";
import { AlertUtils } from "../../alerts.js";

const connectWalletModal = document.getElementById("connect-wallet-modal");
const walletAuthInputFieldPanel = document.getElementById("connect-with-wallet-id");
const connectWalletStepOne = document.getElementById("connect-wallet-modal__step-one");
const connectWalletStepThree = document.getElementById("connect-wallet-modal__step-three");
const connectWalletStepTwo = document.getElementById("connect-wallet-modal__step-two");
const walletManualFormSection = document.getElementById("link-wallet-verifcation");
const walletOptionAuthInputFields = document.querySelectorAll("#connect-wallet-auth-id-wrapper input");



// ---------------------------------------------------------------------------
// Wallet Wizard
// ---------------------------------------------------------------------------

const WalletWizardIds = {
    AUTH_CANCEL_BTN: "auth-wallet__cancel-btn",
    BACK_ANCHOR: "wallet-modal-connect-back-anchor",
    CANCEL_BTN: "connect-wallet__cancel-btn",
    CONNECT_BTN: "connect-wallet-btn",
    MANUAL_CONNECTION: "select-manual-connection",
    MANUAL_FORM_BACK: "wallet-manually-form-back-step",
    PREVIOUS_STEP1: "wallet-modal-previous-step1",
    PREVIOUS_STEP2: "wallet-modal-previous-step2",
    STEP1_BTN: "connect-wallet-step1-btn",
    STEP2_BTN: "connect-wallet-step2-btn",
    WALLET_ID_CONNECT: "wallet-id-connect"
};



/**
 * WalletWizard handles the multi-step connect wallet modal flow.
 *
 * Steps can be navigated dynamically with next/back buttons.
 * It also manages showing/hiding the modal and individual steps.
 */
export const WalletWizard = (() => {
    // Cached DOM elements
    let walletModalStep2Button;

    /**
     * Hides the wallet authentication input panel.
     */
    function closeWalletAuthPanel() {
        toggleElement({
            element: walletAuthInputFieldPanel,
            show: false
        });
    }

    /**
     * Opens the wallet authentication input panel
     * and disables the Step 2 action.
     */
    function openWalletAuthInputPanel() {
        disableStep2Button();

        toggleElement({
            element: walletAuthInputFieldPanel,
            show: true
        });
    }

    /**
     * Disables the Step 2 button in the wallet wizard.
     */
    function disableStep2Button() {
        if (!walletModalStep2Button) {
            walletModalStep2Button = document.getElementById(
                "connect-wallet-step2-btn"
            );
        }

        if (!walletModalStep2Button) {
            return;
        }

        walletModalStep2Button.disabled = true;
        walletModalStep2Button.textContent = "Disabled";
        walletModalStep2Button.style.opacity = "0.5";
    }

    /**
     * Enables the Step 2 button in the wallet wizard.
     */
    function enableStep2Button() {
        if (!walletModalStep2Button) {
            walletModalStep2Button = document.getElementById(
                "connect-wallet-step2-btn"
            );
        }

        if (!walletModalStep2Button) {
            return;
        }

        walletModalStep2Button.disabled = false;
        walletModalStep2Button.textContent = "Continue";
        walletModalStep2Button.style.opacity = "1";
    }

    /**
     * Handles wallet ID selection and prepares authentication fields.
     *
     * @param {Event} e Click event.
     */
    function selectWalletIdConnect(e) {
        disableStep2Button();
        handleWalletConnectAuthInputFields(e);
    }

    /**
     * Shows or hides the manual wallet connection form.
     *
     * @param {boolean} show Whether to display the manual connection form.
     */
    function selectManualConnection(show = true) {
        if (show) {
            disableStep2Button();

            toggleElement({
                element: walletManualFormSection,
                show: true
            });

            return;
        }

        enableStep2Button();

        toggleElement({
            element: walletManualFormSection,
            show: false
        });
    }

    /**
     * Opens the modal and displays step one.
     */
    function goToStepOne() {
        openModal();
        showStep(connectWalletStepOne);
    }

    /**
     * Navigates to wallet connection step two.
     */
    function goToStepTwo() {
        hideAllSteps();
        showStep(connectWalletStepTwo);
    }

    /**
     * Navigates to wallet connection step three.
     */
    function goToStepThree() {
        hideAllSteps();
        showStep(connectWalletStepThree);
    }

    /**
     * Opens the wallet modal and resets steps.
     */
    function openModal() {
        toggleElement({
            element: connectWalletModal,
            show: true
        });

        hideAllSteps();
    }

    /**
     * Closes the wallet modal and clears step visibility.
     */
    function closeModal() {
        toggleElement({
            element: connectWalletModal,
            show: false
        });

        hideAllSteps();
    }

    /**
     * Displays a given wizard step.
     *
     * @param {HTMLElement} step Step element to show.
     */
    function showStep(step) {
        toggleElement({
            element: step,
            show: true
        });
    }

    /**
     * Navigates to the previous step.
     *
     * @param {number} stepNumber Current step number.
     */
    function previousStep(stepNumber) {
        if (stepNumber === 2) {
            goToStepTwo();
            return;
        }

        goToStepOne();
    }

    /**
     * Hides all wizard steps.
     */
    function hideAllSteps() {
        [
            connectWalletStepOne,
            connectWalletStepTwo,
            connectWalletStepThree
        ].forEach((step) => {
            toggleElement({
                element: step,
                show: false
            });
        });
    }

    /**
     * Handles deletion navigation in auth input fields.
     *
     * @param {KeyboardEvent} e Key event.
     */
    function handleBackspaceOrDelete(e) {
        if (e.key === "Backspace" || e.key === "Delete") {
            handleWalletConnectAuthInputFields(e, true);
        }
    }

    /**
     * Manages auth input field focus and navigation.
     *
     * @param {Event} e Input event.
     * @param {boolean} deleteMode Whether navigation is triggered by deletion.
     */
    function handleWalletConnectAuthInputFields(e, deleteMode = false) {
        openWalletAuthInputPanel();

        walletOptionAuthInputFields[0]?.focus();

        if (e?.target) {
            e.target.value = sanitizeText(e.target.value, true);
        }

        for (
            let currentIndex = 1;
            currentIndex < walletOptionAuthInputFields.length;
            currentIndex++
        ) {
            const previousIndex = currentIndex - 1;
            const lastIndex = walletOptionAuthInputFields.length - 1;

            if (!walletOptionAuthInputFields[previousIndex].value) {
                return;
            }

            if (!deleteMode) {
                walletOptionAuthInputFields[currentIndex].focus();
            } else {
                walletOptionAuthInputFields[previousIndex].focus();
            }

            // Ensure the last field clears correctly during deletion.
            if (currentIndex === lastIndex && deleteMode) {
                walletOptionAuthInputFields[currentIndex].value = "";
            }

            if (currentIndex === lastIndex && !deleteMode) {
                walletOptionAuthInputFields[currentIndex].focus();
            }
        }
    }

    /**
     * Central event handler for wallet connection UI actions.
     *
     * @param {Event} e Click event.
     */
    function handleWalletConnectionSteps(e) {
        const elementID = e.target.id;

        if (elementID === "modal-close-btn") {
            closeModal();
            return;
        }

        switch (elementID) {
            case WalletWizardIds.CONNECT_BTN:
                goToStepOne();
                break;

            case WalletWizardIds.STEP1_BTN:
                goToStepTwo();
                break;

            case WalletWizardIds.STEP2_BTN:
                goToStepThree();
                break;

            case WalletWizardIds.WALLET_ID_CONNECT:
                selectWalletIdConnect(e);
                break;

            case WalletWizardIds.CANCEL_BTN:
                closeModal();
                break;

            case WalletWizardIds.AUTH_CANCEL_BTN:
                enableStep2Button();
                closeWalletAuthPanel();
                break;

            case WalletWizardIds.PREVIOUS_STEP2:
                previousStep(2);
                break;

            case WalletWizardIds.PREVIOUS_STEP1:
                previousStep(1);
                break;

            case WalletWizardIds.BACK_ANCHOR:
                enableStep2Button();
                closeWalletAuthPanel();
                previousStep(2);
                break;

            case WalletWizardIds.MANUAL_CONNECTION:
                selectManualConnection();
                break;

            case WalletWizardIds.MANUAL_FORM_BACK:
                previousStep(2);
                selectManualConnection(false);
                break;

            default:
                break;
        }
    }


    /**
     * Handles submission of the manual wallet connection form.
     * Shows a success alert, hides the manual form, and enables Step 2 button.
     * @param {Event} e Form submit event.
     */
    function handleManualFormSubmission(e) {

        e.preventDefault();

        AlertUtils.showAlert({
            title: "Wallet verified",
            text: "Your wallet credentials have been successfully verified. You can now proceed with linking the wallet",
            icon: "success",
            confirmButtonText: "Continue"
        });

        toggleElement({ element: walletManualFormSection, show: false });
        enableStep2Button();
    }


    // Public API
    return {
        goToStepOne,
        goToStepTwo,
        goToStepThree,
        openModal,
        closeModal,
        showStep,
        previousStep,
        hideAllSteps,
        handleBackspaceOrDelete,
        handleWalletConnectAuthInputFields,
        handleWalletConnectionSteps,
        handleManualFormSubmission,
    };
})();




/**
 * Delegates wallet wizard click events to the existing WalletWizard object.
 */
function handleWalletWizardClick(event, WalletWizard) {
    WalletWizard.handleWalletConnectionSteps(event);
}

/**
 * Delegates wallet wizard input events to the existing WalletWizard object.
 */
function handleWalletWizardInput(event, WalletWizard) {
    const excludedTypes = new Set([
        "checkbox",
        "radio",
        "password",
        "email",
        "textarea"
    ]);

    const excludedFields = new Set([
        "username",
        "email",
        "wallet-disconnect-inputfield",
        "transfer-type",
        "from",
        "to",
        "transaction-type",
        "transfer-amount"
    ]);

    const target = event.target;

    if (
        excludedTypes.has(target.type) ||
        excludedFields.has(target.id)
    ) {
        return;
    }

    WalletWizard.handleWalletConnectAuthInputFields(event);
}

/**
 * Delegates wallet wizard keyboard events.
 */
function handleWalletWizardKeydown(event, WalletWizard) {
    WalletWizard.handleBackspaceOrDelete(event);
}





/**
 * Handles the form link confirmation form, the final step before
 * a wallet is linked to the bank account.
 */
export async function handleWalletLinkFormSubmission(e) {
    e.preventDefault();

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



export {
    WalletWizardIds,
    handleWalletWizardClick,
    handleWalletWizardInput,
    handleWalletWizardKeydown,

};
