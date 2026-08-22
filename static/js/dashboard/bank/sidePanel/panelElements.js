

const viewExtraCardInfo        = document.getElementById("view-more-bank-card");
const extraCardInfoPanel       = document.getElementById("view-card-panel");
const fullCardDetailsContainer = document.getElementById("full-card-details");
const cardDetailsContainer     = document.getElementById("full-card-details-info");
const bankCardButtons          = document.querySelector(".view-card-panel-buttons");
const cardTransferFormSection  = document.getElementById("bank-funds-transfer");
const viewBankTransactionPanel = document.getElementById("bank-account-view-transactions");
const selectCardsContainer     = document.getElementById("bank-funds-transfer__select-cards-panel");
const bankCardSelectionTypes   = document.querySelectorAll(".account-card");


export const BANK_DASHBOARD_ELEMENTS = {
    EXTRA_CARD_INFO_PANEL: extraCardInfoPanel,
    VIEW_EXTRA_CARD_INFO: viewExtraCardInfo,
    FULL_CARD_DETAILS_CONTAINER: fullCardDetailsContainer,
    CARD_DETAILS_CONTAINER: cardDetailsContainer,
    BANK_CARD_BUTTONS: bankCardButtons,
    CARD_TRANSFER_FORM_SECTION: cardTransferFormSection,
    VIEW_BANK_TRANSACTION_PANEL: viewBankTransactionPanel,
    SELECT_CARDS_CONTAINER: selectCardsContainer,
    BANK_CARD_SELECTION_TYPES: bankCardSelectionTypes,
};


export const BANK_DASHBOARD_SELECTORS = {
    EXTRA_CARD_INFO_PANEL: "#view-card-panel",
    VIEW_EXTRA_CARD_INFO: "#view-more-bank-card",
    FULL_CARD_DETAILS_CONTAINER: "#full-card-details",
    CARD_DETAILS_CONTAINER: "#full-card-details-info",
    BANK_CARD_BUTTONS: ".view-card-panel-buttons",
    CARD_TRANSFER_FORM_SECTION: "#bank-funds-transfer",
    VIEW_BANK_TRANSACTION_PANEL: "#bank-account-view-transactions",
    SELECT_CARDS_CONTAINER: "#bank-funds-transfer__select-cards-panel",
    BANK_CARD_SELECTION_TYPES: ".account-card",
};
