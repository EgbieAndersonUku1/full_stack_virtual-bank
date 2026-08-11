



// records the select option for the select form,
// so that can be displayed in the confirmation
// modal panel.
export const transferFormSelectOption = {

    optionSelection: null,

    /**
     * Stores the selected option for the form  e.g wallet or bank
     * Only accepts a valid HTMLElement to prevent invalid state.
     */
    set(selection) {
        this.optionSelection = selection
    },


    /**
     * Returns the selected option e.g "wallet" or "bank"
     */
    getSelection() {

        return  this.optionSelection ? toTitle(this.optionSelection): null;
    },


    /**
     * Clears the option for the selection
     */
    clear() {
        this.optionSelection = null;
    }
}








