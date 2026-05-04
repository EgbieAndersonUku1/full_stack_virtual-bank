import { sanitizeText, formatCurrency, parseCurrency, checkIfHTMLElement, deselectAllElements, selectElement, toTitle  } from "../utils.js";
import { AlertUtils } from "../alerts.js";
import { cardImplementer, createCardDetails } from "../card/cardBuilder.js";
import { minimumCharactersToUse } from "../utils/password/textboxCharEnforcer.js";
import { warnError } from "../logger.js";
import { parseFormData } from "../formUtils.js";




const connectWalletModal = document.getElementById("connect-wallet-modal");
const connectWalletStepOne = document.getElementById("connect-wallet-modal__step-one");
const connectWalletStepThree = document.getElementById("connect-wallet-modal__step-three");
const connectWalletStepTwo = document.getElementById("connect-wallet-modal__step-two");
const dashboard = document.getElementById("dashboard");
const linkAccountForm = document.getElementById("link-wallet-form");
const progressElement = document.getElementById("walletProgress");
const progressValue = document.getElementById("walletProgressValue");
const walletAuthForm = document.getElementById("connect-wallet-form");
const walletAuthInputFieldPanel = document.getElementById("connect-with-wallet-id");
const walletManualForm = document.getElementById("manually-verification-wallet-form");
const walletManualFormSection = document.getElementById("link-wallet-verifcation");
const walletOptionAuthInputFields = document.querySelectorAll("#connect-wallet-auth-id-wrapper input");
const statusWalletDisconnectPanel = document.getElementById("dashboard__status")
const disconnectInputFieldElement = document.getElementById("wallet-disconnect-inputfield");
const disconnectConfirmaionPanel = document.getElementById("wallet-disconnection-confirmation");
const amountInputField = document.getElementById("account-card__amount");
const bankCardSelectionTypes = document.querySelectorAll(".account-card");
const addFundsToBankPanel = document.getElementById("bank-account-add-funds");
const viewBankTransacionPanel = document.getElementById("bank-account-view-transactions");
const fullCardDetailsContainer = document.getElementById("full-card-details");
const cardDetailsContainer = document.getElementById("full-card-details-info");
const bankCardButtons = document.querySelector(".view-card-panel-buttons");
let creditCardsNodeElements = document.querySelectorAll(".bank-card");

const viewExtraCardInfo = document.getElementById("view-more-bank-card");
const extraCardInfoPanel = document.getElementById("view-card-panel");
const cardTransferFormSection = document.getElementById("bank-funds-transfer");
const selectCardsContainer = document.getElementById("bank-funds-transfer__select-cards-panel");

const transferFormTextArea = document.getElementById("bank-transfer-note");
const fundsTransferForm = document.getElementById("funds-transfer-form")
const askTransferConfirmationPanel = document.getElementById("bank-transfer-quick-confirmation");

const sourceCardNumberElement = document.querySelector(".transfer-confirmation__source-account-value");
const targetCardNumberElement = document.querySelector(".transfer-confirmation__target-account-value");
const transferAmountElement = document.querySelector('.transfer-confirmation__summary-value');

// hidden form values

const MAX_TRANSFER_AMOUNT = 1_000_000;
let walletModalStep2Button;

const excludeFields = new Set(["username", "email", "wallet-disconnect-inputfield", 
                             "transfer-type", "from", "to", "transaction-type", "transfer-amount"]);
const excludeTypes = new Set(["checkbox", "radio", "password", "email", "textarea"]);


// controls the number of characters the user can use in the textarea form for the transfer
minimumCharactersToUse(transferFormTextArea, {
    minCharClass: ".num-of-characters-remaining",
    maxCharClass: ".num-of-characters-to-use",
    minCharMessage: "Minimum characters to use: ",
    maxCharMessage: "Number of characters remaining: ",
    minCharsLimit: 50,
    maxCharsLimit: 255,
    disablePaste: true,
})



// Constants for wallet modal element IDs
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



// TODO add one time checker here for one time static element check

dashboard.addEventListener("click", handleDelegation);
dashboard.addEventListener("change", handleDelegation)
walletAuthForm.addEventListener("submit", handleWalletAuthForm);
amountInputField.addEventListener("keydown", handleEnter);
fundsTransferForm.addEventListener("submit", handleTransferForm)




// records the select option for the select form,
// so that can be displayed in the confirmation
// modal panel.
const transferFormSelectOption = {

    optionSelection: null,

    /**
     * Stores the selected option for the form  e.g wallet or bank
     * Only accepts a valid HTMLElement to prevent invalid state.
     */
    set(selection) {
        this.optionSelection = selection
    },

    
    /**
     * Returns the selected option e.g "wallet" or "bank"
     */
    getSelection() {

        return  this.optionSelection ? toTitle(this.optionSelection): null;
    },

    
    /**
     * Clears the option for the selection
     */
    clear() {
        this.optionSelection = null;
    }
}



/**
 * Manages the open/closed state of the card selection panel.
 *
 * This object is used to track whether the card selection panel
 * is currently open, allowing the application to handle user
 * interactions appropriately (e.g., ensuring a target card is
 * selected before confirming a transfer).
 */
const cardSelectionPanelState = {

    /** Whether the card selection panel is open (true) or closed (false). */
    isOpen: false,

    /**
     * Sets the panel state to open or closed.
     *
     * @param {boolean} open - True to open the panel, false to close. Defaults to false.
     * @throws {Error} If `open` is not a boolean.
     */
    set(open = false) {
        if (typeof open !== "boolean") {
            throw new Error(`Expected boolean but received ${typeof open}: ${open}`);
        }
        this.isOpen = open;
    },

    /**
     * Returns whether the panel is currently open.
     *
     * @returns {boolean} True if open, false if closed.
     */
    isPanelOpen() {
        return this.isOpen;
    },

    /**
     * Resets the panel state to closed.
     */
    clear() {
        this.isOpen = false;
    }

};



// records which card was clicked
const selectedCardStore = {
    element: null,

    /**
     * Stores the selected card element.
     * Only accepts a valid HTMLElement to prevent invalid state.
     *
     * @param {HTMLElement|null} cardElement - The card DOM element to store.
     *                                           Pass null to clear selection.
     */
    set(cardElement) {

        if (!checkIfHTMLElement(cardElement, "selectedCardStore", true)) return;
        this.element = cardElement;
    },

    /**
     * Returns the currently stored card element.
     *
     * @returns {HTMLElement|null} The selected card element or null if none is selected.
     */
    get() {
        return this.element;
    },

    /**
     * Clears the stored card selection.
     */
    clear() {
        this.element = null;
    }
};




