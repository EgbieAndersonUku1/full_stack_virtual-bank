import { enableAutoFocusNavigation } from "../../../utils.js";
import { AddFundModal } from "../funds/addFunds.js";
import { parseFormData } from "../../../formUtils.js";
import { parseCharsFromObject } from "../../../utils.js";
import { submitBankFundTransaction, handleBankFundRespData } from "../funds/bankFundTransaction.js";
import { warnError } from "../../../logger.js";
import { BankFundAmountInputField } from "../funds/bankFundAmountInputField.js";
import { BankCardType } from "../cards/bankCard/bankCard.js";
import { BankCard } from "../cards/bankCard/bankCard.js";


const main            = document.querySelector("main");
const pinModalElement = document.getElementById("bank-pin-transaction");
const pinFields       = document.querySelectorAll("#bank-pin-input-fields input");
const pinForm         = document.getElementById("bank-pin-transaction-form");
const pinFormbutton   = document.getElementById("pin-btn");




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

    function validateOrRaiseError() {
        if (!pinModalElement) {
            throw new Error("Expect a pin element but got null")
        }
    }

    function show(cssSelectorToShow = "show") {
        validateOrRaiseError();
        main.removeAttribute("aria-hidden");
        AddFundModal.hide();
        pinModalElement.classList.add(cssSelectorToShow.trim());
        enableAutoFocusNavigation(pinFields);

    }

    function hide(cssSelectorToHide="show") {
        pinModalElement.classList.remove(cssSelectorToHide.trim());
    }


    /**
     * The function extract the pin from a given pin form and
     * returns the pin as a string
     * @returns pin
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
     * Process the pin form and if the form fields are valid returns the pin as a string
     * @returns The pin as a string
     */
    function handlePinForm() {

        if (!pinForm.checkValidity()) {
            pinForm.reportValidity();
            return null;
        }

        return processPin();
    }

    function disablePinFormButton() {
        pinFormbutton.disabled = true;
    }

    function enablePinFormButton() {
        pinFormbutton.disabled = false;

    }

    return {
        show,
        hide,
        handlePinForm,
        disablePinFormButton,
        enablePinFormButton

    }


})()



/**
 * Resets the funding flow to its initial state.
 *
 * Hides the PIN modal, restores the add-funds modal,
 * re-enables PIN submission, and clears the funding amount.
 */
function resetFundingFlow() {
    PinModal.hide();
    AddFundModal.show();
    PinModal.enablePinFormButton();
    BankFundAmountInputField.clearAmountInputField();
}



/**
 * Handles submission of the bank-fund form using the entered PIN.
 *
 * @param {SubmitEvent} e
 * @returns {Promise<void>}
 */
async function handleBankFundSubmission(e) {
    e.preventDefault();

    const pin = PinModal.handlePinForm();

    if (!pin) {
        return;
    }

    const cardSelectedName = BankCard.getSelectCardName()

    PinModal.disablePinFormButton()

    switch(cardSelectedName) {

        case BankCardType.CURRENT_ACCOUNT:
            const resp = await submitBankFundTransaction(pin);
            const data = resp.data;

            handleBankFundRespData(data)
            resetFundingFlow();
            break;

        case BankCardType.SAVING_ACCOUNT:
            break;

        case BankCardType.DEBIT_CARD:
            break;

        case BankCardType.WALLET:
            break;
    }



}



pinForm.addEventListener("submit", handleBankFundSubmission);

