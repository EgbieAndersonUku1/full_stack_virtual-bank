
import { checkIfHTMLElement } from "../utils.js";
import { logError, warnError } from "../logger.js";




const CARD_IMAGES = {

    visa: {
        src: "../static/images/icons/visa.svg",
        alt: "Visa card logo",
        brand: "visa",
       
    },

    mastercard: {
        src: "../static/images/icons/mastercard.svg",
        alt: "Mastercard logo",
        brand: "mastercard",
    },

    discover: {
        src: "../static/images/icons/discover.svg",
        alt: "Discover logo",
        brand: "discover",
    }
    
}


export const cardImplementer = {

    /**
     * Creates a new card element with the specified details.
     *
     * This function delegates the creation of a single card element to another function, `createSingleCreateCard`, 
     * which takes care of the details of how the card is structured.
     *
     * @function createCard
     * @param {Object} cardDetails - An object containing the details to create the card.
     * @returns {HTMLElement} The newly created card element.
     */
    createCardDiv: (cardDetails) => {
        return createSingleCreateCard(cardDetails);
    },

    
    /**
     * Places a card element into a specified location within the DOM.
     *
     * This function checks if both the location and card div elements are valid HTML elements before appending
     * the card div to the location div. If either element is invalid, an error is logged. Optionally, it can 
     * clear the location div before appending the new card div.
     *
     * @function placeCardDivIn
     * @param {HTMLElement} locationDiv - The DOM element where the card div should be appended.
     * @param {HTMLElement} cardDiv - The card div element that will be added to the location div.
     * @param {boolean} [clearBeforeAppend=false] - If true, clears the location div before appending the card div.
     */

    placeCardDivIn: (locationDiv, cardDiv, clearBeforeAppend = false) => {

        if (!checkIfHTMLElement(locationDiv, "Location card div") ||  !checkIfHTMLElement(cardDiv, "Card div element")) {
            logError("cards.placeCardDivIn", "An error occurred trying to place card div element inside the given location");
            return;
        }

        try {
            if (clearBeforeAppend) {
                locationDiv.innerHTML = "";
              
            }
            locationDiv.appendChild(cardDiv);
            return true;
        } catch (error) {
            logError("cards.placeCardDivIn", `An error occurred while appending the card div: ${error.message}`);
            return false;
        }
    },

};




 /* Creates and returns a DOM element representing a single bank card.
 *
 * @param {Object} cardDetails - Card data used to build the card UI.
 * @returns {HTMLDivElement} The fully constructed card element.
 */
export function createSingleCreateCard(cardDetails) {
    const cardDiv = document.createElement("div");

    // Build modular sections
    cardDiv.appendChild(createCardHeadDiv(cardDetails));
    cardDiv.appendChild(createCardBodyDiv(cardDetails));
    cardDiv.appendChild(createFooterDiv(cardDetails));

    // Main card classes
    cardDiv.classList.add(
        "bank-card",
        `credit-${cardDetails.cardBrand.toLowerCase()}-card`
    );

    cardDiv.setAttribute(
        "aria-label",
        `${cardDetails.bankName} ${cardDetails.cardBrand} ${cardDetails.cardType}, balance ${cardDetails.cardAmount}`
    );

    // Create overlay div (will be reused for blocked status)
    const cardOverlay = document.createElement("div");
    cardOverlay.id = `card_${cardDetails.id}`;
    cardDiv.appendChild(cardOverlay);

   
    if (!cardDetails.isActive) applyCardBlockStatus(cardDiv, cardDetails);

    return cardDiv;
}

/**
 * Creates the card header section containing bank info and card logo.
 *
 * @param {Object} cardDetails - Card data.
 * @returns {HTMLDivElement} Card header element.
 */