/**
 * WalletWizard handles the multi-step connect wallet modal flow.
 * Steps can be navigated dynamically with next/back buttons.
 * It also manages showing/hiding the modal and individual steps.
 */const WalletWizard = (() => {

    // Cached DOM elements

    /** Hides the wallet authentication input panel. */
    function closeWalletAuthPanel() {
        toggleElement({ element: walletAuthInputFieldPanel, show: false });
    }

    /** Opens the wallet authentication panel and disables step 2 action. */
    function openWalletAuthInputPanel() {
        disableStep2Button();
        toggleElement({ element: walletAuthInputFieldPanel });
    }

    /** Handles wallet ID selection and prepares auth input fields. */
    function selectWalletIdConnect(e) {
        disableStep2Button();
        WalletWizard.handleWalletConnectAuthInputFields(e);
    }

    /**
     * Shows or hides manual wallet connection form.
     * @param {boolean} show Whether to display the manual connection form.
     */
    function selectManualConnection(show = true) {
        if (show) {
            disableStep2Button();
            toggleElement({ element: walletManualFormSection });
            return;
        }

        enableStep2Button();
        toggleElement({ element: walletManualFormSection, show: false });
    }

    // Public object
    return {

        /** Opens the modal and displays step one. */
        goToStepOne() {
            this.openModel();
            this.showStep(connectWalletStepOne);
        },

        /** Navigates to wallet connection step two. */
        goToStepTwo() {
            this.hideAllSteps();
            this.showStep(connectWalletStepTwo);
        },

        /** Navigates to wallet connection step three. */
        goToStepThree() {
            this.hideAllSteps();
            this.showStep(connectWalletStepThree);
        },

        /** Opens the wallet modal and resets steps. */
        openModel() {
            toggleElement({ element: connectWalletModal, show: true });
            this.hideAllSteps();
        },

        /** Closes the wallet modal and clears step visibility. */
        closeModal() {
            toggleElement({ element: connectWalletModal, show: false });
            this.hideAllSteps();
        },

        /**
         * Displays a given wizard step.
         * @param {HTMLElement} step Step element to show.
         */
        showStep(step) {
            toggleElement({ element: step, show: true });
        },

        /**
         * Navigates to the previous step.
         * @param {number} stepNumber Current step number.
         */
        previousStep(stepNumber) {
            if (stepNumber === 2) {
                this.goToStepTwo();
                return;
            }
            this.goToStepOne();
        },

        /** Hides all wizard steps. */
        hideAllSteps() {
            [connectWalletStepOne, connectWalletStepTwo, connectWalletStepThree].forEach(el =>
                toggleElement({ element: el, show: false })
            );
        },

        /**
         * Handles deletion navigation in auth input fields.
         * @param {KeyboardEvent} e Key event.
         */
        handleBackspaceOrDelete(e) {
            if (e.key === "Backspace" || e.key === "Delete") {
                this.handleWalletConnectAuthInputFields(e, true);
            }
        },

        /**
         * Manages auth input field focus and navigation.
         * @param {Event} e Input event.
         * @param {boolean} deleteMode Whether navigation is triggered by deletion.
         */
        handleWalletConnectAuthInputFields(e, deleteMode = false) {

            openWalletAuthInputPanel();
            walletOptionAuthInputFields[0]?.focus();

            if (e && e.target) {
                e.target.value = sanitizeText(e.target.value, true);
            }

            for (let currentIndex = 1; currentIndex < walletOptionAuthInputFields.length; currentIndex++) {
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

                // Ensure last field clears correctly during deletion.
                if (currentIndex === lastIndex && deleteMode) {
                    walletOptionAuthInputFields[currentIndex].value = "";
                }

                if (currentIndex === lastIndex && !deleteMode) {
                    walletOptionAuthInputFields[currentIndex].focus();
                }
            }
        },

        /**
         * Central event handler for wallet connection UI actions.
         * @param {Event} e Click event.
         */
        handleWalletConnectionSteps(e) {
            const elementID = e.target.id;

            if (elementID === "modal-close-btn") {
                WalletWizard.closeModal();
                return;
            }

            switch (elementID) {
                case WalletWizardIds.CONNECT_BTN:
                    WalletWizard.goToStepOne();
                    break;
                case WalletWizardIds.STEP1_BTN:
                    WalletWizard.goToStepTwo();
                    break;
                case WalletWizardIds.STEP2_BTN:
                    WalletWizard.goToStepThree();
                    break;
                case WalletWizardIds.WALLET_ID_CONNECT:
                    selectWalletIdConnect();
                    break;
                case WalletWizardIds.CANCEL_BTN:
                    WalletWizard.closeModal();
                    break;
                case WalletWizardIds.AUTH_CANCEL_BTN:
                    enableStep2Button();
                    closeWalletAuthPanel();
                    break;
                case WalletWizardIds.PREVIOUS_STEP2:
                    WalletWizard.previousStep(2);
                    break;
                case WalletWizardIds.PREVIOUS_STEP1:
                    WalletWizard.previousStep(1);
                    break;
                case WalletWizardIds.BACK_ANCHOR:
                    enableStep2Button();
                    closeWalletAuthPanel();
                    WalletWizard.previousStep(2);
                    break;
                case WalletWizardIds.MANUAL_CONNECTION:
                    selectManualConnection();
                    break;
                case WalletWizardIds.MANUAL_FORM_BACK:
                    WalletWizard.previousStep(2);
                    selectManualConnection(false);
                    break;
            }
        }
    };
})();







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
walletManualForm.addEventListener("submit", handleManualFormSubmission);




/**
 * Delegates wallet connection UI events to WalletWizard.
 * @param {Event} e Click or submit event.
 */
function handleDelegation(e) {

    WalletWizard.handleWalletConnectionSteps(e);
    handleStatusButtonClick(e);
    handleBankFundInput(e);
    handleBankCardTypes(e);
    handleFundAccountBtn(e);
    handleToggleAddFundsPanel(e);
    handleTableHightlight(e);
    handleToggleViewBankTransactionPanel(e);
    handleCardClick(e);
    handleViewMoreInfoCardClick(e);
    handleCardPanelButtons(e);
    handleCardSelectionTimeout(e);
    handleBankTransferSelectFormOptions(e);
    handleTransferConfirmationButtonClick(e);
    handleTransferCancelConfirmationButtonClick(e)



}




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



/**
 * Handles wallet authentication form submission.
 * Prevents default submit behaviour and starts progress flow.
 *
 * @param {Event} e - Form submit event
 */
function handleWalletAuthForm(e) {
    e.preventDefault();
    console.log(e.target.id)
    startProgress();
    removeAuthWalletVerifyBtn();
}


/**
 * Displays the wallet authentication completion message.
 */
function showWalletAuthCompletionMsg() {
    const container = document.getElementById("wallet-auth-completion");
    toggleElement({ element: container, cSSSelector: "hide", show: false });
}


/**
 * Removes the wallet verification button after successful authentication.
 */
