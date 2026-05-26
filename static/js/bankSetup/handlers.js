import { sanitizeText } from "../utils.js";
import { warnError } from "../logger.js";



export function handleNameSanitization(e) {
    const includeChars = [" ", "&", "-", "'", "."];
    handleInputSanitization(e, includeChars);
}


export function handleAddressSanitization(e) {
    const includeChars = [" ",  "&",  "-",  "'",  "/",  ".",  ",", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ];
    handleInputSanitization(e, includeChars);
}


export function handlePostCode(e) {
    const includeChars = [" ",  "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];
     handleInputSanitization(e, includeChars);
}


function handleInputSanitization(e, includeChars, allowNumber=false) {

    if (!Array.isArray(includeChars)) {
        warnError( handleInputSanitization, {
            expected: "Expected the includeChars to be a list",
            received: `${typeof includeChars}`
        })
        return;
    }

    e.target.value = sanitizeText(e.target.value, false, true, includeChars)

}

