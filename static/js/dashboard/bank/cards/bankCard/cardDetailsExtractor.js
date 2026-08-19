/**
 * @fileoverview
 * Provides functionality for extracting bank card details from
 * card DOM elements.
 */

import { checkIfHTMLElement } from "../../../../utils.js";


/**
 * @typedef {Object} CardDetails
 * @property {string} cardId - The unique identifier of the card.
 * @property {string} bankName - The name of the bank.
 * @property {string} cardBrand - The card brand.
 * @property {string} cardAmount - The current card balance.
 * @property {string} cardType - The type of card.
 * @property {string} cardNumber - The card number.
 * @property {string} expiryMonth - The card expiry month.
 * @property {string} expiryYear - The card expiry year.
 * @property {string} cardName - The name associated with the card.
 * @property {string} issueDate - The date the card was issued.
 * @property {string} cardCreationDate - The date the card was created.
 * @property {string} cardCVC - The card CVC.
 * @property {string} isActive - Whether the card is active.

 * Extracts card details from a bank card DOM element.
 *
 * @param {HTMLElement} bankCardElement - The DOM element representing a bank card.
 * @returns {CardDetails} The extracted card details.
 */
export function getCardDetailsFromElement(bankCardElement) {

    if (!checkIfHTMLElement(bankCardElement, "bankElements", false)) return;


    const bankName   = bankCardElement.querySelector(".card-head-info h3")?.textContent;
    const amount     = bankCardElement.querySelector(".bank-card-amount")?.textContent;
    const cardType   = bankCardElement.querySelector(".card-type")?.textContent.trim();
    const cardNumber = bankCardElement.querySelector(".card-number")?.textContent;
    const cardName   = bankCardElement.querySelector(".card-name")?.textContent;
    const expiryDate = bankCardElement.querySelector(".card-expiry-date")?.textContent;

    const [month, year] = expiryDate.split("Expiry date: ")


    const cardDetails = {
        cardId: bankCardElement.dataset.cardId,
        bankName: bankName,
        cardBrand: bankCardElement.dataset.cardBrand,
        cardAmount: amount,
        cardType: cardType,
        cardNumber: cardNumber,
        expiryMonth: month,
        expiryYear: year,
        cardName: cardName,
        issueDate: bankCardElement.dataset.issued,
        cardCreationDate: bankCardElement.dataset.creationDate,
        cardCVC: bankCardElement.dataset.cvc,
        isActive: bankCardElement.dataset.isActive,
    }
    return cardDetails;

}

