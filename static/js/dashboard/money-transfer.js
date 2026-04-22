import { selectElement, toggleSpinner, toTitle, formatCurrency, enableAutoFocusNavigation } from "../utils.js";
import { warnError } from "../logger.js";
import { parseFormData } from "../formUtils.js";
import { AlertUtils } from "../alerts.js";
import { minimumCharactersToUse } from "../utils/password/textboxCharEnforcer.js";

// ---------------------------
// Transfer Form Elements
// ---------------------------

// ----- Containers / Sections -----
const transferSection                 = document.getElementById("dashboard-transfer");
const addRecipient                    = document.getElementById("add-recipient-section");
const futureScheduleDateContainer     = document.getElementById("future-schedule-date");
const verifiedUserPanel               = document.getElementById("transfer-to-user");
const pinPanel                        = document.getElementById("add-pin");
const pinImg                          = document.getElementById("pin-lock-img");


// ----- Forms / Inputs -----
const findRecipientForm               = document.getElementById("find-recipient-form");
const scheduleDateTimeInputField      = document.getElementById("future-schedule-date-input");
const amountInputField                = document.getElementById("amount");
const noteTextArea                    = document.getElementById("transfer-recipient-note");
const requestTextArea                 = document.getElementById("request-note");
const recipientAccountInputs          = document.querySelectorAll(".recipient-account input");
const requestRecipientAccountInputs   = document.querySelectorAll(".request-recipient-account input")
const bankTransferForm                = document.getElementById("bank-transfer-to-form");
const bankRequestForm                 = document.getElementById("bank-request-form");
const pinForm                         = document.getElementById("add-pin-form");
const firstPinInputField              = document.getElementById("pin_1");


// ----- Select Elements -----
const recipientSelects                = document.getElementById("recipient");
const transferSchedule                = document.getElementById("bank-transfer-schedule");
const bankTransfersSelectsOptions     = document.getElementById("bank-transfer-type");
const transferFromSelectOption        = document.getElementById("bank-transfer-selection");

// ----- Display / Feedback Elements -----
const transferTotal                   = document.getElementById("transfer-total");
const transferFeeSpan                 = document.getElementById("transfer-fee-span");
const verifiedUserName                = document.getElementById("verified-user-name");


// ----- Buttons / Spinners -----
const addRecipientSpinner             = document.getElementById("add-recipient__spinner");
const findRecipientBtns               = document.getElementById("find-recipient-buttons");
const pinSpinner                      = document.getElementById("add-pin__spinner");


// ----- transfer amount/labels -----
const transferringAccountNameSpan     = document.getElementById("transfer-account-label");
const transferringAccountAmountSpan   = document.getElementById("transfer-account-amount")

// ----- tabs -----
const tabLinks                       = document.querySelectorAll(".tab-link");


// todo add one time check if static elements abovie exists before calling them in functions

transferSection.addEventListener("click", handleDelegation);

// select recipient e.g "add recipient"
recipientSelects.addEventListener("change", handleRecipientSelection);

// select bank type internal vs external
bankTransfersSelectsOptions.addEventListener("change", handleExternalTransferFee);

// select schedule e.g send now vs send later
transferSchedule.addEventListener("change", handleTransferScheduleSelection)

// select the account that is being transferred from e.g wallet or bank
transferFromSelectOption.addEventListener("change", handleTransactionAccountBalanceDetails)


amountInputField.addEventListener("input", handleUpdateTotalTransferFee);


// handle form submits
findRecipientForm.addEventListener("submit", handleFindRecipientFormSubmission);
bankTransferForm.addEventListener("submit", handleBankTransferSubmission);
bankRequestForm.addEventListener("submit", handleBankRequestSubmission);
pinForm.addEventListener("submit", handlePinFormSubmission)



document.addEventListener("DOMContentLoaded", ()=> {
    // When the page loads for the transfer/request money we want the transfer tab form elements to be shown
    selectElement(bankTransferForm, "show")
})




const MAX_TRANSFER_AMOUNT = 1_000_000_000;

