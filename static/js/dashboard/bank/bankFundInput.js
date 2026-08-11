import { toggleElement } from "../../utils.js";
import { AlertUtils } from "../../alerts.js";

const addFundsToBankPanel = document.getElementById("bank-account-add-funds");
const amountInputField = document.getElementById("account-card__amount");



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
     * Adjusts a currency input value by a specified number of pennies.
     *
     * @param {HTMLInputElement} amountInputField
     * The input element containing the currency amount.
     *
     * @param {number} [deltaPennies=1]
     * Number of pennies to adjust by.
     * Positive values increase the amount.
     * Negative values decrease the amount.
     *
     * @param {number} [maxAmount=1_000_000]
     * Maximum amount the field can contain.
     *
     * @param {number} [minAmount=0]
     * Minimum amount the field can contain.
     */
    function adjustCurrencyInput(
        amountInputField,
        deltaPennies = 1,
        maxAmount = 1_000_000,
        minAmount = 0
    ) {
        const current = Number(amountInputField.value) || 0;

        const pennies = Math.round(current * 100);
        const newAmount = (pennies + deltaPennies) / 100;

        if (newAmount > maxAmount || newAmount < minAmount) {
            return;
        }

        amountInputField.value = newAmount.toFixed(2);
    }

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
                adjustCurrencyInput(amountInputField);
                break;

            case "minus":
                adjustCurrencyInput(amountInputField, -1);
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

        const maxAmount = 1000000;
        const minAmount = 0;

        let value = Number(amountInputField.value) || 0;
        value = Math.min(Math.max(value, minAmount), maxAmount);

        amountInputField.value = value.toFixed(2);
    }

    /**
     * Closes the "Add Funds" panel.
     *
     * This function hides the add funds panel by setting its visibility to false.
     */
    function closeAddFundsPanel() {
        toggleElement({ element: addFundsToBankPanel, show: false }); // Hide the panel
    }

    /**
     * Opens the "Add Funds" panel.
     *
     * This function toggles the visibility of the add funds panel and sets focus
     * to the amount input field for immediate user input.
     */
    function openAddFundsPanel() {
        // console.log("open");
        toggleElement({ element: addFundsToBankPanel });
        amountInputField.focus(); // Focus input for convenience
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
                closeAddFundsPanel();
                break;
            case addFundsBtn:
                openAddFundsPanel();
                break;
        }
    }




    return {
        handleInput,
        handleEnter,
        handleToggleAddFundsPanel,
    };
})();




export const BankFundBtn = (() => {

    const MAX_TRANSFER_AMOUNT = 10_000;

    /**
     * Clears the amount input field by setting its value to an empty string.
     */
    function clearAmountInputField() {
        amountInputField.value = "";
    }


    /**
     * Resets the transfer amount to the default amount
     */
    function resetTransferAmountToDefault() {
        amountInputField.value = MAX_TRANSFER_AMOUNT.toFixed(2)
    }



    /**
     * Handles the "Add Funds" button click for transferring money to the user's bank account
     * when the add funds button is clicked. The functions shows a confirmation message
     * before and after the transfer
     *
     * @param {Event} e - The click event triggered by the user.
     */
    async function handleFundAccountBtn(e) {
        const buttonId = "account_card__add_funds-btn";
        if (e.target.id !== buttonId) return;

        const amount = amountInputField.value;
        if (!amount || amount <= 0) return;


        if (amount > MAX_TRANSFER_AMOUNT) {
            resetTransferAmountToDefault();
            AlertUtils.showAlert({
                title: "Transfer amount too high",
                text: `The amount you entered exceeds the maximum allowed transfer of £${MAX_TRANSFER_AMOUNT.toLocaleString()}. Please enter an amount up to £${MAX_TRANSFER_AMOUNT.toLocaleString()}.`,
                icon: "warning",
                confirmButtonText: "OK",
            });


            return;
        }

        const confirmed = await AlertUtils.showConfirmationAlert({
            title: "Do you want to proceed?",
            text: `You about to add £${amount} to your bank account, do you want to proceed?`,
            confirmButtonText: "Add funds",
            messageToDisplayOnSuccess: "The funds have been added",
            denyButtonText: "Cancel funding",
            cancelMessage: "No action taken."
        });

        if (confirmed) {
            // This will be replaced with a fetch and at the momemnt it is simply a placeholder
            console.log("Funds have been transferred");
            clearAmountInputField();
        }

        }

        return {
            handleFundAccountBtn,
        }

})();




amountInputField.addEventListener("keydown", BankFundInput.handleEnter);