function removeAuthWalletVerifyBtn() {
    const btn = document.getElementById("auth-verify-btn");
    btn.style.display = "none";
}



/**
 * Handles the form link confirmation form, the final step before
 * a wallet is linked to the bank account.
 */
async function handleWalletLinkFormSubmission(e) {
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


/**
 * Disables the Step 2 button in the wallet wizard.
 * Sets the button text to "Disabled" and reduces opacity.
 */
function disableStep2Button() {
    if (!walletModalStep2Button) {
        walletModalStep2Button = document.getElementById("connect-wallet-step2-btn");
    }

    walletModalStep2Button.disabled = true;
    walletModalStep2Button.textContent = "Disabled";
    walletModalStep2Button.style.opacity = "0.5";
}


/**
 * Enables the Step 2 button in the wallet wizard.
 * Sets the button text to "Continue" and restores full opacity.
 */
function enableStep2Button() {
    walletModalStep2Button.disabled = false;
    walletModalStep2Button.textContent = "Continue";
    walletModalStep2Button.style.opacity = "1";
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


/**
 * Handles clicks on status buttons.
 * Delegates the click to toggleStatusPanel.
 * @param {MouseEvent} e - The click event.
 * @returns {void}
 */
function handleStatusButtonClick(e) {
    toggleStatusPanel(e)
}

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

/**
 * Handles the wallet connection refresh action.
 * Shows a confirmation alert and displays a success message if confirmed.
 * @async
 * @returns {Promise<void>}
 */
async function handleRefreshConnection() {
    const confirmed = await AlertUtils.showConfirmationAlert({
        title: "Refresh wallet connection?",
        text: "This will refresh your current wallet connection.",
        confirmButtonText: "Refresh connection",
        messageToDisplayOnSuccess: "Wallet connection refreshed successfully.",
        denyButtonText: "Cancel",
        cancelMessage: "No changes were made."
    });
}

/**
 * Handles testing the wallet connection.
 * Shows a confirmation alert and displays a success message if confirmed.
 * @async
 * @returns {Promise<void>}
 */
async function handleTestConnection() {
    const confirmed = await AlertUtils.showConfirmationAlert({
        title: "Test wallet connection?",
        text: "This will test if your wallet connection is working properly.",
        confirmButtonText: "Run test",
        messageToDisplayOnSuccess: "Wallet connection is working!",
        denyButtonText: "Cancel",
        cancelMessage: "No changes were made."
    });
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


/**
 * Toggles the visibility of a DOM element.
 * @param {Object} options - Options object.
 * @param {HTMLElement} options.element - The element to toggle.
 * @param {cSSSelector} - The selector for the element
 * @param {boolean} options.show - Whether to show (true) or hide (false) the element.
 * @returns {void}
 */

function toggleElement({ element, cSSSelector = "show", show = true }) {
    if (!checkIfHTMLElement(element, "Unknown"));

    if (show) {
        element.classList.add(cSSSelector);
        return;
    }

    element.classList.remove(cSSSelector);
}




/**
 * Handles clicks on the plus and minus buttons for the bank fund input.
 *
 * This function:
 * 1. Checks the ID of the clicked element.
 * 2. If the "plus" button is clicked, increments the amount input field by 1 (default).
 * 3. If the "minus" button is clicked, decrements the amount input field by 1.
 *
 * @param {MouseEvent} e - The click event triggered on the plus or minus button.
 *
 * @example
 * // Attach this handler to the plus and minus buttons
 * plusButton.addEventListener('click', handleBankFundInput);
 * minusButton.addEventListener('click', handleBankFundInput);
 */
function handleBankFundInput(e) {

    switch (e.target.id) {
        case "plus":
            adjustCurrencyInput(amountInputField);
            break;
        case "minus":
            adjustCurrencyInput(amountInputField, -1);
            break;

    }

}




/**
 * Adjusts a currency input value by a specified number of pennies.
 * The function increase or decrease the amount by `0.01`. It also
 * assures that amount doesn't pass the maximum amount or minimum 
 * threshold
 *
 *
 * @param {HTMLInputElement} amountInputField - The input element containing the currency amount.
 * @param {number} [deltaPennies=1] - Number of pennies to adjust by.
 *        Use positive values to increase and negative values to decrease.
 * @param {number} - The maximum number the field cannot exceed by. Default 1,000,000
 * @param {number} - The minimun number the field cannot go below by. Default -
 *
 * @example
 * stepCurrencyInput(input, 1);   // Increase by £0.01
 * stepCurrencyInput(input, -1);  // Decrease by £0.01
 */
function adjustCurrencyInput(amountInputField, deltaPennies = 1, maxAmount = 1_000_000, minAmount = 0) {

    const current = Number(amountInputField.value) || 0;

    const pennies = Math.round(current * 100);
    const newAmount = (pennies + deltaPennies) / 100;


    if (newAmount > maxAmount || newAmount < minAmount) return;

    amountInputField.value = newAmount.toFixed(2);
}


/**
 * Handles the Enter key press on the amount input field.
 * 
 * When the Enter key is pressed, the function ensures that the input value
 * is within the defined minimum and maximum limits. It also formats it to two
 * decimal places.
 * 
 * @param {KeyboardEvent} e - The keyboard event triggered by a key press.
 */
function handleEnter(e) {
    if (e.key !== "Enter") return;

    const maxAmount = 1000000;
    const minAmount = 0;

    let value = Number(amountInputField.value) || 0;
    value = Math.min(Math.max(value, minAmount), maxAmount);

    amountInputField.value = value.toFixed(2);
}




/**
 * Handles the selection of bank card types when a user interacts with an account card.
 * 
 * This function checks if the clicked card is one of the expected account types 
 * (savings account, debit card, or wallet). If it is, it deselects all other 
 * bank card types and selects the clicked card.
 * 
 * @param {Event} e - The event triggered by user interaction (e.g., click).
 */
function handleBankCardTypes(e) {
    const accountCardSelector = ".account-card";
    const accountCard = e.target.closest(`${accountCardSelector}`);

    const expectedAccountTypes = ["savings-account", "debit-cards", "wallet"]

    if (!expectedAccountTypes.includes(accountCard?.dataset.account)) return;
    if (!checkIfHTMLElement(accountCard, "account card")) return;

    deselectAllElements(bankCardSelectionTypes, "active");
    selectElement(accountCard, "active")

}






/**
 * Handles the "Add Funds" button click for transferring money to the user's bank account
 * when the add funds button is clicked. The functions shows a confirmation message
 * before and after the transfer
 * 
 * @param {Event} e - The click event triggered by the user.
 */
async function handleFundAccountBtn(e) {
    const buttonId = "account_card__add_funds-btn";
    if (e.target.id !== buttonId) return;

    const amount = amountInputField.value;
    if (!amount || amount <= 0) return;


    if (amount > MAX_TRANSFER_AMOUNT) {
        resetTransferAmountToDefault();
        AlertUtils.showAlert({
            title: "Transfer amount too high",
            text: `The amount you entered exceeds the maximum allowed transfer of £${MAX_TRANSFER_AMOUNT.toLocaleString()}. Please enter an amount up to £${MAX_TRANSFER_AMOUNT.toLocaleString()}.`,
            icon: "warning",
            confirmButtonText: "OK",
        });


        return;
    }

    const confirmed = await AlertUtils.showConfirmationAlert({
        title: "Do you want to proceed?",
        text: `You about to transfer £${amount} to your bank account, do you want to proceed?`,
        confirmButtonText: "Transfer funds",
        messageToDisplayOnSuccess: "The funds have been transferred",
        denyButtonText: "Cancel Transfer",
        cancelMessage: "No action taken."
    });

    if (confirmed) {
        // This will be replaced with a fetch and at the momemnt it is simply a placeholder
        console.log("Funds have been transferred");
        clearAmountInputField();
    }

}


/**
 * Clears the amount input field by setting its value to an empty string.
 */
function clearAmountInputField() {
    amountInputField.value = "";
}


/**
 * Resets the transfer amount to the default amount
 */
function resetTransferAmountToDefault() {
    amountInputField.value = MAX_TRANSFER_AMOUNT.toFixed(2)
}


/**
 * Handles toggling the "Add Funds" panel open or closed based on which element is clicked.
 * 
 * Depending on the clicked button, this function either opens or closes the add funds panel.
 * 
 * @param {Event} e - The click event triggered by the user.
 */
function handleToggleAddFundsPanel(e) {
    const closeBtnId = "add-funds-close-panel";
    const addFundsBtn = "add-funds-bank";

    // console.log(e.target.id)
    // console.log("I am here")
    switch (e.target.id) {

        case closeBtnId:
            closeAddFundsPanel();
            break;
        case addFundsBtn:
            openAddFundsPanel();
            break;
    }
}



/**
 * Opens the "Add Funds" panel.
 * 
 * This function toggles the visibility of the add funds panel and sets focus 
 * to the amount input field for immediate user input.
 */
function openAddFundsPanel() {
    // console.log("open");
    toggleElement({ element: addFundsToBankPanel });
    amountInputField.focus(); // Focus input for convenience
}




/**
 * Closes the "Add Funds" panel.
 * 
 * This function hides the add funds panel by setting its visibility to false.
 */
function closeAddFundsPanel() {
    toggleElement({ element: addFundsToBankPanel, show: false }); // Hide the panel
}



/**
 * Toggles highlighting on a table row when clicked.
 *
 * This function listens for clicks on table rows and toggles a CSS class
 * to visually highlight the row. Rows with an `id` are ignored, as they
 * may represent special rows (e.g., headers or totals).
 *
 * Note for this work there must a css selector in the css file called1 `highlight-row`
 * otherwise no hightlight takes place.
 *
 * @param {MouseEvent} e - The click event object.
 * @returns {void} - Does not return a value; applies/removes highlight as a side effect.
 *
 * Usage:
 * document.querySelector("table").addEventListener("click", handleTableHighlight);
 */
function handleTableHightlight(e) {
    const tableRow = e.target.closest("tr");
    const cssSelector = "highlight-row";

    if (!tableRow || tableRow.id) return;

    tableRow.classList.toggle(cssSelector);

    // Accessibility: announce selection state
    const isSelected = tableRow.classList.contains(cssSelector);
    tableRow.setAttribute("aria-selected", isSelected);


}


/**
 * Handles clicks on the view and close buttons for the bank transaction panel.
 *
 * If the user clicks the "view transaction" button or the "close transaction" button,
 * this function toggles the visibility of the bank transaction panel. Clicks on any
 * other part of the document are ignored.
 *
 * This function also supports clicks on child elements inside the buttons using `closest`.
 *
 * @param {MouseEvent} e - The click event object.
 * @returns {void} - Does not return a value; toggles panel visibility as a side effect.
 */
function handleToggleViewBankTransactionPanel(e) {

    const viewTransactionButtonId = "view-transaction-btn";
    const closePanelId = "close-transaction-panel";

    const clickedViewBtn = e.target.closest(`#${viewTransactionButtonId}`);
    const clickedCloseBtn = e.target.closest(`#${closePanelId}`);


    if (!clickedViewBtn && !clickedCloseBtn) return;


    if (e.target.id === viewTransactionButtonId) {
        toggleElement({ element: viewBankTransacionPanel });
        return;
    }

    if (closePanelId) {
    
        toggleElement({ element: viewBankTransacionPanel, show: false });
    }




}

/**
 * Handles a click on a card by delegating to the appropriate card click handlers.
 *
 * This function:
 * 1. Processes clicks in the credit card overview panel.
 * 2. Processes clicks in the transfer card selection panel.
 *
 * Essentially, what it does is it centralizes all card click logic by calling:
 *  - `processCreditCardOverviewClick`
 *  - `processSelectedCardClick`
 *
 * @param {MouseEvent} e - The click event triggered on a card element.
 *
 * @example
 * // Attach this handler to the card container
 * cardContainer.addEventListener('click', handleCardClick);
 */
function handleCardClick(e) {
    processCreditCardOverviewClick(e);
    processSelectedCardClick(e);

}




/**
 * Handles the click event for the "View More Info" button on a bank card.
 *
 * This function:
 * 1. Checks if the clicked element is the correct "View More Info" button.
 *    - If not, exits early.
 * 2. Shows the extra card info panel.
 * 3. Displays the full details of the currently selected card.
 *
 * @param {MouseEvent} e - The click event triggered on the "View More Info" button.
 *
 * @example
 * // Attach this handler to the "View More Info" button
 * viewMoreButton.addEventListener('click', handleViewMoreInfoCardClick);
 */
function handleViewMoreInfoCardClick(e) {
    const viewMoreButtonId = "view-more-bank-card";

    if (e.target.id !== viewMoreButtonId) return;

    toggleElement({ element: extraCardInfoPanel, show: true });
    viewFullCardDetails();
}





/**
 * Handles a click on a card within the transfer card selection panel.
 *
 * This function:
 * 1. Determines if the clicked element is a selectable bank card.
 *    - If not, exits early.
 * 2. Deselects all other selectable transfer cards and marks the clicked card as selected.
 * 3. Updates hidden input fields with the source and target card IDs and the target card number,
 *    to be used in the transfer submission.
 *
 * @param {MouseEvent} e - The click event triggered on a selectable card in the transfer panel.
 *
 * @example
 * // Attach this handler to the card selection panel
 * transferCardSelectionPanel.addEventListener('click', processSelectedCardClick);
 */
function processSelectedCardClick(e) {


    const bankCardClass = "bank-card";
    const cssSelector = "is-selected"
    const targetCard = getSelectableCardElement(e, bankCardClass);


    if (targetCard === null) return;

    const transferToHiddenValueField = document.getElementById("transfer-to-card-id");
    const sourceCardHiddenValueField = document.getElementById("source-card");
    const targetCardHiddenNumberValueField = document.getElementById("transfer-to-card-number")


    // console.log("I have been clicked")
    // get the cards that the user can can choose from selection card window
    const transferCreditCardElement = document.querySelectorAll("#bank-funds-transfer__select-cards-panel .bank-transfer-card");

    deselectAllCards(transferCreditCardElement, cssSelector);
    selectElement(targetCard, cssSelector)

    if (!(transferToHiddenValueField && sourceCardHiddenValueField)) {
        warnError("processSelectedCardClick", `one or more of the hidden field is empyty.  
                                              transferToHiddenValueField = ${transferToHiddenValueField}  
                                              sourceCardHiddenValueField  = ${sourceCardHiddenValueField}
                                              `);

        return;
    }


    // save the card ids to the hidden input field to be sent along with the fetch api
    // tells the backend that the source card is transfering to the target card
    sourceCardHiddenValueField.value = getCardDetailsFromElement(selectedCardStore.get()).cardId;

    const targetCardDetails = getCardDetailsFromElement(targetCard);

    if (Object.keys(targetCardDetails).length === 0) {

        warnError("processSelectedCardClick", {
            targetCardDetails: targetCardDetails
        })
        return;
    }

    transferToHiddenValueField.value = targetCardDetails.cardId;
    targetCardHiddenNumberValueField.value = targetCardDetails.cardNumber;

}




/**
 * Returns the closest selectable card element from an event target.
 *
 * The element must:
 * - Have the provided base card class
 * - NOT contain the excluded class (if provided)
 * 
 * @param {Event} event - The DOM event triggered by user interaction.
 * @param {string} baseClass - The required card class (e.g., "bank-card").
 * @param {string} [excludedClass] - Optional class that disqualifies the card.
 * @returns {HTMLElement|null} The valid card element, or null if invalid.
 */
export function getSelectableCardElement(event, baseClass, excludedClass) {
    const element = event.target.closest(`.${baseClass}`);
    if (!element) return null;

    if (excludedClass && element.classList.contains(excludedClass)) {
        return null;
    }

    return element;
}



/**
 * Handles a click on a credit card in the overview panel.
 *
 * This function:
 * 1. Determines if the clicked element is a selectable bank card (excluding transfer cards).
 *    - If not, exits early.
 * 2. Deselects all currently selected cards.
 * 3. Marks the clicked card as selected.
 * 4. Updates the selected card store with the clicked card.
 * 5. Shows the extra card info panel such as the details for the selected card.
 *
 * @param {MouseEvent} e - The click event triggered on the credit card overview panel.
 *
 * @example
 * // Attach this handler to the credit card overview container
 * creditCardOverviewContainer.addEventListener('click', processCreditCardOverviewClick);
 */
function processCreditCardOverviewClick(e) {

    const bankCardClass = "bank-card";
    const excludeClass = "bank-transfer-card";

    const bankCardElement = getSelectableCardElement(e, bankCardClass, excludeClass);

    if (bankCardElement === null) return;

    const cardVisibleSelector = "is-selected";

    deselectAllCards();
    selectElement(bankCardElement, cardVisibleSelector)

    selectedCardStore.set(bankCardElement);
    toggleElement({ element: viewExtraCardInfo })
}




/**
 * Deselects all cards in the provided card elements list.
 *
 * This function is a wrapper around `deselectAllElements` and
 * marks all cards as not selected by removing the specified visibility class.
 *
 * @param {HTMLElement[]} [cardsNodeElements=creditCardsNodeElements] - Array of card elements to deselect.
 * @param {string} [cardVisibleSelector="is-selected"] - CSS class indicating a selected card.
 *
 * @example
 * // Deselect all cards in the default credit card container
 * deselectAllCards();
 *
 * // Deselect cards in a custom container
 * deselectAllCards(customCardElements, "active-card");
 */
function deselectAllCards(cardsNodeElements = creditCardsNodeElements, cardVisibleSelector = "is-selected") {
    deselectAllElements(cardsNodeElements, cardVisibleSelector)
}






/**
 * Displays the full details of the currently selected card in the side panel.
 *
 * This function:
 * 1. Retrieves the selected card from the store.
 * 2. Hides any previously displayed extra card info view.
 * 3. Creates a visual representation of the selected card and adds it to the full card details container.
 * 4. Masks sensitive card data (e.g., CVC) before creating the detailed card info element.
 * 5. Adds the detailed card info element to the side panel.
 * 6. Ensures bank card buttons are visible in the extra card view.
 *
 * @returns {void} - Exits early if no card is currently selected.
 *
 * @example
 * // Display the full details for the currently selected card
 * viewFullCardDetails();
 */
function viewFullCardDetails() {

    const bankCardElement = selectedCardStore.get();

    if (!bankCardElement) return;

    toggleElement({ element: viewExtraCardInfo, show: false })

    const cardDetails = getCardDetailsFromElement(bankCardElement);
    const card = cardImplementer.createCardDiv(cardDetails);

    // Add the card image to the side panel display view window
    cardImplementer.placeCardDivIn(fullCardDetailsContainer, card, true)


    cardDetails.cardStatus = bankCardElement.dataset.isActive;
    cardDetails.cvc = "***"
    const cardDetailsElement = createCardDetails(cardDetails);

    // Add the card details to the side panel display view window
    cardImplementer.placeCardDivIn(cardDetailsContainer, cardDetailsElement, true);

    removeBankCardButtonsFromCardExtraView(false);

}



/**
 * @typedef {Object} CardDetails
 * @property {string} cardId
 * @property {string} bankName
 * @property {string} cardBrand
 * @property {string} cardAmount
 * @property {string} cardType
 * @property {string} cardNumber
 * @property {string} expiryMonth
 * @property {string} expiryYear
 * @property {string} cardName
 * @property {string} issueDate
 * @property {string} cardCreationDate
 * @property {string} cardCVC
 */

/**
 * Extracts card details from a bank card DOM element.
 *
 * @param {HTMLElement} bankCardElement - The DOM element representing a bank card.
 * @returns {CardDetails}
 */
function getCardDetailsFromElement(bankCardElement) {

    const bankName = bankCardElement.querySelector(".card-head-info h3")?.textContent;
    const amount = bankCardElement.querySelector(".bank-card-amount")?.textContent;
    const cardType = bankCardElement.querySelector(".card-type")?.textContent.trim();
    const cardNumber = bankCardElement.querySelector(".card-number")?.textContent;
    const cardName = bankCardElement.querySelector(".card-name")?.textContent;
    const expiryDate = bankCardElement.querySelector(".card-expiry-date")?.textContent;

    const [month, year] = expiryDate.split("Expiry date: ")

    const cardDetails = {
        cardId: bankCardElement.dataset.cardId,
        bankName: bankName,
        cardBrand: bankCardElement.dataset.cardBrand,
        cardAmount: amount,
        cardType: cardType,
        cardNumber: cardNumber,
        expiryMonth: month,
        expiryYear: year,
        cardName: cardName,
        issueDate: bankCardElement.dataset.issued,
        cardCreationDate: bankCardElement.dataset.creationDate,
        cardCVC: bankCardElement.dataset.cvc,
        isActive: bankCardElement.dataset.isActive === "true" ? true : false,
    }
    return cardDetails;

}




/**
 * Handles clicks on buttons within a card panel.
 *
 * Depending on which button was clicked:
 * 1. "card-close-btn":
 *    - Hides the extra card info panel.
 *    - Deselects all cards.
 *    - Closes all related transfer panels.
 * 2. "card-transfer-btn":
 *    - Initiates the transfer process for the selected source card.
 *
 * @param {MouseEvent} e - The click event triggered by the user on a card panel button.
 *
 * @example
 * // Attach this handler to the card panel container
 * cardPanelContainer.addEventListener('click', handleCardPanelButtons);
 */
function handleCardPanelButtons(e) {


    switch (e.target.id) {
        case "card-close-btn":
            toggleElement({ element: extraCardInfoPanel, show: false });
            deselectAllCards();
            closeAllRelatedTransferPanels()
            break;

        case "card-transfer-btn":
            handleSourceCardTransfer();
            break;
    }
}



/**
 * Handles the opening of the transfer form for the selected source card.
 *
 * This function:
 * 1. Retrieves details of the currently selected source card.
 * 2. Checks if the card is active:
 *    - If the card is blocked, displays an alert and prevents opening the transfer form.
 *    - If the card is active, toggles the visibility of the transfer form section.
 *
 * @returns {void} - Returns early if the source card is blocked.
 *
 * @example
 * // Open the transfer form for the selected source card
 * handleSourceCardTransfer();
 */
function handleSourceCardTransfer() {

    const sourceCard = getCardDetailsFromElement(selectedCardStore.get());

    if (!sourceCard.isActive) {
        // console.log("This is being executed")
        AlertUtils.showAlert({
            title: "Card blocked",
            text: "You cannot open the transfer window because this card is blocked.",
            icon: "info",
            confirmButtonText: "OK"
        });
        return;
    }
    toggleElement({ element: cardTransferFormSection });
    return;

}




/**
 * Shows or hides bank card buttons in the extra card view.
 *
 * @param {boolean} [remove=true] - If true, hides the buttons; if false, shows them.
 *
 * @returns {null} - Returns null if the button container does not exist.
 *
 * @example
 * // Hide bank card buttons
 * removeBankCardButtonsFromCardExtraView();
 *
 * // Show bank card buttons
 * removeBankCardButtonsFromCardExtraView(false);
 */
function removeBankCardButtonsFromCardExtraView(remove = true) {

    if (!bankCardButtons) return null;
    toggleElement({ element: bankCardButtons, show: !remove })
}




/**
 * handleCardSelectionTimeout
 *
 * Automatically deselects any selected card if the card details panel 
 * ("view-card-panel") is not opened within a specified timeout.
 *
 * This function waits for 5 seconds (`MILLI_SECONDS`) and then:
 *   1. Deselects all cards using `deselectAllCards()`.
 *   2. Hides the "view more bank card" element using `toggleElement()`.
 *
 * The timeout is only applied if the extra card info panel is currently hidden.
 *
 * Usage:
 * Call this function after a card is selected to ensure that a card does 
 * not remain selected indefinitely without the user viewing its details.
 *
 * @function
 * @returns {void} Does not return any value.
 */

function handleCardSelectionTimeout() {
    const MILLI_SECONDS = 10000;


    // Must query elements dynamically each time because their visibility can change
    const viewExtraCardInfo = document.getElementById("view-more-bank-card");
    const extraCardInfoPanel = document.getElementById("view-card-panel");


    const isSideCardPanelOpen = getComputedStyle(extraCardInfoPanel).display;

    let timeoutId;

    if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
    }

    if (isSideCardPanelOpen === "none") {

        timeoutId = setTimeout(() => {
            deselectAllCards();
            toggleElement({ element: viewExtraCardInfo, show: false })
        }, MILLI_SECONDS);
        return
    }


}



/**
 * Handles changes to the transfer type select field in the transfer form.
 *
 * This function:
 * 1. Checks if the changed element is the transfer type selector; if not, exits early.
 * 2. If the selected value is not "another-card":
 *    - Hides the card selection panel.
 *    - Hides the transfer amount confirmation panel.
 *    - Resets the transfer form.
 * 3. If the selected value is "another-card":
 *    - Shows the card selection panel.
 *    - Retrieves the currently selected card from the store.
 *    - Renders a message prompting the user to select a transfer card.
 *    - Loops through the cards and displays only cards that haven't been blocked:
 *
 * @param {Event} e - The change event triggered on the transfer type select field.
 *
 * @example
 * // Attach this handler to the transfer type selector
 * transferTypeSelect.addEventListener('change', handleBankTransferSelectFormOptions);
 */
function handleBankTransferSelectFormOptions(e) {
    if (!e.target.matches("#transfer-type")) return


    const select = e.target;
    const value = select.value;


    // hide the select card panel if another option is selected.

    switch(value) {
        case "another-card":
            handleAnotherCardSelectTransferFormOption();
            cardSelectionPanelState.set(true);
            break;
        case "wallet":
            closeSelectCardTransferSidePanel();
            cardSelectionPanelState.clear();
            transferFormSelectOption.set("Wallet");
            break;
        case "bank":
             closeSelectCardTransferSidePanel();
             cardSelectionPanelState.clear();
             transferFormSelectOption.set("bank");
             break

    }

   
  
}


function closeSelectCardTransferSidePanel() {
    toggleElement({ element: selectCardsContainer, show: false });
    handleTransferAmountConfirmation(false);
   
}

function handleAnotherCardSelectTransferFormOption() {
      toggleElement({ element: selectCardsContainer })

    const selectedCard = selectedCardStore.get();

    if (!selectedCard) return;

    const cardBrand = selectedCard.dataset.cardBrand;

    renderTransferCardSelectionMessage();

    creditCardsNodeElements.forEach((card) => {

        if (card.dataset.cardBrand.toLowerCase() !== cardBrand.toLowerCase()) {

            const cardDetails = getCardDetailsFromElement(card);
            const cardElement = cardImplementer.createCardDiv(cardDetails);

            cardElement.classList.add("account-card", "bank-transfer-card");
            cardElement.dataset.account = "debit-cards";
            cardElement.dataset.cardId = cardDetails.cardId;

            attachCardDetails(cardElement, cardDetails);

            if (cardDetails.isActive && getCardDetailsFromElement(selectedCardStore.get()).cardId !== cardDetails.cardId) {
                cardImplementer.placeCardDivIn(selectCardsContainer, cardElement, false)
            }

        }
    })


}

/**
 * Attaches card metadata to a DOM card element using data attributes.
 *
 * This function mutates the provided `cardElement` by dynamically
 * assigning all properties from the `cardDetails` object to the
 * element's dataset.
 *
 * Each key in `cardDetails` becomes a corresponding `data-*` attribute.
 *
 * Example:
 *   cardDetails.cardId → data-card-id
 *   cardDetails.cardBrand → data-card-brand
 *
 * @param {HTMLElement} cardElement - The DOM element representing the card.
 * @param {Object} cardDetails - An object containing the card's metadata.
 * @returns {void}
 */
function attachCardDetails(cardElement, cardDetails) {
    Object.entries(cardDetails).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            cardElement.dataset[key] = value;
        }
    });
}



