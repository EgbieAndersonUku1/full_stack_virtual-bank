import { checkIfHTMLElement } from "../utils.js";

/**
 * Simulates a UI content update in the absence of a backend response.
 *
 * Copies the HTML content of the source element into the target element
 * to demonstrate UI changes during development.
 *
 * @param {HTMLElement} target - The element whose contents will be updated.
 * @param {HTMLElement} source - The element containing the simulated content.
 */
export function simulateDivContentUpdate(target, source) {
    checkIfHTMLElement(target, "target");
    checkIfHTMLElement(source, "source");

    target.innerHTML = source.innerHTML;
}

