import { getCsrfToken } from "../security/csrf.js";
import fetchData from "../fetch.js";
import CheckFrontEndPasswordStrength from "../utils/password/checkPasswordStrength.js";
import { applyDashToInput, checkIfHTMLElement, dimBackground, showSpinnerFor, toggleSpinner } from "../utils.js";



const walletHelperMoodle          = document.getElementById("wallet-registration-code-explained");
const registerFormSectionElement  = document.getElementById("register");
const walletCodeInputFieldElement = document.getElementById("wallet-code");
const dimBackgroundElement        = document.getElementById("dim");
const djangoUsernameError         = document.getElementById("id_username_error");
const djangoEmailError            = document.getElementById("id_email_error");
const registerForm                = document.getElementById("wallet-register-form");
const registerFormSpinner         = document.getElementById("registration-spinner")


// TODO one time function checker to be added later. This is a one time check that checks if the elements are available before the addEventListener is called
registerFormSectionElement.addEventListener("click", handleDelegation)
walletCodeInputFieldElement.addEventListener("click",  handleCodeInputField);
walletCodeInputFieldElement.addEventListener("input",  handleCodeInputField);
registerForm.addEventListener("submit", handleRegisterForm)


// input fields
const emailInputField = document.getElementById("id_email");
const usernameInputField = document.getElementById("id_username");

// field check
const usernnameExists = document.getElementById("username-exists");
const emailExists     = document.getElementById("email-exists")



// write a one time check to verify input field is correct
usernameInputField.addEventListener("blur",  handleUserInputFieldClick);
emailInputField.addEventListener("blur", handleEmailInputFieldClick)


async function handleEmailInputFieldClick(e) {

    if (isFieldEmpty(e)) return;

    const url  = "/email/exists/";
    const resp = await fetchData({
        url: url,
        csrfToken: getCsrfToken(),
        body: {
            email: e.target.value,
        },
        method: "POST",

    });
    
    clearElementField(djangoEmailError)    
    toggleFieldMsg(emailExists, resp.data);

}


async function handleUserInputFieldClick(e) {
    if (isFieldEmpty(e)) return;

    const url  = "/username/exists/";
    const resp = await fetchData({
        url: url,
        csrfToken: getCsrfToken(),
        body: {
            username: e.target.value,
        },
        method: "POST",

    })   

    clearElementField(djangoUsernameError)
    toggleFieldMsg(usernnameExists, resp.data);
   
}



function toggleFieldMsg(element, data) {
   
    element.classList.remove("active-text", "deactivate-text")
    if (!data.IS_AVAILABLE) {
         element.classList.add("deactivate-text");
    } else {
        element.classList.add("active-text");
    }

    element.textContent = data.MSG;
    element.style.display = "block";
  
}


function isFieldEmpty(e) {
    return e.target.value === "" ? true : false;
}





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


function clearElementField(element) {
    if (!checkIfHTMLElement(element, "unknown", true)) return;
 
    element.textContent = "";
}


function handleRegisterForm(e) {
    e.preventDefault();

    const SUBMIT_DELAY = 2000;

    if (!registerForm) return;

    if (registerForm.checkValidity()) {
        console.log("submitted");

        toggleSpinner(registerFormSpinner, true);

        setTimeout(() => {
            registerForm.submit();
        }, SUBMIT_DELAY);
    } else {
        registerForm.reportValidity();
    }
}