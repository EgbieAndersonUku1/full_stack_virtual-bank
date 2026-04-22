import { warnError, logError } from "../logger.js";
import { selectElement, toggleSpinner } from "../utils.js";
import { AlertUtils } from "../alerts.js";

const hiddenInputFields = document.querySelectorAll(".profile-input-hidden-field");
const dashboard         = document.getElementById("dashboard");
const tabs              = document.querySelectorAll(".tab");
const sectionTabs       = document.querySelectorAll(".section-tab");


// =======================================================
// SECURITY SETTINGS RADIO CONTROLS (ON / OFF TOGGLES)
// =======================================================
// This section contains DOM references for all radio button
// groups used in the Security & Notification settings panel.
//
// Each feature is represented as a binary toggle (ON / OFF):
// - Two-Factor Authentication (2FA)
// - Suspicious Activity Alerts
// - Account Activity Notifications
// - Transaction Alerts
// - Promotional Notifications
//
// These elements are intentionally grouped in pairs so they
// can be managed generically through a shared toggle handler
// with confirmation logic and state rollback support.
// =======================================================


// 2FA radio buttons
const twoFaOnRadio  = document.getElementById("two-fa-on");
const twoFaOffRadio = document.getElementById("two-fa-off");

// Suspicious activity alerts
const suspiciousOnRadio  = document.getElementById("suspicious-alert-on");
const suspiciousOffRadio = document.getElementById("suspicious-alert-off");

// Account activity notifications
const accountActivityOnRadio  = document.getElementById("account-activity-on");
const accountActivityOffRadio = document.getElementById("account-activity-off");

// Transaction alerts
const transactionAlertsOnRadio  = document.getElementById("transaction-alerts-on");
const transactionAlertsOffRadio = document.getElementById("transaction-alerts-off");

// Promotional notifications
const promotionalOnRadio  = document.getElementById("promotional-on");
const promotionalOffRadio = document.getElementById("promotional-off");


// hidden form values
// checks if hiddenInputFieds are all nodelist
document.addEventListener("DOMContentLoaded", () => {
    
    if (!(hiddenInputFields instanceof NodeList) && !(tabs instanceof NodeList)) {

        logError("updateHiddenInputField", {
            result: "The hidden input fields is not a node list",
            hiddenInputFields: hiddenInputFields,
            typeOfFields: typeof hiddenInputFields,
            
        })
        return;

       
    };

     // show the first section when loaded e.g profile page tab
     const profileSection = sectionTabs[0];
     selectElement(profileSection, "show")
})




// TODO add one time checker here for one time static element check
dashboard.addEventListener("click", handleDelegation);
dashboard.addEventListener("change", handleDelegation)




// This cache stores references to input, spinner, and label elements for each field.
//
// Although these elements exist in the DOM on page load, they are initially hidden.
// Without caching, we would need to repeatedly query the DOM every time the user
// clicks "Edit", which is inefficient and unnecessary.
//
// Instead, the first time an "Edit" action occurs, we locate the relevant elements
// and store them in this cache using their associated ID. Now on subsquent clicks are then
// retrieve the elements directly from memory rather than querying the DOM again.
//
// This improves performance and keeps the logic cleaner by avoiding repeated DOM lookups.
const cacheHiddenInputElements = {
    inputElements: {},

    getInputElementById(id) {
        const data = this.inputElements[id];
        return data === undefined ? null : data;

    },

    setInputElementToCache(element, spinnerElement, fieldLabelElement,  id) {
        this.inputElements[id] = {
            element: element,
            spinnerElement: spinnerElement,
            labelElement: fieldLabelElement
        }
    },

}




/**
 * Delegates wallet connection UI events to WalletWizard.
 * @param {Event} e Click or submit event.
 */
function handleDelegation(e) {

   const EXPECTED_CLASS_SELECTOR  = "profile_edit";
   const EDIT = "edit";
   const SAVE = "save";
   const EXPECTED_FIELD_TYPE = "radio"

  
    if (e.target.classList.contains("tab")) {
         console.log(e.target.classList.contains("tab"))
        handleTabs(e)
    }

    if ( !e.target.classList.contains(EXPECTED_CLASS_SELECTOR) &&  
    (e.target.tagName !== "INPUT" || e.target.type !== EXPECTED_FIELD_TYPE)) {
    return false;
    }
    
   
    
    const linkTextContent = e.target.textContent.toLowerCase().trim();
    switch(linkTextContent) {

        case EDIT:
            handleEditClick(e);
            break;
        case SAVE:
            handleSaveClick(e);
            break;
        default:
            handleRadioButtonClick(e)
            break;

    }
   
}




