/**
 * Removes the active state from all tab links.
 *
 * This is typically called before activating a new tab to ensure that
 * only one tab appears highlighted at a time.
 *
 * @param {NodeList HTMLElement} tabs -A list of html elements for tab
 * @param {string} [cssSelector="active"] - The CSS class representing
 * the active/selected tab state.
 */
export function deselectAllTabs(tabLinks, cssSelector="active") {
    tabLinks.forEach((link) => {
        link.classList.remove(cssSelector);
    })

}


/**
 * Applies the active state to a specific tab element.
 *
 * @param {HTMLElement} tab - The tab element that should be highlighted.
 * @param {string} [cssSelector="active"] - The CSS class used to indicate
 * the active/selected state.
 */
export function highlightTab(tab, cssSelector="active") {
    tab.classList.add(cssSelector);

}
