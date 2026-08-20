import { toggleElement } from "../../../../utils.js";
import { BANK_DASHBOARD_ELEMENTS } from "../../sidePanel/panelElements.js";
import { setBankCardButtonsVisibility } from "./cardDetailsView.js";
import { cardSelectionPanelState, deselectAllCards } from "./cardSelector.js";


const askTransferConfirmationPanel = document.getElementById("bank-transfer-quick-confirmation");
const fundsTransferForm = document.getElementById("funds-transfer-form");


/**
 * Resets the funds transfer form to its default state.
 *
 * Uses the form's native `reset()` method to restore all form controls
 * to their initial values.
 *
 * @returns {void}
 *
 * @example
 * // Reset the transfer form after cancelling a transfer.
 * resetTransferForm();
 */
function resetTransferForm() {
    fundsTransferForm.reset();
}


/**
 * Controls the visibility of the transfer amount confirmation panel.
 *
 * The confirmation panel is displayed by default and can be hidden by
 * passing `false`.
 *
 * @param {boolean} [visible=true] - Whether the confirmation panel should
 * be visible.
 * @returns {void}
 *
 * @example
 * // Show the transfer confirmation panel.
 * setTransferConfirmationVisibility();
 *
 * // Hide the transfer confirmation panel.
 * setTransferConfirmationVisibility(false);
 */
export function setTransferConfirmationVisibility(visible = true) {
    toggleElement({
        element: askTransferConfirmationPanel,
        show: visible
    });
}



/**
 * Closes and resets all UI elements and state associated with the
 * funds transfer workflow.
 *
 * This function:
 * - Hides all transfer-related panels and sections.
 * - Deselects all bank cards.
 * - Removes bank card buttons from the extra card view.
 * - Resets the transfer amount confirmation state.
 * - Resets the transfer form.
 * - Clears the card selection panel state.
 *
 * Use this function when cancelling or completing a transfer to ensure
 * the transfer workflow is returned to its default state.
 *
 * @returns {void}
 *
 * @example
 * // Reset the transfer workflow after cancelling a transfer.
 * resetTransferWorkflow();
 */
export function resetTransferWorkflow() {

    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.VIEW_BANK_TRANSACTION_PANEL, show: false });
    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.EXTRA_CARD_INFO_PANEL, show: false });
    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.VIEW_EXTRA_CARD_INFO, show: false });
    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.CARD_TRANSFER_FORM_SECTION, show: false });
    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.SELECT_CARDS_CONTAINER, show: false });

    setBankCardButtonsVisibility();
    setTransferConfirmationVisibility(false)

    deselectAllCards();
    resetTransferForm();
    cardSelectionPanelState.clear();
}
