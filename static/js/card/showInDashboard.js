import fetchData from "../fetch.js";
import { AlertUtils } from "../alerts.js";
import { getCsrfToken } from "../security/csrf.js";


const dashboardTransferSection = document.getElementById("dashboard-transfer");
const numOfCardSelected        = document.getElementById("num-of-card-selected");



dashboardTransferSection?.addEventListener("click", handleDelegation);



function handleDelegation(e) {
    const checkboxValue = e.target.closest("input[type='checkbox']");

    if (checkboxValue === null) return;

    const cardNumber = e.target.dataset.cardNumber;
    handleCardDashboardToggle(checkboxValue.checked, cardNumber);

}


async function handleCardDashboardToggle(checkMarkValue, cardNumber) {

    const resp = await fetchData({
        url: "/cards/add-to-dashboard/",
        csrfToken: getCsrfToken(),
        body: {
            display_in_dashboard: checkMarkValue,
            card_number: cardNumber
        },
        method: "POST",

    })

    const data = resp.data;

    if (resp && data.SUCCESS) {
        AlertUtils.showAlert({
            title: data.ACTION,
            text: data.SUCCESS_MSG,
            icon: "success",
            confirmButtonText: "Ok!",
        })

        numOfCardSelected.textContent = data.NUM_OF_CARDS_IN_DASHBOARD;
        return;
    };

      AlertUtils.showAlert({
            title: "Error",
            text: "Something went wrong, please try again later!",
            icon: "error",
            confirmButtonText: "Ok!",
        })
        return;




}
