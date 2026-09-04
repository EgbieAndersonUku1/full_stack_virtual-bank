import { logError, warnError } from "./logger.js";
import { specialChars } from "./specialChars.js";


export function checkIfHTMLElement(element, elementName = "Unknown", warn = false) {
    if (!(element instanceof HTMLElement || element instanceof DocumentFragment)) {

        if (warn) {
            console.warn(`Could not find the element: '${elementName}'. Ensure the selector is correct.`);
        } else {
            console.error(`Could not find the element: '${elementName}'. Ensure the selector is correct.`);
        }
        return false;

    }
    return true;
}



export function generateRandomID(maxDigit = 10000000) {
    if (maxDigit <= 0) {
        throw Error(`The max digit cannot be less or equal to 0. Expected a number higher than 0 but got ${maxDigit}`)
    }
    return Math.ceil(Math.random() * maxDigit);
}


/**
 * Toggles the visibility of the spinner.
 *
 * This function shows or hides the spinner by setting its display property to either 'block' or 'none'.
 *
 * @param {boolean} [show=true] - A boolean indicating whether to show or hide the spinner.
 *                               If `true`, the spinner is shown; if `false`, it is hidden.
 */
export function toggleSpinner(spinnerElement, show = true, hideScroller = false) {
    if (!checkIfHTMLElement(spinnerElement)) {
        console.error("Missing spinner element");
    }
    spinnerElement.style.display = show ? "block" : "none";

    if (hideScroller) {
        toggleScrolling(show);
    }

}


/**
 * Shows the spinner for a specified duration and then hides it.
 *
 * This function uses the `toggleSpinner` function to show the spinner immediately,
 * and then hides it after the specified amount of time (default is 500ms).
 *
 * @param {HTMLElement} spinnerElement - The spinner element to display.
 * @param {number} [timeToDisplay=500] - The duration (in milliseconds) to display the spinner. Defaults to 500ms.
 */
export function showSpinnerFor(spinnerElement, timeToDisplay = 500, hideToggle = false) {
    toggleSpinner(spinnerElement);

    setTimeout(() => {
        toggleSpinner(spinnerElement, false, hideToggle);
    }, timeToDisplay);
}


export function toggleScrolling(disable) {
    document.body.style.overflow = disable ? "hidden" : "auto";
    document.body.style.overflowX = "hidden";
}


export function findByIndex(id, items) {
    if (!Array.isArray(items)) {
        throw new Error(`Expected an array, but got ${typeof items}`);
    }

    if (id === undefined || id === null) {
        throw new Error(`Invalid id: ${id}`);
    }

    return items.findIndex((item) => item?.id === id);
}


/**
 * Sanitizes the input text based on the specified criteria:
 * - Optionally removes non-numeric characters.
 * - Optionally removes non-alphabet characters.
 * - Optionally ensures that specific special characters are included and valid.
 * - Removes hyphens from the input text.
 *
 * @param {string} text - The input text to be sanitized.
 * @param {boolean} [onlyNumbers=false] - If true, removes all non-numeric characters.
 * @param {boolean} [onlyChars=false] - If true, removes all non-alphabetic characters.
 * @param {Array<string>} [includeChars=[]] - An array of special characters that should be included in the text.
 * @throws {Error} If `includeChars` is not an array or contains invalid characters that are not in the `specialChars` list.
 * @returns {string} - The sanitized version of the input text.
 *
 * @example
 * // Only numbers will remain (non-numeric characters removed)
 * sanitizeText('abc123', true);
 * // Output: '123'
 *
 * @example
 * // Only alphabetic characters will remain (non-alphabet characters removed)
 * sanitizeText('abc123!@#', false, true);
 * // Output: 'abc'
 *
 * @example
 * // Ensures specific special characters are valid (will remove invalid ones)
 * sanitizeText('@hello!world', false, false, ['!', '@']);
 * // Output: '@hello!world' (if both '!' and '@' are in the valid list of special characters)
 *
 * @example
 * // Removes hyphens from the input
 * sanitizeText('my-name-is', false, false);
 * // Output: 'mynameis'
 */
