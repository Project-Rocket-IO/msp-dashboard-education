/*
Template Name: Velzon - Admin & Dashboard Template
Author: Themesbrand
Website: https://Themesbrand.com/
Contact: Themesbrand@gmail.com
File: Profile-setting init js
*/


// Cover Image Preview Logic
document.querySelector("#profile-foreground-img-file-input") &&       
document
    .querySelector("#profile-foreground-img-file-input")
    .addEventListener("change", function () {
      var o = document.querySelector(".profile-wid-img"),
      e = document.querySelector(".profile-foreground-img-file-input")
      .files[0],
      i = new FileReader();
      i.addEventListener(
        "load",
        function () {
          o.src = i.result;
        },
        !1
      ),
      e && i.readAsDataURL(e);
    }),
// Profile Picture Preview Logic
    document.querySelector("#profile-img-file-input") &&
    document
      .querySelector("#profile-img-file-input")
      .addEventListener("change", function () {
        var o = document.querySelector(".user-profile-image"),
          e = document.querySelector(".profile-img-file-input").files[0],
          i = new FileReader();
        i.addEventListener(
          "load",
          function () {
            o.src = i.result;
          },
          !1
        ),
          e && i.readAsDataURL(e);
      });

// Web Integrations Image preview logic
let input = document.getElementById('webview-image-input');
let img = document.getElementById('webview-img');

input.addEventListener('change', function() {
    console.log(input.files)
    if (input.files && input.files[0]) {
        let reader = new FileReader();
        reader.onload = function(e) {
            img.src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
});


function deleteEl(id) {
  var element = document.getElementById(id);
  if (element) {
      document.getElementById("newlink").removeChild(element);
  }
}

let clientChoiceDropDown = document.getElementById('client-choice-dropdown-div')
let userRoleChoice = document.getElementById('user-role-choice')
clientChoiceDropDown.style.display = 'none'
// Display Client Choice only if Client is selected
userRoleChoice.addEventListener('change', (event) => {
        let selectedOption = event.target.value;
        if (selectedOption == '10') {
                        clientChoiceDropDown.style.display = 'block'
        } else {
                        clientChoiceDropDown.style.display = 'none'
        }
})