/**
 * Renders the transfer card selection instruction message
 * inside the select cards container.
 *
 * This function clears any existing content in the container
 * and displays a message prompting the user to choose a card
 * to transfer funds to.
 *
 * @returns {void}
 */
function renderTransferCardSelectionMessage() {

    selectCardsContainer.innerHTML = "";

    const message = document.createElement("p");
    message.textContent = "Choose a card to transfer to. Only active cards are shown.";

    message.style.marginBottom = "24px"


    selectCardsContainer.append(message);
}



/**
 * Handles the submission of the transfer form.
 *
 * This function:
 * 1. Extracts source and target card IDs from hidden input fields.
 * 2. Validates the card selection using `assertTransferSelection`.
 *    - If validation fails, the function exits early.
 * 2. Shows the transfer amount confirmation panel.
 * 2. Updates the confirmation panel with the current transfer details.
 *
 * @param {Event} e - The form submission event.
 *
 * @example
 * // Attach this handler to the transfer form
 * fundsTransferForm.addEventListener('submit', handleTransferForm);
 */
function handleTransferForm(e) {
    e.preventDefault(); 

    // console.log("I am in the transfer form")

    if (cardSelectionPanelState.isPanelOpen()) {

        const hiddenInputFieldSelector = ".transfer-hidden-field";
        const hiddenInputValue = Array.from(document.querySelectorAll(hiddenInputFieldSelector));

        const [sourceCardId, targetCardId] = extractSourceAndCardIdFromHiddenField(hiddenInputValue);

        const resp = assertTransferSelection({ sourceCardId: sourceCardId, targetCardId: targetCardId })

        if (!resp) return;
    
    }

    const hasFunds = assertSourceCardHasFunds();
    if (!hasFunds) return;


    handleTransferAmountConfirmation();
    const recipientAccount = getRecipientAccountType()
    updateConfirmationPanel(getTransferFormObject(fundsTransferForm), recipientAccount);

}


