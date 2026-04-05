import PasswordStrengthChecker from "./passwordStrengthChecker.js";



/**
 * A resuable class that Handles frontend password validation, strength checking, and UI feedback.
 *
 * This class:
 * - Validates password strength rules (length, uppercase, lowercase, etc.) and displays in the UI. Note
 * in order to validate the password strength rules, it must be used with `PasswordStrengthChecker` class,
 * this class is responsible for the actually validating, and without that no validation takes places.
 * 
 * - Checks password and confirm-password matching
 * - Controls the visibility of the password strength board
 * 
 *
 * Usage pattern:
 * 1. Instantiate the class
 * 2. Configure DOM elements via fluent setters
 * 3. Call `startEventListener()` to activate behaviour
 *
 * Designed for server-rendered pages (e.g. Django),
 * where a full page reload cleans up event listeners automatically.
 * It can be used for SPA but it won't manually cleanup the event listeners
 * you will need to handle the removal of event listeners manually
 */
export default class CheckFrontEndPasswordStrength {
    #hasCapitalElement;
    #hasLowercaseElement;
    #hasNumberElement;
    #hasMinLengthElement;
    #hasSpecialElement;
    #doPasswordsMatchElement;
    #passwordFieldElement;
    #confirmPasswordFieldElement;
    #validCSSRule;
    #invalidCSSRule;
    #passwordStrengthChecker;
    #passwordFieldMsg;
    #confirmPasswordFieldMsg;
    #activePasswordField;
    #passwordStrengthBoardElement;
    #displayPasswordStrengthBoardClassName;

