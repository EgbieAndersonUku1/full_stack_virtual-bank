import { enableAutoFocusNavigation } from "../utils.js";

const codeInputFields = document.querySelectorAll(".code-wrapper input");


codeInputFields[0].focus()
enableAutoFocusNavigation(codeInputFields, true)