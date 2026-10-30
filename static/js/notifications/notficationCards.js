import { checkIfHTMLElement } from "../utils.js";



/**
 * Design decision:
 *
 * Initialisation is deliberately separated from construction. The
 * constructor stores the card element and sets the initial state,
 * and the init() method performs the DOM queries and caches the
 * results in private fields for subsequent use.
 *
 * This separation is by design, keeps the constructor lightweight and gives the
 * caller explicit control over when DOM queries are performed,
 * rather than executing them automatically whenever a new instance
 * is created.
 *
 * For example, consider an example where four four notification summary cards are created:
 *
 * const notificationAll = new NotificationSummaryCard(notificationAllElement);
 * const notificationRead = new NotificationSummaryCard(notificationReadElement);
 * const notificationUnread = new NotificationSummaryCard(notificationUnreadElement);
 * const notificationToday = new NotificationSummaryCard(notificationTodayElement);
 *
 * All four instances can be constructed first and initialised
 * explicitly when required.
 *
 * Although DOM queries are generally very fast and would not
 * realistically take a second each, this example illustrates the
 * distinction between constructing an instance and initialising it.
 *
 * By performing the queries in init(), rather than in the constructor,
 * the class allows the caller to control when initialisation occurs.
 * The queried elements are then cached in private fields so they can
 * be reused without querying the DOM again whenever those elements
 * are accessed.
 *
 * This approach prioritises explicit control over initialisation
 * and the reuse of cached DOM references, rather than assuming
 * that DOM queries are inherently slow.
 */
export class NotificationSummaryCard {

    #cardElement;
    #isInitialised;
    #img;
    #title;
    #count;
    #msg;

    constructor(cardElement) {
        checkIfHTMLElement(cardElement, "notification card summary");
        this.#cardElement   = cardElement;
        this.#isInitialised = false;
        this.#img           = null;
        this.#title         = null;
        this.#count         = null;
        this.#msg           = null;

    }

    #ensureInitialised() {
        if (!this.#isInitialised) {
            throw new Error(
                "NotificationSummaryCard has not been initialized. Call init() first."
            );
        }
    }

    /**
     * Initialises the notification summary card by querying the card element
     * for its image, title, notification count and subtitle message.
     *
     * The retrieved values are stored in private fields for subsequent use.
     * The title and subtitle are trimmed of leading and trailing whitespace,
     * while the notification count is converted to a number.
     *
     * Once all summary elements have been retrieved successfully, the
     * instance is marked as initialised by setting #isInitialised to true.
     *
     * @throws {Error} If one or more required summary elements are missing.
     */
    init() {
        this.#img = this.#cardElement.querySelector(".icon img");
        const [titleElement, countElement, subtitleElement] = this.#cardElement.querySelectorAll(".notification-card__msg p");

        if (titleElement === null || countElement === null || subtitleElement === null) {
            throw new Error(`One or more of the summary elements for the cards are missing:
                             titleElement: ${titleElement}
                             countElment: ${countElement}
                             subtitleElement: ${subtitleElement}
                             `)
        }


        this.#title = titleElement.textContent.trim();
        this.#count = Number(countElement.textContent.trim());
        this.#msg   = subtitleElement.textContent.trim();

        this.#isInitialised = true;

    }

    /**
     * Checks if an the init method as been run
     * @returns bool
     */
    isInitRun() {
        return this.#isInitialised === true;
    }

    /**
     * Returns the title of notification card
     */
    get title() {
        this.#ensureInitialised();
        return this.#title
    }

    /**
     * returns the image of the notification card
     */
    get image() {
        this.#ensureInitialised();
        return this.#img.src;
    }

    /**
     * returns the subtitle for the notification card
     */
    get subtitle() {
        this.#ensureInitialised();
        return this.#msg
    }

    /**
     * returns the notification count for the notification card
     */
    get notificationCount() {
        this.#ensureInitialised();
        return this.#count;
    }

    /**
     * Updates the notifcation count summary
     */
    set count(notificationCount) {
        this.#ensureInitialised();

        const numType = typeof notificationCount;

        if (numType !== "number" && Number.isFinite(notificationCount)) {
           throw new Error(`The value entered is not a number. Got type ${numType}`)
        }

        if (notificationCount < 0) {
            throw new TypeError(`The number must not be negative number. Expected postive got ${notificationCount}`);
        }

        this.#cardElement.querySelector(".notification-card__msg p:nth-of-type(2)").textContent = notificationCount;
        this.#count = notificationCount;
    }
}
