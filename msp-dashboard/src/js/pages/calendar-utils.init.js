var start_date = document.getElementById("event-start-date");
var timepicker1 = document.getElementById("timepicker1");
var timepicker2 = document.getElementById("timepicker2");

function flatPickrInit() {
  var config = {
    enableTime: true,
    noCalendar: true,
  };
  var date_range = flatpickr(start_date, {
    enableTime: false,
    mode: "range",
    minDate: "today",
    onChange: function (selectedDates, dateStr, instance) {
      var date_range = dateStr;
      var dates = date_range.split("to");
      if (dates.length > 1) {
        document.getElementById("event-time").setAttribute("hidden", true);
      } else {
        document
          .getElementById("timepicker1")
          .parentNode.classList.remove("d-none");
        document
          .getElementById("timepicker1")
          .classList.replace("d-none", "d-block");
        document
          .getElementById("timepicker2")
          .parentNode.classList.remove("d-none");
        document
          .getElementById("timepicker2")
          .classList.replace("d-none", "d-block");
        document.getElementById("event-time").removeAttribute("hidden");
      }
    },
  });
  flatpickr(timepicker1, config);
  flatpickr(timepicker2, config);
}

function flatpicekrValueClear() {
  start_date.flatpickr().clear();
  timepicker1.flatpickr().clear();
  timepicker2.flatpickr().clear();
}

function eventClicked() {
  document.getElementById("form-event").classList.add("view-event");
  document.getElementById("event-title").classList.replace("d-block", "d-none");
  document
    .getElementById("event-category")
    .classList.replace("d-block", "d-none");
  document
    .getElementById("event-start-date")
    .parentNode.classList.add("d-none");
  document
    .getElementById("event-start-date")
    .classList.replace("d-block", "d-none");
  document.getElementById("event-time").setAttribute("hidden", true);
  document.getElementById("timepicker1").parentNode.classList.add("d-none");
  document.getElementById("timepicker1").classList.replace("d-block", "d-none");
  document.getElementById("timepicker2").parentNode.classList.add("d-none");
  document.getElementById("timepicker2").classList.replace("d-block", "d-none");
  document
    .getElementById("event-location")
    .classList.replace("d-block", "d-none");
  document
    .getElementById("event-description")
    .classList.replace("d-block", "d-none");
  document
    .getElementById("event-start-date-tag")
    .classList.replace("d-none", "d-block");
  document
    .getElementById("event-timepicker1-tag")
    .classList.replace("d-none", "d-block");
  document
    .getElementById("event-timepicker2-tag")
    .classList.replace("d-none", "d-block");
  document
    .getElementById("event-location-tag")
    .classList.replace("d-none", "d-block");
  document
    .getElementById("event-description-tag")
    .classList.replace("d-none", "d-block");
  document.getElementById("btn-save-event").setAttribute("hidden", true);
}

function editEvent(data) {


  
  var data_id = data.getAttribute("data-id");
  console.log("Edit Event", data_id)
  if (data_id == "new-event") {
    document.getElementById("modal-title").innerHTML = "";
    document.getElementById("modal-title").innerHTML = "Add Event";
    document.getElementById("btn-save-event").innerHTML = "Add Event";
    eventTyped();
  } else if (data_id == "edit-event") {
    data.innerHTML = "Cancel";
    data.setAttribute("data-id", "cancel-event");
    document.getElementById("btn-save-event").innerHTML = "Update Event";
    data.removeAttribute("hidden");
    eventTyped();

  } else {
    data.innerHTML = "Edit";
    data.setAttribute("data-id", "edit-event");
    eventClicked();
  }
}

function eventTyped() {
  document.getElementById("form-event").classList.remove("view-event");
  document.getElementById("event-title").classList.replace("d-none", "d-block");
  document
    .getElementById("event-category")
    .classList.replace("d-none", "d-block");
  document
    .getElementById("event-start-date")
    .parentNode.classList.remove("d-none");
  document
    .getElementById("event-start-date")
    .classList.replace("d-none", "d-block");
  document.getElementById("timepicker1").parentNode.classList.remove("d-none");
  document.getElementById("timepicker1").classList.replace("d-none", "d-block");
  document.getElementById("timepicker2").parentNode.classList.remove("d-none");
  document.getElementById("timepicker2").classList.replace("d-none", "d-block");
  document
    .getElementById("event-location")
    .classList.replace("d-none", "d-block");
  document
    .getElementById("event-description")
    .classList.replace("d-none", "d-block");
  document
    .getElementById("event-start-date-tag")
    .classList.replace("d-block", "d-none");
  document
    .getElementById("event-timepicker1-tag")
    .classList.replace("d-block", "d-none");
  document
    .getElementById("event-timepicker2-tag")
    .classList.replace("d-block", "d-none");
  document
    .getElementById("event-location-tag")
    .classList.replace("d-block", "d-none");
  document
    .getElementById("event-description-tag")
    .classList.replace("d-block", "d-none");
  document.getElementById("btn-save-event").removeAttribute("hidden");
}

