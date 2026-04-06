export const AlertUtils = {


  /**
   * Shows a warning alert when a conflicting window (like card manager) is already open.
   *
   * @param {Object} options - Optional overrides for the default alert content.
   * @param {string} [options.title] - Custom title for the alert.
   * @param {string} [options.text] - Custom message text.
   * @param {string} [options.icon='warning'] - Alert icon type (e.g., 'warning', 'error', 'info').
   * @param {string} [options.confirmButtonText='Ok'] - Text for the confirmation button.
   *
   * @example
   * AlertUtils.warnWindowConflict();
   *
   * @example
   * AlertUtils.warnWindowConflict({
   *   title: "Oops!",
   *   text: "Another modal is already active.",
   * });
   */
    warnWindowConflict({title = "Card manager window is open",
                        text = "The card manager window is open. Close it before opening this one",
                        icon = "warning",
                        confirmButtonText = "Ok"} = {}) {

                        AlertUtils.showAlert({title, text, icon, confirmButtonText
            });
        },

    /**
     * Show a SweetAlert2 alert.
     *
     * @param {Object} options - The options for the alert.
     * @param {string} options.title - The title of the alert.
     * @param {string} options.text - The text content of the alert.
     * @param {string} options.icon - The icon to display in the alert. 
     *                                Available options: 'success', 'error', 'warning', 'info', 'question'.
     * @param {string} options.confirmButtonText - The text for the confirm button.
     */
    showAlert({ title, text, icon, confirmButtonText }) {
        Swal.fire({
            title: title,
            text: text,
            icon: icon,
            confirmButtonText: confirmButtonText
        });
    },

    async showConfirmationAlert({showDenyButton = true,  
        showCancelButton = true, 
        confirmButtonText = "Remove", 
        denyButtonText = "Don't remove", 
        title = "Do you want to remove these cards from your wallet?",
        text  = "This action is irreversable and cannot be undone",
        icon = "info",
        cancelMessage = "Cards were not removed",
        messageToDisplayOnSuccess="removed!",
      } = {}) {
          return Swal.fire({
              title: title,
              text: text,
              showDenyButton: showDenyButton,
              showCancelButton: showCancelButton,
              confirmButtonText: confirmButtonText,
              denyButtonText: denyButtonText,
              icon: icon,
          }).then((result) => {
              if (result.isConfirmed) {
                  Swal.fire(messageToDisplayOnSuccess, "", "success");
                  return true;
              } else if (result.isDenied) {
                  Swal.fire(cancelMessage, "", "info");
                  return false;
              }
              return null;
          });
      }
 
};



