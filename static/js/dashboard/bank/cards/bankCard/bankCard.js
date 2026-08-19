import { toggleElement, checkIfHTMLElement } from "../../../../utils.js";
import { selectedCardStore } from "../../../dashboard-utils.js";
import { BANK_DASHBOARD_ELEMENTS, BANK_DASHBOARD_SELECTORS } from "../../../panel/panelElements.js";
import { deselectAllCards, selectSingleCard } from "./cardSelector.js";
import { getSelectableCardElement } from "./cardElementUtils.js";
import { warnError } from "../../../../logger.js";
import { getCardDetailsFromElement } from "./cardDetailsExtractor.js";
import { viewFullCardDetails } from "./cardDetailsView.js";

const bankCardSelectionTypes = document.querySelectorAll(".account-card");



export const BankCard = (() => {

    let timeoutId;
    const EXPECTED_ACCOUNT_TYPES   = ["savings-account", "debit-cards", "wallet"];

    const BANK_CARD_CLASS          = "bank-card";
    const BANK_TRANSFER_CARD_CLASS = "bank-transfer-card";
    const SELECTED_CARD_CLASS      = "is-selected";

    /**
     * Handles the selection of bank card types when a user interacts with an account card.
     *
     * This function checks if the clicked card is one of the expected account types
     * (savings account, debit card, or wallet). If it is, it deselects all other
     * bank card types and selects the clicked card.
     *
     * @param {Event} e - The event triggered by user interaction (e.g., click).
     */
    function handleBankCardTypes(e) {
        const accountCardSelector = ".account-card";
        const accountCard = e.target.closest(accountCardSelector);

        if (!EXPECTED_ACCOUNT_TYPES.includes(accountCard?.dataset.account)) return;
        if (!checkIfHTMLElement(accountCard, "account card")) return;

        deselectAllCards(bankCardSelectionTypes, "active");
        selectSingleCard(accountCard, "active");
    }

    /**
     * Handles a click on a card within the transfer card selection panel.
     *
     * This function:
     * 1. Determines if the clicked element is a selectable bank card.
     *    - If not, exits early.
     * 2. Deselects all other selectable transfer cards and marks the clicked card as selected.
     * 3. Updates hidden input fields with the source and target card IDs and the target card number,
     *    to be used in the transfer submission.
     *
     * @param {MouseEvent} e - The click event triggered on a selectable card in the transfer panel.
     *
     * @example
     * // Attach this handler to the card selection panel
     * transferCardSelectionPanel.addEventListener('click', processSelectedCardClick);
     */
    function processSelectedCardClick(e) {

        const bankCardClass = "bank-card";
        const cssSelector   = "is-selected"
        const targetCard    = getSelectableCardElement(e, bankCardClass);

        if (targetCard === null) return;

        const transferToHiddenValueField = document.getElementById("transfer-to-card-id");
        const sourceCardHiddenValueField = document.getElementById("source-card");
        const targetCardHiddenNumberValueField = document.getElementById("transfer-to-card-number")


        // get the cards that the user can can choose from selection card window
        const transferCreditCardElement = document.querySelectorAll("#bank-funds-transfer__select-cards-panel .bank-transfer-card");

        deselectAllCards(transferCreditCardElement, cssSelector);
        selectSingleCard(targetCard, cssSelector)

        if (!(transferToHiddenValueField && sourceCardHiddenValueField)) {
            warnError("processSelectedCardClick", `one or more of the hidden field is empyty.
                                                  transferToHiddenValueField = ${transferToHiddenValueField}
                                                  sourceCardHiddenValueField  = ${sourceCardHiddenValueField}
                                                  `);

            return;
        }


        // save the card ids to the hidden input field to be sent along with the fetch api
        // tells the backend that the source card is transfering to the target card
        sourceCardHiddenValueField.value = getCardDetailsFromElement(selectedCardStore.get()).cardId;

        const targetCardDetails = getCardDetailsFromElement(targetCard);

        if (Object.keys(targetCardDetails).length === 0) {

            warnError("processSelectedCardClick", {
                targetCardDetails: targetCardDetails
            })
            return;
        }

        transferToHiddenValueField.value = targetCardDetails.cardId;
        targetCardHiddenNumberValueField.value = targetCardDetails.cardNumber;
        // startCardSelectionTimeout();

    }


    /**
     * Handles a click on a credit card in the overview panel.
     *
     * This function:
     * 1. Determines if the clicked element is a selectable bank card (excluding transfer cards).
     *    - If not, exits early.
     * 2. Deselects all currently selected cards.
     * 3. Marks the clicked card as selected.
     * 4. Updates the selected card store with the clicked card.
     * 5. Shows the extra card info panel such as the details for the selected card.
     *
     * @param {MouseEvent} e - The click event triggered on the credit card overview panel.
     *
     * @example
     * // Attach this handler to the credit card overview container
     * creditCardOverviewContainer.addEventListener('click', processCreditCardOverviewClick);
     */
    function processCreditCardOverviewClick(e) {

        const bankCardClass = "bank-card";
        const excludeClass = "bank-transfer-card";

        const bankCardElement = getSelectableCardElement(e, bankCardClass, excludeClass);

        if (bankCardElement === null) return;

        const cardSelectedSelector = "is-selected";

        deselectAllCards();
        selectSingleCard(bankCardElement, cardSelectedSelector)

        selectedCardStore.set(bankCardElement);
        toggleElement({ element: BANK_DASHBOARD_ELEMENTS.VIEW_EXTRA_CARD_INFO })
        startCardSelectionTimeout()
    }


    /**
     * Routes a card click event to the appropriate card-selection handler.
     *
     * The individual handlers determine whether the event originated from a
     * card that they are responsible for and return early when it does not.
     * This allows the bank card module to use a single event listener while
     * keeping the individual card behaviours separated.
     *
     * @param {MouseEvent} e - The click event triggered by user interaction.
     * @returns {void}
     */
    function handleCardClick(e) {
        processCreditCardOverviewClick(e);
        processSelectedCardClick(e);

    }


    /**
     * Handles the click event for the "View More Info" button on a bank card.
     *
     * This function:
     * 1. Checks if the clicked element is the correct "View More Info" button.
     *    - If not, exits early.
     * 2. Shows the extra card info panel.
     * 3. Displays the full details of the currently selected card.
     *
     * @param {MouseEvent} e - The click event triggered on the "View More Info" button.
     *
     * @example
     * // Attach this handler to the "View More Info" button
     * viewMoreButton.addEventListener('click', handleViewMoreInfoCardClick);
     */
    function handleViewMoreInfoCardClick(e) {
        const viewMoreButtonId = "view-more-bank-card";

        if (e.target.id !== viewMoreButtonId) return;

        toggleElement({ element: BANK_DASHBOARD_ELEMENTS.EXTRA_CARD_INFO_PANEL, show: true });
        viewFullCardDetails();
    }



    /**
     * Cancels the currently active card-selection timeout, if one exists.
     *
     * @returns {void}
     */
    function clearCardSelectionTimeout() {
        if (!timeoutId) return;

        clearTimeout(timeoutId);
        timeoutId = null;
    }


    /**
     * Starts a countdown for the currently selected bank card.
     *
     * If a previous card-selection timeout is active, it is cancelled before
     * starting a new one. This ensures that each newly selected card receives
     * the full timeout period.
     *
     * When the timeout expires, all cards are deselected and the "View More Info"
     * element is hidden.
     *
     * @param {number} [milliseconds=10000] - The amount of time to wait before
     * deselecting the card and hiding the view-more element.
     * @returns {void}
     */
    function startCardSelectionTimeout(milliSeconds = 10_000) {

        // Must query elements dynamically each time because their visibility can change
        const viewExtraCardInfo = document.querySelector(BANK_DASHBOARD_SELECTORS.VIEW_EXTRA_CARD_INFO);
        const extraCardInfoPanel = document.querySelector(BANK_DASHBOARD_SELECTORS.EXTRA_CARD_INFO_PANEL);


        const isSideCardPanelOpen = getComputedStyle(extraCardInfoPanel).display;


        if (isSideCardPanelOpen === "none") {

            clearCardSelectionTimeout()

            timeoutId = setTimeout(() => {
                deselectAllCards();
                toggleElement({ element: viewExtraCardInfo, show: false })
                clearCardSelectionTimeout();
            }, milliSeconds);
            return
        }


    }

    /**
     * Routes incoming bank-card events to the appropriate handlers.
     *
     * This method acts as the single event entry point for the bank card module.
     * Individual handlers determine whether the event is relevant to them and
     * return early when it is not.
     *
     * @param {MouseEvent} e - The event triggered by user interaction.
     * @returns {void}
     */
    function handleEvents(e) {

        handleBankCardTypes(e)
        handleCardClick(e);
        handleViewMoreInfoCardClick(e);
    }

    return {
       handleEvents
    }

})()
