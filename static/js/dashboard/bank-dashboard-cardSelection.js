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
