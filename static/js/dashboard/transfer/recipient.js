import { AlertUtils } from "../../alerts.js";
import fetchData from "../../fetch.js";
import { parseFormData } from "../../formUtils.js";
import { warnError } from "../../logger.js";
import { getCsrfToken } from "../../security/csrf.js";
import { enableAutoFocusNavigation, selectElement, toggleSpinner, toTitle } from "../../utils.js";
import { getAccountDetailsFromData } from "./utils.js";


// ----- Containers / Sections -----
const addRecipient = document.getElementById("add-recipient-section");
const recipientAccountInputs = document.querySelectorAll(".recipient-account input");
const recipientSelects = document.getElementById("recipient");
const findRecipientBtns = document.getElementById("find-recipient-buttons");
const verifiedRecipientPanel = document.getElementById("recipient-container");
const findRecipientForm = document.getElementById("find-recipient-form");
const addRecipientSpinner = document.getElementById("add-recipient__spinner");



findRecipientForm.addEventListener("submit", handleFindRecipientFormSubmission);




// Manages the state and button visibility of the "Find Recipient" panel.
// Prevents users from bypassing the workflow by manually hiding the panel in the inspector.
export const findRecipientPanel = {
    // Tracks whether the panel is currently open
    panelIsOpen: false,

    /**
     * Returns true if the panel is open, false otherwise.
     * @returns {boolean}
     */
    isOpen() {
        return this.panelIsOpen === true;
    },

    /**
     * Sets the panel's open state.
     * @param {boolean} value - true to open the panel, false to close it.
     */
    setOpen(value) {
        this.panelIsOpen = value;
    },

    /**
     * Hides the Find Recipient buttons by adding the 'hide' class.
     * Usually called when the panel is open to enforce proper workflow.
     */
    hideButtons() {
        findRecipientBtns.classList.add("hide");
    },

    /**
     * Shows the Find Recipient buttons by removing the 'hide' class.
     * Usually called when the panel is closed or workflow allows interaction.
     */
    showButtons() {
        findRecipientBtns.classList.remove("hide");
    }
};




/**
 * Handles closing the "Find Recipient" modal when the close button is clicked.
 *
 * This function listens for click events on the modal. If the target element
 * is the designated close button, it hides the modal by calling `toggleFindRecipient(false)`.
 *
 * @param {Event} e - The click event triggered by the user.
 *
 * @returns {void}
 */
export function handleRecipientSelectionClose(e) {
    if (e.target.id !== "find-recipient-close-btn") return;

    toggleFindRecipient(false)

}




/**
 * Handles the add recipient option when it is selected from the select option.
 *
 * This function listens for events on elements that have `data-recipient="true"`.
 * When triggered, it calls `toggleFindRecipient()` to open or close the recipient search interface.
 *
 * @param {Event} e - The event triggered by user interaction (e.g., click).
 * @returns {void} - Does not return a value.
 *
 */
export function handleRecipientSelection(e) {
    if (e.target.dataset.recipient !== "true") return;

    toggleFindRecipient()
}






/**
 * Toggle the "Find Recipient" modal in the transfer form.
 *
 * When `show` is true, the modal appears, allowing the user to enter recipient details.
 * When `show` is false, the modal hides. The recipient select field can optionally
 * reset to its default state depending on user interaction.
 *
 * @param {boolean} show - Whether to display the modal. Defaults to true.
 * @param {boolean} resetSelectOption - Determines if the recipient select field should be reset
 *                                      when hiding the modal. Defaults to true.
 * @param {string} cSSelectorName - The selector for opening or closing the panel
 *
 * Behaviour:
 *   - true: Clears the select field when the modal is closed. Use when the user cancels
 *           the action to start fresh.
 *   - false: Preserves the current selection. Use when the user has already interacted
 *            with the field and the selection should be maintained.
 *
 * @returns {void}
 */
export function toggleFindRecipient(show = true, resetSelectOption = true, cSSelectorName = "show") {
    const booleanType = typeof show;

    if (booleanType !== "boolean") {
        warnError("toggleFindRecipient", {
            type: booleanType,
            msg: "Expected a boolean",
            received: `Received a value of ${show}`

        })
        return;
    }


    if (show) {
        selectElement(addRecipient, cSSelectorName);

        enableAutoFocusNavigation(recipientAccountInputs);
        findRecipientPanel.setOpen(true);
        if (findRecipientPanel.isOpen()) {
            findRecipientPanel.hideButtons()
        }
        return;
    }

    addRecipient.classList.remove(cSSelectorName);
    findRecipientPanel.setOpen(false);

    if (!findRecipientPanel.isOpen()) {
        findRecipientPanel.showButtons();
    }
    if (resetSelectOption) {
        recipientSelects.value = "";
    }

}