export function sanitizeText(text, onlyNumbers = false, onlyChars = false, includeChars = []) {
    if (!Array.isArray(includeChars)) {
        throw new Error(`Expected an array but got type ${typeof includeChars}`);
    }

    if (typeof onlyChars !== "boolean" && typeof onlyNumbers !== "boolean") {
        throw new Error(`Parameters onlyNumbers and onlyChars must be boolean but got: onlyNumbers - ${typeof onlyNumbers} and onlyChar - ${typeof onlyChars}`);
    }

    if (onlyNumbers && onlyChars) {
        throw new Error(`onlyNumbers and onlyChars cannot both be true. onlyNumbers - ${onlyNumbers} and onlyChar - ${onlyChars}`);
    }

    const INCLUDE_CHARS_ARRAY_LENGTH = includeChars.length;


    if (INCLUDE_CHARS_ARRAY_LENGTH > 0) {
        const invalidChar = includeChars.find(char => !specialChars[char]);
        if (invalidChar) {
            throw new Error(`Expected a special character but got ${invalidChar}`);
        }
    }

    if (onlyNumbers) {
        return text.replace(/\D+/g, "");
    }

    if (onlyChars) {
        if (INCLUDE_CHARS_ARRAY_LENGTH > 0) {
            return text.replace(/[^A-Za-z]/g, (match) => {
                return includeChars.includes(match) ? match : '';  // Keep if allowed, otherwise remove
            });
        }

        return text.replace(/[^A-Za-z]/g, '');
    }

    return text ? text.split("-").join("") : '';
}



/**
 * Formats a UK mobile number into the international format: `+44 (prefix) exchangeNumber`.
 *
 * @param {string} number - The UK mobile number to format.
 *
 * @throws {Error} If the number is invalid for any of the following reasons:
 *      - The number is not a UK mobile number (i.e., length is not exactly 11 digits after cleaning).
 *      - The number does not start with a `0`.
 *      - The number starts with `08` since valid UK mobile numbers always start with `07`.
 *
 * @returns {string} A formatted, valid UK mobile number in the form: `+44 (prefix) exchangeNumber`.
 *
 * @example
 * formatUKMobileNumber("+44 7947 106 747")    // Returns: "+44 (7947) 106747"
 * formatUKMobileNumber("0044 7947 106 747")   // Returns: "+44 (7947) 106747"
 * formatUKMobileNumber("44 07947 106 747")    // Returns: "+44 (7947) 106747"
 * formatUKMobileNumber("+44 (0)7947-106-747") // Returns: "+44 (7947) 106747"
 * formatUKMobileNumber("07947106747")         // Returns: "+44 (7947) 106747"
 * formatUKMobileNumber("447947106747")        // Returns: "+44 (7947) 106747"
 *
 * @example
 * // Errors:
 * formatUKMobileNumber("0797106747");      // Throws Error: Number must be exactly 11 digits long.
 * formatUKMobileNumber("07971067479255");  // Throws Error: Number must be exactly 11 digits long.
 * formatUKMobileNumber("08971067479255");  // Throws Error: Number must start with '07'.
 */
export function formatUKMobileNumber(number) {

    const cleanedNumber = cleanUKMobileNumber(number);
    const prefix = cleanedNumber.slice(1, 5);
    const exchangeNumber = cleanedNumber.slice(5);

    const formattedMobileNumber = `+44 (${prefix}) ${exchangeNumber}`;
    return formattedMobileNumber;
}



