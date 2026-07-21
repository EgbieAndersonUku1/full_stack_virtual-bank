/**
 * Retrieves the CSRF token from the current HTML document.
 *
 * @throws {Error}
 * Throws if the CSRF token element cannot be found.
 *
 * @returns {string}
 * The CSRF token.
 *
 * Notes:
 * - The current page must include the following meta element:
 *
 *   <meta name="csrf-token" content="{{ csrf_token }}" id="csrf_token">
 *
 * - The token is read from this element.
 */
export function getCsrfToken() {
    const csrfToken = document.getElementById("csrf_token");

    if (csrfToken === null) {
        throw new Error("The CSRF token return null, CSRF Token is needed for security of the application")

    }

    return csrfToken.content
}
