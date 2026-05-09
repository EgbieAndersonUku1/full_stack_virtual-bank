import { minimumCharactersToUse } from "../utils/password/textboxCharEnforcer.js"

const bankDescriptionTextArea = document.getElementById("id_description")



// Displays the number of characters to display in a given textbox area
minimumCharactersToUse(bankDescriptionTextArea, {
    minCharClass: ".num-of-characters-remaining",
    maxCharClass: ".num-of-characters-to-use",
    minCharMessage: "Minimum characters to use: ",
    maxCharMessage: "Number of characters remaining: ",
    minCharsLimit: 50,
    maxCharsLimit: 255,
    disablePaste: true,
})
