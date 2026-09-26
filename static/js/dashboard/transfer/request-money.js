import { minimumCharactersToUse } from "../../utils/password/textboxCharEnforcer.js";
const requestTextArea  = document.getElementById("request-note");

const textAreaConfig = {
    minCharClass: ".num-of-characters-remaining",
    maxCharClass: ".num-of-characters-to-use",
    minCharMessage: "Minimum characters to use: ",
    maxCharMessage: "Number of characters remaining: ",
    minCharsLimit: 50,
    maxCharsLimit: 255,
    disablePaste: true,
};


[requestTextArea].forEach((textAreaElement) => {
    minimumCharactersToUse(textAreaElement, textAreaConfig);
});
