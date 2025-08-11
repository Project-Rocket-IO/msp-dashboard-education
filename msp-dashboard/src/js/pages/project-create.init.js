/*
Template Name: Velzon - Admin & Dashboard Template
Author: Themesbrand
Website: https://Themesbrand.com/
Contact: Themesbrand@gmail.com
File: Project create init js
*/

import * as validation from "./select-validation.js";
let isSubmitting = false;
let attachedFiles = [];
// ckeditor
var ckeditorClassic = document.querySelector("#ckeditor-classic");
if (ckeditorClassic) {
  ClassicEditor.create(document.querySelector("#ckeditor-classic"))
    .then(function (editor) {
      editor.ui.view.editable.element.style.height = "200px";
    })
    .catch(function (error) {
      console.error(error);
    });
}

// Dropzone
var dropzonePreviewNode = document.querySelector("#dropzone-preview-list");
if (dropzonePreviewNode) {
  dropzonePreviewNode.id = "";
  var previewTemplate = dropzonePreviewNode.parentNode.innerHTML;
  dropzonePreviewNode.parentNode.removeChild(dropzonePreviewNode);

  var dropzone = new Dropzone(".dropzone", {
    headers: {
      "Cache-Control": null,
      "X-Requested-With": null,
      "X-CSRF-TOKEN": $('meta[name="token"]').attr("content"),
    },
    url: "https://httpbin.org/post",
    method: "get",
    previewTemplate: previewTemplate,
    autoProcessQueue: false,
    uploadMultiple: true,
    parallelUploads: 10,
    maxFiles: 10,
    paramName: "file",
    addRemoveLinks: true,
    maxFilesize: 500,
    previewsContainer: "#dropzone-preview",
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
  });
}

async function uploadForm() {
  const form = document.getElementById("createProjectDropzone");
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
  let description = document.getElementsByClassName('ck-content')[0].innerHTML;
  formData.append("description", description);

  try {
    await fetch(projectCreateURL, {
      method: "POST",
      body: formData,
    });
    // Redirecting is important to prevent multiple form submission (case: user clicks button multiple times)
    location.href = projectListURL;
  } catch (error) {
    console.error("Error:", error);
    location.href = projectCreateURL;
  }
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
 // Call uploadForm and handle completion
 uploadForm().finally(function () {
    // Reset the flag after uploadForm completes (success or failure)
    isSubmitting = false;
  });
});


// TODO: contact formatting
// contactNo = new Cleave("#contactNumber", {
//   delimiters: ["(", ")", "-"],
//   blocks: [0, 3, 3, 4],
// }),