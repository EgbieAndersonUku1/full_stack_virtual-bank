import { warnError } from "../logger.js";
import { toggleSpinner, toggleRequiredInput, isFormFieldEmpty, toTitle } from "../utils.js";
import { parseFormData } from "../formUtils.js";
import { AlertUtils } from "../alerts.js";

const cardRequestForm                   = document.getElementById("card-request-form");
const cardRequestEmploymentContainer    = document.getElementById("card-request-employment-information");
const employmentMessageElement          = document.getElementById("card-request-employment-details-message");
const employmentContainerElement        = document.getElementById("employment-container");
const employmentSpinner                 = document.getElementById("employment-details-spinner");
const requiredEmploymentInputFields     = document.querySelectorAll(".required-input");


// event listeners
cardRequestEmploymentContainer?.addEventListener("click",  handleEmploymentOptions);



// listen when page is loaded
document.addEventListener("DOMContentLoaded", () => {
    
    // Since the backend loads the employment data for the user into the form if the user has entered
    // This ensures that if the user has checked marked yes and has refreshed the page or navigated away
    // from the page and then back the employment fields will be displayed and not hidden
    if (getIsEmployedRadioValue() === "yes") {

        toggleEmploymentFieldsAndMessage()
        return
    }
    toggleRequiredInput({elementsNodeList: requiredEmploymentInputFields, required: false});
   
    
})


/**
 * Returns the selected employment status from the "is_employed" radio buttons.
 *
 * @returns {string|undefined} The selected value (`"yes"` or `"no"`), or
 * `undefined` if no option is selected.
 */
function getIsEmployedRadioValue() {
    return document
        .querySelector("input[name='is_employed']:checked")
        ?.value.toLowerCase();
}



/**
 * A helper function that handles a form submission.
 *
 * Validates the form, processes the
 * required fields together with any optional fields that contain a value, and
 * stores the processed form data using the specified session name.
 * 
 * Note:
 * 
 * This is not intended to be used on its own. It must be called from
 * a form submission and the relevant data passed.
 * 
 *
 * @param {Object} options - Configuration object.
 * @param {SubmitEvent} options.e - The form submission event.
 * @param {HTMLFormElement} options.form - The form being submitted.
 * @param {string[]} options.requiredFields - The names of fields that should always be processed.
 * @param {string[]} options.optionalFields - The names of optional fields to process only when they contain a value. Default empty array.
 * @param {string} options.sessionName - The storage key used to save the processed form data. Default name `session`
 *
 * @returns {void}
 *
 * @example
 * handleFormSubmission({
 *     e,
 *     form,
 *     requiredFields,
 *     optionalFields,
 *     sessionName: "card-request"
 * });
 */
function handleFormSubmission({ e,
                            form,
                            requiredFields,
                            optionalFields = [],
                            sessionName = "session",
                        }) {

    e.preventDefault();

    if (!form.reportValidity()) {
        return;
    }

    if (!Array.isArray(optionalFields)) {
        throw new Error("The optional fields must be an array or an empty array")
    }


    if (typeof sessionName !== "string") {
        throw new Error("The session name parameter must be a string")
    }

    const fieldsToProcess = [...requiredFields];

    optionalFields.forEach((fieldName) => {
        if (!isFormFieldEmpty({ form, fieldName })) {
            fieldsToProcess.push(fieldName);
        }
    });

    const parsedFormData = parseFormData(new FormData(form), fieldsToProcess);

    setLocalStorage(sessionName, parsedFormData);
}




/**
 * Toggles the visibility of the employment form and its accompanying message.
 *
 * When `show` is `true`, the employment form is displayed, the message is
 * hidden, and all required employment input fields are marked as required.
 * When `show` is `false`, the employment form is hidden, the message is
 * displayed, and the required attribute is removed from the employment
 * input fields.
 *
 * @param {boolean} [show=true] - Determines whether the employment form
 * should be displayed. Must be a boolean value.
 *
 * @throws {Error} If `show` is not a boolean.
 */
function toggleEmploymentFieldsAndMessage(show = true) {

    if ( typeof show !== "boolean") {
        throw new Error(`The parameter show must be a boolean. Expected a boolean but got ${typeof show} with value ${show}`)
    }

    toggleElementHelper(employmentContainerElement, show);
    toggleElementHelper(employmentMessageElement, !show);
    toggleRequiredInput({elementsNodeList: requiredEmploymentInputFields, required: show});
}





/**
 * Handles changes to the employment status radio buttons.
 *
 * Updates the UI based on whether the user is currently employed by
 * showing or hiding the employment details section, displaying the
 * appropriate message, toggling the required state of the employment
 * input fields, and persisting the user's employment status to session
 * storage.
 *
 * @param {Event} e - The change event triggered by selecting an
 * employment status radio button.
 *
 * @returns {void}
 */
function handleEmploymentOptions(e) {

     const radioInputElement = e.target.closest("input[type='radio']")

    if (!radioInputElement) {
        warnError("handleEmploymentContainer", {
            error: "Received null instead of radio input value"
        });
        return;
    }

    switch(radioInputElement.value.toLowerCase()) {

        case "yes":
           toggleEmploymentFieldsAndMessage();
           break;
        
        case "no":
           toggleEmploymentFieldsAndMessage(false)
           break;

    }

}



/**
 * Shows or hides an element after displaying a loading spinner for a
 * short delay.
 * @param {HTMLElement|null} element - The element to show or hide.
 * @param {boolean} [show=true] - Determines whether the element should
 * be displayed (`true`) or hidden (`false`).
 *
 * @returns {void}
 */
function toggleElementHelper(element, show = true) {
    if (!element) {
        return;
    }

    if (typeof show !== "boolean") {
        warnError("toggleEmploymentHelper");
        return;
    }

    const DELAY_MS = 1000;

    toggleSpinner(employmentSpinner)
    setTimeout(() => {
        toggleSpinner(employmentSpinner, false)
        element.style.display = show ? "block" : "none";
    }, DELAY_MS)

 
}













