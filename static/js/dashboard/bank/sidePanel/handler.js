import { toggleElement } from "../../../utils.js";
import { deselectAllCards } from "../bank/_bankCard.js";
import { BANK_DASHBOARD_ELEMENTS } from "./panelElements.js";



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
export function handleCardPanelButtons(e) {


    switch (e.target.id) {
        case "card-close-btn":
            toggleElement({ element: BANK_DASHBOARD_ELEMENTS.EXTRA_CARD_INFO_PANEL, show: false });
            deselectAllCards();
            closeAllRelatedTransferPanels()
            break;

        case "card-transfer-btn":
            handleSourceCardTransfer();
            break;
    }
}

