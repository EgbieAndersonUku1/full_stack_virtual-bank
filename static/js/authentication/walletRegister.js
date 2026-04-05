import CheckFrontEndPasswordStrength from "../utils/password/checkPasswordStrength.js";
import { applyDashToInput, dimBackground } from "../utils.js";

const walletHelperMoodle          = document.getElementById("wallet-registration-code-explained");
const registerFormSectionElement  = document.getElementById("register");
const walletCodeInputFieldElement = document.getElementById("wallet-code");
const dimBackgroundElement        = document.getElementById("dim");

// TODO one time function checker to be added later. This is a one time check that checks if the elements are available before the addEventListener is called
registerFormSectionElement.addEventListener("click", handleDelegation)
walletCodeInputFieldElement.addEventListener("click",  handleCodeInputField);
walletCodeInputFieldElement.addEventListener("input",  handleCodeInputField);




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






function handleDelegation(e) {
    const WALLET_ICON_HELPER = "wallet-helper-icon";

    const helperIcon = e.target.closest(`#${WALLET_ICON_HELPER}`);

   
    if (!helperIcon) {
        walletHelperMoodle.classList.remove("show");
        dimBackground(dimBackgroundElement, false);
        return;
    }

    dimBackground(dimBackgroundElement, true);
    walletHelperMoodle.classList.add("show");
}


function handleCodeInputField(e) {
    const lengthPerDash = 5;
    e.preventDefault();
    applyDashToInput(e, lengthPerDash, false, true);
}