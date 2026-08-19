import { BANK_DASHBOARD_ELEMENTS } from "../../../panel/panelElements.js";
import { getCardDetailsFromElement } from "./cardDetailsExtractor.js";
import { cardImplementer } from "../../../../card/cardBuilder.js";
import { toggleElement } from "../../../../utils.js";
import { selectedCardStore } from "../../../dashboard-utils.js";
import { createCardDetails } from "../../../../card/cardBuilder.js";




/**
 * Controls the visibility of bank card buttons in the extra card details view.
 *
 * Hides the buttons by default and displays them when explicitly requested.
 * If the button container does not exist, the function exits without making
 * any changes.
 *
 * @param {boolean} [visible=false] - Whether the bank card buttons should be visible.
 * @returns {void}
 *
 * @example
 * // Hide the bank card buttons.
 * setBankCardButtonsVisibility();
 *
 * // Show the bank card buttons.
 * setBankCardButtonsVisibility(true);
 */
export function setBankCardButtonsVisibility(remove = true) {

    const bankCardButtons = BANK_DASHBOARD_ELEMENTS.BANK_CARD_BUTTONS;

    if (!bankCardButtons) return null;
    toggleElement({ element: bankCardButtons, show: !remove })
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
export function viewFullCardDetails() {

    const bankCardElement = selectedCardStore.get();

    if (!bankCardElement) return;

    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.VIEW_EXTRA_CARD_INFO, show: false })

    const cardDetails      = getCardDetailsFromElement(bankCardElement);
    const card             = cardImplementer.createCardDiv(cardDetails);

    // Add the card image to the side panel display view window
    cardImplementer.placeCardDivIn(BANK_DASHBOARD_ELEMENTS.FULL_CARD_DETAILS_CONTAINER, card, true);

    cardDetails.cvc = "***"

    const cardDetailsElement = createCardDetails(cardDetails);

    // Add the card details to the side panel display view window
    cardImplementer.placeCardDivIn(BANK_DASHBOARD_ELEMENTS.CARD_DETAILS_CONTAINER, cardDetailsElement, true);

    setBankCardButtonsVisibility(false);

}

