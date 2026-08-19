import { toggleElement } from "../../../utils.js";
import { deselectAllCards } from "../cards/bankCard/cardSelector.js";
import { BANK_DASHBOARD_ELEMENTS } from "../../panel/panelElements.js";
import { openSourceCardTransferForm } from "../cards/bankCard/cardTransfer.js";
import { resetTransferWorkflow } from "../cards/bankCard/cardTransferWorkflow.js";
import { handleTransferTypeChange } from "../cards/bankCard/cardTransfer.js";


const bankCardButtons              = document.querySelector(".view-card-panel-buttons");
const askTransferConfirmationPanel = document.getElementById("bank-transfer-quick-confirmation");


/**
 * Manages interactions with the dashboard card side panel.
 *
 * Handles user actions for closing the card details panel and opening
 * the transfer form for the currently selected source card. Closing
 * the panel resets the associated transfer workflow and returns the
 * relevant UI and state to their default values.
 */
export const DashboardCardSidePanel = (() => {

    /**
     * Handles user interactions within the dashboard card side panel.
     *
     * @param {MouseEvent} e - The event triggered by user interaction.
     * @returns {void}
     */
    function handleEvent(e) {
        switch (e.target.id) {
            case "card-close-btn":
                toggleElement({
                    element: BANK_DASHBOARD_ELEMENTS.EXTRA_CARD_INFO_PANEL,
                    show: false
                });

                resetTransferWorkflow();
                break;

            case "card-transfer-btn":
                openSourceCardTransferForm();
                break;
        }
    }

    function handleEvents(e) {
        handleEvent(e);
        handleTransferTypeChange(e)
    }

    return {
        handleEvents
    };
})();
