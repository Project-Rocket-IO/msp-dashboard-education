import { showConfirmationPopup } from './confirmationPopup.js';
import * as validation from "./select-validation.js";


!(function () {
  "use strict";
  var forms = document.querySelectorAll(".needs-validation");
  Array.prototype.slice.call(forms).forEach(function (form) {
    console.log("Calling this function")
    form.addEventListener(
      "submit",
      function (e) {
        form.classList.add("was-validated");
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
            // Scroll all the way up, where the validation has failed
            window.scrollTo({ top: 0, behavior: "smooth" });
            validation.setCustomValidity(form);
            validation.setCustomValidityDates(form);
            return null;
            }
        },
      !1
    );
  });
})();

var str_dt = function (e) {
  var t =
      "" +
      [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ][(e = new Date(e)).getMonth()],
    a = "" + e.getDate(),
    e = e.getFullYear();
  return (
    t.length < 2 && (t = "0" + t),
    [(a.length < 2 ? "0" + a : a) + " " + t, e].join(", ")
  );
};

let salesElements = document.getElementsByClassName("delete-new-sales");
Array.from(salesElements).forEach((button) => {
    button.addEventListener('click', (e) => {
    e.preventDefault()
      showConfirmationPopup({
        title: 'Delete Sales?',
        text: 'This action cannot be undone!',
        confirmButtonText: 'Yes, delete it!',
        onConfirm: () => {
          // Your delete logic for tickets here
          console.log('Sales deleted');
          button.closest('form').submit();

        }
      });
    });
  });
  