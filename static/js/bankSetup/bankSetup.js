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

runObserver({thresholdPercent: 0.10});


const chooseBankForm = document.getElementById("chooose-bank-form");
const bankCards = document.querySelectorAll(".choose-bank__card");

const IS_SELECTED_CLASS = "is-selected";

// add one time checker later
chooseBankForm.addEventListener("click", handleDelegation);
chooseBankForm.addEventListener("keydown", handleKeydown);


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
