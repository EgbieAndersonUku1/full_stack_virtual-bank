import { checkIfHTMLElement } from "../utils.js";

// records which card was clicked


export const selectedCardStore = {
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

