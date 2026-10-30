import { deselectAllTabs, highlightTab } from "../utils/tab-utils.js";
import { AlertUtils } from "../alerts.js";
import { checkIfHTMLElement, toTitle } from "../utils.js";
import { NotificationSummaryCard } from "./notficationCards.js";
import { warnError } from "../logger.js";
import { simulateDivContentUpdate } from "./simulator.js";


const notificationTabs = document.querySelectorAll(".tab");
const notificationAll = document.getElementById("notifications__all");
const notificationUnread = document.getElementById("notifications__unread");
const notificationRead = document.getElementById("notifications__read");
const notificationsStatus =  document.querySelectorAll(".notification-row .notification-row__footer p:nth-of-type(2)")

// Notification summary cards
const notificationCardUnRead = document.getElementById("notifications__card_unread");
const notificationCardRead   = document.getElementById("notifications__card_read");

const notificationCardUnreadSummary = new NotificationSummaryCard(notificationCardUnRead);
const notificationCardReadSummary   = new NotificationSummaryCard(notificationCardRead);

notificationCardReadSummary.init();
notificationCardUnreadSummary.init();


document.addEventListener("click", handleDelegation);

const notifications = {
    read: "read",
    unread: "unread",
    all: "all",
    markAsRead: "mark-all-as-read",
    markAsUnread: "mark-all-as-unread"
};


const isMarkedState = {
    MARK_AS_READ: false,
    MARK_AS_UNREAD: false,
}


const notificationTabsArray = [
        notifications.read,
        notifications.unread,
        notifications.all,
        notifications.markAsRead,
        notifications.markAsUnread
    ];


const currentSection = {
    isInReadSection: false,
    isUnReadSection: false
}



function hideAllTabInformation() {
    const notificationSections = [
        notificationAll,
        notificationUnread,
        notificationRead
    ];

    const notificationTabsElement = [
        notificationAll,
        notificationRead,
        notificationRead
    ]

    if (notificationSections.length !== notificationTabsElement.length){
        throw new Error("The notificationSection Array and notifcationTabsElement must have the same length")
    }


    notificationSections.forEach((section, index) => {
        if (!section) return;


        section.style.display = "none";
        // turn off the aria-press for notifications tab button
        notificationTabsElement[index].setAttribute("aria-pressed", "false");


    });
}


function showNotificationContent(notificationElement) {
    checkIfHTMLElement(notificationElement);
    notificationElement.style.display = "block";
}



function showNotificationElement(notificationElement, notificationTabElement) {

    checkIfHTMLElement(notificationTabElement);
    showNotificationContent(notificationElement);

    notificationTabElement.setAttribute("aria-pressed", "true");

}



function hideNotificationElement(notificationElement) {
    checkIfHTMLElement(notificationElement);
    notificationElement.style.display = "none";
}



function handleNotificationUnRead(tabElement) {
    showNotificationElement(notificationUnread, tabElement);
}



function handleNotificationAll(tabElement) {
    showNotificationElement(notificationAll, tabElement);
}



function handleNotificationRead(tabElement) {
    showNotificationElement(notificationRead, tabElement);
}




/**
 * Updates the status of all notifications and refreshes the summary card counts.
 *
 * Validates the requested status, updates notification status labels where
 * necessary, and synchronises the Read and Unread summary card counts.
 *
 * @param {Object} options - Configuration for the notification status update.
 * @param {string} options.callingFunctionName - Name of the calling function, used for error reporting.
 * @param {string} options.status - Target status ("read" or "unread").
 * @param {number} options.notificationReadCount - Updated count of read notifications.
 * @param {number} options.notificationUnreadCount - Updated count of unread notifications.
 *
 * @returns {boolean|undefined} Returns true on success, or undefined if the
 * notification status container is not found.
 *
 * @throws {Error} If the status or calling function name is invalid.
 * @throws {TypeError} If either notification count is not a finite number.
 */
function updateNotificationsStatus({
        callingFunctionName,
        status,
        notificationReadCount,
        notificationUnreadCount
    }) {

    if (!notificationsStatus) {
        warnError(callingFunctionName, "Notification status container was not found.");
        return;
    }

    if (typeof status !== "string") {
        throw new Error(
            `Status must be a string. Received ${typeof status}.`
        );
    }

    if (typeof callingFunctionName !== "string") {
        throw new Error(
            `callingFunctionName must be a string. Received ${typeof callingFunctionName}.`
        );
    }

    const NOTIFICATION_STATUS = [notifications.read, notifications.unread];
    const normalisedStatus = status.toLowerCase();

    if (!NOTIFICATION_STATUS.includes(normalisedStatus)) {
        throw new Error(
            `Status must be either "read" or "unread". Received "${status}".`
        );
    }


    notificationsStatus.forEach(notification => {
        const msgStatus = notification.lastChild.textContent.toLowerCase().trim();

        if (msgStatus !== normalisedStatus) {
            notification.lastChild.textContent = toTitle(normalisedStatus);
        }
    });

    notificationCardUnreadSummary.count = notificationUnreadCount;
    notificationCardReadSummary.count   = notificationReadCount;

    return true;
}




