/*
Project Rocket - Admin & Dashboard Template
Author: John Lang
Version: 2.0.0
Website: https://projectrocket-psa.com/
Contact: projectRocket@gmail.com
File: Main Js File
*/

//Common plugins
if(document.querySelectorAll("[toast-list]") || document.querySelectorAll('[data-choices]') || document.querySelectorAll("[data-provider]")){ 
  document.writeln("<script type='text/javascript' src='https://cdn.jsdelivr.net/npm/toastify-js'></script>");
  document.writeln("<script type='text/javascript' src='/static/libs/choices.js/public/assets/scripts/choices.min.js'></script>");
  document.writeln("<script type='text/javascript' src='/static/libs/flatpickr/dist/flatpickr.min.js'></script>");    
}