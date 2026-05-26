import fetchData from "../fetch.js"
import { warnError } from "../logger.js"
import { toggleElement, toggleSpinner } from "../utils.js";
import { getCsrfToken } from "../security/csrf.js";


const profileImgInput = document.getElementById("profile-pic")
const profileImgPreview = document.getElementById("profile-bank-placeholder-img");
const savePreviewButton = document.getElementById("profile-preview-btn");
const spinner           = document.getElementById("create-profile-spinner");



const state = {
    cropper: null,
    file: null
}


document.addEventListener("DOMContentLoaded", () => {

    if (!(profileImgInput instanceof HTMLInputElement)) {
        throw new Error("profileImgInput not found")
    }

    if (!(profileImgPreview instanceof HTMLImageElement)) {
        throw new Error("profileImgPreview not found")
    }
})


savePreviewButton.addEventListener("click", handleSavePreviewButtonClick);
profileImgInput.addEventListener("change", handleProfileImageChange)


/**
 * Listen on the image input field in order to load the image
 * into the preview section
 */
profileImgInput.addEventListener("change", (event) => {

    const DELAY_MS = 1000;

    toggleSpinner(spinner, true);

    setTimeout(() => {
         const file = getSelectedImageFile(event)

        if (!file) {
            return
        }

        setImagePreview(profileImgPreview, file, (previewUrl) => {
            setCropper(profileImgPreview, previewUrl)
        })

        toggleSpinner(spinner, false);

    }, DELAY_MS);
   

})





/**
 * Returns the first selected file from a file input event.
 *
 * @param {Event} event - The input change event.
 * @returns {File|null} The selected file or null.
 */
function getSelectedImageFile(event) {

    if (!(event?.target instanceof HTMLInputElement)) {

        warnError("getSelectedImageFile", {
            error: "Expected HTMLInputElement event target",
            received: typeof event?.target,
        })

        return null
    }

    return event.target.files?.[0] ?? null
}





/**
 * Sets an image preview using a temporary object URL.
 * Runs the callback after the image has fully loaded.
 *
 * @param {HTMLImageElement} imgElement - The image element used for previewing.
 * @param {File} file - The selected image file.
 * @param {Function} callback - Runs after the image loads.
 */
function setImagePreview(imgElement, file, callback) {

    if (!(imgElement instanceof HTMLImageElement)) {

        warnError("setImagePreview", {
            message: "imgElement is not an instance of HTMLImageElement",
        })

        return
    }

    if (!(file instanceof File)) {

        warnError("setImagePreview", {
            message: "file is not an instance of File",
        })

        return
    }

    if (!file.type.startsWith("image/")) {

        warnError("setImagePreview", {
            message: "Expected an image file",
            received: file.type,
        })

        return
    }

    const objectUrl = URL.createObjectURL(file);

    state.file = file;

    toggleElement({element: savePreviewButton, show: true});

    imgElement.addEventListener("load", () => {

        if (typeof callback === "function") {
            callback(objectUrl)
        }

    }, { once: true })

    imgElement.src = objectUrl
}




/**
 * Creates a new Cropper instance for the preview image.
 * Destroys the previous cropper instance if one exists.
 *
 * @param {HTMLImageElement} imgElement - The image element to attach Cropper to.
 * @param {string} objectUrl - Temporary blob URL created from the uploaded image.
 */
function setCropper(imgElement, objectUrl) {

    if (!(imgElement instanceof HTMLImageElement)) {

        warnError("setCropper", {
            message: "imgElement is not an instance of HTMLImageElement",
        })

        return
    }

    if (state.cropper !== null) {
        state.cropper.destroy()
    }

        state.cropper = new Cropper(imgElement, {
        aspectRatio: 1,
        viewMode: 1,
        dragMode: "move",
        autoCropArea: 0.7,
        responsive: true,

        ready() {
            URL.revokeObjectURL(objectUrl)
        }
    })
}




/**
 * Generates a cropped image file from the current cropper selection.
 *
 * Retrieves the cropped canvas from the cropper instance, converts the
 * canvas into a JPEG blob, and creates a File object that can be uploaded
 * or appended to FormData.
 *
 * @async
 * @function getCropFile
 * @returns {Promise<File>} A JPEG file containing the cropped image.
 */
async function getCropFile() {

    const canvas = state.cropper.getCroppedCanvas();

    const blob = await new Promise((resolve) => {
        canvas.toBlob((blob) => {
            resolve(blob);
        }, "image/jpeg");
    });

    const croppedFile = new File(
        [blob],
        "cropped-image.jpg",
        {
            type: "image/jpeg",
        }
    );
    return croppedFile;
}




/**
 * Uploads the cropped image to the server and performs cleanup operations.
 *
 * Sends the provided FormData containing the cropped image to the backend.
 * After the request completes handles the cleanup.
 *
 * @async
 * @function handleFetchAndCleanUp
 * @param {FormData} formData - The form data containing the cropped image file.
 * @returns {Promise<void>} Resolves when the upload and cleanup process completes.
 */
async function handleFetchAndCleanUp(formData) {
    const data = await fetchData({
        url: "/bank/setup/upload/cropped/image/",
        csrfToken: getCsrfToken(),
        method: "POST",
        body: formData,
    });

    if (state.cropper) {
        state.cropper.destroy();
        state.cropper = null;
        state.file = null;
    }

    if (data.SUCCESSFUL) {
        profileImgPreview.src = data.EXTRA_INFO.temp_url;

        toggleElement({
            element: savePreviewButton,
            show: false,
        });
    }

    
    
    clearProfileInputField();
    removeCropperContainer()
    
}


/**
 * Remove all traces of the cropper container
 */
function removeCropperContainer(){
   document.querySelectorAll(".cropper-container").forEach(element => element.remove());
}



/**
 * Clear the profile input otherwise the same image can't be cropped
 * again
 */
function clearProfileInputField() {
    profileImgInput.value = "";
  
}



/**
 * Handles the save preview button click event.
 *
 * After the user clicks the save button for the cropped image, this
 * function is responsible for handling the fetch for the cropped image
 * and storing the cropped image in the preview location by delegating
 * the work to appropriate functions
 *
 * @async
 * @function handleSavePreviewButtonClick
 * @param {Event} e - The click event triggered by the save preview button.
 * @returns {Promise<void>} Resolves when the cropped image has been processed.
 */
async function handleSavePreviewButtonClick(e) {

    if (!state.cropper) {

        warnError("handleSavePreviewButtonClick", {
            message: "Cropper instance not found",
        });

        return;
    }
    
    const formData   = new FormData()
    const croppedFile = await getCropFile()
    formData.append("image", croppedFile);
  
    await handleFetchAndCleanUp(formData)

}



function handleProfileImageChange(e) {
  const DELAY_MS = 1000;

    toggleSpinner(spinner, true);

    console.log("clicked");

    setTimeout(() => {
         const file = getSelectedImageFile(event)

        if (!file) {
            return
        }

        setImagePreview(profileImgPreview, file, (previewUrl) => {
            setCropper(profileImgPreview, previewUrl)
        })

        toggleSpinner(spinner, false);

    }, DELAY_MS);

}