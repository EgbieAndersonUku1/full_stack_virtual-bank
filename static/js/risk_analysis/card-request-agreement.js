import { AlertUtils } from "../alerts.js";
import fetchData from "../fetch.js";
import { getCsrfToken } from "../security/csrf.js";


const agreementForm = document.getElementById("review-agreement-form");


agreementForm?.addEventListener("submit", handleAgreementSubmitForm)



async function get_card_request_completion_status() {

    const url = "/card-request/is_all_stages_complete/"
    const resp = await fetchData({
        url: url,
        csrfToken: getCsrfToken(),
        body: {},
        method: "POST"
    })

    return resp.data;

}

/**
 * Handles submission of the agreement form.
 *
 * The function does a couple of things: validates the form and checks that
 * both the card request and employment sections have been completed before
 * allowing the application to be submitted. If any required information is
 * missing, an appropriate alert is displayed.
 *
 * Once the user acknowledges the submission confirmation, the saved session data
 * is cleared and the user is redirected to the credit card management page.
 *
 * @async
 * @param {SubmitEvent} e - The form submit event.
 * @returns {Promise<void>}
 */
async function handleAgreementSubmitForm(e) {
   
    e.preventDefault();

    if (!agreementForm.reportValidity()) {
        return;
    }

    const data = await get_card_request_completion_status();

    if (!data.IS_PERSONAL_INFORMATION_COMPLETE) {
        AlertUtils.showAlert({
            title: "Card Request Incomplete",
            text: data.STAGE_1_ERROR_MSG,
            icon: "error",
            confirmButtonText: "Ok!"
        });
        return;
    }

    if (!data.IS_EMPLOYMENT_INFORMATION_COMPLETE) {
        AlertUtils.showAlert({
            title: "Employment Details Incomplete",
            text: data.STAGE_2_ERROR_MSG,
            icon: "error",
            confirmButtonText: "Ok!"
        });
        return;
    }

    if (!data.SUCCESS) {
        return;
    }

    const isClicked = await AlertUtils.showConfirmationAlert({
        title: "Application Submitted",
        text: data.SUCCESS_MSG,
        icon: "success",
        confirmButtonText: "Submit request",
        denyButtonText: "Don't sumbit!",
        cancelMessage: "No action taken",
        messageToDisplayOnSuccess: "Great, your application has been submitted",
    });



    if (isClicked ) {
        agreementForm.submit();
    }
}