/**
 * 
 * Checks if the source card (card dong the transferring) 
 * has a valid balance 
 * 
 * */
function assertSourceCardHasFunds() {
    let sourceCard = selectedCardStore.get();
    if (!sourceCard) return;

    sourceCard = getCardDetailsFromElement(sourceCard)
    const amount = parseCurrency(sourceCard.cardAmount);

    if (isNaN(amount) || amount <= 0) {
        AlertUtils.showAlert({
            title: "Invalid balance",
            text: "The card balance is insufficient and a transfer cannot be inititated.",
            icon: "error",
            confirmButtonText: "OK",
        });
        return false;
    }
    return true;
}


/**
 * Returns an object containing only the required fields from the transfer form.
 *
 * @param {HTMLFormElement} transferForm - The funds transfer form element.
 * @returns {Object} An object with the "transfer-amount" and "note" fields.
 *
 * @example
 * const formObject = getTransferFormObject(fundsTransferForm);
 * // formObject = { "transfer-amount": "100", "note": "Payment for invoice #123" }
 */
function getTransferFormObject(transferForm) {
    const requiredFields = ["transfer-amount", "note"];
    return parseFormData(new FormData(transferForm), requiredFields);
}




/**
 * Validates that both a source and a target card have been selected for a transfer.
 *
 * This function performs two checks:
 * 1. Ensures that both `sourceCardId` and `targetCardId` are provided.
 *    - If either is missing, an alert is shown and a warning is logged.
 * 2. Ensures that the source and target cards are not the same.
 *    - If they are the same, it means a target card was never selected in the panel, and 
 * an alert is shown and a warning is logged.
 *
 * @param {Object} params - The parameters object.
 * @param {string|number} params.sourceCardId - The ID of the source card.
 * @param {string|number} params.targetCardId - The ID of the target card.
 * @param {string} [params.context="assertTransferSelection"] - Optional context for logging warnings.
 *
 * @returns {boolean} - Returns `true` if the transfer selection is valid; otherwise, `false`.
 *
 * @example
 * const isValid = assertTransferSelection({
 *   sourceCardId: selectedSourceCardId,
 *   targetCardId: selectedTargetCardId
 * });
 * if (isValid) {
 *   // Proceed with transfer
 * }
 */