async function markNotificationStatusAsUnRead(){

    if (isMarkedState.MARK_AS_UNREAD) {
        AlertUtils.showAlert({
            title: "Already marked as unread",
            text: "You have already marked the notifications as unread",
            icon: "info",
            confirmButtonText: "Ok",
        })
        return
    }

    const confirmation = await AlertUtils.showConfirmationAlert({
        title: "Mark all notification as unread?",
        text: "Are you sure you want to mark all notifications as unread?",
        icon: "info",
        messageToDisplayOnSuccess: "All notifications marked as unread.",
        cancelMessage: "No action taken",
        confirmButtonText: "Mark as unread",
        denyButtonText: "Do nothing!"
    });

    if (!confirmation) return;

    updateNotificationsStatus({
        callingFunctionName: "markNotificationStatusAsUnread",
        status: notifications.unread,
        notificationUnreadCount: 6,
        notificationReadCount: 0,
    })

    hideNotificationElement(notificationRead);

    simulateDivContentUpdate(notificationUnread, notificationAll);


    isMarkedState.MARK_AS_UNREAD = true;
    isMarkedState.MARK_AS_READ   = false;

    // Updates the unread tab content dynamically so newly unread notifications appear
    // immediately without reloading the page or switching tabs only when the user is in that
    // tab section.

    if (currentSection.isUnReadSection) {
         showNotificationContent(notificationUnread);
    }


}



async function markNotificationStatusAsRead(){

    if (isMarkedState.MARK_AS_READ) {
        AlertUtils.showAlert({
            title: "Already marked as read",
            text: "You have already marked the notifications as read",
            icon: "info",
            confirmButtonText: "Ok",
        })
        return
    }

    const confirmation = await AlertUtils.showConfirmationAlert({
        title: "Mark all notifications as read?",
        text: "Are you sure you want to mark all notifications as unread?",
        icon: "info",
        messageToDisplayOnSuccess: "All notifications marked as read.",
        cancelMessage: "No action taken",
        confirmButtonText: "Mark as read",
        denyButtonText: "Do nothing!"
    });

    if (!confirmation) return;

    updateNotificationsStatus({
        callingFunctionName: "markNotificationStatusAsUnread",
        status: notifications.read,
        notificationUnreadCount: 0,
        notificationReadCount: 6,
    })

    hideNotificationElement(notificationUnread);
    simulateDivContentUpdate(notificationRead, notificationAll);


    isMarkedState.MARK_AS_READ   = true;
    isMarkedState.MARK_AS_UNREAD = false;

     // Updates the Read tab content dynamically so newly read notifications appear
    // immediately without reloading the page or switching tabs only when the user is in that
    // tab section..
    if (currentSection.isInReadSection) {
        showNotificationContent(notificationRead);
    }


}



function activateNotificationTab(tab) {
    deselectAllTabs(notificationTabs, "notification-active");
    hideAllTabInformation();

    tab.setAttribute("aria-pressed", "true");
    highlightTab(tab, "notification-active");



}



function handleDelegation(e) {
    const tab = e.target.closest(".tab");

    if (!tab) return;

    const tabInfo = tab.dataset.info;

    if (!notificationTabsArray.includes(tabInfo)) return;

    switch (tabInfo) {
        case notifications.all:
            activateNotificationTab(tab);
            handleNotificationAll(tab);
            highlightTab(tab, "notification-active")
            break;

        case notifications.read:
            activateNotificationTab(tab);

            if (!isMarkedState.MARK_AS_UNREAD) {
                handleNotificationRead(tab);
            }

            currentSection.isInReadSection = true;
            currentSection.isUnReadSection = false
            break;

        case notifications.unread:
            activateNotificationTab(tab);
            if (!isMarkedState.MARK_AS_READ) {
                handleNotificationUnRead(tab);
            }
            currentSection.isInReadSection = false;
            currentSection.isUnReadSection = true
            break;

        case notifications.markAsUnread:
            markNotificationStatusAsUnRead()
            break;

        case notifications.markAsRead:
            markNotificationStatusAsRead();
            break;
    }
}