/**
 * Takes a UK mobile number and cleans the number to ensure it follows the correct format.
 * It handles various UK number prefixes and sanitizes the input to return a valid 11-digit number.
 *
 * @param {string} mobileNumber - The mobile number to clean. Can be in formats like:
 *    - `+44 7947 106 747`
 *    - `0044 7947 106 747`
 *    - `44 07947 106 747`
 *    - `+44 (0)7947-106-747`
 *    - `0044(0)7947106747`
 *    - `07947106747`
 *
 * @error Throws errors if:
 *    - The number does not start with a `0`.
 *    - The number length is not 11 digits.
 *    - The number starts with 08 since UK mobile numbers always start with `07`
 *
 * @returns {string} A valid 11-digit UK mobile number.
 *
 * Example usage:
 *
 * // valid numbers
 * cleanUKMobileNumber("+44 7947 106 747")   // returns: 07947106747  // valid
 * cleanUKMobileNumber("0044 7947 106 747")  // returns: 07947106747  // valid
 * cleanUKMobileNumber("44 07947 106 747")   // returns: 07947106747  // valid
 * cleanUKMobileNumber("+44 (0)7947-106-747") // returns: 07947106747  // valid
 * cleanUKMobileNumber("07947106747")         // returns 07947106747  // valid
 * cleanUKMobileNumber("447947106747")       // teturns 07947106747  // valid
 *
 *
 * throws errors:
 *
 * cleanUKMobileNumber("0797106747")     -> throws Error because the length is less than 11
 * cleanUKMobileNumber("07971067479255") -> throws Error because the length is greater than 11
 * cleanUKMobileNumber("08971067479255") -> throws Error Valid length but starts with `08` UK mobile numbers start with "07"
 */
export function cleanUKMobileNumber(mobileNumber) {

    // Replace various UK prefixes with '0' and handle cases like +44 (0)7 or 0044
    const digitsOnly = sanitizeText(mobileNumber, true).replace(/^(?:\+44|44|0044)0?/, "0");
    const VALID_UK_MOBILE_NUM_LENGTH = 11;

    if (!digitsOnly.startsWith("0")) {
        throw new Error("The number is invalid because it doesn't start with a 0");
    }

    if (digitsOnly.length != VALID_UK_MOBILE_NUM_LENGTH) {
        throw new Error(`This not a valid UK mobile number. Expected 11 digits got ${digitsOnly.length} `);

    }

    if (!digitsOnly.startsWith("07")) {
        const START_INDEX = 0;
        const END_INDEX = 2;
        throw new Error(`UK mobile numbers always start with a "07". Expected a prefix of "07" but got ${digitsOnly.slice(START_INDEX, END_INDEX)}`);
    }
    return digitsOnly;
}


export function toTitle(text) {
    if (typeof text != "string") {
        throw new Error(`Expected a string but got text with type ${text} `);
    }

    const title = `${text.charAt(0).toUpperCase()}${text.slice(1).toLowerCase()}`;
    return title;
}


/**
 * Compares two non-nested objects to check if they have identical keys and values.
 *
 * @param {Object} object1 - The first object to compare.
 * @param {Object} object2 - The second object to compare.
 * @returns {Object} - Returns an object with comparison result and changes, if any.
 * @throws {Error} - Throws an error if either argument is not a valid object.
 *
 * @example
 * const obj1 = { name: "Alice", age: "25", location: "London" };
 * const obj2 = { name: "Alice", age: "26", location: "Manchester" };
 * console.log(compareTwoObjects(obj1, obj2));
 * // Output: { areEqual: false, changes: { age: { previous: "25", current: "26" }, location: { previous: "London", current: "Manchester" } } }
 */
export function compareTwoObjects(object1, object2) {
    if (typeof object1 !== "object" || object1 === null || Array.isArray(object1)) {
        throw new Error(`The first argument must be a non-null object. Got type ${typeof object1} and ${object1}`);
    }

    if (typeof object2 !== "object" || object2 === null || Array.isArray(object2)) {
        throw new Error(`The second argument must be a non-null object. Got type ${typeof object2} and ${object2}`);
    }

    const keys1 = Object.keys(object1);
    const keys2 = Object.keys(object2);

    if (keys1.length !== keys2.length) {
        return { areEqual: false, changes: null };
    }

    const changes = {};

    for (const key of keys1) {
        const value1 = object1[key]?.trim?.() || object1[key];
        const value2 = object2[key]?.trim?.() || object2[key];

        if (value1 !== value2) {
            changes[key] = { previous: value1, current: value2 };
        }
    }

    const areEqual = Object.keys(changes).length === 0;
    return { areEqual, changes: areEqual ? null : changes };
}