function assertTransferSelection({
    sourceCardId,
    targetCardId,
    context = "assertTransferSelection"
}) {

    console.log( {
        sourceCardId: sourceCardId,
        targetCardId: targetCardId
    })
    if (!sourceCardId || !targetCardId) {
        AlertUtils.showAlert({
            title: "Unable to continue",
            text: "Please select a source card and a target card to complete the transfer.",
            icon: "error",
            confirmButtonText: "OK"
        });

        warnError(context, {
            code: "TRANSFER_MISSING_CARD",
            sourceCardId,
            targetCardId
        });

        return false;
    }

    // If the Source card id equals the target card id, it means that the target card was never selected
    if (sourceCardId === targetCardId) {
        AlertUtils.showAlert({
            title: "Invalid transfer",
            text: "Please select a target card to complete the transfer.",
            icon: "error",
            confirmButtonText: "OK"
        });

        warnError(context, {
            code: "TRANSFER_SAME_CARD",
            cardId: sourceCardId
        });

        return false;
    }

    return true;
}



/**
 * Extracts the source and target card IDs from a collection of hidden input elements.
 *
 * Expects an array-like object (e.g. NodeList or Array) where:
 * - index 0 contains the source card input
 * - index 1 contains the target card input
 *
 * If the input is missing, invalid, or contains fewer than two elements,
 * the function safely returns [null, null].
 *
 * @param {Array|NodeList} hiddenInputValue
 *     A collection of hidden input elements containing card IDs.
 *
 * @returns {[string|null, string|null]}
 *     A tuple containing:
 *     - sourceCardId
 *     - targetCardId
 */
