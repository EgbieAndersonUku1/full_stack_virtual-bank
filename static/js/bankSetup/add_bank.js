import { minimumCharactersToUse } from "../utils/password/textboxCharEnforcer.js"
import { AlertUtils } from "../alerts.js"
import { toggleSpinner, sanitizeText, applyDashToInput } from "../utils.js"
import { warnError } from "../logger.js";


const bankDescriptionTextArea = document.getElementById("id_description");
const bankName      = document.getElementById("id_name")
const addBankForm   = document.getElementById("add-bank-form");
const spinner       = document.getElementById("bank-add-form-spinner");
const phoneNumber   = document.getElementById("id_phone_number");
const branchName    = document.getElementById("id_branch_name");
const addressOne    = document.getElementById("id_address_line_1");
const addressTwo    = document.getElementById("id_address_line_2")
const postCode      = document.getElementById("id_post_code")



// add one time checker later
addBankForm.addEventListener("submit", handleBankFormSubmission);
phoneNumber.addEventListener("input", handlePhoneNumber);
bankName.addEventListener("input", handleNameSanitization);
branchName.addEventListener("input", handleNameSanitization);
addressOne.addEventListener("input", handleAddressSanitization);
addressTwo.addEventListener("input",handleAddressSanitization);
postCode.addEventListener("input", handlePostCode)



// Displays the number of characters to display in a given textbox area
minimumCharactersToUse(bankDescriptionTextArea, {
    minCharClass: ".num-of-characters-remaining",
    maxCharClass: ".num-of-characters-to-use",
    minCharMessage: "Minimum characters to use: ",
    maxCharMessage: "Number of characters remaining: ",
    minCharsLimit: 50,
    maxCharsLimit: 255,
    disablePaste: true,
})



function handlePhoneNumber(e) {
    const includeChars = ["+",  "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ];
    handleInputSanitization(e, includeChars);
}


function handleNameSanitization(e) {
    const includeChars = [" ", "&", "-", "'", "."];
    handleInputSanitization(e, includeChars);
}


function handleAddressSanitization(e) {
    const includeChars = [" ",  "&",  "-",  "'",  "/",  ".",  ",", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ];
    handleInputSanitization(e, includeChars);
}


function handlePostCode(e) {
    const includeChars = [" ",  "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];
     handleInputSanitization(e, includeChars);
}


function handleInputSanitization(e, includeChars, allowNumber=false) {

    if (!Array.isArray(includeChars)) {
        warnError( handleInputSanitization, {
            expected: "Expected the includeChars to be a list",
            received: `${typeof includeChars}`
        })
        return;
    }

    e.target.value = sanitizeText(e.target.value, false, true, includeChars)

}


async function handleBankFormSubmission(e) {
  
     e.preventDefault();

    if (addBankForm.checkValidity()) {
       
        const DELAY_MS = 1000;

        toggleSpinner(spinner, true);

        setTimeout(async () => {
            const confirmed = await AlertUtils.showConfirmationAlert({
                title: "Add bank",
                text: "Are you sure you want to add this bank?",
                icon: "info",

                cancelMessage: "No action taken",
               
                denyButtonText: "Don't add",
                confirmButtonText: "Add bank",
            });

            if (!confirmed) {
                toggleSpinner(spinner, false);
                return;
            }

            addBankForm.submit();
        }, DELAY_MS);

    } else {
        addBankForm.reportValidity();
    }
}