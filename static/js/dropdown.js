const dropdownMenu = document.getElementById("virtual-bank-container__dropdown-menu");
const navProfileElement = document.getElementById("virtual-bank-nav-profile");
const securityDropdownLink = document.getElementById("navbar-security-dropdown");
const accountDropdownLink  = document.getElementById("navbar-account-dropdown");
const navBar = document.querySelector(".navbar")



document.addEventListener("DOMContentLoaded", () => {
    if (navProfileElement) {
    navProfileElement.addEventListener("click", handleDropDownMenu);

    }


})



function handleDropDownMenu(e) {
    const profileImg = e.target.closest("img");
    if (profileImg) {
        dropdownMenu.classList.toggle("show")
    }
}