function extractSourceAndCardIdFromHiddenField(hiddenInputValue) {

    const EXPECTED_RETURN_VALUE = 2;
    if (!hiddenInputValue || hiddenInputValue.length < EXPECTED_RETURN_VALUE) {
        return [null, null];
    }

    return [
        hiddenInputValue[0].value ?? null,
        hiddenInputValue[1].value ?? null
    ];
}





/**
 * Shows or hides the transfer amount confirmation panel.
 *
 * @param {boolean} [show=true] - If true, displays the confirmation panel; 
 *                                 if false, hides it.
 *
 * @example
 * // Show the confirmation panel
 * handleTransferAmountConfirmation(true);
 *
 * // Hide the confirmation panel
 * handleTransferAmountConfirmation(false);
 */
function handleTransferAmountConfirmation(show = true) {
    toggleElement({ element: askTransferConfirmationPanel, show: show })

}



/**
 * Resolves the recipient account for the current transfer.
 *
 * If a recipient type is selected from the transfer form that is used excluding "another-card".
 *  The options are "another-card", "wallet" or "bank" that value is returned.
 * 
 * However, If "bank" or "wallet" wasn't selected the recipient type becomes (null), 
 * and the function falls back to the "another-card" as the selection picked
 *
 *
 * @returns {string|null} The resolved recipient account identifier,
 * or null if none can be determined.
 */
