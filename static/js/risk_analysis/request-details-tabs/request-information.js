import { capitaliseEveryFirstWord, toTitle } from "../../utils.js";
import { ApplicationValidators } from "./validator.js";


export class RecipientCardApplicationInformation extends ApplicationValidators {
    constructor(applicationData) {
        super(applicationData);

        this.validateResponse(applicationData);

        this.data = applicationData;
        this.elements = {
            recipientName: document.getElementById("card-request-details__recipient-name"),
            cardBrand: document.getElementById("card-request-details__card-brand"),
            cardVariant: document.getElementById("card-request-details__card-variant"),
            deliveryAddress: document.getElementById("request-card__recipient_address"),
            phoneNumber: document.getElementById("request-card__phoneNumber"),
            specialInstructions: document.getElementById("request-card__special-instructions"),
        }

        this.validateElements(this.elements);
    }

    #setRecipientCardInformation() {
        this.elements.recipientName.textContent = this.data.USER_INFORMATION.FULL_NAME;
        console.log(this.data.USER_INFORMATION.FULL_NAME)
    }


    #setRecipientcardBrand() {
        this.elements.cardBrand.textContent = toTitle(this.data.REQUEST_CARD_INFO.CARD);
    }

    #setRecipeintCardVariant() {
        this.elements.cardVariant.textContent = toTitle(this.data.REQUEST_CARD_INFO.CARD_VARIANT)
    }

    #setRecipientAddress() {
        const cleanedAddress = capitaliseEveryFirstWord(this.data.REQUEST_CARD_INFO.RECIPIENT_ADDRESS);
        this.elements.deliveryAddress.textContent = cleanedAddress;
    }

    #setRecipientPhoneNumber() {
        this.elements.phoneNumber.textContent = this.data.REQUEST_CARD_INFO.PHONE_NUMBER
    }

    #setSpecialInstructions() {
        this.elements.specialInstructions.textContent = this.data.REQUEST_CARD_INFO.SPECIAL_REQUESTS;
    }

    render() {

        this.#setRecipientCardInformation();
        this.#setRecipientcardBrand();
        this.#setRecipeintCardVariant();
        this.#setRecipientAddress();
        this.#setRecipientPhoneNumber();
        this.#setSpecialInstructions();

    }

}
