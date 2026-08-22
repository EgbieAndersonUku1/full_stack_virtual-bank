import { AlertUtils } from "../../../../alerts.js";
import { clearInnerHTML, toggleElement } from "../../../../utils.js";
import { minimumCharactersToUse } from "../../../../utils/password/textboxCharEnforcer.js";
import { selectedCardStore } from "../../../dashboard-utils.js";
import { BANK_DASHBOARD_ELEMENTS } from "../../sidePanel/panelElements.js";
import { transferDestinationState } from "../transferState.js";
import { getCardDetailsFromElement } from "./cardDetailsExtractor.js";
import { attachCardDetails } from "./cardElementUtils.js";
import { cardSelectionPanelState } from "./cardSelector.js";
import { setTransferConfirmationVisibility } from "./cardTransferWorkflow.js";


const selectCardsContainer = BANK_DASHBOARD_ELEMENTS.SELECT_CARDS_CONTAINER;
const creditCardsNodeElements = document.querySelectorAll(".bank-card");
const fundsTransferForm = document.getElementById("funds-transfer-form");
const transferFormTextArea = document.getElementById("bank-transfer-note");



minimumCharactersToUse(transferFormTextArea, {
    minCharClass: ".num-of-characters-remaining",
    maxCharClass: ".num-of-characters-to-use",
    minCharMessage: "Minimum characters to use: ",
    maxCharMessage: "Number of characters remaining: ",
    minCharsLimit: 50,
    maxCharsLimit: 255,
    disablePaste: true,
});





/**
 * Renders the instruction message for selecting a transfer destination card.
 *
 * Clears the existing content from the card selection container and displays
 * a message informing the user that they must choose a card to transfer funds
 * to and that only active cards are available for selection.
 *
 * @returns {void}
 */
function renderTransferCardSelectionMessage() {

    clearInnerHTML(selectCardsContainer);

    const message = document.createElement("p");
    message.textContent = "Choose a card to transfer to. Only active cards are shown.";
    message.style.marginBottom = "24px";

    selectCardsContainer.append(message);
}



/**
 * Opens the transfer form for the currently selected source card.
 *
 * Before opening the transfer form, the function checks whether the
 * selected card is active. If the card is blocked, an informational
 * alert is displayed and the transfer form is not opened.
 *
 * @returns {void} Returns early if no active source card is available.
 */
export function openSourceCardTransferForm() {
    const sourceCard = getCardDetailsFromElement(selectedCardStore.get());

    if (!sourceCard.isActive) {
        AlertUtils.showAlert({
            title: "Card blocked",
            text: "You cannot open the transfer window because this card is blocked.",
            icon: "info",
            confirmButtonText: "OK"
        });

        return;
    }

    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.CARD_TRANSFER_FORM_SECTION });
}



/**
 * Displays alternative bank cards that can be selected as the destination
 * for a card transfer.
 *
 * The currently selected source card is excluded, along with cards that
 * belong to the same card brand as the source card. Only active cards
 * are added to the transfer-card selection container.
 *
 * The function:
 * 1. Opens the card selection container.
 * 2. Retrieves the currently selected source card.
 * 3. Displays the transfer-card selection message.
 * 4. Filters out cards belonging to the same brand as the source card.
 * 5. Creates and displays eligible active cards as transfer options.
 *
 * @returns {void} Returns early if no source card is currently selected.
 */
export function showAlternativeTransferCards() {
    toggleElement({ element: BANK_DASHBOARD_ELEMENTS.SELECT_CARDS_CONTAINER });

    const selectedCard = selectedCardStore.get();

    if (!selectedCard) return;

    const cardBrand = selectedCard.dataset.cardBrand;

    renderTransferCardSelectionMessage();

    creditCardsNodeElements.forEach((card) => {
        if (
            card.dataset.cardBrand.toLowerCase() !==
            cardBrand.toLowerCase()
        ) {
            const cardDetails = getCardDetailsFromElement(card);
            const cardElement = cardImplementer.createCardDiv(cardDetails);

            cardElement.classList.add(
                "account-card",
                "bank-transfer-card"
            );

            cardElement.dataset.account = "debit-cards";
            cardElement.dataset.cardId = cardDetails.cardId;

            attachCardDetails(cardElement, cardDetails);

            if (
                cardDetails.isActive &&
                getCardDetailsFromElement(selectedCardStore.get()).cardId !== cardDetails.cardId
            ) {
                cardImplementer.placeCardDivIn(
                    BANK_DASHBOARD_ELEMENTS.SELECT_CARDS_CONTAINER,
                    cardElement,
                    false
                );
            }
        }
    });
}




/**
 * Handles changes to the transfer type selected in the transfer form.
 *
 * Delegates the appropriate UI and state updates based on the selected
 * transfer destination.
 *
 * Supported transfer types:
 * - `"another-card"`: Shows the alternative card selection interface
 *   and activates the card selection workflow.
 * - `"wallet"`: Shows the transfer confirmation panel and sets the
 *   transfer destination to the user's wallet.
 * - `"bank"`: Hides the transfer confirmation panel and sets the
 *   transfer destination to a bank.
 *
 * @param {Event} e - The change event triggered by the transfer type selector.
 * @returns {void}
 *
 * @example
 * // Handle changes to the transfer type selector.
 * transferTypeSelect.addEventListener("change", handleTransferTypeChange);
 */
export function handleTransferTypeChange(e) {

    if (!e.target.matches("#transfer-type")) return;

    const value = e.target.value;

    switch (value) {
        case "another-card":
            showAlternativeTransferCards();
            cardSelectionPanelState.set(true);
            break;

        case "wallet":
            setTransferConfirmationVisibility();
            cardSelectionPanelState.clear();
            transferDestinationState.set("wallet");
            break;

        case "bank":
            setTransferConfirmationVisibility(false);
            cardSelectionPanelState.clear();
            transferDestinationState.set("bank");
            break;
    }
}