function createCardHeadDiv(cardDetails) {
    const headDiv = document.createElement("div");
    headDiv.classList.add("card-head");

    const infoDiv = document.createElement("div");
    infoDiv.classList.add("card-head-info");
    infoDiv.innerHTML = `
        <h3>${cardDetails.bankName}</h3>
        <p class="bank-card-amount">${cardDetails.cardAmount}</p>
    `;

    const logoDiv = document.createElement("div");
    logoDiv.classList.add("card-type-logo", "flex", "flex-end");
    logoDiv.appendChild(createImageElementBasedOnCardType(cardDetails));

    headDiv.appendChild(infoDiv);
    headDiv.appendChild(logoDiv);

    return headDiv;
}


/**
 * Creates the main card body section (chip, type, and number).
 *
 * @param {Object} cardDetails - Card data.
 * @returns {HTMLDivElement} Card body element.
 */
function createCardBodyDiv(cardDetails) {
    const bodyDiv = document.createElement("div");
    bodyDiv.classList.add("card-body");

    // Chip
    const chipDiv = document.createElement("div");
    chipDiv.classList.add("chip");
    chipDiv.innerHTML = `<img src="/static/images/icons/sim-card-chip.svg" alt="Card chip">`;

    // Card type
    const typeDiv = document.createElement("div");
    typeDiv.className = "credit-transaction-type flex flex-end";
    typeDiv.innerHTML = `<span>${cardDetails.cardType}</span>`;

    // Card number
    const numberDiv = document.createElement("div");
    numberDiv.className = "card-number flex flex-end";
    numberDiv.innerHTML = `<span class="card-number">${cardDetails.cardNumber}</span>`;

    bodyDiv.appendChild(chipDiv);
    bodyDiv.appendChild(typeDiv);
    bodyDiv.appendChild(numberDiv);

    return bodyDiv;
}



/**
 * Creates the card footer section with cardholder name and expiry date.
 *
 * @param {Object} cardDetails - Card data.
 * @returns {HTMLDivElement} Card footer element.
 */
function createFooterDiv(cardDetails) {
    const footerDiv = document.createElement("div");
    footerDiv.classList.add("card-footer", "flex", "flex-space-between");

    const nameDiv = document.createElement("div");
    nameDiv.className = "card-name";
    nameDiv.textContent = cardDetails.cardName;

    const expiryDiv = document.createElement("div");
    expiryDiv.className = "card-expiry-date";
    expiryDiv.innerHTML = `<p>Expiry date: ${cardDetails.expiryMonth} ${cardDetails.expiryYear}</p>`;

    footerDiv.appendChild(nameDiv);
    footerDiv.appendChild(expiryDiv);

    return footerDiv;
}


/**
 * Returns an image element based on the card brand.
 *
 * @param {Object} cardDetails - Card data.
 * @returns {HTMLImageElement} Card brand image element.
 */
function createImageElementBasedOnCardType(cardDetails) {
    const img = document.createElement("img");
    const cardBrand = cardDetails.cardBrand.toLowerCase();

    if (CARD_IMAGES[cardBrand]) {
        img.src = CARD_IMAGES[cardBrand].src;
        img.alt = CARD_IMAGES[cardBrand].alt;
    } else {
        img.src = "";
        img.alt = "";
    }

    img.className = "card-icon";
    return img;
}



/**
 * Applies a blocked overlay and styling to a card element.
 *
 * @param {HTMLElement} cardDiv - Card container element.
 * @param {Object} cardDetails - Card data.
 */
function applyCardBlockStatus(cardDiv, cardDetails) {
    if (!checkIfHTMLElement(cardDiv, "Card div element")) return;

    const overlayId = `card_${cardDetails.id}`;
    let cardOverlay = cardDiv.querySelector(`#${overlayId}`);

  
    if (!cardOverlay) {
        cardOverlay = document.createElement("div");
        cardOverlay.id = overlayId;
        cardDiv.appendChild(cardOverlay);
    }

    cardOverlay.className = "card-overlay"; // reset classes
    cardOverlay.textContent = "Blocked";

    cardDiv.classList.remove("card-is-blocked", "card-not-blocked");
    cardDiv.classList.add("card-is-blocked");
}