/**
 * Returns a new object (or array) excluding the specified `key` or `property`.
 *
 * @param {Object|Array} obj - The object or array to be processed.
 * @param {String|Number} key - The key (for objects) or index (for arrays) to exclude.
 *
 * @returns {Object|Array} - A new object or array excluding the specified key or index.
 *
 * @throws {TypeError} - If `obj` is not an object or array.
 * @throws {RangeError} - If the provided index is out of range for arrays.
 *
 * @example
 * // Usage with an object
 * const user = { id: 1, name: 'Marcus', group: 'admin' };
 * console.log(excludeKey(user, 'group'));
 * // Expected Output: { id: 1, name: 'Marcus' }
 *
 * @example
 * // Usage with an array
 * const numbers = [10, 20, 30, 40];
 * console.log(excludeKey(numbers, 2));
 * // Expected Output: [10, 20, 40]
 *
 * @example
 * // Handling invalid index for array
 * const numbers = [10, 20, 30, 40];
 * try {
 *     console.log(excludeKey(numbers, -1));  // Invalid index
 * } catch (error) {
 *     console.log(error.message);  // Expected Output: Invalid array index
 * }
 *
 * @example
 * // Handling invalid object
 * try {
 *     console.log(excludeKey(123, 'group'));  // Invalid object (not an array or object)
 * } catch (error) {
 *     console.log(error.message);  // Expected Output: Expected an object or array
 * }
 */
export function excludeKey(obj, key) {

    if (typeof obj !== 'object' || obj === null) {
        throw new TypeError('Expected an object or array');
    }

    // Handle an array
    if (Array.isArray(obj)) {
        if (typeof key !== 'number' || key < 0 || key >= obj.length) {
            throw new RangeError('Invalid array index');
        }
        return [...obj.slice(0, key), ...obj.slice(key + 1)];
    }

    const { [key]: _, ...rest } = obj;
    return rest;
}


export function checkNumber(value) {
    const numberValue = parseFloat(value);

    return {
        isNumber: !isNaN(numberValue) && isFinite(numberValue),
        isInteger: Number.isInteger(numberValue),
        isFloat: !Number.isInteger(numberValue) && !isNaN(numberValue) && isFinite(numberValue)
    };
}


export function getCombinedCode(a, b) {
    if (typeof a !== 'string' || typeof b !== 'string') {
        throw new TypeError('Both inputs must be strings.');
    }

    if (!a.trim() || !b.trim()) {
        throw new Error('Inputs cannot be empty or whitespace only.');
    }

    return `${a} ${b}`;
}


export function dimBackground(dimBackgroundElement, dim = false) {
    dimBackgroundElement.style.display = dim ? "block" : "none";
};




/**
 * Formats input text by inserting a dash ('-') at specified intervals.
 *
 * This function listens for input changes and automatically adds dashes
 * after every specified number of characters. It also provides an option
 * to keep only digits by removing all non-numeric characters.
 *
 * @param {string} value  - The value to add the dashes to
 * @param {number} lengthPerDash - The number of characters between dashes (default: 5).
 * @param {boolean} digitsOnly - If true, removes all non-numeric characters (default: false).
 */
export function applyDashToInput(value, lengthPerDash = 5, digitsOnly = false, charsOnly = false) {

    if (typeof value !== "string") {
        throw new TypeError(`The value must be a string. Expected string got type ${typeof value}`)
    }
    value = value.trim();

    if (!value) return;
    if (!Number.isInteger(lengthPerDash)) {
        console.error(`The lengthPerDash must be integer. Expected an integer but got ${typeof lengthPerDash}`);
    };

    let santizeValue = sanitizeText(value, digitsOnly, charsOnly);
    let formattedText = [];


    for (let i = 0; i < santizeValue.length; i++) {

        const fieldValue = santizeValue[i];

        if (i > 0 && i % lengthPerDash === 0) {
            formattedText.push(concatenateWithDelimiter("-", fieldValue));
        } else {
            formattedText.push(fieldValue);

        }
    }

   return formattedText.join("");

};


/**
 * Concatenates two strings with a delimiter in between.
 * @param {string} first     - The first string.
 * @param {string} second    - The second string.
 * @param {string} delimiter - The delimiter to use if none is provide concatenates the two strings.
 * @returns {string}         - The concatenated string.
 */
export function concatenateWithDelimiter(first, second, delimiter = "") {
    return `${first}${delimiter}${second}`;
}




