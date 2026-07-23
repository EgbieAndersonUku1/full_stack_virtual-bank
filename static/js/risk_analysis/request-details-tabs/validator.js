

export class ApplicationValidators {


     validateResponse(data) {
        if (
            typeof data !== "object" || data === null
                   || !data.APPLICATION_ID || !data.STATUS || !data.USER_INFORMATION
                   || !data.ACCOUNT_DETAILS || !data.BANK_DETAILS || !data.USER_STATS
                  ) {

                throw new TypeError(
                "Invalid request header data structure."
            );
        }
    }


    validateElements() {
        for (const [name, element] of Object.entries(this.elements)) {
            if (!element) {
                throw new Error(`Missing required DOM element: ${name}`);
            }
        }
    }
}
