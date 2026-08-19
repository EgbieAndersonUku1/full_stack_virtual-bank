/**
 * Stores and manages the current transfer destination selection.
 *
 * The selected destination can be retrieved, updated, or cleared as the
 * user progresses through the transfer workflow.
 */
export const transferDestinationState = {
    optionSelection: null,

    /**
     * Stores the selected transfer destination.
     *
     * @param {string} selection - The selected transfer destination,
     * such as "wallet" or "bank".
     * @returns {void}
     */
    set(selection) {
        this.optionSelection = selection;
    },

    /**
     * Returns the currently selected transfer destination.
     *
     * @returns {string|null} The selected destination, formatted for display,
     * or null if no destination has been selected.
     */
    get() {
        return this.optionSelection
            ? toTitle(this.optionSelection)
            : null;
    },

    /**
     * Clears the currently selected transfer destination.
     *
     * @returns {void}
     */
    clear() {
        this.optionSelection = null;
    }
};