/**
 * Handles the "Edit" click event for a profile field.
 *
 * This function retrieves the associated input/select element, spinner,
 * and label for the clicked field. It first attempts to fetch these elements
 * from the cache. If they are not cached, it queries the DOM, stores them
 * in the cache, and then retrieves them.
 *
 * Once the required elements are available, it passes them to
 * `showhiddenStats` to toggle the UI into edit mode.
 *
 * @param {Event} e - The click event triggered by the "Edit" link.
 *
 * @returns {void} Early returns if required elements cannot be found.
 *
 * Workflow:
 * 1. Extract the field ID from the clicked element.
 * 2. Attempt to retrieve cached DOM references for that field.
 * 3. If not cached:
 *    - Query the DOM for input/select, spinner, and label elements.
 *    - Store them in the cache for future use.
 * 4. Pass the retrieved elements to the UI handler.
 */
function handleEditClick(e) {

  const inputFieldId = parseIdFromEvent(e);
  let data           = cacheHiddenInputElements.getInputElementById(inputFieldId);


  if (data === null) {

    console.log("Not found, getting and storing elements to cache");

    const parent         = e.target.parentElement;
    const element        = parent.querySelector("input") || parent.querySelector("select");
    const spinnerElement = parent.querySelector('[data-spinner="true"]');
    const fieldLabel     = parent.querySelector(".profile-p-label-value");
    

    if (!element || !spinnerElement || !fieldLabel) return;

    cacheHiddenInputElements.setInputElementToCache(element, spinnerElement, fieldLabel, inputFieldId);

    data = cacheHiddenInputElements.getInputElementById(inputFieldId);
 

  } else {
    
    console.log("Retrieving elementts from cache...");

  }
  
   const link = e.target;
   showhiddenStats(data, link);


}





/**
 * Toggles a profile field into "edit mode" with a loading spinner effect.
 *
 * This function simulates a short loading state by displaying a spinner,
 * then reveals the input/select element while hiding the label. It also
 * updates the "Edit" link to a "Save" state.
 *
 * @param {Object} data - Cached DOM references for the field.
 * @param {HTMLElement} data.element - The input or select element to show.
 * @param {HTMLElement} data.spinnerElement - The spinner element to toggle.
 * @param {HTMLElement} data.labelElement - The label element to hide.
 * @param {HTMLElement} link - The clicked "Edit" link element.
 *
 * @returns {void}
 */
function showhiddenStats(data, link) {

    const MILLI_SECONDS = 1000;

    toggleSpinner(data.spinnerElement, true);

    setTimeout(() => {

        toggleElement(data.element);
        toggleElement(data.labelElement, false);
        toggleSpinner(data.spinnerElement, false, false);
        handleLink.changeEditLinkToSave(link);

    }, MILLI_SECONDS);

 
}



/**
 * Extracts the input field ID from a click event.
 *
 * This function reads the `data-input-id` attribute from the event target,
 * which is expected to be the element that triggered the event (e.g. an
 * "Edit" link). 
 *
 * @param {Event} e - The event object triggered by user interaction.
 *
 * @returns {string|undefined} The value of `data-input-id` if present,
 * otherwise undefined. Returns early if the event is invalid.
 */
function parseIdFromEvent(e) {
    if (!(e && e.target)) {
        warnError("parseIdFromEvent", {
            expected: "Expected an event",
            received: e,
            type: typeof e,
        })
        return;
    }
    return e.target.dataset?.inputId;
}











/**
 * Toggles a CSS class on an element to control its visibility/state.
 *
 * When `show` is true, the provided CSS class is added to the element
 * (via `selectElement`). When false, the class is removed directly.
 *
 * @param {HTMLElement} element - The DOM element to modify.
 * @param {boolean} [show=true] - Determines whether to add or remove the class.
 * @param {string} [cssSelector="show"] - The CSS class to toggle.
 *
 * @returns {void} Returns early if `show` is not a boolean.
 *
 * Behaviour:
 * 1. Validates that `show` is a boolean.
 * 2. If true, applies the CSS class using `selectElement`.
 * 3. If false, removes the CSS class from the element.
 *
 * Note:
 * - This function assumes `selectElement` is responsible for adding the class.
 * - The default "show" class should control visibility via CSS and must be in the css file.
 */
function toggleElement(element, show = true, cssSelector = "show") {
    
    if (!(typeof show === "boolean")) return;


    if (show) {
        selectElement(element, cssSelector);
        return;
    }
   
    element.classList.remove(cssSelector);
 
}





/**
 * Handles the link by changing the link to either edit or save when it is clicked.
 * If the link is edit, it changes to save and vice versa.
 */
