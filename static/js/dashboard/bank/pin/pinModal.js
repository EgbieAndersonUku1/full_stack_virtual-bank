import { enableAutoFocusNavigation } from "../../../utils.js";
import { AddFundModal } from "../funds/addFunds.js";
import { parseFormData } from "../../../formUtils.js";
import { parseCharsFromObject, toggleSpinner } from "../../../utils.js";
import { submitBankFundTransaction, handleBankFundRespData, submitBankFundSavingTransaction } from "../funds/bankFundTransaction.js";
import { warnError } from "../../../logger.js";
import { BankFundAmountInputField } from "../funds/bankFundAmountInputField.js";
import { BankCardType } from "../cards/bankCard/bankCard.js";
import { BankCard } from "../cards/bankCard/bankCard.js";


const main            = document.querySelector("main");
const pinModalElement = document.getElementById("bank-pin-transaction");
const pinFields       = document.querySelectorAll("#bank-pin-input-fields input");
const pinForm         = document.getElementById("bank-pin-transaction-form");
const pinFormbutton   = document.getElementById("pin-btn");
const pinSpinner      = document.getElementById("pin-form-spinner");




 /**
  * Controls the bank PIN modal by showing or hiding and manages
  *  its accessibility and focus behaviour.
  *
  * When the PIN modal is shown, any aria-hidden state on the main element is
  * removed so the PIN inputs remain accessible to assistive technologies.
  * The PIN input navigation is then enabled and focus is placed on the first
  * PIN input once the modal has been rendered.
  *
  *
  * @returns {{
  *     show: (cssSelectorToShow?: string) => void,
  *     hide: (cssSelectorToHide?: string) => void
  * }} An object containing methods for showing and hiding the PIN modal.
  */
export const PinModal = (() => {

    /**
     * Validates that the PIN modal element exists.
     *
     * @throws {Error} Throws an error when the PIN modal element cannot be found.
     */
    function validateOrRaiseError() {
        if (!pinModalElement) {
            throw new Error("Expect a pin element but got null")
        }
    }

    /**
     * Displays the PIN modal and prepares its input fields for user interaction.
     *
     * Hides the Add Funds modal, makes the main content accessible, and enables
     * automatic focus navigation between the PIN input fields.
     *
     * @param {string} [cssSelectorToShow="show"] - CSS class used to display the modal.
     * @returns {void}
     */
    function show(cssSelectorToShow = "show") {
        validateOrRaiseError();
        main.removeAttribute("aria-hidden");
        AddFundModal.hide();
        pinModalElement.classList.add(cssSelectorToShow.trim());
        enableAutoFocusNavigation(pinFields);

    }

    /**
     * Focuses the first available PIN input field.
     */
    function focusPinInput() {
        enableAutoFocusNavigation(pinFields);
    }


    /**
     * Hides the PIN modal.
     *
     * @param {string} [cssSelectorToHide="show"] - CSS class used to control the modal visibility.
     * @returns {void}
     */
    function hide(cssSelectorToHide="show") {
        pinModalElement.classList.remove(cssSelectorToHide.trim());
    }


    /**
     * Clears all PIN input fields.
     *
     * @returns {void}
     */
    function clearAllPinFields() {
        pinFields.forEach((field) => {
            field.value = "";
        })
    }


    /**
     * Extracts the PIN from the PIN form fields.
     *
     * @returns {string|null} The extracted PIN, or null when the PIN
     * could not be processed.
     */
    function processPin() {
        const formData   = new FormData(pinForm);
        const parsedData = parseFormData(formData, [
                'pin_1',
                'pin_2',
                'pin_3',
                'pin_4',
                'pin_5',
                'pin_6',

            ])

        const pin = parseCharsFromObject(parsedData);
        if (!pin) {
            warnError("handleForm", {error: "pin not found", received: pin})
            return null;
        }
        return pin
    }

    /**
     * Validates the PIN form and returns the entered PIN when valid.
     *
     * @returns {string|null} The PIN when the form is valid, otherwise null.
     */
    function handlePinForm() {

        if (!pinForm.checkValidity()) {
            pinForm.reportValidity();
            return null;
        }

        return processPin();
    }


    function setPinButtonLoading(isLoading) {
        pinFormbutton.classList.toggle("loading", isLoading);
    }


    /**
     * Disables the PIN form submission button.
     *
     * Prevents the user from submitting the PIN form multiple times
     * while a transaction is being processed.
     *
     * @returns {void}
     */
    function disablePinFormButton() {
        pinFormbutton.disabled = true;
    }

    /**
     * Enables the PIN form submission button.
     *
     * @returns {void}
     */
    function enablePinFormButton() {
        pinFormbutton.disabled = false;

    }


    /**
     * Displays the PIN submission spinner and enables the button's loading state.
     *
     * @returns {void}
     */
    function showSpinner() {
        toggleSpinner(pinSpinner, true);
        setPinButtonLoading(true);
    }

    /**
     * Hides the PIN submission spinner and restores the button's normal state.
     *
     * @returns {void}
     */
    function hideSpinner() {
        setPinButtonLoading(false)
        toggleSpinner(pinSpinner, false);
    }


    return {
        show,
        hide,
        handlePinForm,
        disablePinFormButton,
        enablePinFormButton,
        showSpinner,
        hideSpinner,
        clearAllPinFields,
        focusPinInput

    }


})()


