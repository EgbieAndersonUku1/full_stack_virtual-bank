import { toggleElement, enableAutoFocusNavigation } from "../../../utils.js";
import { AddFundModal } from "../funds/addFunds.js";

const main            = document.querySelector("main");
const pinModalElement = document.getElementById("bank-pin-transaction");
const pinFields       = document.querySelectorAll("#bank-pin-input-fields input")



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

    return {
        show,
        hide,
    }


})()