/**
 * Removes the blocked overlay and styling from a card element.
 *
 * @param {HTMLElement} cardDiv - Card container element.
 * @param {Object} cardDetails - Card data.
 */
export function removeCardBlockStatus(cardDiv, cardDetails) {
    if (!checkIfHTMLElement(cardDiv, "Card div element")) return;

    const overlayId = `card_${cardDetails.id}`;
    const cardOverlay = cardDiv.querySelector(`#${overlayId}`);

    if (cardOverlay) {
        cardOverlay.classList.remove("card-overlay");
        cardOverlay.textContent = "";
    }

    cardDiv.classList.remove("card-is-blocked");
}




export function createCardDetails(cardDetails) {
    
    const fragment  = document.createDocumentFragment()
   
   const cardFields = [
     { fieldName: "Card ID", fieldValue: cardDetails.cardId },
    { fieldName: "Bank", fieldValue: cardDetails.bankName },
    { fieldName: "Card Name", fieldValue: cardDetails.cardName },
    { fieldName: "Card Number", fieldValue: cardDetails.cardNumber },
    { fieldName: "Card Amount", fieldValue: cardDetails.cardAmount },
    { fieldName: "Card Brand", fieldValue: cardDetails.cardBrand },
    { fieldName: "Card Type", fieldValue: cardDetails.cardType },
    { fieldName: "CVC", fieldValue: cardDetails.cardCVC },
    { fieldName: "Expiry date", fieldValue: cardDetails.expiryYear },
    { fieldName: "Creation Date", fieldValue: cardDetails.cardCreationDate },
    { fieldName: "Issue Date", fieldValue: cardDetails.issueDate },
    { fieldName: "Is card active", fieldValue: cardDetails.isActive}
];


    const isActiveElement    = updateCardActiveStatus(cardDetails, document.createElement("p")); 
    cardFields.forEach((cardField) => createFieldElement(cardField.fieldName, cardField.fieldValue, fragment))

    createFieldElement("Can the card be used", cardDetails.cardStatus, fragment);
    fragment.appendChild(isActiveElement)
    return fragment;
    

}


/**
 * Creates and appends a field row to a container.
 *
 * Output example:
 *   Card Number: **** 1234
 *
 * @param {string} fieldName - Label for the field.
 * @param {string} fieldDescription - Value/content of the field.
 * @param {HTMLElement} divToAddTo - Container to append the field to.
 */
function createFieldElement(fieldName, fieldDescription, divToAddTo) {
    const pTag = document.createElement("p");

    const label = document.createElement("span");
    label.className = "field-label";
    label.textContent = fieldName;

    const description = document.createElement("span");
    description.className = "field-value bold";
    description.textContent = fieldDescription;

    pTag.append(label, ": ", description);
    if (!divToAddTo) return;

    divToAddTo.appendChild(pTag);
}



/**
 * Updates the UI element to reflect whether a card is active or inactive.
 *
 * The function checks the card's active status and applies the appropriate
 * CSS class to the provided DOM element to visually indicate the state.
 *
 * @param {Object} cardDetails - Object containing card information.
 * @param {boolean} cardDetails.isCardActive - Indicates whether the card is active.
 * @param {HTMLElement} cardActiveElement - DOM element displaying the card's status.
 *
 * @returns {void}
 */

function updateCardActiveStatus(cardDetails, cardActiveElement) {


    if (cardDetails.cardStatus === "true") {
        cardActiveElement.className = "active-text";
        cardActiveElement.textContent = "The card is active";
        return cardActiveElement;
    } 
    
    cardActiveElement.className = "deactivate-text";
    cardActiveElement.textContent = "The card is blocked";
    return cardActiveElement;

    
}