    /**
     * Creates a new password strength controller.
     *
     * @param {string} passwordFieldMsg - Message shown when the password field is active
     * @param {string} confirmPasswordFieldMsg - Message shown when the confirm password field is active
     */
    constructor(
        passwordFieldMsg        = "Currently using password field",
        confirmPasswordFieldMsg = "Currently using confirm password field"
    ) {
        this.#passwordStrengthChecker = new PasswordStrengthChecker();
        this.#passwordFieldMsg = passwordFieldMsg;
        this.#confirmPasswordFieldMsg = confirmPasswordFieldMsg;
    }

   
    /**
     * Starts all DOM event listeners.
     *
     * This method must be called only after all required DOM elements
     * have been configured via the setter methods.
     *
     * Throws an error if required fields are missing to fail fast.
     */
    startEventListener() {
        if (!this.#passwordFieldElement || !this.#confirmPasswordFieldElement) {
            throw new Error("Password fields must be set before starting listeners.");
        }

        console.log("Password strength listeners started.");

        // bind the password field first
        this.#bindEvents(this.#passwordFieldElement, {
            input: () => this.#handlePasswordFieldValidation({
                fieldMessage: this.#passwordFieldMsg,
                passwordField: this.#confirmPasswordFieldElement,
                fieldToCheck: this.#passwordFieldElement
            }),

            click: () => this.#handlePasswordFieldValidation({
                fieldMessage: this.#passwordFieldMsg,
                passwordField: this.#confirmPasswordFieldElement,
                fieldToCheck: this.#passwordFieldElement,
                isFieldClicked: true
            }),

            focus: () => this.#showPasswordStrengthBoard(),
            blur: () => this.#hidePasswordStrengthBoardIfEmpty()
        });

        // bind the confirm password field 
        this.#bindEvents(this.#confirmPasswordFieldElement, {
            input: () => this.#handlePasswordFieldValidation({
                fieldMessage: this.#confirmPasswordFieldMsg,
                passwordField: this.#passwordFieldElement,
                fieldToCheck: this.#confirmPasswordFieldElement
            }),

            click: () => this.#handlePasswordFieldValidation({
                fieldMessage: this.#confirmPasswordFieldMsg,
                passwordField: this.#passwordFieldElement,
                fieldToCheck: this.#confirmPasswordFieldElement,
                isFieldClicked: true
            }),

            focus: () => this.#showPasswordStrengthBoard(),
            blur: () => this.#hidePasswordStrengthBoardIfEmpty()
        });
    }

    /**
     * Binds multiple DOM events to an element using a declarative mapping.
     * This ensurs that it belongs to the class
     *
     * @param {HTMLElement} element - Target element
     * @param {Object<string, Function>} handlers - Event-to-handler map
     */
    #bindEvents(element, handlers) {
        if (!(element instanceof HTMLElement)) {
            throw new Error("Expected HTMLElement for event binding.");
        }

        for (const [event, handler] of Object.entries(handlers)) {
            element.addEventListener(event, handler);
        }
    }

     /**
     * Coordinates password validation and UI updates for a single interaction.
     *
     * @param {Object} params
     * @param {string} params.fieldMessage - Active field message
     * @param {HTMLInputElement} params.passwordField - Opposing password field
     * @param {HTMLInputElement} params.fieldToCheck - Field currently being validated
     * @param {boolean} [params.isFieldClicked=false] - Indicates whether the field was clicked
     */
    #handlePasswordFieldValidation({
        fieldMessage,
        passwordField,
        fieldToCheck,
        isFieldClicked = false
    }) {
        this.#passwordStrengthHelper(fieldToCheck, fieldMessage);
        this.#doPasswordMatch(passwordField.value, fieldToCheck.value);
        this.#showPasswordStrengthBoard(isFieldClicked);
    }

    /**
     * Displays the password strength board when appropriate.
     *
     * @param {boolean} isFieldClicked - Whether the field was explicitly clicked
     */
    #showPasswordStrengthBoard(isFieldClicked = true) {
        if (!this.#passwordStrengthBoardElement) return;

        if (isFieldClicked) {
            this.#passwordStrengthBoardElement.classList.add(
                this.#displayPasswordStrengthBoardClassName
            );
        }
    }

    /**
     * Hides the password strength board if both password fields are empty.
     */
    #hidePasswordStrengthBoardIfEmpty() {
        if (!this.#passwordStrengthBoardElement) return;

        if (
            !this.#passwordFieldElement.value &&
            !this.#confirmPasswordFieldElement.value
        ) {
            this.#passwordStrengthBoardElement.classList.remove(
                this.#displayPasswordStrengthBoardClassName
            );
        }
    }

    /**
     * Checks whether the password and confirm-password values match.
     *
     * @param {string} password
     * @param {string} confirmPassword
     * @returns {boolean} Whether the passwords match
     */
    #doPasswordMatch(password, confirmPassword) {
        const match = password && password === confirmPassword;

        this.#doPasswordsMatchElement?.classList.toggle(this.#validCSSRule, match);
        this.#doPasswordsMatchElement?.classList.toggle(this.#invalidCSSRule, !match);

        return match;
    }

     /**
     * Performs password strength validation and updates UI indicators.
     *
     * @param {HTMLInputElement} passwordInputField - Field containing the password
     * @param {string} msg - Message to display for the active field
     */
    #passwordStrengthHelper(passwordInputField, msg) {
        const password = passwordInputField.value;

        this.#passwordStrengthChecker.setPassword(password);
        const report = this.#passwordStrengthChecker.checkPasswordStrength();

        this.#activePasswordField?.classList.add(this.#validCSSRule);

        if (this.#activePasswordField?.innerText) { this.#activePasswordField.innerText = msg;}

        this.#updateRequirement(this.#hasCapitalElement, report.HAS_AT_LEAST_ONE_UPPERCASE);
        this.#updateRequirement(this.#hasLowercaseElement, report.HAS_AT_LEAST_ONE_LOWERCASE);
        this.#updateRequirement(this.#hasSpecialElement, report.HAS_AT_LEAST_ONE_SPECIAL_CHARS);
        this.#updateRequirement(this.#hasNumberElement, report.HAS_AT_LEAST_ONE_NUMBER);
        this.#updateRequirement(this.#hasMinLengthElement, report.HAS_AT_LEAST_LENGTH_CHARS);
    }

    /**
     * Toggles CSS classes for a single password requirement.
     *
     * @param {HTMLElement|null} element - Requirement indicator element
     * @param {boolean} isMet - Whether the requirement is satisfied
     */
    #updateRequirement(element, isMet) {
        if (!element) return;

        element.classList.toggle(this.#validCSSRule, isMet);
        element.classList.toggle(this.#invalidCSSRule, !isMet);
    }

   
     /**
     * Sets the password input field by element ID.
     *
     * @param {string} id
     * @returns {this}
     */
    setPasswordFieldElementId(id) {
        this.#passwordFieldElement = this.#getElementById(id);
        return this;
    }

    /**
     * Sets the confirm-password input field by element ID.
     *
     * @param {string} id
     * @returns {this}
     */
    setConfirmPasswordFieldElementId(id) {
        this.#confirmPasswordFieldElement = this.#getElementById(id);
        return this;
    }

    /** Sets the uppercase requirement indicator element. */
    setHasCapitalElementId(id) {
        this.#hasCapitalElement = this.#getElementById(id);
        return this;
    }

    /** Sets the lowercase requirement indicator element. */
    setHasLowercaseElementId(id) {
        this.#hasLowercaseElement = this.#getElementById(id);
        return this;
    }

    /** Sets the numeric requirement indicator element. */
    setHasNumberElementId(id) {
        this.#hasNumberElement = this.#getElementById(id);
        return this;
    }

    /** Sets the minimum length requirement indicator element. */
    setHasMinLengthElementId(id) {
        this.#hasMinLengthElement = this.#getElementById(id);
        return this;
    }

    /** Sets the special character requirement indicator element. */
    setHasSpecialElementId(id) {
        this.#hasSpecialElement = this.#getElementById(id);
        return this;
    }

    /** Sets the password-match indicator element. */
    setDoPasswordsMatchElementId(id) {
        this.#doPasswordsMatchElement = this.#getElementById(id);
        return this;
    }

    /** Sets the active password field message element. */
    setActivePasswordFieldId(id) {
        this.#activePasswordField = this.#getElementById(id);
        return this;
    }

    /** Sets the password strength board container element. */
    setPasswordStrengthBoardId(id) {
        this.#passwordStrengthBoardElement = this.#getElementById(id);
        return this;
    }

    /**
     * Sets the CSS class used to show the password strength board.
     */
    setPasswordStrengthDisplayBoardCssSelector(className) {
        this.#validateString(className);
        this.#displayPasswordStrengthBoardClassName = className;
        return this;
    }

    /** Sets the CSS class for valid states. */
    setValidCSSRuleId(rule) {
        this.#validateString(rule);
        this.#validCSSRule = rule;
        return this;
    }

    /** Sets the CSS class for invalid states. */
    setInvalidCSSRuleId(rule) {
        this.#validateString(rule);
        this.#invalidCSSRule = rule;
        return this;
    }

  
     /**
     * Retrieves and validates an element by ID.
     *
     * @param {string} id
     * @returns {HTMLElement}
     */
    #getElementById(id) {
        this.#validateString(id);

        const element = document.getElementById(id);
        if (!(element instanceof HTMLElement)) {
            throw new Error(`Expected HTMLElement with id "${id}"`);
        }

        return element;
    }

    /**
     * Validates that a value is a string.
     *
     * @param {*} value
     */
    #validateString(value) {
        if (typeof value !== "string") {
            throw new Error(`Expected string but got ${typeof value}`);
        }
    }
}
