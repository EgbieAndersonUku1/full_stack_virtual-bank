/**
 * @fileoverview
 * Provides functionality for managing the bank fund amount input field,
 * including clearing the field, retrieving and formatting its value,
 * resetting the value to the maximum transfer amount, adjusting the
 * amount by pennies, and configuring the permitted transfer limits.
 */

const amountInputField = document.getElementById("account-card__amount");

/**
 * Manages the bank fund amount input field and provides functionality
 * for retrieving, clearing, resetting, validating, and adjusting the
 * transfer amount.
 */
export const BankFundAmountInputField = {
    MAX_TRANSFER_AMOUNT: 10_000,
    MIN_TRANSFER_AMOUNT: 0,

    /**
     * Clears the current value from the bank fund amount input field.
     *
     * @returns {void}
     */
    clearAmountInputField() {
        amountInputField.value = "";
    },

    /**
     * Retrieves the current value from the bank fund amount input field
     * and converts it to a number rounded to two decimal places.
     *
     * @returns {number} The current transfer amount.
     */
    getAmountInputFieldValue() {
        return Number(Number(amountInputField.value).toFixed(2));
    },

    /**
     * Updates the bank fund amount input field with the supplied amount.
     *
     * @param {number} amount - The amount to display in the input field.
     * @returns {void}
     * @throws {Error} If the supplied amount is not a finite number.
     */
    setAmount(amount) {
        this._validateAmountType(amount);

        amountInputField.value = amount.toFixed(2);
    },

    /**
     * Resets the bank fund amount input field to the maximum transfer amount.
     *
     * @returns {void}
     */
    resetTransferAmountToMax() {
        amountInputField.value = this.MAX_TRANSFER_AMOUNT.toFixed(2);
    },

    /**
     * Updates the maximum permitted transfer amount.
     *
     * @param {number} amount - The new maximum transfer amount.
     * @returns {void}
     * @throws {Error} If the supplied amount is not a finite number.
     */
    setMaxTransferAmount(amount) {
        this._validateAmountType(amount);

        this.MAX_TRANSFER_AMOUNT = amount;
    },

    /**
     * Returns the maximum transfer amount permitted by the system.
     *
     * @returns {number} The maximum permitted transfer amount.
     */
    getMaxTransferAmount() {
        return this.MAX_TRANSFER_AMOUNT;
    },

    /**
     * Returns the bank fund amount input field DOM element.
     *
     * @returns {HTMLInputElement} The bank fund amount input field element.
     */
    getElement() {
        return amountInputField;
    },

    /**
     * Validates that the supplied amount is a finite number.
     *
     * @param {*} amount - The amount to validate.
     * @throws {Error} If the supplied amount is not a finite number.
     */
    _validateAmountType(amount) {
        const amountType = typeof amount;

        if (amountType !== "number" || !Number.isFinite(amount)) {
            throw new Error(`Expected a valid number but got ${amountType}`);
        }
    },

    /**
     * Adjusts the currency input value by a specified number of pennies.
     *
     * @param {number} [deltaPennies=1] - The number of pennies to adjust by.
     * Positive values increase the amount, while negative values decrease it.
     * @returns {void}
     */
    adjustAmountByPennies(deltaPennies = 1) {
        this._validateAmountType(deltaPennies);

        const current = Number(amountInputField.value) || 0;

        const pennies = Math.round(current * 100);
        const newAmount = (pennies + deltaPennies) / 100;

        if (
            newAmount > this.MAX_TRANSFER_AMOUNT ||
            newAmount < this.MIN_TRANSFER_AMOUNT
        ) {
            return;
        }

        amountInputField.value = newAmount.toFixed(2);
    },

    /**
     * Clamps the current input amount between the minimum and maximum
     * permitted transfer amounts.
     *
     * If the current amount is below the minimum, it is set to the minimum.
     * If the current amount is above the maximum, it is set to the maximum.
     *
     * @returns {void}
     */
    clampAmountToRange() {
        let amount = Number(amountInputField.value) || 0;

        amount = Math.min(
            Math.max(amount, this.MIN_TRANSFER_AMOUNT),
            this.MAX_TRANSFER_AMOUNT
        );

        amountInputField.value = amount.toFixed(2);
    },
};
