/*
Template Name: Velzon - Admin & Dashboard Template
Author: Themesbrand
Website: https://Themesbrand.com/
Contact: Themesbrand@gmail.com
File: Ticket detail init js
*/
import * as validation from "./select-validation.js";

// favourite btn
Array.from(document.querySelectorAll(".favourite-btn")).forEach(function (
  item
) {
  item.addEventListener("click", function (event) {
    this.classList.toggle("active");
  });
});

var str_dt = function formatDate(date) {
  var monthNames = [
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
  ];
  var d = new Date(date),
    month = "" + monthNames[d.getMonth()],
    day = "" + d.getDate(),
    year = d.getFullYear();
  if (month.length < 2) month = "0" + month;
  if (day.length < 2) day = "0" + day;
  return [day + " " + month, year].join(", ");
};

var ticket_list = localStorage.getItem("ticket-list");
var options = localStorage.getItem("option");
var ticket_no = localStorage.getItem("ticket_no");
var ticket = JSON.parse(ticket_list);

if (ticket) {
  document.getElementById("ticket-title").innerHTML =
    "#VLZ" + ticket_no + " - " + ticket.tasks_name;
  document.getElementById("t-no").innerHTML = ticket_no;
  document.getElementById("create-date").innerHTML = str_dt(ticket.create_date);
  document.getElementById("due-date").innerHTML = str_dt(ticket.due_date);
  document.getElementById("c-date").innerHTML = str_dt(ticket.create_date);
  document.getElementById("d-date").innerHTML = str_dt(ticket.due_date);

  let status_badge;
  switch (ticket.status) {
    case "New":
      status_badge = "info";
      break;
    case "Open":
      status_badge = "success";
      break;
    case "Inprogress":
      status_badge = "warning";
      break;
    case "Closed":
      status_badge = "danger";
  }

  let priority_badge;
  switch (ticket.priority) {
    case "Low":
      priority_badge = "success";
      break;
    case "Medium":
      priority_badge = "warning";
      break;
    case "High":
      priority_badge = "danger";
  }

  document
    .getElementById("ticket-status")
    .classList.replace("bg-info", "bg-" + status_badge);
  document.getElementById("ticket-status").innerHTML = ticket.status;
  document
    .getElementById("ticket-priority")
    .classList.replace("bg-danger", "bg-" + priority_badge);
  document.getElementById("ticket-priority").innerHTML = ticket.priority;
  var div = document.createElement("div");
  div.innerHTML = ticket.status;
  document.getElementById("t-status").value = div.innerText;
  document
    .getElementById("t-priority")
    .classList.replace("bg-danger", "bg-" + priority_badge);
  document.getElementById("t-priority").innerHTML = ticket.priority;
  document.getElementById("ticket-client").innerHTML = ticket.client_name;
  document.getElementById("t-client").innerHTML = ticket.client_name;
}

let form = document.querySelector(".needs-validation");
form.addEventListener("submit", (e) => {
  e.preventDefault();
  form.classList.add("was-validated");

  const dateInput = document.getElementById("date-field");
  let hours = document.getElementById("hours");
  let minutes = document.getElementById("minutes");
  const hoursdiv = hours.parentElement.parentElement;
  const invalidFeedbackHours = hoursdiv.nextElementSibling;
  const minutesdiv = minutes.parentElement.parentElement;
  const invalidFeedbackMinutes = minutesdiv.nextElementSibling;
  let shouldSubmit = true;

  if (dateInput.value === "") {
    validation.setCustomValidityDates(form);
    shouldSubmit = false;
  }

  if (hours.value === "" && minutes.value === "") {
    validation.toggleSelectValidation(hours, invalidFeedbackHours, hoursdiv);

    validation.toggleSelectValidation(
      minutes,
      invalidFeedbackMinutes,
      minutesdiv
    );

    // Events

    // Events
    minutes.addEventListener("change", function () {
      handleTimeChange(
        this,
        hours,
        invalidFeedbackMinutes,
        document.getElementById("hours-invalid-feedback"),
        minutesdiv,
        hoursdiv
      );
    });

    hours.addEventListener("change", function () {
      handleTimeChange(
        this,
        minutes,
        invalidFeedbackHours,
        document.getElementById("minutes-invalid-feedback"),
        hoursdiv,
        minutesdiv
      );
    });
    shouldSubmit = false;
  } else {
    if (hoursdiv.firstChild) {
      hoursdiv.firstChild.style.borderColor = "#0ab39c";
    }
    if (minutesdiv.firstChild) {
      minutesdiv.firstChild.style.borderColor = "#0ab39c";
    }
  }

  validation.setCustomValidity(form)
  if (!form.checkValidity()) {
    // Scroll all the way up, where the validation has failed
    window.scrollTo({ top: 0, behavior: "smooth" });
    return null;
  }
  if (shouldSubmit) form.submit();
});

function handleTimeChange(
  changedInput,
  otherInput,
  changedFeedback,
  otherFeedback,
  changedDiv,
  otherDiv
) {
  validation.toggleSelectValidation(changedInput, changedFeedback, changedDiv);

  const isEitherInputEmpty = !minutes.value && !hours.value;
  const feedbackDisplay = isEitherInputEmpty ? "block" : "none";
  const borderColor = isEitherInputEmpty ? "#f06548" : "#0ab39c";

  otherFeedback.style.display = feedbackDisplay;
  if (otherDiv.firstChild) {
    otherDiv.firstChild.style.borderColor = borderColor;
  }
}