// upcoming Event
function upcomingEvent(a) {
  a.sort(function (o1, o2) {
    return new Date(o1.start) - new Date(o2.start);
  });
  document.getElementById("upcoming-event-list").innerHTML = null;
  Array.from(a).forEach(function (element) {
    var title = element.title;
    if (element.end) {
      endUpdatedDay = new Date(element.end);
      var updatedDay = endUpdatedDay.setDate(endUpdatedDay.getDate() - 1);
    }
    var e_dt = updatedDay ? updatedDay : undefined;
    if (e_dt == "Invalid Date" || e_dt == undefined) {
      e_dt = null;
    } else {
      const newDate = new Date(e_dt).toLocaleDateString("en", {
        year: "numeric",
        month: "numeric",
        day: "numeric",
      });
      e_dt = new Date(newDate)
        .toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
        .split(" ")
        .join(" ");
    }
    var st_date = element.start ? str_dt(element.start) : null;
    var ed_date = updatedDay ? str_dt(updatedDay) : null;
    if (st_date === ed_date) {
      e_dt = null;
    }
    var startDate = element.start;
    if (startDate === "Invalid Date" || startDate === undefined) {
      startDate = null;
    } else {
      const newDate = new Date(startDate).toLocaleDateString("en", {
        year: "numeric",
        month: "numeric",
        day: "numeric",
      });
      startDate = new Date(newDate)
        .toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
        .split(" ")
        .join(" ");
    }

    var end_dt = e_dt ? " to " + e_dt : "";
    var category = element.className.split("-");
    var description = element.description ? element.description : "";
    var e_time_s = tConvert(getTime(element.start));
    var e_time_e = tConvert(getTime(updatedDay));
    if (e_time_s == e_time_e) {
      var e_time_s = "Full day event";
      var e_time_e = null;
    }
    var e_time_e = e_time_e ? " to " + e_time_e : "";

    u_event =
      "<div class='card mb-3'>\
        <div class='card-body'>\
          <div class='d-flex mb-3'>\
            <div class='flex-grow-1'><i class='mdi mdi-checkbox-blank-circle me-2 text-" +
      category[2] +
      "'></i><span class='fw-medium'>" +
      startDate +
      end_dt +
      " </span></div>\
    <div class='flex-shrink-0'><small class='badge badge-soft-primary ms-auto'>" +
      e_time_s +
      e_time_e +
      "</small></div>\
                        </div>\
      <h6 class='card-title fs-16'> " +
      title +
      "</h6> <p class='text-muted text-truncate-two-lines mb-0'> " +
      description +
      "</p>\
      </div>\
      </div>";
    document.getElementById("upcoming-event-list").innerHTML += u_event;
  });
}

function getTime(params) {
  params = new Date(params);
  if (params.getHours() != null) {
    var hour = params.getHours();
    var minute = params.getMinutes() ? params.getMinutes() : 0;
    return hour + ":" + minute;
  }
}

function tConvert(time) {
  var t = time.split(":");
  var hours = t[0];
  var minutes = t[1];
  var newformat = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  hours = hours ? hours : 12;
  minutes = minutes < 10 ? "0" + minutes : minutes;
  return hours + ":" + minutes + " " + newformat;
}

var str_dt = function formatDate(date) {
  var monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  var d = new Date(date),
    month = "" + monthNames[d.getMonth()],
    day = "" + d.getDate(),
    year = d.getFullYear();
  if (month.length < 2) month = "0" + month;
  if (day.length < 2) day = "0" + day;
  return [day + " " + month, year].join(",");
};

function toggleFields() {
  var checkbox = document.getElementById("isRepeating");
  var RepeatFields = document.getElementById("RepeatFields");
  if (checkbox.checked) {
    RepeatFields.style.display = "block";
  } else {
    RepeatFields.style.display = "none";
  }
}