/**
 * Restricts the length of a given  input field to a maximum of 10 characters which is default.
 *
 * This function ensures that the user cannot enter more than the allowed number of characters
 * in the input field. It also performs safety checks to prevent errors
 * when accessing `e.target.value`.
 *
 * @errors {Error}  - Raises two errors:
 *                      - If the maximum length value is not a valid number
 *                      - If an attempt is made to convert the value returned from input field to an integer or a float,
 *                        however the value is a text and not a digit.
 *
 * @param {Event} e         - The input event triggered when the user types in the field.
 * @param {maximumLength}   - The maximum lenght to a given character. Default is 10
 * @param {convertToFloat } - An optional value that allows the given value to be converted to a float.
 *                            If true converts to a float else leaves the value as it is.
 *                            Note - To convert to a float the digit must be an integer or a float otherwise
 *                            an error is raised
 * @param {number} - Returns the input value
 */
export function handleInputFieldValueLength({ e, maximumLength = 10, convertToFloat = false, returnInputValue = false }) {

    if (!e.target || typeof e.target.value !== "string") {
        return;
    }

    const isNumberValid = checkNumber(maximumLength).isInteger || checkNumber(maximumLength).isNumber;

    if (!isNumberValid) {
        logError("handleFundAmountLength", `The maximum length must be an integer. Expected an integer but got type: ${typeof maximumLength}`);
        throw new Error("The number is not a valid number");
    }

    let trimmedValue = e.target.value.slice(0, maximumLength);

    if (trimmedValue && convertToFloat) {
        const canBeConverted = checkNumber(trimmedValue).isInteger || checkNumber(trimmedValue).isNumber || checkNumber(trimmedValue).isFloat;
        if (!canBeConverted) {
            logError("handleFundAmountLength", `The value cannot be converted to a float because it is not digit. Expected an integer/float but got text: ${trimmedValue}`);
            throw new Error(`Cannot convert to a float because the value is not an integer or a float. Value received ${trimmedValue}`)
        }
        trimmedValue = parseFloat(trimmedValue);
    }


    if (trimmedValue !== e.target.value) {
        e.target.value = convertToFloat ? trimmedValue : trimmedValue;  // middle is number converted to float and else is not
    }

    if (returnInputValue) {
        return trimmedValue;
    }

}





/**
 * Masks a credit card number, hiding all but the last four digits.
 *
 * The function replaces the leading digits with '*' while keeping the last four digits visible.
 * It ensures that the credit card number is within a valid range (12 to 19 digits) and that
 * it contains non-numeric characters.
 *
 * @param {string} creditCardNo - The credit card number to be masked.
 * @returns {string} The masked credit card number.
 * @throws {Error} If the input is not a string or has an invalid length.
 * @throws {Error} If the input are non-numeric characters
 *
 * @example
 * maskCreditCardNo("1234567812345678"); // "************5678"
 * maskCreditCardNo("378282246310005");  // "***********0005" (Amex)
 * maskCreditCardNo("30569309025904");   // "**********5904" (Diners Club)
 */
export function maskCreditCardNo(creditCardNo) {
    if (!creditCardNo || typeof creditCardNo !== "string") {
        throw new Error("Invalid credit card number");
    }

    const CREDIT_CARD_LENGTH = sanitizeText(creditCardNo, true).length;
    const MIN_CREDIT_CARD_LENGTH = 12;
    const MAX_CREDIT_CARD_LENGTH = 19;


    if (CREDIT_CARD_LENGTH < MIN_CREDIT_CARD_LENGTH) {
        throw new Error(`The credit card is invalid because it contains non-numeric values. Credit card no: ${creditCardNo}`);
    };

    if (CREDIT_CARD_LENGTH > MAX_CREDIT_CARD_LENGTH) {
        throw new Error("Credit card length must be: Visa, Mastercard, Discover: 16, American Express: 15, Diners Club: 14, Maestro: 12 to 19");
    }

    const numberToMask = CREDIT_CARD_LENGTH - 4;
    const maskedNumber = "*".repeat(numberToMask);
    const lastFourDigits = creditCardNo.slice(-4);

    return concatenateWithDelimiter(maskedNumber, lastFourDigits);
};


