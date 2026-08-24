/**
 * Add funds UI
 *
 * Provides the client-side functionality for the bank account funding interface.
 *
 * This module is responsible for managing the presentation and user
 * interactions associated with adding funds, including:
 *
 * - Opening and closing the Add Funds panel.
 * - Handling the funding amount input.
 * - Increasing and decreasing the funding amount.
 * - Validating and formatting the amount for UI purposes.
 * - Confirming the user's intention to add funds.
 * - Handling bank card selection and related card interactions.
 *
 * The module is responsible only for client-side interaction and presentation.
 * It does not determine whether a funding transaction is valid from a business
 * or financial perspective.
 *
 * The backend FundingService remains responsible for the actual funding
 * workflow, including:
 *
 * - Validating the funding request.
 * - Determining whether the funding request requires review.
 * - Crediting the user's account.
 * - Creating the corresponding ledger entry.
 * - Updating the account balance.
 * - Persisting the transaction.
 *
 * Once the funding UI is connected to the backend, this module will submit
 * the user's funding request to the appropriate backend endpoint rather than
 * performing the funding operation itself.
 *
 * This separation keeps the UI responsible for user interaction while the
 * backend remains the source of truth for financial operations and business
 * rules.
 */


import { AlertUtils } from "../../../alerts.js";
import { toggleElement, dimBackground } from "../../../utils.js";

import { AddFundBtn } from "./addFundBtn.js";
import { BankFundAmountInputField } from "./bankFundAmountInputField.js";
import { BankCard } from "../cards/bankCard/bankCard.js";
import { PinModal } from "../pin/pinModal.js";



const addFundsToBankPanel  = document.getElementById("bank-account-add-funds");
const dimBackgroundElement = document.getElementById("dim");




/**
 * Manages the Add Funds modal and provides functionality for
 * displaying and hiding the modal window.
 *
 * The modal's visibility is controlled through the `show()` and
 * `hide()` methods, while the underlying toggle implementation
 * remains encapsulated within the module.
 */
export const AddFundModal = (() => {

    /**
     * Toggles the Add Funds modal between its visible and hidden states.
     *
     * @param {boolean} [open=true] - Determines whether the modal should
     * be displayed (`true`) or hidden (`false`).
     */
    function toggleWindow(open=true) {
        toggleElement({ element: addFundsToBankPanel, show: open });
    }

    /**
     * Displays the modal that allows the user to add funds
     */
    function show() {
        toggleWindow();
        dimBackground(dimBackgroundElement, true)
    }

    /**
     * Hides the add fund window from view
     */
    function hide() {
        toggleWindow(false);
        dimBackground(dimBackgroundElement, false)
    }

    return {
        show,
        hide,
    }

})()




/**
 * Handles the bank fund amount input.
 *
 * Responsible for:
 * - Increasing the amount by £0.01.
 * - Decreasing the amount by £0.01.
 * - Enforcing minimum and maximum amounts.
 * - Keeping the value formatted to two decimal places.
 */
export const BankFundInput = (() => {


    /**
     * Handles clicks on the plus and minus buttons
     * for the bank fund amount input.
     *
     * @param {MouseEvent} e Click event.
     * @param {HTMLInputElement} amountInputField
     * The bank fund amount input.
     */
    function handleInput(e) {
        switch (e.target.id) {
            case "plus":
                BankFundAmountInputField.adjustAmountByPennies();
                break;

            case "minus":
                BankFundAmountInputField.adjustAmountByPennies(-1);
                break;

            default:
                break;
        }
    }


    /**
     * Handles the Enter key press on the amount input field.
     *
     * When the Enter key is pressed, the function ensures that the input value
     * is within the defined minimum and maximum limits. It also formats it to two
     * decimal places.
     *
     * @param {KeyboardEvent} e - The keyboard event triggered by a key press.
     */
    function handleEnter(e) {
        if (e.key !== "Enter") return;

        BankFundAmountInputField.clampAmountToRange()
    }



    /**
     * Handles toggling the "Add Funds" panel open or closed based on which element is clicked.
     *
     * Depending on the clicked button, this function either opens or closes the add funds panel.
     *
     * @param {Event} e - The click event triggered by the user.
     */
    function handleToggleAddFundsPanel(e) {
        const closeBtnId = "add-funds-close-panel";
        const addFundsBtn = "add-funds-bank";

        switch (e.target.id) {

            case closeBtnId:
                AddFundModal.hide();
                break;
            case addFundsBtn:
                AddFundModal.show();
                break;
        }
    }



    async function handleEvents(e) {
        handleToggleAddFundsPanel(e);
        handleEnter(e);
        handleInput(e);
        const isClicked = await AddFundBtn.handleFundAccountBtn(e)

        if (isClicked) {
           PinModal.show();


        }

        BankCard.handleEvents(e)

    }



    return {
        handleEvents,

    };


})();






