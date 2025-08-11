import * as validation from "./select-validation.js";

// Example starter JavaScript for disabling form submissions if there are invalid fields
(function () {
  "use strict";

  // Fetch all the forms we want to apply custom Bootstrap validation styles to
  var forms = document.querySelectorAll(".needs-validation");

  // Loop over them and prevent submission
  Array.prototype.slice.call(forms).forEach(function (form) {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          validation.setCustomValidity(form);
          event.preventDefault();
          event.stopPropagation();
        }

        form.classList.add("was-validated");
      },
      false
    );
  });
})();

function setCookie(name, value, days) {
  const d = new Date();
  d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
  const expires = "expires=" + d.toUTCString();
  document.cookie = name + "=" + value + ";" + expires + ";path=/";
}
function uploadForm() {
  const form = document.getElementById("editClientDropzone");
  const formData = new FormData(form);

  // Add files to formData
  for (const file of attachedFiles) {
    formData.append("files", file);
  }

  fetch(clientUpdateURL, {
    method: "POST",
    body: formData,
  })
    .then((response) => (location.href = clientListURL))
    .catch((error) => {
      console.error("Error:", error);
      setCookie("message", "An unexpected error occurred.", 1);
      setCookie("message_tag", "error", 1);
      location.href = clientListURL;
    });
}

var submitButton = document.querySelector("#add-btn");
submitButton.addEventListener("click", function (e) {
  e.preventDefault();
  uploadForm();
});

let attachedFiles = [];
var previewTemplate,
  dropzone,
  ckeditorClassic = document.querySelector("#ckeditor-classic"),
  dropzonePreviewNode =
    (ckeditorClassic &&
      ClassicEditor.create(document.querySelector("#ckeditor-classic"))
        .then(function (e) {
          e.ui.view.editable.element.style.height = "200px";
        })
        .catch(function (e) {
          console.error(e);
        }),
    document.querySelector("#dropzone-preview-list"));
dropzonePreviewNode &&
  ((dropzonePreviewNode.id = ""),
  (previewTemplate = dropzonePreviewNode.parentNode.innerHTML),
  dropzonePreviewNode.parentNode.removeChild(dropzonePreviewNode),
  (dropzone = new Dropzone(".dropzone", {
    headers: {
      "Cache-Control": null,
      "X-Requested-With": null,
      "X-CSRF-TOKEN": $('meta[name="token"]').attr("content"),
    },
    // url: "create",
    method: "get",
    previewTemplate: previewTemplate,
    previewsContainer: "#dropzone-preview",
    autoProcessQueue: false,
    uploadMultiple: true,
    parallelUploads: 10,
    maxFiles: 10,
    paramName: "file",
    addRemoveLinks: true,
    maxFilesize: 500,
    init: function () {
      dropzone = this; // closure

      // files are dropped here:
      this.on("addedfile", (file) => {
        console.log(file);
        attachedFiles.push(file);
        console.log("File Added");
        console.log(attachedFiles);
        // Show submit button here and/or inform user to click it.
      });
      this.on("removedfile", (file) => {
        console.log(file);
        attachedFiles = attachedFiles.filter((f) => f !== file);
        console.log("File removed");
        console.log(attachedFiles);
        // Show submit button here and/or inform user to click it.
      });
    },
  })));

document.querySelector("#company-logo-input")
  .addEventListener("change", function () {
    var e = document.querySelector("#companylogo-img"),
      t = document.querySelector("#company-logo-input").files[0],
      a = new FileReader();
    a.addEventListener(
      "load",
      function () {
        e.src = a.result;
      },
      !1

      
    ),
      t && a.readAsDataURL(t);
  });
