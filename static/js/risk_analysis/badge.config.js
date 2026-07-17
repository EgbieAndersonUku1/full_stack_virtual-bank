/**
 * Central configuration for UI badge states.
 *
 * Maps badge status keys to their corresponding display text and CSS classes.
 * This ensures consistent styling and wording across the application.
 *
 * Add new badge states here instead of modifying UI logic.
 */
export const badgeConfig = {
    verified: {
        text: "Verified",
        class: "status--approved",
    },
    unverified: {
        text: "Not verified",
        class: "status--rejected",
    },
    active: {
        text: "Active",
        class: "status--active",
    },
    deactivated: {
        text: "Deactivated",
        class: "status--disabled",
    },
};
