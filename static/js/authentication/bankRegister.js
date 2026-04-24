import { getCsrfToken } from "../security/csrf.js";
import fetchData from "../fetch.js";

// input fields
const emailInputField = document.getElementById("id_email");
const usernameInputField = document.getElementById("id_username");

// field check
const usernnameExists = document.getElementById("username-exists");
const emailExists     = document.getElementById("email-exists")



// write a one time check to verify input field is correct
usernameInputField.addEventListener("blur",  handleUserInputFieldClick);
emailInputField.addEventListener("blur", handleEmailInputFieldClick)


async function handleEmailInputFieldClick(e) {

    if (isFieldEmpty(e)) return;

    const url  = "/email/exists/";
    const resp = await fetchData({
        url: url,
        csrfToken: getCsrfToken(),
        body: {
            email: e.target.value,
        },
        method: "POST",

    });
    
    toggleFieldMsg(emailExists, resp.data);

}


async function handleUserInputFieldClick(e) {
    if (isFieldEmpty(e)) return;

    const url  = "/username/exists/";
    const resp = await fetchData({
        url: url,
        csrfToken: getCsrfToken(),
        body: {
            username: e.target.value,
        },
        method: "POST",

    })   

    toggleFieldMsg(usernnameExists, resp.data);
   
}



function toggleFieldMsg(element, data) {
   
    element.classList.remove("active-text", "deactivate-text")
    if (!data.IS_AVAILABLE) {
         element.classList.add("deactivate-text");
    } else {
        element.classList.add("active-text");
    }

    element.textContent = data.MSG;
    element.style.display = "block";
  
}


function isFieldEmpty(e) {
    e.target.value === "" ? true : false;
}