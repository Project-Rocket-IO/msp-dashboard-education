import * as validation from "./select-validation.js";

let attachedFiles = [];

function uploadForm() {
  const form = document.getElementById("editProjectDropzone");
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
    return;
  }

  // Get CKEditor content and sanitize it
  let description = document.getElementsByClassName('ck-content')[0].innerHTML;
  formData.append("description", description);

  fetch(projectEditURL, {
    method: "POST",
    body: formData,
  })
    .then(response => location.href = projectEditURL)
    .catch((error) => {
      console.error("Error:", error.message);
      location.href = projectEditURL;
    });
}

var submitButton = document.querySelector("#add-btn");
submitButton.addEventListener("click", function (e) {
  e.preventDefault();
  uploadForm();
});

var previewTemplate;
var dropzone;
var ckeditorClassic = document.querySelector("#ckeditor-classic");

if (ckeditorClassic) {
  ClassicEditor
    .create(ckeditorClassic)
    .then(function(editor) {
      editor.ui.view.editable.element.style.height = "200px";
    })
    .catch(function(error) {
      console.error(error);
    });
}

var dropzonePreviewNode = document.querySelector("#dropzone-preview-list");

if (dropzonePreviewNode) {
  dropzonePreviewNode.id = "";
  previewTemplate = dropzonePreviewNode.parentNode.innerHTML;
  dropzonePreviewNode.parentNode.removeChild(dropzonePreviewNode);

  dropzone = new Dropzone(".dropzone", {
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
    maxFilesize: 500, // in MB
    init: function() {
      dropzone = this;

      // When a file is added:
      this.on("addedfile", function(file) {
        console.log(file);
        attachedFiles.push(file);
        console.log("File Added");
        console.log(attachedFiles);
        // You can show a submit button here or inform the user to click it.
      });

      // When a file is removed:
      this.on("removedfile", function(file) {
        console.log(file);
        attachedFiles = attachedFiles.filter(function(f) {
          return f !== file;
        });
        console.log("File removed");
        console.log(attachedFiles);
        // You can show a submit button here or inform the user to click it.
      });
    },
  });
}

