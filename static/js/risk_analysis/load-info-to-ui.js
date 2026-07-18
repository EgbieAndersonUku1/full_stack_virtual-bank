import { deselectAllTabs, highlightTab } from "../utils/tab-utils.js";
import { formatCurrency, sanitizeText, toggleSpinner } from "../utils.js";
import { badgeConfig } from "./badge.config.js";
import { warnError } from "../logger.js";
import { updateTable } from "./table.js";
import { renderTable, populateCardHistoryTable } from "./table.js";
import { minimumCharactersToUse } from "../utils/password/textboxCharEnforcer.js";


const tabs                = document.querySelectorAll(".tabs .tab")
const mainSectionContainer = document.querySelector(".dashboard__container__main");
const requestTabContents  = document.querySelectorAll(".request-tab-content");
const firstTabContent     = document.getElementById("request-first-tab");
const secondTabContent    = document.getElementById("request-second-tab");
const thirdTabContent     = document.getElementById("request-third-tab");
const fourthTabContent    = document.getElementById("request-fourth-tab");
const auditSpinner        = document.getElementById("load-audit-spinner");




mainSectionContainer.addEventListener("click", handleDelegation);




document.addEventListener("DOMContentLoaded", () => {

        showFirstTab();


});


/**
 * Handles tab click delegation and activates the corresponding tab content.
 */
function handleDelegation(e) {

    const id = e.target.dataset.tab || e.target.id;
    const tab = e.target;

    switch (id) {
        case "request-first-tab":
            activateTab(tab, firstTabContent);
            break;

        case "request-second-tab":
            activateTab(tab, secondTabContent);
            break;

        case "request-third-tab":
            activateTab(tab, thirdTabContent);
            break;

        case "request-fourth-tab":
            activateTab(tab, fourthTabContent);
            break;

        case "load-more":
            console.log("I am here")
            handleRendererAuditClick(e.target);
            break;
    }
}





/**
 * Sets the text content of an element by ID.
 * Falls back to an empty string if no value is provided.
 */
function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value || "";
}



/**
 * Activates a tab and displays its associated content panel.
 *
 * @param {HTMLElement} tab - The tab element to activate.
 * @param {HTMLElement} tabContent - The content panel to display.
 */
function activateTab(tab, tabContent) {
    deselectAllTabs(tabs);
    highlightTab(tab);
    hideAllTabContent();
    showTabContent(tabContent);
}


/**
 * Hides all tab content sections.
 */
function hideAllTabContent() {
    requestTabContents.forEach((tabContent) => {
        tabContent.style.display = "none";
    });
}

/**
 * Displays a specific tab content section.
 */
function showTabContent(tabConent) {
    tabConent.style.display = "block";
}

/**
 * Automatically activates and shows the first available tab.
 */
function showFirstTab() {
    if (Array.from(tabs).length > 0) {
        const firstTab = tabs[0];
        activateTab(firstTab, firstTabContent);
    }
}







function showNumOfCharsRemaining() {
   const requestTextArea = document.getElementById("notes");

   if (!requestTextArea) {
     warnError("showNumOfCharsRemaining", {
        error: "The id for the notes text area is invalid"
     });
     return;
   }


    minimumCharactersToUse(notes, {
        minCharClass: ".num-of-characters-remaining",
        maxCharClass: ".num-of-characters-to-use",
        minCharMessage: "Minimum characters to use: ",
        maxCharMessage: "Number of characters remaining: ",
        minCharsLimit: 50,
        maxCharsLimit: 255,
        disablePaste: true,
    })


}