const handleLink = {
    setLinkText(link, text) {
        const isValid = this._validateLink(link, "setLinkText");
        if (!isValid) return false;

        link.textContent = text;
    },

    changeEditLinkToSave(link) {
        this.setLinkText(link, "Save");
    },

    changeSaveLinkToEdit(link) {
        this.setLinkText(link, "Edit");
    },

    _validateLink(link, caller) {
        if (!(link instanceof HTMLAnchorElement)) {
            warnError(caller, {
                link: link,
                typeOfLink: typeof link,
                expected: "Expected an anchor link",
            });
            return false;
        }
        return true;
    }
};





/**
 * Handles the "Save" click event for a profile field.
 *
 * This function updates the visible label with the value from the input/select
 * element, then transitions the UI back to "view mode". 
 *
 * @param {Event} e - The click event triggered by the "Save" link.
 *
 * @returns {void}
 *
 * Note:
 * - Assumes the field has already been cached during the edit phase.
 * - This function currently simulates saving; no backend request is made.
 */
function handleSaveClick(e) {
   const id = parseIdFromEvent(e);

   const data = cacheHiddenInputElements.getInputElementById(id)
   data.labelElement.textContent = data.element.value;


   const MILLI_SECONDS = 1000;
   
   toggleSpinner(data.spinnerElement, true)

   setTimeout(() => {
     toggleElement(data.element, false);
     toggleElement(data.labelElement, true);
     handleLink.changeSaveLinkToEdit(e.target);
      toggleSpinner(data.spinnerElement, false)

   }, MILLI_SECONDS)
  



}



/**
 * Routes radio button interactions to the appropriate handler.
 *
 * This function acts as a dispatcher for radio input events, determining
 * which feature-specific handler to invoke based on the parsed identifier
 * from the event target.
 *
 * It currently supports:
 * - 2FA recovery code backup toggling
 * - Suspicious activity alert toggling (default fallback)
 *
 * The routing logic relies on a parsed identifier (via `parseIdFromEvent`)
 * to decide which handler to execute.
 *
 * @function handleRadioButtonClick
 * @param {Event} e - The event triggered by a radio button interaction.
 * @param {HTMLInputElement} e.target - The radio input element that was interacted with.
 *
 * @returns {void}
 */
function handleRadioButtonClick(e) {

    const id = parseIdFromEvent(e)
    const AUTH_RECOVERY_CODE_ID = "two-fa-status";
    const SUSPICIOUS_CODE_ID    = "suspicious-alerts-status";
    const ACCOUNT_ACTIVITY_CODE_ID = "account-activity-status";
    const TRANSACTION_ALERTS_CODE_ID = "transaction-alerts-status";
    const PROMOTIONAL_ALERTS_CODE_ID  = "promotional-status";
 
    switch(id) {

        case AUTH_RECOVERY_CODE_ID:
            handle2FARecoveryCodeBackup(e);
            break;
        case SUSPICIOUS_CODE_ID:
            handleSuspiciousAlert(e);
            break;
        case ACCOUNT_ACTIVITY_CODE_ID:
            handleAccountActivityAlert(e);
            break;
        case TRANSACTION_ALERTS_CODE_ID:
            handleTransactionAlert(e);
            break;
        case PROMOTIONAL_ALERTS_CODE_ID:
            handlePromotionalAlert(e);
            break;
    }
    
}



/**
 * Handles toggling of 2FA recovery code backup for the user account.
 *
 * This function presents a confirmation alert before enabling or disabling
 * backup codes used for account recovery. The messaging dynamically reflects
 * the selected state, clearly explaining the benefit of enabling (account
 * recovery access) and the risk of disabling (losing a backup option).
 *
 *
 * @async
 * @function handle2FARecoveryCodeBackup
 * @param {Event} e - The change event triggered by the radio input.
 * @param {HTMLInputElement} e.target - The input element containing the selected value ("on" or "off").
 *
 * @returns {Promise<void>} Resolves once the confirmation flow is completed.
 */
async function handle2FARecoveryCodeBackup(e) {
    const value = e.target.value;


    const isEnabling = value === "on";
    const previousRadioBtnStatus = isEnabling ? twoFaOffRadio : twoFaOnRadio;
   
    const confirm = await AlertUtils.showConfirmationAlert({
        title: isEnabling ? "Enable backup codes?" : "Disable backup codes?",
        text: isEnabling
            ? "Backup codes let you access your account if you lose your 2FA device."
            : "Disabling this removes your backup access option if you lose your 2FA device.",
        icon: "warning",
        cancelMessage: "No changes made",
        messageToDisplayOnSuccess: isEnabling
            ? "Backup codes enabled successfully."
            : "Backup codes disabled successfully.",
        denyButtonText: "Cancel action",
        confirmButtonText: isEnabling ? "Enable" : "Disable",
    });

    if (confirm) {
        // perform action with fetch. No backend yet.
        e.target.checked = true;
        return;
        
    } 
     previousRadioBtnStatus.checked = true;
    
}





