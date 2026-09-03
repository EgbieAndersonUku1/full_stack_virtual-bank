import { parseFormData } from "../../../formUtils.js";
import fetchData from "../../../fetch.js";
import { getCsrfToken } from "../../../security/csrf.js";
import { warnError } from "../../../logger.js";

const recentBankTransactionForm = document.getElementById("bank-transaction-form");



recentBankTransactionForm?.addEventListener("submit", handleForm);



async function handleForm(e) {
    e.preventDefault();

    if (recentBankTransactionForm.checkValidity()) {

        const formData = new FormData(recentBankTransactionForm);
        const parsedData = parseFormData(formData, [
            "from_date",
            "to_date",
            "account_type",
            "movement",
            "status"

        ])

        if (!parsedData) {
            warnError("handleForm", {
                error:"Parsed data for the form data return none"
            });
            return;
        }

        console.log(parsedData)

        const data = await fetchData({
            url: "/dashboard/search/recent_transactions/",
            csrfToken: getCsrfToken(),
            body: {
                from_date: parsedData.fromDate,
                to_date: parsedData.toDate,
                account_type: parsedData.accountType,
                movement: parsedData.movement,
                status: parsedData.status,
            },
            method: "POST",

        })

        console.log(parsedData)

    } else {
        recentBankTransactionForm.reportValidity();
    }
}
