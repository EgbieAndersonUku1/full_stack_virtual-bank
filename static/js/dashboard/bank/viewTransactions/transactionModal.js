import { dimBackground, toggleElement } from "../../../utils.js";


const viewBankTransacionPanel = document.getElementById("bank-account-view-transactions");

const dimBackgroundElement = document.getElementById("dim");



export const ViewTransactionsModal = (() => {
    const viewTransactionButtonId = "view-transaction-btn";
    const closePanelId = "close-transaction-panel";

    function showPanel() {
        toggleElement({ element: viewBankTransacionPanel });
        dimBackground(dimBackgroundElement, true);
    }

    function hidePanel() {
        toggleElement({ element: viewBankTransacionPanel, show: false });
        dimBackground(dimBackgroundElement, false);
    }

    function handleEvent(e) {

        const clickedViewBtn = e.target.closest(`#${viewTransactionButtonId}`);
        const clickedCloseBtn = e.target.closest(`#${closePanelId}`);


        if (!clickedViewBtn && !clickedCloseBtn) return;


        if (e.target.id === viewTransactionButtonId) {

            showPanel();
            return;

        }

        if (closePanelId) {
            hidePanel();
            return;
        }


    }

    return {
        handleEvent
    }

})()