/**
 * Handles toggling of suspicious activity alerts for the user account.
 *
 * This function prompts the user with a confirmation alert before enabling
 * or disabling suspicious activity notifications. The messaging is dynamically
 * adjusted based on the selected state to clearly communicate the impact
 * of the action (e.g., missing important security alerts when disabled).
 *
 *
 * @async
 * @function handleSuspiciousAlert
 * @param {Event} e - The change event triggered by the radio input.
 * @param {HTMLInputElement} e.target - The input element containing the selected value ("on" or "off").
 *
 * @returns {Promise<void>} Resolves once the confirmation flow is completed.
 */
async function handleSuspiciousAlert(e) {
    const value = e.target.value;
    const isEnabling = value === "on";

    // const previousValue = 
    const previousRadioBtnStatus = isEnabling ? suspiciousOffRadio : suspiciousOnRadio;

    const confirm = await AlertUtils.showConfirmationAlert({
        title: isEnabling 
            ? "Enable suspicious activity alerts?" 
            : "Disable suspicious activity alerts?",
        text: isEnabling
            ? "You’ll be notified if we detect unusual activity on your account."
            : "You may miss important alerts about unusual activity on your account.",
        icon: isEnabling ? "info" : "warning",
        cancelMessage: "No changes made",
        messageToDisplayOnSuccess: isEnabling
            ? "Suspicious activity alerts enabled."
            : "Suspicious activity alerts disabled.",
        denyButtonText: "Cancel alert",
        confirmButtonText: isEnabling ? "Enable alerts" : "Disable alerts",
    });

    if (confirm) {
            // perform action with fetch. No backend yet.
        e.target.checked = true;
        return;
    }

    previousRadioBtnStatus.checked = true;
}



/**
 * Handles toggling of account activity alerts for the user account.
 *
 * This function presents a confirmation alert before enabling or disabling
 * notifications related to account activity (e.g. login attempts and account changes).
 * The messaging dynamically reflects the selected state, highlighting the benefit
 * of staying informed when enabled and the potential risk of missing important
 * security updates when disabled.
 *
 * @async
 * @function handleAccountActivityAlert
 * @param {Event} e - The change event triggered by the radio input.
 * @param {HTMLInputElement} e.target - The input element containing the selected value ("on" or "off").
 *
 * @returns {Promise<void>} Resolves once the confirmation flow is completed.
 */
async function handleAccountActivityAlert(e) {
    const value = e.target.value;
    const isEnabling = value === "on";

    const previousRadioBtnStatus = isEnabling ? accountActivityOffRadio : accountActivityOnRadio;

    const confirm = await AlertUtils.showConfirmationAlert({
        title: isEnabling 
            ? "Enable account activity alerts?" 
            : "Disable account activity alerts?",
        text: isEnabling
            ? "You’ll be notified about login attempts and important changes to your account."
            : "You may miss important updates about login attempts or changes to your account.",
        icon: isEnabling ? "info" : "warning",
        cancelMessage: "No changes made",
        messageToDisplayOnSuccess: isEnabling
            ? "Account activity alerts enabled."
            : "Account activity alerts disabled.",
        denyButtonText: "Cancel action",
        confirmButtonText: isEnabling ? "Enable alerts" : "Disable alerts",
    });

    if (confirm) {
        // perform action with fetch. No backend yet.
        e.target.checked = true;
        return;
    }

    previousRadioBtnStatus.checked = true;
}




/**
 * Handles toggling of transaction alerts for the user account.
 *
 * This function presents a confirmation alert before enabling or disabling
 * notifications related to account transactions and unusual financial activity.
 * The messaging dynamically reflects the selected state, highlighting the benefit
 * of staying informed about account activity when enabled and the potential risk
 * of missing important transaction updates when disabled.
 *
 * @async
 * @function handleTransactionAlert
 * @param {Event} e - The change event triggered by the radio input.
 * @param {HTMLInputElement} e.target - The input element containing the selected value ("on" or "off").
 *
 * @returns {Promise<void>} Resolves once the confirmation flow is completed.
 */
