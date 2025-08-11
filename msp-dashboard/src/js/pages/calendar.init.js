/*
Template Name: Velzon - Admin & Dashboard Template
Author: Themesbrand
Website: https://Themesbrand.com/
Contact: Themesbrand@gmail.com
File: Calendar init js
*/
import * as dateUtils from "./dateUtils.init.js";

var modalTitle, formEvent, formDeleteEvent, forms, selectedEvent, addEvent;

// Calendar variables define
var Draggable, externalEventContainerEl, calendarEl;

var eventCategoryChoice = null;
var date_range = null;
var T_check = null;

// Create New Event (Start & End Date calculation)
timepicker1.addEventListener("change", () => {
  let { start: startDate, end: endDate } = dateUtils.calculateStartEnd(
    start_date,
    timepicker1,
    timepicker2
  );

  document.getElementById("start").value = startDate;
  document.getElementById("end").value = endDate;
});
timepicker2.addEventListener("change", () => {
  let { start: startDate, end: endDate } = dateUtils.calculateStartEnd(
    start_date,
    timepicker1,
    timepicker2
  );

  document.getElementById("start").value = startDate;
  document.getElementById("end").value = endDate;
});
start_date.addEventListener("change", () => {
  let { start: startDate, end: endDate } = dateUtils.calculateStartEnd(
    start_date,
    timepicker1,
    timepicker2
  );

  document.getElementById("start").value = startDate;
  document.getElementById("end").value = endDate;
});

/**
 * Populate the event details in the edit modal based on the selected event.
 * @param {Object} selectedEvent - The event object returned by FullCalendar
 */
function populateEventDetails(selectedEvent) {
  /*
   * Populate the event details in the modal based on the selected event.
   */
  document.getElementById("event-title").value = selectedEvent.title;
  document.getElementById("event-location").value = selectedEvent.extendedProps
    .location
    ? selectedEvent.extendedProps.location
    : "No Location";
  document.getElementById("event-description").value = selectedEvent
    .extendedProps.description
    ? selectedEvent.extendedProps.description
    : "No Description";
  document.getElementById("eventid").value = selectedEvent.id;

  /*
   * Clear the event category choice if it already exists.
   */
  if (eventCategoryChoice) eventCategoryChoice.destroy();

  /*
   * Set the event category choice based on the selected event.
   */
  if (selectedEvent.extendedProps.type) {
    eventCategoryChoice = new Choices("#event-category", {
      searchEnabled: false,
    });
    eventCategoryChoice.setChoiceByValue(selectedEvent.extendedProps.type);
  }

  /*
   * Set the list of guests invited to the event in the guests_list based on the selected event.
   */
  var guestsSelect = document.getElementById("event-guests");
  var guestOptions = guestsSelect.options;

  var selectedGuestIds = selectedEvent.extendedProps.guest_list.map(
    (guest) => guest.user_id
  );

  for (var i = 0; i < guestOptions.length; i++) {
    if (selectedGuestIds.includes(guestOptions[i].value)) {
      guestOptions[i].selected = true;
    }
  }
}

/**
 * Show the modal to add a new event to the calendar.
 *
 * @param {Object} dateClickedInfo The event object that contains the start and end dates
 *   and other information about the event.
 */
function showAddNewEventModal(dateClickedInfo) {
  // Reset the form
  document.getElementById("form-event").reset();

  // Hide the delete button
  document.getElementById("btn-delete-event").setAttribute("hidden", true);

  // Show the add event modal
  addEvent.show();

  // Reset the form validation
  formEvent.classList.remove("was-validated");
  formEvent.reset();

  // Set the selected event to null
  selectedEvent = null;

  // Set the modal title to "Add Event"
  modalTitle.innerText = "Add Event";

  // Set the data-id attribute of the edit button to "new-event"
  document
  .getElementById("edit-event-btn")
  .setAttribute("data-id", "new-event");
  
  // Click the edit button and hide it
  document.getElementById("edit-event-btn").click();
  document.getElementById("edit-event-btn").setAttribute("hidden", true);
}


