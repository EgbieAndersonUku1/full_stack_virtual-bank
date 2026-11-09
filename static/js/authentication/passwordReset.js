
import CheckFrontEndPasswordStrength from "../utils/password/checkPasswordStrength.js";

const passwordForm          = document.getElementById("wallet-reset-password-form");
const passwordFormSpinner   = document.getElementById("reset-password-spinner");

passwordForm.addEventListener("submit", handlepasswordForm)


new CheckFrontEndPasswordStrength()
.setPasswordFieldElementId("password")
.setConfirmPasswordFieldElementId("confirm-password")
.setHasCapitalElementId("rule-uppercase")
.setHasLowercaseElementId("rule-lowercase")
.setHasNumberElementId("rule-number")
.setHasMinLengthElementId("rule-length")
.setHasSpecialElementId("rule-symbol")
.setDoPasswordsMatchElementId("rule-match")
.setValidCSSRuleId("valid")
.setInvalidCSSRuleId("invalid")
.setActivePasswordFieldId("active-password-field")
.setPasswordStrengthBoardId("password-strength")
.setPasswordStrengthDisplayBoardCssSelector("show")
.startEventListener()


function handlepasswordForm(e) {
    e.preventDefault();

    const SUBMIT_DELAY = 900;

    if (!passwordForm) return;

    if (passwordForm.checkValidity()) {
        console.log("submitted");

        toggleSpinner(passwordFormSpinner, true);

        setTimeout(() => {
            passwordForm.submit();
        }, SUBMIT_DELAY);
        
    } else {
        passwordForm.reportValidity();
    }
}