/**
 * Formats a given amount into a currency string with the specified currency symbol and locale.
 *
 * @param {number|string} amount - The amount to format. This can be a number or a string representation of a number.
 * @param {string} [locale='en-GB'] - The locale string (e.g., 'en-GB' for UK, 'en-US' for the US). Defaults to 'en-GB'.
 * @param {string} [currency='GBP'] - The ISO 4217 currency code (default is 'GBP' for British Pounds).
 *
 * @returns {string} - A string formatted as a currency value with two decimal places and a currency symbol (e.g., '£12,345.60' or '$12,345.60').
 *
 * @throws {Error} - Throws an error if the amount is not a valid number or string that can be parsed into a number.
 *
 * @example
 * formatCurrency("12345.6"); // returns '£12,345.60' (default locale 'en-GB')
 * formatCurrency(50); // returns '£50.00' (default locale 'en-GB')
 * formatCurrency(5000, 'en-US', 'USD'); // returns '$5,000.00'
 * formatCurrency(5000, 'de-DE', 'EUR'); // returns '5.000,00 €' (German locale)
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/toLocaleString
 */
export function formatCurrency(amount, locale = 'en-GB', currency = 'GBP') {
    const parsedAmount = typeof amount === "string" ? parseFloat(amount) : amount;

    if (isNaN(parsedAmount)) {
        throw new Error(`Invalid amount: ${amount}`);
    }

    return parsedAmount.toLocaleString(locale, {
        style: 'currency',
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}


export function parseErrorMessage(errorMsg) {
    if (typeof errorMsg !== "string") return null;

    const [titleRaw, textRaw] = errorMsg.split(":");

    if (titleRaw === undefined || textRaw === undefined) {
        return { title: "Oops, something went wrong", text: "" };
    }

    const title = titleRaw.trim();
    const text = textRaw.trim();

    return { title, text }

}




/**
 * Removes a CSS class from all elements in a collection.
 *
 * Typically used to deselect or reset UI elements that were
 * previously marked with a given class (e.g., removing a
 * "selected" state from cards).
 *
 * @param {NodeList|Array<HTMLElement>} elements
 * A collection of DOM elements, commonly returned by
 * querySelectorAll().
 *
 * @param {string} cssClass
 * The CSS class to remove from each element.
 *
 * @returns {void}
 */
export function deselectAllElements(elements, cssClass) {

    // Ensure the function receives a collection of elements that can be used by forEach loop
    if (!elements || typeof elements.forEach !== "function") return;

    if (typeof cssClass !== "string" || cssClass.length === 0) return;

    elements.forEach((element) => {
        element.classList.remove(cssClass);
    });
}




/**
 * Adds a CSS class to a DOM element to mark it as selected or active.
 *
 * Commonly used to visually highlight UI elements such as cards,
 * buttons, or list items when they are selected by the user.
 *
 * @param {HTMLElement} elementToSelect
 * The DOM element that should receive the CSS class.
 *
 * @param {string} [cssSelectorElement="active"]
 * The CSS class to add to the element. Defaults to "active".
 *
 * Note:
 * There must a CSS rule that determines how the element should be highlighted
 * and that name should be passed to the function.
 *
 * @returns {void}
 */
export function selectElement(elementToSelect, cssSelectorElement = "active") {
    if (!checkIfHTMLElement(elementToSelect)) return;
    elementToSelect.classList.add(cssSelectorElement);
}



/**
 * Parses a currency-formatted string and returns its numeric value.
 *
 * This function removes common currency symbols (e.g. £, $, €),
 * whitespace (including non-breaking spaces), and thousands separators.
 * It supports decimal values and negative amounts expressed either with
 * a leading minus sign (e.g. "-£100") or parentheses (e.g. "(£100)").
 *
 * @param {string} value - The currency string to parse (e.g. "£1,234.56").
 * @returns {number} The numeric representation of the currency value.
 *                   Returns NaN if the value cannot be parsed.
 *                   Doesn't return 0 because 0 hides the errors
 *
 * @example
 * parseCurrency("£1,234.56") // 1234.56
 * parseCurrency("(€99.99)")  // -99.99
 * parseCurrency("-$100")     // -100
 * parseCurrency("-$100??????????")     // -100
 */
export function parseCurrency(currency) {

    if (typeof currency !== "string") {
        warnError("parseCurrency", {
            currency: currency,
            type: typeof currency,
            error: "Must be a string"
        })
        return NaN;
    }

    const cleanedValues = [];
    let isNegative = false;

    for (let char of currency) {

        if (!isNaN(char) && char !== " " || char === ".") {
            cleanedValues.push(char)
        }
        if (char === "-" && !isNegative) {
            isNegative = true;
        }
    }

    if (cleanedValues.length === 0) return NaN;

    const cleanedNumbers = parseFloat(cleanedValues.join(""))
    return isNegative ? cleanedNumbers * -1 : cleanedNumbers;
}



/**
 * Enables auto-focus and navigation behaviour for a group of input elements.
 *
 * Behaviour:
 * - Automatically moves focus to the next input when a character is entered.
 * - Moves focus to the previous input when Backspace is pressed on an empty input.
 * - Optionally restricts input values to numeric characters only.
 *
 * Common use cases: OTP fields, account numbers, sort codes, PINs.
 *
 * @param {NodeList|HTMLElement[]} inputElements
 *   Collection of DOM input elements (NodeList or array).
 *
 * @param {boolean} [onlyNumbers=true]
 *   If true, input values are sanitised to allow only numeric characters.
 */
export function enableAutoFocusNavigation(inputElements, onlyNumbers = true) {

    if (!(inputElements instanceof NodeList) && !Array.isArray(inputElements)) {
        warnError("autoFocusInputFields", {
            expected: "NodeList or array of DOM elements",
            received: inputElements,
        });
        return;
    }

    inputElements[0].focus();

    inputElements.forEach((input) => {

        if (input.dataset.autoFocusNavigation === "true") {
            return;
        }

        input.dataset.autoFocusNavigation = "true";

        input.addEventListener("input", (e) => {

            if (onlyNumbers) {
                e.target.value = sanitizeText(e.target.value, true);
            }

            if (e.target.value.length === 1) {
                e.target.nextElementSibling?.focus();
            }
        });

        input.addEventListener("keydown", (e) => {

            if (e.key === "Backspace" && !e.target.value) {
                e.target.previousElementSibling?.focus();
            }

        });

    });
}

export function parseCharsFromObject(fieldObject) {

    const objectType = typeof fieldObject

    if (objectType !== "object") {
        logError("parseCharsFromObject", {
            field: "fieldObject",
            error: "The field must be an object",
            typeReceived: objectType
        });
        return;
    }

    const values = [];

    for (const [key, value] of Object.entries(fieldObject)) {
        values.push(value);
    }

    return {
        values: values.join("")
    };


}



/**
 * Toggles the visibility of a DOM element.
 * @param {Object} options - Options object.
 * @param {HTMLElement} options.element - The element to toggle.
 * @param {cSSSelector} - The selector for the element
 * @param {boolean} options.show - Whether to show (true) or hide (false) the element.
 * @returns {void}
 */

export function toggleElement({ element, cSSSelector = "show", show = true }) {
    if (!checkIfHTMLElement(element, "Unknown"));

    if (show) {
        element.classList.add(cSSSelector);
        return;
    }

    element.classList.remove(cSSSelector);
}




/**
 * Checks whether a form field is empty.
 *
 * A field is considered empty if its value is missing or contains only
 * whitespace.
 *
 * @param {Object} options - Configuration object.
 * @param {HTMLFormElement} options.form - The form containing the field.
 * @param {string} options.fieldName - The name attribute of the field to check.
 *
 * @returns {boolean} Returns true if the field is empty; otherwise, false.
 *
 * @throws {Error} Throws an error if the provided form is not an HTMLFormElement
 * or if the field name is not a string.
 *
 * @example
 * const isEmpty = isFormFieldEmpty({
 *     form,
 *     fieldName: "card-request-address2"
 * });
 */
export function isFormFieldEmpty({ form, fieldName }) {
    if (!(form instanceof HTMLFormElement)) {
        throw new Error("The form value provided is not a form element");
    }

    if (typeof fieldName !== "string") {
        throw new Error("The value to check must be a string");
    }

    const formData = new FormData(form);
    const formFieldValue = formData.get(fieldName);

    return typeof formFieldValue === "string" && formFieldValue.trim() === "";
}





/**
 * Checks whether an element supports the required attribute.
 *
 * @param {HTMLElement} element - The element to check.
 *
 * @returns {boolean} True if the element can have the required attribute.
 */
function isRequiredInputElement(element) {
    return (
        element instanceof HTMLInputElement ||
        element instanceof HTMLSelectElement ||
        element instanceof HTMLTextAreaElement
    );
}



/**
 * Toggles the required attribute for a collection of HTML elements.
 *
 * Converts the provided NodeList into an array, validates the required value,
 * checks that each item is an HTML element, and updates the required attribute.
 *
 * @param {Object} options - Configuration object.
 * @param {NodeList} options.elementsNode - A NodeList containing HTML elements to update.
 * @param {boolean} options.required - Whether the elements should be required.
 *
 * @returns {void}
 *
 * @example
 * const inputs = document.querySelectorAll("input");
 *
 * toggleRequiredInput({
 *    elementsNodeList,: inputs,
 *     required: true
 * });
 */
export function toggleRequiredInput({elementsNodeList, required }) {
    const elementsArray = Array.from(elementsNodeList);
    const invalidElements = [];

    if (typeof required !== "boolean") {
        warnError("toggleRequiredInput", {
            error: "The required value must be a boolean",
            received: typeof required
        });

        return;
    }

    if (elementsArray.length === 0) {
        warnError("toggleRequiredInput", {
            error: "The elements list is empty"
        });

        return;
    }

    elementsArray.forEach((element) => {
        if (!isRequiredInputElement(element)) {
            invalidElements.push(element);
        } else {
            element.required = required;
        }
    });

    if (invalidElements.length > 0) {
        warnError("toggleRequiredInput", {
            error: "The elements list contains invalid HTML elements",
            invalidElements
        });
    }
}



/**
 * Smoothly scrolls a DOM element into the viewport.
 *
 * This is a helper wrapper around `Element.scrollIntoView` that standardises
 * scrolling behaviour across the application.
 *
 * @param {HTMLElement} divElement
 * The DOM element to scroll into view.
 *
 * @returns {void}
 */
export function scrollToView(divElement) {
    divElement.scrollIntoView({
        behavior: "smooth",
        block: "end"
    });
}



/**
 * capitaliseEveryFirstWord
 *
 * Converts each word within a string to title case and joins the words using
 * the supplied separator.
 *
 * This utility is primarily intended for formatting display text before it is
 * rendered to the user interface.
 *
 * Example:
 *
 * ```javascript
 * capitaliseEveryFirstWord("john smith");
 * // "John, Smith"
 *
 * capitaliseEveryFirstWord("john smith", " ");
 * // "John Smith"
 * ```
 *
 * @param {string} text
 *     The string whose words should be converted to title case.
 *
 * @param {string} [separator=" "]
 *     The separator used when joining the capitalised words.
 *
 * @returns {string|undefined}
 *     A title-cased string joined using the supplied separator. Returns
 *     `undefined` when `text` is empty or not provided.
 *
 * @throws {TypeError}
 *     Thrown when `text` is not a string.
 */
export function capitaliseEveryFirstWord(text, separator =" ") {
    if (!text) return;

    if (typeof text !== "string") {
        throw new TypeError(`Expected a string got value with type ${typeof text}`)
    }

   const phrases = text.split(" ");

    const capitalisedPhrases = phrases.map((phrase) => {
        return toTitle(phrase);
    });

    return capitalisedPhrases.join(separator);

}



/**
 * Clears all HTML content from the given HTML element.
 *
 * @param {HTMLElement} htmlElement - The HTML element to clear.
 * @returns {void}
 */
export function clearInnerHTML(htmlElement) {
    if (!checkIfHTMLElement(htmlElement, "Html element")) {
        return;
    }

    htmlElement.innerHTML = "";
}




export function clearElementField(element) {
    if (!checkIfHTMLElement(element, "unknown", true)) return;

    element.textContent = "";
}
