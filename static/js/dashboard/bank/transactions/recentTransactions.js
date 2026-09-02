import { parseFormData } from "../../../formUtils.js";


const recentBankTransactionForm = document.getElementById("bank-transaction-form");



recentBankTransactionForm?.addEventListener("submit", handleForm);



function handleForm(e) {
    e.preventDefault();

    if (recentBankTransactionForm.checkValidity()) {

        const formData = new FormData(recentBankTransactionForm);
        const parsedData = parseFormData(formData, [
            "from_date",
            "to_date",
            "transaction_type"

        ])

        console.log(parsedData)

    } else {
        recentBankTransactionForm.reportValidity();
    }
}
