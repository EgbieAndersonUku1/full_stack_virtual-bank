const dashboardTransferSection = document.getElementById("dashboard-transfer");

const csrfToken = document.getElementById("csrf_token");
console.log(csrfToken);

dashboardTransferSection?.addEventListener("click", handleDelegation);



function handleDelegation(e) {
    const checkboxElement = e.target.closest("input[type='checkbox']");

    if (checkboxElement === null) return;
    console.log(checkboxElement.checked)
}