/**
 * Displays the verified user panel with the user's full name.

 *
 * @param {string} firstName - The user's first name.
 * @param {string} surname - The user's surname.
 *
 * @returns {void}
 *
 * Behaviour:
 *   - If either `firstName` or `surname` is missing, the function exits without doing anything.
 *   - If either parameter is not a string, a warning is issued via `warnError` and the panel is not shown.
 *   - Otherwise, the panel is displayed and the name is formatted with proper capitalization.
 *
 * Example:
 *   showVerifiedRecipient("Doctor", "Who");
 *   // Verified user panel displays: "Doctor Who"
 */
function showVerifiedRecipient(firstName, surname, msg = null) {
    if (!(firstName && surname)) return;

    if (typeof firstName !== "string" && typeof surname !== "string") {
        warnError("showVerifiedRecipient", {
            firstName: firstName,
            surname: surname,
            firstNameType: typeof firstName,
            surnameType: typeof surname,
            expected: "Expected both values to be string"
        })
        return;
    }

    selectElement(verifiedRecipientPanel, "show");
    verifiedRecipientPanel.textContent = `${toTitle(firstName)} ${toTitle(surname)} - (${msg})`;
    console.log(verifiedRecipientPanel)

}






/**
 * Extracts and parses data from the "Find Recipient" form.
 *
 * This function collects all form fields using FormData and ensures that the
 * required fields are included. The resulting object is filtered and formatted
 * using the `parseFormData` helper function.
 *
 * @returns {Object} parsedFormData - An object containing the validated and parsed form data.
 *
 * Required fields:
 *   - first_name, surname
 *   - sortcode_1 to sortcode_6
 *   - account_digit_1 to account_digit_8
 *
 * Note: Ensure `findRecipientForm` is correctly selected in the DOM before calling.
 */
function getParseFormData(formElement, requiredFields) {
    const formData = new FormData(formElement);

    const parsedFormData = parseFormData(formData, requiredFields);
    return parsedFormData;
}



/**
 * Handles the submission of the "Find Recipient" form.

 * @param {Event} e - The submit event triggered by the form.
 *
 * @returns {void}
 */
export async function handleFindRecipientFormSubmission(e) {
    e.preventDefault();
    const MILL_SECONDS = 1000;

    const requiredFields = [
        "first_name",
        "surname",
        "sortcode_1",
        "sortcode_2",
        "sortcode_3",
        "sortcode_4",
        "sortcode_5",
        "sortcode_6",
        "sortcode_7",
        "account_digit_1",
        "account_digit_2",
        "account_digit_3",
        "account_digit_4",
        "account_digit_5",
        "account_digit_6",
        "account_digit_7",
        "account_digit_8",

    ];
    const parsedFormData = getParseFormData(findRecipientForm, requiredFields);
    const accountDetails = getAccountDetailsFromData(parsedFormData);

    const response = await fetchData({
        url: "/dashboard/verify/recipient/",
        method: "POST",
        csrfToken: getCsrfToken(),
        body: {
            firstName: parsedFormData.firstName || "",
            surname: parsedFormData.surname || "",
            sortCode: accountDetails.sortCode || "",
            accountNumber: accountDetails.accountNumber || "",
        }


    })


    toggleSpinner(addRecipientSpinner, true, true)
    setTimeout(() => {
        toggleSpinner(addRecipientSpinner, false, true);

        const data = response.data;
        console.log(data)

        const isRecipientFound = data.SUCCESS && data.FOUND;
        //  state.IS_RECIPIENT_FOUND = isRecipientFound;
        console.log(isRecipientFound)
        AlertUtils.showAlert({
            title: data.ACTION,
            text: data.MSG,
            icon: isRecipientFound ? "success" : "error",
            confirmButtonText: "OK"
        });

        if (isRecipientFound) {
            toggleFindRecipient(false, false);
            showVerifiedRecipient(parsedFormData.firstName, parsedFormData.surname, data.MSG);
            return true;
        }

        return false;

    }, MILL_SECONDS)

}
