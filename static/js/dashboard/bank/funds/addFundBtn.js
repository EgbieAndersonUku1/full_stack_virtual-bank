/**
 * @fileoverview
 * Handles the "Add Funds" button functionality for the user's bank account.
 *
 * This module validates the transfer amount, checks it against the maximum
 * permitted transfer limit, displays appropriate validation and confirmation
 * alerts, and initiates the fund transfer process.
 *
 * The module relies on BankFundAmountInputField for managing the transfer
 * amount input, getting the correct amount, resetting the amount field
 * and AlertUtils for displaying user notifications and confirmation dialogs.
 *
 * @module AddFundBtn
 */

import { AlertUtils } from "../../../alerts.js";
import { BankFundAmountInputField } from "./bankFundAmountInputField.js";


export const AddFundBtn = {

    /**
     * Handles the "Add Funds" button click for transferring money to the user's
     * bank account. Validates the transfer amount and displays confirmation
     * and validation messages to the user.
     *
     * @param {Event} e - The click event triggered by the user.
     * @returns {Promise<void>} A promise that resolves when the operation is complete.
     */
    async handleFundAccountBtn(e) {
        const buttonId = "account_card__add_funds-btn";

        if (e.target.id !== buttonId) return;

        const amount = BankFundAmountInputField.getAmountInputFieldValue();

        if (!amount || amount <= 0) return;

        if (amount > BankFundAmountInputField.getMaxTransferAmount()) {
            BankFundAmountInputField.resetTransferAmountToMax()

            AlertUtils.showAlert({
                title: "Transfer amount too high",
                text: `The amount you entered exceeds the maximum allowed transfer of £${BankFundAmountInputField.MAX_TRANSFER_AMOUNT.toLocaleString()}. Please enter an amount up to £${BankFundAmountInputField.MAX_TRANSFER_AMOUNT.toLocaleString()}.`,
                icon: "warning",
                confirmButtonText: "OK",
            });

            return;
        }

        const confirmed = await AlertUtils.showConfirmationAlert({
            title: "Do you want to proceed?",
            text: `You are about to add £${amount.toFixed(2)} to your bank account. Do you want to proceed?`,
            confirmButtonText: "Add funds",
            messageToDisplayOnSuccess: "The funds have been added",
            denyButtonText: "Cancel funding",
            cancelMessage: "No action taken."
        });

        if (confirmed) {
            // TODO: Replace with a fetch request to process the transfer.
            console.log("Funds have been transferred");
            BankFundAmountInputField.clearAmountInputField()
        }
    }
};
