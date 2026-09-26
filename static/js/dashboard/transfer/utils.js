import { warnError } from "../../logger.js";


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
export function getAccountDetailsFromData(data){

    if (typeof data !== "object") {
        warnError("getAccountNumberFromData", {
            type: typeof data,
            expected: "Expected an object",
            received: `Value received ${data}`
        });
        return;
    }

    const sortCode      = [];
    const accountNumber = [];
    const account       = {};

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

