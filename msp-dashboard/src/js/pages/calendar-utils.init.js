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
  console.log('DEBUG: upcomingEvent called with data:', a);
  console.log('DEBUG: Number of events received:', a.length);
  
  // Filter out events without valid start dates and only show future events
  const now = new Date();
  const validEvents = a.filter(event => {
    const hasValidStart = event.start && event.start !== "Invalid Date";
    if (!hasValidStart) return false;
    
    try {
      const eventDate = new Date(event.start);
      const isFuture = eventDate >= now;
      console.log('DEBUG: Event', event.title, 'is future:', isFuture, 'event date:', eventDate, 'now:', now);
      return isFuture;
    } catch (e) {
      console.warn('Invalid date for event:', event.title, event.start);
      return false;
    }
  });
  
  console.log('DEBUG: Valid future events after filtering:', validEvents.length);
  
  validEvents.sort(function (o1, o2) {
    return new Date(o1.start) - new Date(o2.start);
  });
  
  document.getElementById("upcoming-event-list").innerHTML = "";
  
  Array.from(validEvents).forEach(function (element) {
    var title = element.title;
    var eventType = element.event_type || 'event';
    var description = element.description ? element.description.substring(0, 50) + (element.description.length > 50 ? '...' : '') : "";
    
    // Format the start date
    var startDate = null;
    if (element.start) {
      try {
        const date = new Date(element.start);
        if (!isNaN(date.getTime())) {
          startDate = date.toLocaleDateString("en-GB", {
            day: "numeric",
            month: "short",
            year: "numeric",
          });
        }
      } catch (e) {
        console.warn('Invalid start date:', element.start);
      }
    }
    
    // Format the end date
    var endDate = null;
    if (element.end && element.end !== element.start) {
      try {
        const date = new Date(element.end);
        if (!isNaN(date.getTime())) {
          endDate = date.toLocaleDateString("en-GB", {
            day: "numeric",
            month: "short",
            year: "numeric",
          });
        }
      } catch (e) {
        console.warn('Invalid end date:', element.end);
      }
    }
    
    // Format times
    var startTime = null;
    var endTime = null;
    
    if (element.start) {
      try {
        const date = new Date(element.start);
        if (!isNaN(date.getTime()) && date.getHours() !== undefined) {
          startTime = tConvert(getTime(element.start));
        }
      } catch (e) {
        console.warn('Invalid start time:', element.start);
      }
    }
    
    if (element.end && element.end !== element.start) {
      try {
        const date = new Date(element.end);
        if (!isNaN(date.getTime()) && date.getHours() !== undefined) {
          endTime = tConvert(getTime(element.end));
        }
      } catch (e) {
        console.warn('Invalid end time:', element.end);
      }
    }
    
    // Determine color class based on event type
    var colorClass = 'primary'; // default for events
    if (eventType === 'ticket') {
      colorClass = 'info';
    } else if (eventType === 'project') {
      colorClass = 'warning';
    }
    
    // Format date range
    var dateRange = startDate;
    if (endDate && endDate !== startDate) {
      dateRange += " to " + endDate;
    }
    
    // Format time range
    var timeRange = "";
    if (startTime && endTime && startTime !== endTime) {
      timeRange = startTime + " to " + endTime;
    } else if (startTime) {
      timeRange = startTime;
    } else {
      timeRange = "All day";
    }
    
    // Add event type prefix to title if not already present
    var displayTitle = title;
    if (eventType === 'ticket' && !title.startsWith('Ticket:')) {
      displayTitle = 'Ticket: ' + title;
    } else if (eventType === 'project' && !title.startsWith('Project:')) {
      displayTitle = 'Project: ' + title;
    } else if (eventType === 'event' && !title.startsWith('Event:')) {
      displayTitle = 'Event: ' + title;
    }

    var u_event =
      "<div class='card mb-3'>\
        <div class='card-body'>\
          <div class='d-flex mb-3'>\
            <div class='flex-grow-1'><i class='mdi mdi-checkbox-blank-circle me-2 text-" +
      colorClass +
      "'></i><span class='fw-medium'>" +
      (dateRange || 'No date') +
      " </span></div>\
    <div class='flex-shrink-0'><small class='badge badge-soft-primary ms-auto'>" +
      timeRange +
      "</small></div>\
                        </div>\
      <h6 class='card-title fs-16'> " +
      displayTitle +
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
