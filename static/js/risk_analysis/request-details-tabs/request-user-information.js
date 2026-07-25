import { ApplicationValidators } from "./validator.js";
import { toTitle, capitaliseEveryFirstWord } from "../../utils.js";
import { warnError } from "../../logger.js";


export class UserStatsAndProfileInformation extends ApplicationValidators{
    constructor(applicationData) {
        super(applicationData);

        this.validateResponse(applicationData);

        this.data = applicationData;
        this.elements = {
            fullName: document.getElementById("profile-information__fullName"),
            phoneNumber: document.getElementById("profile-information__phoneNum"),
            fullAddress: document.getElementById("profile-information__full-address"),
            email: document.getElementById("profile-information__email-address"),
            isEmailVerified: document.getElementById("profile-information__is-email-verified"),
            passport: document.getElementById("profile-information__passport"),
            isPassportVerified: document.getElementById("profile-information__is-passport-verified"),
            nationality: document.getElementById("profile-information__nationality"),
            prefferedLanguage: document.getElementById("profile-information__preferred-language"),
            totalAccounts: document.getElementById("total-accounts-value"),
            totalCards: document.getElementById("total-cards-value"),
            transactionsCount: document.getElementById("transactions-value"),
            accountBalance: document.getElementById("balance-value"),
            totalApplications: document.getElementById("total-application-value")

        }

        this.validateElements(this.elements);
    }


    /**
     * mapVerificationStatusToCSSStatus
     *
     * Maps a boolean verification status to a visual CSS status representation
     * and updates the supplied DOM element with the corresponding display text
     * and CSS classes.
     *
     * This method separates the verification value from the DOM element:
     *
     * - `isVerified` represents the data state returned from the backend.
     * - `statusElement` represents the UI element that should be updated.
     *
     * A verified state applies the "approved" CSS status and displays "Verified".
     * An unverified state applies the "rejected" CSS status and displays
     * "Unverified".
     *
     * Example:
     *
     * ```javascript
     * this.#mapVerificationStatusToCSSStatus(
     *     true,
     *     this.elements.emailVerification
     * );
     *
     * // Updates the element:
     * // textContent: "Verified"
     * // className: "status status--approved"
     * ```
     *
     * @param {boolean} isVerified
     *     The verification state received from the application data.
     *
     * @param {HTMLElement} statusElement
     *     The DOM element that displays the verification status.
     *
     * @returns {void}
     *
     * @throws {TypeError}
     *     Throws an error when `isVerified` is not a boolean or when the supplied
     *     DOM element is invalid.
     */
    #mapVerificationStatusToCSSStatus(isVerified, statusElement) {

        if (typeof isVerified !== "boolean") {
            warnError("mapVerificationStatusToCSSStatus", {
                error: "The verification status parameter is not a boolean",
                returnType: typeof isVerified,
            });
            return;
        }

        if (!statusElement) {
            throw new TypeError(
                "Expected a valid DOM element for verification status rendering."
            );
        }

        const cssStatus = isVerified ? "approved" : "rejected";

        statusElement.textContent = isVerified
            ? "Verified"
            : "Unverified";

        statusElement.className = `status status--${cssStatus}`;
        }


    #setProfileInformation() {
        const profile = this.data.PROFILE_INFORATION;
        const phoneNumber = this.data.PROFILE_INFORATION.PHONE_NUMBER

        this.elements.fullName.textContent = capitaliseEveryFirstWord(profile.FULL_NAME);
        this.elements.phoneNumber.textContent = `+${phoneNumber.COUNTRY_CODE} ${phoneNumber.NATIONAL_NUMBER}`;
        this.elements.fullAddress.textContent  = capitaliseEveryFirstWord(profile.ADDRESS);
        this.elements.email.textContent  = profile.EMAIL_ADDRESS.EMAIL;
        this.elements.passport.textContent = profile.PASSPORT.PASSPORT;
        this.elements.nationality.textContent = profile.NATIONALITY;
        this.elements.prefferedLanguage.textContent = profile.PREF_LANGUAGE;

        this.#mapVerificationStatusToCSSStatus(profile.EMAIL_ADDRESS.IS_VERIFIED, this.elements.isEmailVerified);
        this.#mapVerificationStatusToCSSStatus(profile.PASSPORT.IS_VERIFIED, this.elements.isPassportVerified)
    }


    #setUserStats() {
        this.elements.totalAccounts.textContent      = this.data.USER_STATS.TOTAL_ACCOUNTS;
        this.elements.totalCards.textContent         = this.data.USER_STATS.TOTAL_CARDS;
        this.elements.transactionsCount.textContent  = this.data.USER_STATS.TOTAL_TRANSACTIONS;
        this.elements.accountBalance.textContent     = this.data.USER_STATS.ACCOUNT_BALANCE;
        this.elements.totalApplications.textContent  = this.data.USER_STATS.TOTAL_APPLICATIONS;
    }


    render() {
        this.#setProfileInformation();
        this.#setUserStats();

    }
}
