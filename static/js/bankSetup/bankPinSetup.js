import runObserver from "../animation.js";

runObserver();

const bankPinForm           = document.getElementById("bank-pin-form")
const inputPinFieldsElements = document.querySelectorAll(".pin-number")


// TODO
// Add one time check for bank form element exist before running


bankPinForm.addEventListener("click", handleDelegation)



/**
 * Handles click events on the PIN pad buttons.
 *
 * Depending on the button pressed, this function either:
 *   - adds a number to the PIN input field, or
 *   - removes the last number when the backspace button is pressed.
 * *
 * @param {Event} e - The click event from the PIN pad button.
 */
function handleDelegation(e) {
    const pinPadBtn = e.target;
    const number    = pinPadBtn.dataset.number;

    if (number && number !== "backspace") {
         addDigitToNextEmptyPinField(number)
         handlePinPadClick(pinPadBtn);
    } else if (number === "backspace"){
         removeLastDigitFromPin();
         handlePinPadClick(pinPadBtn);
    }
   
}



/**
 * Inserts a single digit into the next empty PIN input field
 * (left to right), updates its background state, and focuses it.
 * Does not overwrite existing values.
 *
 * @param {string|number} digit - The digit to add to the PIN.
 */
function addDigitToNextEmptyPinField(number) {

    for (let i = 0; i < inputPinFieldsElements.length; i++) {
        const inputPinFieldElement = inputPinFieldsElements[i]

        if (!inputPinFieldElement.value) {
            inputPinFieldElement.value = number;
            inputPinFieldElement.focus();
            togglePinInputFieldBackgroundState(inputPinFieldElement);
            cloakPreviousDigit(i);
            return;
        }
      
    }
   
}



/**
 * Cloaks the previous digit with a disc.
 * The first digit is visible initially, but once the user
 * enters the next digit, the previous one is cloaked.
 *
 * Note: the last digit has no following digit, so it is
 * cloaked immediately.
 */
function cloakPreviousDigit(currentPinIndex) {
  const previousIndex = currentPinIndex - 1;
  const lastIndex     = inputPinFieldsElements.length -1;

  
  if (previousIndex >= 0) {
    inputPinFieldsElements[previousIndex].classList.add("cloak")
  } 
  
  if (lastIndex === currentPinIndex) {
    inputPinFieldsElements[currentPinIndex].classList.add("cloak")
  }



}


/**
 * Removes the last entered digit from the PIN input fields (right to left).
 * Clears the field, updates its background state, and moves focus to the
 * previous input field.
 *
 * If no digits are present, the function exits early.
 */
function removeLastDigitFromPin() {

    for (let i = inputPinFieldsElements.length - 1; i >= 0; i--) {

        const inputPinFieldElement = inputPinFieldsElements[i];
       
        if (inputPinFieldElement.value ) {
            inputPinFieldElement.value = "";
            inputPinFieldElement.classList.remove("cloak")

            addFocusToPreviousPinInputField(i);
            togglePinInputFieldBackgroundState(inputPinFieldElement, false)
            return;
        }
      
    }
}


/**
 * Moves focus to the previous PIN input field.
 * @param {number} currentPinNumberField - The index of the currently active PIN input field.
 */
function addFocusToPreviousPinInputField(currentPinNumberField) {
    const previousPinNumberField = currentPinNumberField - 1;
    if (previousPinNumberField >= 0) {
        inputPinFieldsElements[previousPinNumberField].focus();
    }
    return;
}




/**
 * Adds a temporary visual click effect to a PIN pad button.
 *
 * The function adds a CSS class to the button element to create a visual
 * feedback effect that simulates a click
 *
 * @param {HTMLElement} pinPadBtn - The button element that was clicked.
 */
function handlePinPadClick(pinPadBtn) {
    const MILLISECONDS = 200;
    const cssSelector = "clicked";

    pinPadBtn.classList.add(cssSelector);
   
    setTimeout(() => {
        pinPadBtn.classList.remove(cssSelector)
    }, MILLISECONDS)


}


/**
 * Toggles the background state of a PIN input field.
 *
 * Adds or removes a CSS class to visually indicate whether the field is
 * filled/active. By default, the function activates the field unless
 * explicitly set to false.
 *
 * @param {HTMLElement} pinInputField - The PIN input field element.
 * @param {boolean} [isActive=true] - Whether to activate (true) or deactivate (false) the field.
 */
function togglePinInputFieldBackgroundState(pinInputField, isActive = true) {
    const cssSelector = "filled";

    if (isActive){
        pinInputField.classList.add(cssSelector);
        return
    }
     pinInputField.classList.remove(cssSelector);
}