import { deselectAllTabs, highlightTab } from "../utils/tab-utils.js";
import { formatCurrency, sanitizeText, toggleSpinner } from "../utils.js";
import { badgeConfig } from "./badge.config.js";
import { warnError } from "../logger.js";
import { minimumCharactersToUse } from "../utils/password/textboxCharEnforcer.js";
import fetchData from "../fetch.js";
import { getCsrfToken } from "../security/csrf.js";
import { RequestHeader } from "./request-details-tabs/request-.tab-header.js";


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
        showFirstTableRowData();


});


/**
 * Handles tab click delegation and activates the corresponding tab content.
 */
async function handleDelegation(e) {

    const id = e.target.dataset.tab || e.target.id;
    const tab = e.target;


    const applicationId = e.target.closest("tr")?.dataset;

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

    if (applicationId) {
       const response = await getApplicationInfoRequest(applicationId.id);
       renderApplicationDetailsToUI(response.data.APPLICATION_DATA)
       console.log(response)

    }
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



async function getApplicationInfoRequest(applicationID) {

    const resp = await fetchData({
        url: "/card-request/application/details/",
        csrfToken: getCsrfToken(),
        body: {
            application_id: applicationID,
        },

        method: "POST",

    })

    return resp;

}



/**
 * Renders all the parts that make up the application
 * request info, user information, account details
 * and the audit trail
 *
 * @param {*} data: The application data containing the necessary
 * fields for the rendering
 * @returns
 */
function renderApplicationDetailsToUI(data) {
    if (!data) return;
    renderRequestInHeader(data)

    // The rest of tab rendering to go here
}



/**
 * Takes the application data and renders it to the application
 * page. The function renders the profile pic, full name, email
 * address, submission data and the status of the application
 * @param {*} applicationData - The application data
 */
function renderRequestInHeader(applicationData) {


    const header = new RequestHeader(applicationData);
    header.render();

}





/**
 * showFirstTableRowData
 *
 * Retrieves and displays the application details for the first card request
 * displayed in the applications table when the page first loads.
 *
 * This function acts as an orchestration layer between the application table,
 * the API request, and the UI rendering components. It retrieves the first
 * application's ID from the table row, requests the corresponding application
 * data, and passes the returned data to the UI rendering layer.
 *
 * Expected HTML structure:
 *
 * <tbody id="card-requests-tbody">
 *     <tr data-id="application-id">
 *         ...
 *     </tr>
 * </tbody>
 *
 * Example:
 *
 * await showFirstTableRowData();
 *
 * @async
 * @returns {Promise<void>}
 */
async function showFirstTableRowData() {
    const tableBody = document.getElementById("card-requests-tbody")

    if (!tableBody) return;

    const firstRowApplicationId = tableBody.querySelector("tr").dataset.id;
    const response = await getApplicationInfoRequest(firstRowApplicationId);
    console.log(response)
    renderApplicationDetailsToUI(response.data.APPLICATION_DATA)
}
