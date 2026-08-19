import { deselectAllElements, selectElement } from "../../../../utils.js"




/**
 * Deselects all cards in the provided card elements collection.
 *
 * This function is a wrapper around `deselectAllElements` and removes
 * the specified selection class from each card.
 *
 * @param {NodeListOf<HTMLElement>} [cardsNodeElements=creditCardElements]
 * The card elements to deselect.
 *
 * @param {string} [cardVisibleSelector="is-selected"]
 * The CSS class indicating that a card is selected.
 *
 * @returns {void}
 */
export function deselectAllCards(cardsNodeElements, cardVisibleSelector = "is-selected") {
    deselectAllElements(cardsNodeElements, cardVisibleSelector)
}



/**
 * Selects a single card by applying the specified CSS class.
 *
 * @param {HTMLElement} cardElement - The card element to select.
 * @param {string} cssSelector - The CSS class used to indicate selection.
 * @returns {void}
 */
export function selectSingleCard(cardElement, cssSelector) {
    selectElement(cardElement, cssSelector)
}



/**
 * Manages the open/closed state of the card selection panel.
 *
 * This object is used to track whether the card selection panel
 * is currently open, allowing the application to handle user
 * interactions appropriately (e.g., ensuring a target card is
 * selected before confirming a transfer).
 */
export const cardSelectionPanelState = {

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