/**
 * Resets the funding flow to its initial state.
 *
 * Hides the PIN modal, restores the Add Funds modal, re-enables PIN
 * submission, clears the funding amount, and clears all entered PIN fields.
 *
 * @returns {void}
 */
function resetFundingFlow() {
    PinModal.hideSpinner();
    PinModal.hide();
    AddFundModal.show();
    PinModal.enablePinFormButton();
    BankFundAmountInputField.clearAmountInputField();
    PinModal.clearAllPinFields();
}



/**
 * Resets the PIN form after an unsuccessful funding attempt.
 *
 * Re-enables PIN submission and clears all previously entered PIN digits.
 *
 * @returns {void}
 */
function resetPinFormAfterFailure() {
    PinModal.enablePinFormButton();
    PinModal.clearAllPinFields();
    PinModal.hideSpinner();
    PinModal.focusPinInput()
}



/**
 * Handles the response from a funding transaction.
 *
 * On success, the funding response is processed and the funding flow
 * is reset. On failure, the PIN form is restored so the user can try again.
 *
 * @param {Object} data - The funding transaction response data.
 * @returns {void}
 */
function handleFundingResponse(data) {
    if (data.SUCCESS) {
        handleBankFundRespData(data);
        resetFundingFlow();
    } else {
        resetPinFormAfterFailure();

    }
}



/**
 * Handles submission of the bank-fund form using the entered PIN.
 *
 * Validates the PIN, determines the selected funding destination, disables
 * the PIN submission controls, displays the loading state, and submits the
 * appropriate funding transaction.
 *
 * @param {SubmitEvent} e - The form submission event.
 * @returns {Promise<void>}
 */
async function handleBankFundSubmission(e) {
    e.preventDefault();

    const pin = PinModal.handlePinForm();

    if (!pin) {
        return;
    }

    const cardSelectedName = BankCard.getSelectCardName();
    let resp;

    PinModal.disablePinFormButton();
    PinModal.showSpinner();

    switch (cardSelectedName) {

        case BankCardType.CURRENT_ACCOUNT:
            resp = await submitBankFundTransaction(pin);
            handleFundingResponse(resp.data);
            break;

        case BankCardType.SAVING_ACCOUNT:
            resp = await submitBankFundSavingTransaction(pin);
            handleFundingResponse(resp.data);
            break;

        case BankCardType.DEBIT_CARD:
            break;

        case BankCardType.WALLET:
            break;
    }
}


pinForm.addEventListener("submit", handleBankFundSubmission);