function getRecipientAccountType() {

    const recipientType = transferFormSelectOption.getSelection();
    let transferToAccount;

    if (recipientType === null) {

        const targetCardHiddenValue = document.getElementById("transfer-to-card-number")

        if (!(sourceCardNumberElement && targetCardNumberElement && transferAmountElement)) {

            warnError("updateConfirmationPanel", {
                sourceCardNumberElement: sourceCardNumberElement,
                targetCardNumberElement: targetCardNumberElement,
                transferAmountElement: transferAmountElement,
            })
            return;
         }

         transferToAccount = targetCardHiddenValue && targetCardHiddenValue !== undefined ? targetCardHiddenValue.value : null
    } else {
        transferToAccount = recipientType;
    }
    return transferToAccount
}


/**
 * Renders the transfer confirmation panel.
 *
 * Displays the selected source card, recipient type,
 * and formatted transfer amount.
 *
 * @param {Object} formData
 * @param {string|number} formData.transferAmount
 * @param {string} recipientType
 */
function updateConfirmationPanel(formData, recipientType) {

  
    // If recipient account is nulll it means that the user has selected "bank" or "wallet" from the select transfer form
    if (recipientType === null || typeof recipientType !== "string")  {
        warnError("updateConfirmationPanel", {
            recipientType: recipientType,
            type: typeof recipientType,
            expected: "Expected a string value",
            
        })
        return;
      
    } 

    sourceCardNumberElement.textContent = getCardDetailsFromElement(selectedCardStore.get()).cardNumber;
    targetCardNumberElement.textContent = recipientType;
    transferAmountElement.textContent   = formatCurrency(formData.transferAmount)

}



/**
 * Handles the click event for the transfer cancellation button within the confrimation panel.
 *
 * When the user clicks the cancel button:
 * 1. Verifies that the clicked element is the correct cancel button.
 * 2. Closes all related transfer panels to reset the UI.
 *
 * @param {MouseEvent} e - The click event triggered by the user.
 *
 * @example
 * // Attach this handler to the transfer cancel button
 * transferCancelButton.addEventListener('click', handleTransferCancelConfirmationButtonClick);
 */
function handleTransferCancelConfirmationButtonClick(e) {
    const buttonId = "transfer-confirmation-cancel-btn";

    if (e.target.id !== buttonId) {
        return;
    }

    closeAllRelatedTransferPanels();
}




/**
 * Handles the click event for the transfer confirmation button.
 *
 * When the user clicks the confirmation button:
 * 1. Displays a confirmation alert to verify if the user wants to proceed with the transfer.
 * 2. If confirmed:
 *    - Retrieves the transfer form data (amount and note) using `getTransferFormObject`.
 *    - Sends the data to the backend (currently simulated with console.log).
 *    - Closes all related transfer panels to reset the UI.
 * 3. If cancelled, no action is taken.
 *
 * @param {MouseEvent} e - The click event triggered by the user.
 *
 * @example
 * // Attach this handler to the transfer confirmation button
 * transferConfirmationButton.addEventListener('click', handleTransferConfirmationButtonClick);
 */
async function handleTransferConfirmationButtonClick(e) {

    const buttonId = "transfer-confirmation-confirm-btn";

    if (e.target.id !== buttonId) {
        return;
    }

    const confirmed = await AlertUtils.showConfirmationAlert({
        title: "Transfer process",
        text: "Are you sure you want to proceed with the transfer?",
        icon: "info",
        cancelMessage: "No action was taken",
        confirmButtonText: "Yes, proceed!",
        messageToDisplayOnSuccess: "Your transfer was successfully",
        denyButtonText: "Cancel transfer!"
    })

    if (confirmed) {
        // simulation - The console log will be replaced by a real fetch API but for now it is a console.log

        const formData = getTransferFormObject(fundsTransferForm);
        console.log(`fetch data sent to the backend note=${formData.note} and amount amount=${formData.transferAmount}`);
        closeAllRelatedTransferPanels();
        return;

    }


}







/**
 * Closes all panels and sections related to the funds transfer workflow
 * and resets associated UI elements to their default state.
 *
 * This function hides:
 *  - Bank transaction view panel
 *  - Extra card info panel
 *  - Extra card info view
 *  - Card transfer form section
 *  - Card selection container
 *  - Deselects all cards
 *
 * It also:
 *  - Removes bank card buttons from the extra card view
 *  - Resets transfer amount confirmation state
 *
 * Use this function when cancelling or completing a transfer
 * to ensure all related UI elements are properly closed and reset.
 *
 * @example
 * // Close all transfer panels when the user cancels a transfer
 * closeAllRelatedTransferPanels();
 */
function closeAllRelatedTransferPanels() {
    toggleElement({ element: viewBankTransacionPanel, show: false });
    toggleElement({ element: extraCardInfoPanel, show: false });
    toggleElement({ element: viewExtraCardInfo, show: false })
    toggleElement({ element: cardTransferFormSection, show: false });
    toggleElement({ element: selectCardsContainer, show: false });

    removeBankCardButtonsFromCardExtraView();
    handleTransferAmountConfirmation(false)
    deselectAllCards();
    resetTransferForm();
    cardSelectionPanelState.clear();
}


function resetTransferForm() {
    fundsTransferForm.reset()
}