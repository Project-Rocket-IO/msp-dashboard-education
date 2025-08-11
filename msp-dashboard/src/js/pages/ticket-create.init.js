import * as validation from "./select-validation.js";
var isSubmitting = false; // Flag to track form submission

function setCookie(name, value, days) {
  const d = new Date();
  d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
  const expires = "expires=" + d.toUTCString();
  document.cookie = name + "=" + value + ";" + expires + ";path=/";
}
async function uploadForm() {
  const form = document.getElementById("createTicketDropzone");
  const formData = new FormData(form);

  // Add files to formData
  for (const file of attachedFiles) {
    formData.append("files", file);
  }

  form.classList.add("was-validated");
  if (!form.checkValidity()) {
    // Scroll all the way up, where the validation has failed
    window.scrollTo({ top: 0, behavior: "smooth" });
    validation.setCustomValidity(form);
    return null;
  }

  // Get CKEditor content and sanitize it
  let description = document.getElementsByClassName("ck-content")[0].innerHTML;
  formData.append("description", description);

  fetch(ticketCreateURL, {
    method: "POST",
    body: formData,
  })
    .then((response) =>
      response.json().then((data) => ({ status: response.status, body: data }))
    )
    .then(({ status, body }) => {
      location.href = ticketListURL;
    })
    .catch((error) => {
      location.href = ticketListURL;
    });
}

var submitButton = document.querySelector("#add-btn");
submitButton.addEventListener("click", function (e) {
  // Check if the form is already being submitted
  e.preventDefault();
  if (isSubmitting) {
    return; // Do nothing if the form is currently being submitted
  }

  // Set the flag to indicate the form is being submitted
  isSubmitting = true;
  uploadForm()
    .then(function (result) {
      if (result === null) {
        // If uploadForm returns null, reset the flag
        isSubmitting = false;
      }
      // If uploadForm succeeds, the page will refresh automatically
      console.log("Add Button");
    })
    .catch(function (error) {
      console.error("Error:", error);
      // Reset the flag in case of an error
      isSubmitting = false;
    });
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
