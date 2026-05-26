import { enableAutoFocusNavigation, toggleSpinner, parseCharsFromObject } from "../utils.js";
import { parseFormData } from "../formUtils.js";
import { warnError } from "../logger.js";

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

        const EXPECTED_PIN_LENGTH = 12;
        const formData   = new FormData(confirmVerificationForm);
        const parsedData = parseFormData(formData, [
                'first_code',
                'second_code',
                'third_code',
                'fourth_code',
                'fifth_code',
                'six_code',
                'seventh_code',
                'eighth_code',
                'ninth_code',
                'tenth_code',
                'eleventh_code',
                'twelfth_code'
        ])
        
             
        const code = parseCharsFromObject(parsedData);
        if (!code) {
            warnError("handleForm", {
                error: "Code not found",
                received: code,
            })
            return
        }
        hiddenFullCodeElement.value = code.values;
        console.log(code.values)

        toggleSpinner(spinner, true)

        setTimeout(() => {
            confirmVerificationForm.submit()
        }, DELAY_MS)
      

    } else {
        confirmVerificationForm.reportValidity()
    }
}
