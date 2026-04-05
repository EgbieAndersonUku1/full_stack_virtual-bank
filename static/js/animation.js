/**
 * animations.js
 * 
 * Modular IntersectionObserver-based animations for scroll-triggered effects.
 * 
 * Note: For this to work, you must define the corresponding CSS rules.
 * For example:
 *   - Active class (e.g., `.is-visible`) with your animation transitions.
 *   - Selector elements (e.g., `.fade-up`, `.fade-left`, `.scale-up`) in HTML.
 * 
 * Example usage:
 * 
 * const selector         = ".fade-up"
 * const activeClass      = "is-visible"
 * const thresholdPercent = 1
 *  runObserver(selector, activeClass, thresholdPercent, )
 */

import { warnError } from "./logger.js";



/**
 * Convert a number to a fraction (percentage / 100)
 * @param {number} numberValue - A number between 0 and 100
 * @returns {number|null} - Float between 0 and 1, or null if invalid
 */
function getPercentage(numberValue) {

    if (!isNaN(numberValue)) {
        return numberValue / 100;
    }
    return null;
}



/**
 * Creates an IntersectionObserver instance that adds a class when elements become visible.
 * @param {string} activeClass - The class to add when element is visible
 * @param {number} thresholdPercent - Number between 0 and 100 defining how much of element must be visible
 * @returns {IntersectionObserver|null} - IntersectionObserver instance or null if invalid
 */
function initialIntersectionObserver(activeClass, thresholdPercent = 15) {
    if (typeof activeClass !== "string") {
        warnError("initialIntersectionObserver", `Expected string for class, got ${typeof activeClass}`);
        return;
    }

    if (typeof thresholdPercent !== "number" || thresholdPercent < 0 || thresholdPercent > 100) {
        warnError("initialIntersectionObserver", `Expected thresholdPercent between 0 and 100, got ${thresholdPercent}`);
        return;
    }

    const observationPercentage = getPercentage(thresholdPercent);

    if (!observationPercentage) {
        warnError("initialIntersectionObserver", `Invalid thresholdPercent: ${thresholdPercent}`);
        return;
    }

    return new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add(activeClass);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: observationPercentage });
}



/**
 * Runs the IntersectionObserver on all elements matching a selector
 * 
 * Note: For this to work, you must define the corresponding CSS rules.
 * For example, create the active class (e.g., `.is-visible`) and ensure
 * your elements have the proper selector (e.g., `.fade-up`).
 * 
 * @param {string} selector - CSS selector for target elements (default: ".fade-up")
 * @param {string} activeClass - Class to add when visible (default: "is-visible")
 * @param {number} thresholdPercent - Percent of element visible to trigger (default: 15)
 */
export default function runObserver({
    selector = ".fade-up",
    activeClass = "is-visible",
    thresholdPercent = 15
} = {}) {
    const elements = document.querySelectorAll(selector);
    const observer = initialIntersectionObserver(activeClass, thresholdPercent);
    if (!observer) return;
    elements.forEach(element => observer.observe(element));
}
