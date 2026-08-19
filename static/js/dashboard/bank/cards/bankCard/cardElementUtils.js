

  /**
   * Returns the closest selectable card element from an event target.
   *
   * The element must:
   * - Have the provided base card class
   * - NOT contain the excluded class (if provided)
   *
   * @param {Event} event - The DOM event triggered by user interaction.
   * @param {string} baseClass - The required card class (e.g., "bank-card").
   * @param {string} [excludedClass] - Optional class that disqualifies the card.
   * @returns {HTMLElement|null} The valid card element, or null if invalid.
   */
export function getSelectableCardElement(event, baseClass, excludedClass) {
        const element = event.target.closest(`.${baseClass}`);
        if (!element) return null;

        if (excludedClass && element.classList.contains(excludedClass)) {
            return null;
        }

        return element;
    }



/**
 * Attaches card metadata to a DOM card element using data attributes.
 *
 * This function mutates the provided `cardElement` by dynamically
 * assigning all properties from the `cardDetails` object to the
 * element's dataset.
 *
 * Each key in `cardDetails` becomes a corresponding `data-*` attribute.
 *
 * Example:
 *   cardDetails.cardId → data-card-id
 *   cardDetails.cardBrand → data-card-brand
 *
 * @param {HTMLElement} cardElement - The DOM element representing the card.
 * @param {Object} cardDetails - An object containing the card's metadata.
 * @returns {void}
 */
export function attachCardDetails(cardElement, cardDetails) {
    Object.entries(cardDetails).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            cardElement.dataset[key] = value;
        }
    });
}