function getInitialView() {
  if (window.innerWidth >= 768 && window.innerWidth < 1200) {
    return "timeGridWeek";
  } else if (window.innerWidth <= 768) {
    return "listMonth";
  } else {
    return "dayGridMonth";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  // Variables, Pre-requisites
  addEvent = new bootstrap.Modal(document.getElementById("event-modal"), {
    keyboard: false,
  });
  document.getElementById("event-modal");
  modalTitle = document.getElementById("modal-title");
  formEvent = document.getElementById("form-event");
  formDeleteEvent = document.getElementById("form-delete-event");
  forms = document.getElementsByClassName("needs-validation");
  selectedEvent = null;

  flatPickrInit();
  // var e = new Date();
  Draggable = FullCalendar.Draggable;
  externalEventContainerEl = document.getElementById("external-events");
  calendarEl = document.getElementById("calendar");

  // init draggable
  new Draggable(externalEventContainerEl, {
    itemSelector: ".external-event",
    eventData: function (eventEl) {
      return {
        id: Math.floor(Math.random() * 11000),
        title: eventEl.innerText,
        allDay: true,
        start: new Date(),
        className: eventEl.getAttribute("data-class"),
      };
    },
  });

  eventCategoryChoice = new Choices("#event-category", {
    searchEnabled: false,
  });

  var mycalendar = new FullCalendar.Calendar(calendarEl, {
    timeZone: "local",
    editable: !0,
    droppable: !0,
    selectable: !0,
    navLinks: !0,
    initialView: getInitialView(),
    themeSystem: "bootstrap",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay,listMonth",
    },
    windowResize: function (e) {
      var t = getInitialView();
      mycalendar.changeView(t);
    },
    eventResize: function (info) {
      console.log("Event resize", info);
      var indexOfSelectedEvent = events.findIndex(function (x) {
        return x.id == info.event.id;
      });
      if (events[indexOfSelectedEvent]) {
        events[indexOfSelectedEvent].title = info.event.title;
        events[indexOfSelectedEvent].start = info.event.start;
        events[indexOfSelectedEvent].end = info.event.end
          ? info.event.end
          : null;
        events[indexOfSelectedEvent].allDay = info.event.allDay;
        events[indexOfSelectedEvent].className = info.event.classNames[0];
        events[indexOfSelectedEvent].description = info.event._def.extendedProps
          .description
          ? info.event._def.extendedProps.description
          : "";
        events[indexOfSelectedEvent].location = info.event._def.extendedProps
          .location
          ? info.event._def.extendedProps.location
          : "";
      }
      upcomingEvent(events);
    },
    eventClick: function (eventClickInfo) {
      selectedEvent = eventClickInfo.event;

      document.getElementById("edit-event-btn").removeAttribute("hidden");
      document.getElementById("btn-save-event").setAttribute("hidden", true);
      document
        .getElementById("edit-event-btn")
        .setAttribute("data-id", "edit-event");
      document.getElementById("edit-event-btn").innerHTML = "Edit";

      eventClicked();
      flatPickrInit();
      flatpicekrValueClear();
      addEvent.show();
      formEvent.reset();

      // Pass selected event
      populateEventDetails(selectedEvent);

      var st_date = selectedEvent.start;
      var ed_date = selectedEvent.end;

      var date_r = function formatDate(date) {
        var d = new Date(date),
          month = "" + (d.getMonth() + 1),
          day = "" + d.getDate(),
          year = d.getFullYear();
        if (month.length < 2) month = "0" + month;
        if (day.length < 2) day = "0" + day;
        return [year, month, day].join("-");
      };
      var r_date =
        ed_date == null
          ? str_dt(st_date)
          : str_dt(st_date) + " to " + str_dt(ed_date);
      var er_date =
        ed_date == null
          ? date_r(st_date)
          : date_r(st_date) + " to " + date_r(ed_date);

      flatpickr(start_date, {
        defaultDate: er_date,
        altInput: true,
        altFormat: "j F Y",
        dateFormat: "Y-m-d",
        mode: ed_date !== null ? "range" : "range",
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
      document.getElementById("event-start-date-tag").innerHTML = r_date;

      var gt_time = getTime(selectedEvent.start);
      var ed_time = getTime(selectedEvent.end);

      const timePickerConfig = {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
      };

      if (gt_time == ed_time) {
        document.getElementById("event-time").setAttribute("hidden", true);
        flatpickr(document.getElementById("timepicker1"), timePickerConfig);
        flatpickr(document.getElementById("timepicker2"), timePickerConfig);
      } else {
        document.getElementById("event-time").removeAttribute("hidden");
        flatpickr(document.getElementById("timepicker1"), {
          ...timePickerConfig,
          defaultDate: gt_time,
        });
        flatpickr(document.getElementById("timepicker2"), {
          ...timePickerConfig,
          defaultDate: ed_time,
        });

        document.getElementById("event-timepicker1-tag").innerHTML =
          tConvert(gt_time);
        document.getElementById("event-timepicker2-tag").innerHTML =
          tConvert(ed_time);
      }

      modalTitle.innerText = selectedEvent.title;

      // formEvent.classList.add("view-event");
      document.getElementById("btn-delete-event").removeAttribute("hidden");
    },
    dateClick: function (dateClickInfo) {
      showAddNewEventModal(dateClickInfo);
    },
    eventReceive: function (eventReceiveInfo) {
      let event = {
        id: parseInt(eventReceiveInfo.event.id),
        title: eventReceiveInfo.event.title,
        start: eventReceiveInfo.event.start,
        allDay: eventReceiveInfo.event.allDay,
        guests_list: eventReceiveInfo.event.guest_list,
        className: eventReceiveInfo.event.classNames[0],
      };
      events.push(event);
      upcomingEvent(events);
    },
    eventDrop: function (t) {
      var e = events.findIndex(function (e) {
        return e.id == t.event.id;
      });
      events[e] &&
        ((events[e].title = t.event.title),
        (events[e].start = t.event.start),
        (events[e].end = t.event.end || null),
        (events[e].allDay = t.event.allDay),
        (events[e].className = t.event.classNames[0]),
        (events[e].description = t.event._def.extendedProps.description || ""),
        (events[e].location = t.event._def.extendedProps.location || "")),
        upcomingEvent(events);
    },
    events: events,
  });

  // Render the calendar view
  mycalendar.render();
  // Render Upcoming Events
  upcomingEvent(events);

  // Event listener for delete button
  document
    .getElementById("btn-delete-event")
    .addEventListener("click", function (event) {
      if (selectedEvent) {
        document.getElementById("delete-event-id").value = selectedEvent.id;
        formDeleteEvent.submit();
      }
    });

  // Event listener for new event button
  document
    .getElementById("btn-new-event")
    .addEventListener("click", function (event) {
      flatpicekrValueClear();
      flatPickrInit();
      showAddNewEventModal();
      // TODO: Juggar laga hoa he
      document
        .getElementById("edit-event-btn")
        .setAttribute("data-id", "new-event");
      document.getElementById("edit-event-btn").click();
      document.getElementById("edit-event-btn").setAttribute("hidden", true);
    });
});
