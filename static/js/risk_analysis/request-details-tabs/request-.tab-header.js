/**
 * RequestHeader
 *
 * Responsible for rendering the header section of a card request application
 * within the admin application view.
 *
 * This class receives application data, validates the expected structure,
 * retrieves the required DOM elements, and updates the header UI with
 * applicant information and application metadata.
 *
 * Responsibilities:
 * - Validate incoming application data.
 * - Validate required DOM elements exist before rendering.
 * - Display the applicant's profile picture, full name, and email address.
 * - Display application ID, submission date, and current status.
 * - Apply status-specific styling and accessibility attributes.
 * - Render all header information to the page.
 *
 * Expected data structure:
 *
 * {
 *     APPLICATION_ID: String,
 *     SUBMISSION_DATE: ISO Date String,
 *     STATUS: String,
 *     USER_INFORMATION: {
 *         FULL_NAME: String,
 *         EMAIL_ADDRESS: String,
 *         PROFILE_PIC: String
 *     }
 * }
 *
 * Usage:
 *
 * const requestHeader = new RequestHeader(applicationData);
 * requestHeader.render();
 *
 */



/**
 * RequestHeader
 *
 * Represents the header renderer for a card request application within the
 * administration dashboard.
 *
 * This class is responsible for taking a validated application data object
 * and rendering the applicant's profile information and application metadata
 * into the corresponding header DOM elements.
 *
 * The class does not handle data retrieval or API communication. It assumes
 * that application data has already been fetched and passed into the class.
 *
 * Responsibilities:
 * - Store application header data.
 * - Validate required application data structure.
 * - Validate required DOM elements exist before rendering.
 * - Render applicant profile information.
 * - Render application metadata such as ID, submission date, and status.
 * - Apply status-related styling and accessibility attributes.
 *
 * Example:
 *
 * const requestHeader = new RequestHeader(applicationData);
 * requestHeader.render();
 *
 */

import { ApplicationValidators } from "./validator.js";

export class RequestHeader extends ApplicationValidators {

    constructor(applicationData) {
        super(applicationData);
        
        this.validateResponse(applicationData);

        this.data = applicationData;

        this.elements = {
            profilePic: document.getElementById("request-status-profile-pic"),
            profileName: document.getElementById("full-name"),
            profileEmail: document.getElementById("profile-email"),
            applicationId: document.getElementById("application-id"),
            status: document.getElementById("current-status"),
            submissionDate: document.getElementById("application-submission-date"),
        };

        this.validateElements();
    }


    #setApplicationId() {
        this.elements.applicationId.textContent = `Application ID  (${this.data.APPLICATION_ID})`

    }

    #setApplicationSubmissionDateTime() {
        const submissionDate = new Date(this.data.SUBMISSION_DATE).toLocaleDateString();
        this.elements.submissionDate.textContent = `Submission date: ${submissionDate}`;
    }

    #setProfileName() {
        this.elements.profileName.textContent = this.data.USER_INFORMATION.FULL_NAME;
    }

    #setProfileEmail() {
        this.elements.profileEmail.textContent = this.data.USER_INFORMATION.EMAIL_ADDRESS;
    }

    #setApplicationCurrentStatus() {

        const applicationStatus = this.data.STATUS;
        this.elements.status.textContent = applicationStatus;
        this.elements.status.className = `status status--${applicationStatus} capitalise center`;
        this.elements.status.ariaLabel = `Current status: ${applicationStatus}`;
    }

    #setProfilePicPath() {

        this.elements.profilePic.src = this.data.USER_INFORMATION.PROFILE_PIC;

    }

    render() {
        this.#setProfilePicPath();
        this.#setProfileName();
        this.#setProfileEmail();
        this.#setApplicationCurrentStatus();
        this.#setApplicationId();
        this.#setApplicationSubmissionDateTime();
    }
}