async function handleTransactionAlert(e) {
    const value = e.target.value;
    const isEnabling = value === "on";
    
    const previousRadioBtnStatus = isEnabling ? transactionAlertsOffRadio : transactionAlertsOnRadio;

    const confirm = await AlertUtils.showConfirmationAlert({
        title: isEnabling 
            ? "Enable transaction alerts?" 
            : "Disable transaction alerts?",
        text: isEnabling
            ? "You’ll be notified about important transactions and unusual activity."
            : "You may miss important updates about transactions or unusual activity on your account.",
        icon: isEnabling ? "info" : "warning",
        cancelMessage: "No changes made",
        messageToDisplayOnSuccess: isEnabling
            ? "Transaction alerts enabled."
            : "Transaction alerts disabled.",
        denyButtonText: "Cancel action",
        confirmButtonText: isEnabling ? "Enable alerts" : "Disable alerts",
    });

   if (confirm) {
        // perform action with fetch. No backend yet.
        e.target.checked = true;
        return;
        
    } 
    previousRadioBtnStatus.checked = true;
}



/**
 * Handles toggling of promotional notifications for the user account.
 *
 * This function presents a confirmation alert before enabling or disabling
 * marketing-related notifications such as offers, updates, and product announcements.
 * The messaging dynamically reflects the selected state, emphasising the benefit
 * of staying informed about new features and promotions when enabled, while making
 * it clear that disabling will stop non-essential communications.
 *
 * @async
 * @function handlePromotionalAlert
 * @param {Event} e - The change event triggered by the radio input.
 * @param {HTMLInputElement} e.target - The input element containing the selected value ("on" or "off").
 *
 * @returns {Promise<void>} Resolves once the confirmation flow is completed.
 */
async function handlePromotionalAlert(e) {
    const value      = e.target.value;
    const isEnabling = value === "on";

    const previousRadioBtnStatus = isEnabling ? promotionalOffRadio : promotionalOnRadio;

    const confirm = await AlertUtils.showConfirmationAlert({
        title: isEnabling 
            ? "Enable promotional notifications?" 
            : "Disable promotional notifications?",
        text: isEnabling
            ? "You’ll receive updates about offers, new features, and announcements."
            : "You will no longer receive promotional updates or offers.",
        icon: "info",
        cancelMessage: "No changes made",
        messageToDisplayOnSuccess: isEnabling
            ? "Promotional notifications enabled."
            : "Promotional notifications disabled.",
        denyButtonText: "Cancel action",
        confirmButtonText: isEnabling ? "Enable" : "Disable",
    });

    if (confirm) {
        // perform action with fetch. No backend yet.
        e.target.checked = true;
        return;
        
    } 
     previousRadioBtnStatus.checked = true;
}




/**
 * Handles tab switching logic for the UI.
 *
 * This function manages the active tab state and corresponding content sections.
 * It assumes a strict 1:1 index-based relationship between `tabs` and `sectionTabs`,
 * meaning each tab directly maps to a section at the same index.
 *
 * On user interaction, it:
 * - deselects all tabs but leaves the clicked tab
 * - Hides all sections
 * - Displays the corresponding section based on the clicked tab's dataset value
 *
 * If the number of tabs and sections is mismatched, the function logs an error
 * and exits early to prevent UI inconsistencies.
 *
 * @function handleTabs
 * @param {Event} e - Click event from a tab element.
 * @param {HTMLElement} e.target - The clicked tab element containing dataset.sectionName.
 *
 * @returns {void}
 */
function handleTabs(e) {
    const clickedTab          = e.target;
    const ACTIVE_TAB_SELECTOR = "active";
    const SHOW_SELECTOR       = "show";
    let sectionToShow;


   if (tabs.length !== sectionTabs.length) {
    warnError("handleTabs", {
        numberOfTabs: tabs.length,
        numberOfSections: sectionTabs.length,
        errorMsg: "Tabs and sections count mismatch. Each tab must correspond to a section."
    });
    return;
}

//  console.log("I am here")
  
 // Single pass to update both tabs and sections.
// This relies on tabs and sections being equal in number and index-aligned,
// meaning each tab corresponds directly to a section at the same index.
// This avoids separate loops and keeps the operation efficient.
  for (let i = 0; i < tabs.length; i++) {

      const tab = tabs[i];
      tab.classList.remove(ACTIVE_TAB_SELECTOR);

      const section = sectionTabs[i];
      section.classList.remove(SHOW_SELECTOR)

      if (section && section.id === clickedTab.dataset.sectionName) {
         sectionToShow = section
      }
  }

  
  // show the active tab and section corresponding to the tab
  toggleElement(clickedTab, true,  ACTIVE_TAB_SELECTOR);
  toggleElement(sectionToShow, true,  SHOW_SELECTOR)


}


