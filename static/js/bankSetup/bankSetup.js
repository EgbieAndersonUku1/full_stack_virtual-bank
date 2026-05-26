/**
 * Handles bank card selection using event delegation and keyboard accessibility.
 *
 * This module allows users to select a bank card by either clicking on it
 * or using the keyboard (Enter or Space). Selection state is managed by
 * toggling a CSS class on the active card, when one card is selected all
 * other cards are deselected.
 *
 * An Event delegation is used to minimise the number of event listeners and
 * to keep the interaction logic centralised. Keyboard events are delegated
 * in the same way as click events to maintain consistent behaviour.
 *
 * Accessibility considerations:
 * - Bank cards are made focusable via `tabindex`.
 * - Enter and Space trigger selection for keyboard users.
 *
 * The selected card is visually indicated by the `is-selected` CSS class.
 */


import runObserver from "../animation.js";
import { warnError } from "../logger.js";
import { minimumCharactersToUse } from "../utils/password/textboxCharEnforcer.js";
import { sanitizeText } from "../utils.js";
import { handleNameSanitization, handleAddressSanitization, handlePostCode } from "./handlers.js";


runObserver({thresholdPercent: 0.10});


const chooseBankForm       = document.getElementById("chooose-bank-form");
const bankCards             = document.querySelectorAll(".choose-bank__card");
const inputBankFields       = document.querySelectorAll(".card-head--control input")
const createProfileTextArea = document.getElementById("bio");

// personal details
const firstName     = document.getElementById("first-name")
const lastName      = document.getElementById("last-name")
const middleName    = document.getElementById("middle-name")
const address1      = document.getElementById("address-line-1")
const address2      = document.getElementById("address-line-2")
const city          = document.getElementById("city")
const postCode      = document.getElementById("postcode");


const IS_SELECTED_CLASS = "is-selected";

// add one time checker later

if (chooseBankForm != null) {
  chooseBankForm.addEventListener("click", handleDelegation);
  chooseBankForm.addEventListener("keydown", handleKeydown);

}

ifNotNullRunAddListenerForPersonlInformationFields()




// Displays the number of characters to display in a given textbox area
minimumCharactersToUse(createProfileTextArea, {
    minCharClass: ".num-of-characters-remaining",
    maxCharClass: ".num-of-characters-to-use",
    minCharMessage: "Minimum characters to use: ",
    maxCharMessage: "Number of characters remaining: ",
    minCharsLimit: 50,
    maxCharsLimit: 150,
    disablePaste: true,
})



document.addEventListener("DOMContentLoaded", () => {
    if (!inputBankFields){
      warnError("DOMContentLoaded", {
        expected: "Bank card fields not load"
      })
    } else {

      const firstFieldBankInputField =inputBankFields[0];
      if (firstFieldBankInputField !== undefined) {
         firstFieldBankInputField.checked = true;
      }
      
    }
})


// Make cards focusable
bankCards.forEach(card => {
  card.setAttribute("tabindex", "0");
});


/**
 * Handle delegation click events to handle bank card selection.
 */
function handleDelegation(e) {
  selectBankCard(e);
}


/**
 * Enables keyboard interaction (Enter/Space) for bank card selection.
 */
function handleKeydown(e) {
  if (e.key !== "Enter" && e.key !== " ") return;

  const card = e.target.parentElement.parentElement;
  if (!card) return;

  e.preventDefault();
  card.click();     // re-uses the click logic
}


/**
 * Selects a bank card when its associated input is checked.
 */
function selectBankCard(e) {
  const input = e.target;

  if (!input.checked) return;

  const cardElement = input.parentElement.parentElement;
  if (!cardElement) return;

  deSelectAllBankCards();
  cardElement.classList.add(IS_SELECTED_CLASS);
}



function deSelectAllBankCards() {
  bankCards.forEach(card =>
    card.classList.remove(IS_SELECTED_CLASS)
  );
}




function ifNotNullRunAddListenerForPersonlInformationFields() {

  if (!(firstName && lastName && middleName && address1 && address2 && city && postCode)) {
      return;
  }

  firstName.addEventListener("input", handleNameSanitization);
  lastName.addEventListener("input", handleNameSanitization);
  middleName.addEventListener("input", handleNameSanitization);
  address1.addEventListener("input", handleAddressSanitization);
  address2.addEventListener("input", handleAddressSanitization);
  city.addEventListener("input", handleNameSanitization);
  postCode.addEventListener("input", handlePostCode);

}