// Manages the state and button visibility of the "Find Recipient" panel.
// Prevents users from bypassing the workflow by manually hiding the panel in the inspector.
const findRecipientPanel = {
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




// Displays the number of characters used or remaining in the text area for the transfer and request text area form

const textAreaConfig = {
    minCharClass: ".num-of-characters-remaining",
    maxCharClass: ".num-of-characters-to-use",
    minCharMessage: "Minimum characters to use: ",
    maxCharMessage: "Number of characters remaining: ",
    minCharsLimit: 50,
    maxCharsLimit: 255,
    disablePaste: true,
};


[noteTextArea, requestTextArea].forEach((textAreaElement) => {
    minimumCharactersToUse(textAreaElement, textAreaConfig);
});






enableAutoFocusNavigation(requestRecipientAccountInputs);



// ---------------------------
// Transfer Handlers
// ---------------------------

function handleDelegation(e) {
    handleRecipientSelectionClose(e);
    handleUpdateTotalTransferFee(e);
      handleTabs(e);
  
   
}


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
function handleRecipientSelectionClose(e) {
    if (e.target.id !== "find-recipient-close-btn") return;

    toggleFindRecipient(false)

}



/**
 * Updates the displayed total transfer fee and enforces transfer limits
 * whenever the transfer amount input changes.
 *
 * This function does the following".
 *   1. Ensures the entered amount does not exceed `MAX_TRANSFER_AMOUNT`.
 *   2. Updates the UI element `transferTotal` with the formatted amount.
 *
 * @param {Event} e - The input event triggered on the transfer amount field.
 * @returns {void} - Does not return a value.
 *
 * @example
 * const amountInput = document.getElementById("amount");
 * amountInput.addEventListener("input", handleUpdateTotalTransferFee);
 */

function handleUpdateTotalTransferFee(e) {
    if (e.target.id !== "amount") return;
    
    const amount  = e.target.value;

    if (amount > MAX_TRANSFER_AMOUNT) {
        e.target.value = MAX_TRANSFER_AMOUNT;
    }

  
    if (amount) {
        transferTotal.textContent =  formatCurrency(amount);
        transferTotal.classList.add("flash");

        const transferringAccountDetails = getSelectedAccountDetails(transferFromSelectOption);        
        updateAccountTransferDetails(transferringAccountDetails.accountType, transferringAccountDetails.accountAmount, amount)
    
    }
 
}




/**
 * Handles the selection of a transfer schedule type and updates the UI accordingly.
 *
 * This function listens for a user interaction on elements with 
 * `data-transfer-type="true"`. If the user selects the "Schedule for Later" option,
 * it makes the future date input required and shows the corresponding date container.
 * Otherwise, it hides the container and removes the required constraint.
 *
 * @param {Event} e - The event triggered by the user selecting a transfer schedule option.
 * @returns {void} - Does not return a value.
 *
 * @example
 * const scheduleOptions = document.querySelectorAll(".transfer-schedule");
 * scheduleOptions.forEach(element => element.addEventListener("change", handleTransferScheduleSelection));
 */
function handleTransferScheduleSelection(e) {
 
   if (e.target.dataset.transferType !== "true") return;

   const selectValue = e.target.value;
   const SCHEDULE_FOR_LATER = "future_date"

   if (selectValue === SCHEDULE_FOR_LATER) {
        scheduleDateTimeInputField.required = true;
        futureScheduleDateContainer.classList.remove("hide");
        return;
   } 

   scheduleDateTimeInputField.required = false;
   futureScheduleDateContainer.classList.add("hide")
  
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
function handleRecipientSelection(e) {
    if (e.target.dataset.recipient !== "true") return;
    toggleFindRecipient()
}



/**
 * Updates the displayed transfer fee when the user selects an external transfer option.
 *
 * This function listens for a change event on the select element with ID "bank-transfer-type".
 * If the user selects the "external-transfer" option, it retrieves the fee from the 
 * selected option's dataset and updates the `transferFeeSpan` element
 * 
 * Note it only works if there is a *data-* attribrute in select value
 *
 * @param {Event} e - The change event triggered by the transfer type select element.
 * @returns {void} - Does not return a value.
 *
 * @example
 * const transferTypeSelect = document.getElementById("bank-transfer-type");
 * transferTypeSelect.addEventListener("change", handleExternalTransferFee);
 */
function handleExternalTransferFee(e) {

    if (e.target.id !== "bank-transfer-type") return;

    const selectValue = e.target.value;
    const EXPECTED_VALUE = "external-transfer";
    const DEFAULT_FEE = formatCurrency("0")
    
    if (selectValue === EXPECTED_VALUE) {
        const fee = e.target.dataset.externalTransferFee;
        transferFeeSpan.textContent = formatCurrency(fee);
        transferFeeSpan.classList.add("deactivate-text")
        return;
    }

    transferFeeSpan.classList.remove("deactivate-text")
    transferFeeSpan.textContent = DEFAULT_FEE;
}



/**
 * Updates the displayed account name and balance when the user selects an account
 * from the transfer account dropdown.
 *
 * This function listens for a change event on the select element with ID "bank-transfer-selection".
 * When triggered, it retrieves the selected account's details using `getSelectedAccountDetails`,
 * then updates the UI spans to show the account type (formatted as a title) and the account balance
 * (formatted as currency).
 *
 * @param {Event} e - The change event from the select element.
 * @returns {void} - Does not return anything.
 *
 * @example
 * const selectElement = document.getElementById("bank-transfer-selection");
 * selectElement.addEventListener("change", handleTransactionAccountBalanceDetails);
 */
function handleTransactionAccountBalanceDetails(e) {
    const EXPECTED_ID = "bank-transfer-selection";
    
    if (e.target.id !== EXPECTED_ID) return;

    const accountDetails  = getSelectedAccountDetails(e.target);
    if (!accountDetails) {
        warnError("handleTransactionAccountBalanceDetails", {
            errorMsg: "Not found",
            accountDetailsReceivedValue: accountDetails,
        })
        return;
    }
    transferringAccountNameSpan.textContent  = `${toTitle(accountDetails.accountType)}`;

    // console.log(accountDetails);
    // console.log(accountDetails.accountAmount)
    // console.log("I am here")
    updateAccountTransferDetails(accountDetails.accountType, accountDetails.accountAmount, amountInputField.value)

}



/**
 * Handles the submission of the "Find Recipient" form.
 
 * @param {Event} e - The submit event triggered by the form.
 *
 * @returns {void}
 */
function handleFindRecipientFormSubmission(e) {
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
    const accountDetails = getAccountDetailsFromData(parsedFormData)
    
    toggleSpinner(addRecipientSpinner, true, true)
    setTimeout(() => {
    toggleSpinner(addRecipientSpinner, false, true);

          // When the backend is built it will verify the account via fetch.
          const isAccountNumberCorrect = isAccountDetailsCorrect(accountDetails);

            //  console.log(isAccountNumberCorrect)
            // Simulated response for testing.
           
            if (isAccountNumberCorrect) {
                AlertUtils.showAlert({
                    title: "Account recipient found",
                    text: "The recipient account was found. You can proceed with the transfer.",
                    icon: "success",
                    confirmButtonText: "OK"
                })
                toggleFindRecipient(false, false);
                showVerifiedUser(parsedFormData.firstName, parsedFormData.surname);

                return
            } else {
                AlertUtils.showAlert({
                    title: "Account recipient not found",
                    text: "No matching account was found. For this simulation the sort code must start with the digits 400.",
                    icon: "error",
                    confirmButtonText: "OK"
                })
            }
    }, MILL_SECONDS)
    

}


/**
 * Handles the submission of the "bank transfer" form.
 
 * @param {Event} e - The submit event triggered by the form.
 *
 * @returns {void}
 */
async function handleBankTransferSubmission(e) {
    e.preventDefault();

    const accountDetails = getSelectedAccountDetails(transferFromSelectOption);
    const amount         = amountInputField.value;
    const confirmed = await AlertUtils.showConfirmationAlert({
        title: "Confirm Transfer",
        text: `You about to transfer ${formatCurrency(amount)} to your ${accountDetails.accountType} account. Do you want to proceed?`,
        icon: "info",
        cancelMessage: "No action taken",
        messageToDisplayOnSuccess: "Please enter your pin to begin transfer",
        confirmButtonText: "Transfer funds!",
        denyButtonText: "Don't transfer!"
    })


    // when the backend is buit the form data will be submitted to the backend via fetch but for now we simply reset the form.
    if (confirmed) {
        // bankTransferForm.reset();
        // verifiedUserName.classList.remove("show");
        togglePinPanel()
    }

}


/**
 * Handles the submission of the "Request fund" form.
 
 * @param {Event} e - The submit event triggered by the form.
 *
 * @returns {void}
 */
async function handleBankRequestSubmission(e) {
    e.preventDefault();

    const requiredFields = [
           "name",
           "sortcode_1",
           "sortcode_2",
           "sortcode_3",
           "sortcode_4",
           "sortcode_5",
           "sortcode_6",
           "account_digit_1",
           "account_digit_2",
           "account_digit_3",
           "account_digit_4",
           "account_digit_5",
           "account_digit_6",
           "account_digit_7",
           "account_digit_8",
        
        ];

    const parsedFormData = getParseFormData(bankRequestForm, requiredFields);
    const accountDetails = getAccountDetailsFromData(parsedFormData);
  
    if (typeof accountDetails !== "object") {
        warnError("handleBankRequestSubmission", {
            data: accountDetails,
            dataType: typeof accountDetails,
            expected: "Expected an object containing account details"
            
        })
        return;
    }

    
    // Before the confirmation block, the account details will be sent via fetch to verify if it is exists.
    // if doesn't exists then an appropriate alert message informing the user that the account doesn't exists
    // will be displayed to the user. But for now since they is no backend we simple proceed with confirm alert block

    const confirm = await AlertUtils.showConfirmationAlert({
        title: "Confirm account request information",
        text: `You are about to request money from account ${accountDetails.sortCode} ••••${accountDetails.accountNumber.slice(-4)}. Do you want to proceed?`,
        icon: "info",
        confirmButtonText: "Request funds",
        denyButtonText: "Cancel fund Request!", 
        messageToDisplayOnSuccess: "Your request has been sent..."
    })

    if (confirm) {
        bankRequestForm.reset()
        return;
    }

}






/**
 * Handles tab navigation for the bank transfer interface.
 *
 * This function listens for click events on tab elements and determines
 * whether the clicked element is a valid tab. If so, it updates the UI
 * by highlighting the selected tab and displaying the corresponding form.
 *
 * Supported tabs:
 * - "transfer-money" → Displays the bank transfer form.
 * - "request-money"  → Displays the bank request form.
 *
 *
 * @param {MouseEvent} e - The click event triggered on the tab container.
 */
function handleTabs(e) {

    const link = e.target.closest("a");
    if (link === null) return;
    if (!link.classList.contains("tab")) return;

    const action       = link.dataset.action;
    const TRANSFER_TAB = "transfer-money";
    const REQUEST_TAB  = "request-money";
    const cssSelector  = "show";
   
    deselectAllTabs();
    highlightTab(link)
  
    hideTransferAndRequestForms();

    switch(action) {
        case TRANSFER_TAB:
            bankTransferForm.classList.add(cssSelector);
            bankRequestForm.classList.remove(cssSelector)
            break;
        case REQUEST_TAB:
            bankTransferForm.classList.remove(cssSelector);
            bankRequestForm.classList.add(cssSelector)
            break;
    }
       

}


async function handlePinFormSubmission(e) {
    e.preventDefault();
    const requiredFields = [
        "pin_1",
        "pin_2",
        "pin_3",
        "pin_4",
        "pin_5",
        "pin_6",
    ]
    const parsedData   = getParseFormData(pinForm, requiredFields);
    const pinString    = getPinData(parsedData);
    const MILL_SECONDS = 2000;
  
    toggleSpinner(pinSpinner, true, false);

    setTimeout(() => {
          const response = validatePinAPI(pinString);
          if (response.success) {
               
                unlockPinImg();
                toggleSpinner(pinSpinner, false);

              AlertUtils.showAlert({
                title: "Pin verified",
                text: "Your transfer has been completed successfully.",
                icon: "success",
                confirmButtonText: "OK"
            })

                pinPanel.classList.remove("show");

                // since no backend is built yet we simply just clear the form
                // however, when the backend is built the bank form transfer details we be submitted
                // to the back end via fetch but for now simply clear the form
                bankTransferForm.reset();
             

          } else {
           AlertUtils.showAlert({
                    title: "Incorrect PIN",
                    text: "The backend hasn't been built yet. Until it built, The correct PIN for testing/simulating is 123456.",
                    icon: "error",
                    confirmButtonText: "OK"
                })
                 toggleSpinner(pinSpinner, false);

          }
      
    }, MILL_SECONDS)
   

  

    console.log(pinString)  
   
}


function unlockPinImg() {
   pinImg.src = "../static/images/icons/unlocked.svg";
}





// ---------------------------
// helper functions utilities
// ---------------------------


/**
 * Updates the account name and available balance in the UI based on a transfer 
 * for the current account e.g bank or wallet.
 *
 * This function calculates the updated account balance after a transfer 
 * and updates the relevant UI elements to reflect the new state. 
 * It also validates the input parameters and logs a warning if any are invalid.
 *
 * @param {string} accountType - The type of the account (e.g., "wallet", "bank").
 * @param {number} currentAccountAmount - The current available balance of the account.
 * @param {number} newAmount - The amount the user intends to transfer.
 * @returns {void} - Updates the UI elements directly and does not return a value.
 *
 * @example
 * updateAccountTransferDetails("wallet", 1000, 200);
 */
function updateAccountTransferDetails(accountType, currentAccountAmount, newAmount) {
   
    if (typeof accountType !== "string" && typeof amount !== "number" && typeof currentAccountAmount !== "number") {
        warnError("updateTransferDetails", {
            error: "One or more of the parameters is invalid",
            accountType: typeof accountType,
            accountTypeValue: accountType,
            amountType: typeof amount,
            amountValue: amount,
            currentAccountAmountType: typeof currentAccountAmount,
            currentAccountAmountValue: currentAccountAmount,
            expected: "Account type must be a string, the new amount and the correct account must be a number or a float"
        });
        return;
    }

    transferringAccountNameSpan.textContent = `${toTitle(accountType)} :`;

    const updatedAmount = currentAccountAmount - newAmount;
    
    if (updatedAmount < 0 ) {
        transferringAccountAmountSpan.classList.remove("can-transfer")
        transferringAccountAmountSpan.classList.add("cannot-transfer")
    } else {
         transferringAccountAmountSpan.classList.add("can-transfer");
         transferringAccountAmountSpan.classList.remove("cannot-transfer")
    }

    if (newAmount) {
        transferringAccountAmountSpan.textContent = formatCurrency(updatedAmount)

    }
 
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
function toggleFindRecipient(show = true, resetSelectOption = true, cSSelectorName="show") {
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
 * Extracts and formats sort code and account number from form data.
 *
 * This function scans an object containing recipient form data and returns the 
 * sort code and account number within an object
 *
 * @param {Object} data - The form data object, typically returned by `getParseFormData`.
 *
 * @returns {Object} account - An object containing:
 *   - sortCode {string} - Full 6-digit sort code.
 *   - accountNumber {string} - Full 8-digit account number.
 *
 * @throws Will warn if `data` is not an object.
 *
 * Example:
 *   Input: { sortcode_1: "4", sortcode_2: "0", ..., account_digit_1: "1", ... }
 *   Output: { sortCode: "400000", accountNumber: "12345678" }
 */
function getAccountDetailsFromData(data){
    
    if (typeof data !== "object") {
        warnError("getAccountNumberFromData", {
            type: typeof data,
            expected: "Expected an object",
            received: `Value received ${data}`
        });
        return;
    }

    const sortCode      = [];
    const accountNumber = []
    const account       = {}

    for (const [key, value] of Object.entries(data)) {
    
        if (key.startsWith("sort")) {
            sortCode.push(value)
        }
        
        if (key.startsWith("account")) {
            accountNumber.push(value)
        }
    }

    account.sortCode = sortCode.join("");
    account.accountNumber  = accountNumber.join("");
    return account

}




/**
 * Verifies whether the given account details are valid.
 *
 * @param {Object} accountDetails - An object containing the account information.
 *   Expected properties:
 *     - sortCode {string} - The 6-digit sort code.
 *     - accountNumber {string} - The 8-digit account number.
 *
 * @returns {boolean} - Returns true if the account details pass validation, false otherwise.
 *
 * Example:
 *   const details = { sortCode: "400123", accountNumber: "12345678" };
 *   isAccountDetailsCorrect(details); // returns true
 */
function isAccountDetailsCorrect(accountDetails) {
    if (typeof accountDetails !== "object") {
        warnError("verifyAccountDetails", {
            type: typeof accountDetails,
            expected: "Expected an object",
            received: `Value received ${accountDetails}`
        });
        return;
    }

  

    // for now we simulate the authentication respoonse. Later the actually authentication response data will come from the backend
    const isSortCodeValid = accountDetails.sortCode.startsWith("400");
   
    return isSortCodeValid ? true : false;


};



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
 *   showVerifiedUser("Doctor", "Who");
 *   // Verified user panel displays: "Doctor Who"
 */
function showVerifiedUser(firstName, surname) {
    if (!(firstName && surname)) return;

    if (typeof firstName !== "string" && typeof surname !== "string") {
        warnError("showVerifiedUser", {
            firstName: firstName,
            surname: surname,
            firstNameType: typeof firstName,
            surnameType: typeof surname,
            expected: "Expected both values to be string"
        })
        return;
    }
    // console.log("I am here")
    selectElement(verifiedUserPanel, "show");
    verifiedUserName.textContent = `${toTitle(firstName)} ${toTitle(surname)}`
    
}



/**
 * Removes the active state from all tab links.
 *
 * This is typically called before activating a new tab to ensure that
 * only one tab appears highlighted at a time.
 *
 * @param {string} [cssSelector="active"] - The CSS class representing
 * the active/selected tab state.
 */
function deselectAllTabs(cssSelector="active") {
    tabLinks.forEach((link) => {
        link.classList.remove(cssSelector);
    })

}


/**
 * Applies the active state to a specific tab element.
 *
 * @param {HTMLElement} tab - The tab element that should be highlighted.
 * @param {string} [cssSelector="active"] - The CSS class used to indicate
 * the active/selected state.
 */
function highlightTab(tab, cssSelector="active") {
    tab.classList.add(cssSelector);

}


/**
 * Hides both the transfer and request forms.
 * This is typically used before activating the form associated with the selected tab.
 */
function hideTransferAndRequestForms() {
    bankTransferForm.classList.remove("show");
    bankRequestForm.classList.remove("show")
}




/**
 * Takes the form pin data object and extracts the pin into 
 * a pin string.
 * 
 * @param {*} data : The pin data
 * @returns 
 */
function getPinData(data) {
    if (typeof data !== "object") return;

    const pin = [];

    for (const [key, value] of Object.entries(data)) {
        pin.push(value)
    }

    if (pin.length === 0) return;


    return pin.join("");

}


/**
 * validatePinAPI
 *
 * Simulates a backend API request for validating a user's PIN.
 *
 * This is a temporary mock implementation used during frontend development
 * while the real backend endpoint is not yet available.
 *
 * The function intentionally returns a Promise and introduces an artificial
 * delay so the UI behaves exactly as it would with a real network request.
 *
 * Once the backend is implemented, this function should be replaced with
 * an actual API call (e.g. using fetch or axios).
 *
 * @param {string} pin - The PIN entered by the user.
 * @returns {Promise<{ success: boolean }>} Resolves with an object indicating
 * whether the PIN is valid.
 */
function validatePinAPI(pin) {

    const FAKE_EXPECTED_PIN = "123456"

    // Temporary validation logic
    // This will be replaced with a real backend response once the API exists
     if (pin === FAKE_EXPECTED_PIN) {
        return ({ success: true })
     }
     return ({ success: false })
           

}


// ---------------------------
// Get / Extract Utilities
// ---------------------------

/**
 * Retrieves account details from the currently selected option of a select element.
 *
 * This function reads the dataset attributes from the selected <option>
 * and returns the account information as an object.
 *
 * Expected data attributes on the option element:
 * - data-account-amount
 * - data-account-type
 *
 * @param {HTMLSelectElement} selectElement - The select element containing account options.
 * @returns {{accountAmount: string, accountType: string} | null} 
 * Returns an object with account details, or null if no option is selected.
 */
function getSelectedAccountDetails(selectElement) {
    const option = selectElement.selectedOptions[0];
    if (!option) return null;

    const { accountAmount, accountType } = option.dataset;
    return { accountAmount, accountType };
}




/**
 * togglePinPanel
 *
 * Shows or hides the PIN input panel and optionally applies a CSS class.
 * 
 * This function also focuses the first PIN input field when showing the panel.
 * If the panel is inside a modal or initially hidden, it uses requestAnimationFrame
 * to ensure the element is visible before focusing. HTML 'autofocus' does NOT
 * work in hidden elements.
 *
 * @param {boolean} [show=true] - Whether to show (true) or hide (false) the PIN panel.
 * @param {string} [cssSelector="show"] - The CSS class to add/remove for visibility.
 *
 * @example
 * // Show the PIN panel and focus the first input
 * togglePinPanel(true);
 *
 * // Hide the PIN panel
 * togglePinPanel(false);
 */
function togglePinPanel(show=true, cssSelector="show") {

    if (typeof show !== "boolean" && typeof cssSelector !== "string") {
        warnError("togglePinPanel", {
            showType: typeof show,
            cssSelectorType: typeof cssSelector,
            cssSelector: cssSelector,
            show: show,
            expected: "Expected 'show' to be a boolean and cssSelector to be string"
        });
        return;
    }
    if (show) {
       
        selectElement(pinPanel, cssSelector);
        firstPinInputField.focus();
      
        return;
    } 

    pinPanel.classList.remove(cssSelector)
}