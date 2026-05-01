import { enableAutoFocusNavigation, toggleSpinner } from "../utils.js";

const codeInputFields         = document.querySelectorAll(".code-wrapper input");
const confirmVerificationForm = document.getElementById("verify-registration-confirmation-code-form");
const hiddenFullCodeElement   = document.getElementById("code-verification");
const spinner                 = document.getElementById("confirmation-code-spinner")

// right one time check to const before load

codeInputFields[0].focus()
enableAutoFocusNavigation(codeInputFields, true)

confirmVerificationForm.addEventListener("submit", handleForm);


function handleForm(e) {

    e.preventDefault();
    const DELAY_MS = 1500;

    if (confirmVerificationForm.checkValidity()) {
        const code = parseCodeFromInputFields();
        hiddenFullCodeElement.value = code;

        toggleSpinner(spinner, true)

        setTimeout(() => {
            confirmVerificationForm.submit()
        }, DELAY_MS)
      

    } else {
        confirmVerificationForm.reportValidity()
    }
}


function parseCodeFromInputFields() {
   const codeInputs =  document.querySelectorAll("input[class='code-number']");

   const code = [];

   codeInputFields.forEach((inputField) => {
        code.push((inputField.value))

   });

   return code.join("");
   

}