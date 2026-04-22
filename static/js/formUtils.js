import { compareTwoObjects } from "./utils.js";
import { logError } from "./logger.js";

/**
 * Parses FormData and extracts required fields, converting keys to camelCase.
 * 
 * @param {FormData} formData - The FormData object to be parsed.
 * @param {string[]} requiredFields - An array of field names that must be present in the FormData.
 * 
 * @returns {Object} An object containing the parsed data with keys converted to camelCase.
 * 
 * @throws {Error} If:
 *   - formData is not an instance of FormData.
 *   - requiredFields is not a non-empty array.
 *   - A required field is missing or its value is empty.
 * 
 * @example`
 * 
 * <form id="profileForm">
 *      <input type="text" name="first_name">
 *      <input type="email" name="email">
 *      <input type="tel" name="mobile">
 *  </form>
 * 
 * const formElement = document.getElementById("profileForm")
 * 
 * const formData = new FormData(profileForm);
 *
 * 
 * const requiredFields = ["first_name", "email", "mobile"];
 * const parsedData = parseFormData(formData, requiredFields);
 * console.log(parsedData); 
 * // Output: { firstName: "Alice", email: "alice@example.com", mobile: "1234567890" }
 */
export function parseFormData(formData, requiredFields = []) {

    if (!(formData instanceof FormData)) {
        throw new Error(`Expected a FormData object but got type ${typeof formData}`);
    }

    if (!Array.isArray(requiredFields)) {
        throw new Error(`The requiredFields argument must be an array, but got type: ${typeof requiredFields}`);
    }

    if (requiredFields.length === 0) {
        throw new Error(`The required Fields array is empty. Please provide at least one field name.`);
    }

    const result = {};

    for (const field of requiredFields) {
        const value = formData.get(field);
        
        if (!value) { 
            throw new Error(`Missing or empty required field: ${field}`);
        }
        
        const camelCaseField = field.toLowerCase().replace(/[-_](.)/g, (_, char) => char.toUpperCase());
        result[camelCaseField] = value;
    }

    return result;
}



/**
 * Populates an HTML form with data from a provided object.
 * 
 * This function takes an HTMLFormElement and a data object where the keys
 * match the `name` attributes of the form's input fields. The corresponding
 * values in the object are assigned as the values of those fields.
 * 
 * @param {HTMLFormElement} formElement - The form element to populate.
 * @param {Object} dataObject - An object containing form data as key-value pairs.
 *   The keys should match the `name` attributes of the form fields.
 * 
 * @throws {Error} If the provided `formElement` is not a valid HTMLFormElement.
 * 
 * @example
 * // HTML Form Example:
 * // <form id="profileForm">
 * //     <input type="text" name="first_name">
 * //     <input type="email" name="email">
 * //     <input type="tel" name="mobile">
 * // </form>
 * 
 * // JavaScript Usage Example:
 * const profileForm = document.getElementById("profileForm");
 * const formData = { 
 *     first_name: "Alice", 
 *     email: "alice@example.com", 
 *     mobile: "1234567890" 
 * };
 * 
 * populateForm(profileForm, formData);
 * 
 * // After execution, the form fields will have the following values:
 * // - first_name: "Alice"
 * // - email: "alice@example.com"
 * // - mobile: "1234567890"
 */
export function populateForm(formElement, dataObject) {
    if (!(formElement instanceof HTMLFormElement)) {
        throw new Error("Expected an HTMLFormElement.");
    }

    let populated = false;
    for (const [key, value] of Object.entries(dataObject)) {
    
        const input = formElement.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = value;
            if (!populated) {
                populated = true;
            }
        }
    }
    return populated;
}



export const profileCache = {
    _KEY: null,
    _CACHE_OBJECT: null,

    /**
     * Sets the key used for caching profile data.
     * This key is used to interact with both the in-memory cache and localStorage.
     */
    setStorageKey: (storageKey) => {  
        if (!storageKey || typeof storageKey !== "string") {
            throw new Error(`The storage key cannot be empty and must be a string. Got type: ${typeof storageKey}`);
        }
        profileCache._KEY = storageKey;
    },

    /**
     * Retrieves the cached profile data. 
     * If not in memory, attempts to fetch from localStorage.
     */
    getProfileData: () => {
        if (!profileCache._KEY) {
            throw new Error("The storage key is not set. Set the key before proceeding.");
        }

        if (profileCache._CACHE_OBJECT === null) {
            console.log("Fetching from localStorage...");
            profileCache._CACHE_OBJECT = getLocalStorage(profileCache._KEY);
        } else {
            console.log("Fetching from in-memory cache...");
        }

        return profileCache._CACHE_OBJECT;
    },

    /**
     * Adds or updates profile data in cache and localStorage.
     * @param {Object} profileData - The profile data to cache.
     * @returns {boolean} - True if the data was updated successfully, false otherwise.
     */
    addProfileData: (profileData) => {
        if (!profileCache._KEY) {
            throw new Error("The storage key is not set.");
        }

        if (typeof profileData !== "object" || profileData === null) {
            logError("addProfileData", "Invalid profile data. Expected a non-null object.");
            return false;
        }

        let previousData = profileCache.getProfileData();
        previousData     = Array.isArray(previousData) ? {} : previousData;
 
        try {
            const data = compareTwoObjects(previousData, profileData);
        
            if (!data.areEqual) {
                console.log("Saving to cache and localStorage...");
                try {
                    setLocalStorage(profileCache._KEY, profileData);
                    profileCache._CACHE_OBJECT = profileData;
                    return data;
                } catch (error) {
                    const errorMsg = `Failed to save to localStorage: ${error}`;
                    logError("addProfileData", errorMsg);
                    return null;
                }
            }
        } catch (error) {
            console.log(`Error comparing data: ${error}`);
            return null;
        }
      
        return false; 
    }
};



