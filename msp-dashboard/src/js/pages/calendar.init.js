/*
Template Name: Velzon - Admin & Dashboard Template
Author: Themesbrand
Website: https://Themesbrand.com/
Contact: Themesbrand@gmail.com
File: Calendar init js
*/

var modalTitle, formEvent, formDeleteEvent, forms, selectedEvent, addEvent;
var editor; // CKEditor instance

// Calendar variables define
var Draggable, externalEventContainerEl, calendarEl;

var eventCategoryChoice = null;
var date_range = null;
var T_check = null;

// Toggle recurrence fields
function toggleRecurrenceFields() {
  const isRepeating = document.getElementById("isRepeating");
  const recurrenceFields = document.getElementById("recurrenceFields");
  
  if (isRepeating && recurrenceFields) {
    if (isRepeating.checked) {
      recurrenceFields.style.display = "block";
    } else {
      recurrenceFields.style.display = "none";
    }
  }
}

// Toggle custom recurrence options
function toggleCustomRecurrence() {
  const frequency = document.getElementById("repeat-frequency");
  const customOptions = document.getElementById("customRecurrenceOptions");
  
  if (frequency && customOptions) {
    if (frequency.value === "CUSTOM") {
      customOptions.style.display = "block";
    } else {
      customOptions.style.display = "none";
    }
  }
}

// Initialize CKEditor
function initCKEditor() {
  if (editor) {
    editor.destroy();
  }
  
  const descriptionField = document.querySelector('#event-description');
  if (descriptionField && typeof ClassicEditor !== 'undefined') {
    editor = ClassicEditor
      .create(descriptionField, {
        toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', '|', 'outdent', 'indent', '|', 'blockQuote', 'insertTable', 'undo', 'redo'],
        placeholder: 'Enter a description...'
      })
      .catch(error => {
        console.error(error);
      });
  }
}

// Destroy CKEditor
function destroyCKEditor() {
  if (editor) {
    editor.destroy();
    editor = null;
  }
}

/**
 * Show the modal to add a new event to the calendar.
 */
function showAddNewEventModal(dateClickedInfo) {
  // Reset the form
  const formElement = document.getElementById("form-event");
  if (formElement) {
    formElement.reset();
  }
  
  // Initialize CKEditor
  initCKEditor();

  // Hide the delete button
  const deleteBtn = document.getElementById("btn-delete-event");
  if (deleteBtn) {
    deleteBtn.setAttribute("hidden", true);
  }

  // Show the add event modal
  if (addEvent) {
    addEvent.show();
  }

  // Set the selected event to null
  selectedEvent = null;

  // Set the modal title to "New Meeting"
  if (modalTitle) {
    modalTitle.innerText = "New Meeting";
  }
  
  // Reset recurrence fields
  const isRepeating = document.getElementById("isRepeating");
  const recurrenceFields = document.getElementById("recurrenceFields");
  const customOptions = document.getElementById("customRecurrenceOptions");
  
  if (isRepeating) isRepeating.checked = false;
  if (recurrenceFields) recurrenceFields.style.display = "none";
  if (customOptions) customOptions.style.display = "none";
}

function getInitialView() {
  if (window.innerWidth >= 768 && window.innerWidth < 1024) {
    return "timeGridWeek";
  } else {
    return "dayGridMonth";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  // Variables, Pre-requisites
  addEvent = new bootstrap.Modal(document.getElementById("event-modal"), {
    keyboard: false,
  });
  
  modalTitle = document.getElementById("modal-title");
  formEvent = document.getElementById("form-event");
  formDeleteEvent = document.getElementById("form-delete-event");
  forms = document.getElementsByClassName("needs-validation");
  selectedEvent = null;

  // Initialize draggable
  Draggable = FullCalendar.Draggable;
  externalEventContainerEl = document.getElementById("external-events");
  calendarEl = document.getElementById("calendar");

  if (externalEventContainerEl) {
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
  }

  if (calendarEl) {
    var mycalendar = new FullCalendar.Calendar(calendarEl, {
      slotLaneMinHeight: 3,
      initialView: getInitialView(),
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
      },
      height: 800,
      buttonIcons: {
        prev: " ri-arrow-left-s-line",
        next: "ri-arrow-right-s-line",
      },
      themeSystem: "bootstrap",
      bootstrapFontAwesome: {
        close: " ri-close",
        prev: " ri-arrow-left-s-line",
        next: "ri-arrow-right-s-line",
        prevYear: "ri-arrow-left-s-line",
        nextYear: "ri-arrow-right-s-line",
      },
      editable: !0,
      droppable: !0,
      selectable: !0,
      dateClick: function (info) {
        showAddNewEventModal(info);
      },
      eventClick: function (info) {
        selectedEvent = info.event;
        showAddNewEventModal(info);
      },
      events: [], // Start with empty events
    });

    // Render the calendar view
    mycalendar.render();
  }

  // Event listener for delete button
  const deleteBtn = document.getElementById("btn-delete-event");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", function (event) {
      if (selectedEvent) {
        const deleteIdField = document.getElementById("delete-event-id");
        if (deleteIdField) {
          deleteIdField.value = selectedEvent.id;
        }
        if (formDeleteEvent) {
          formDeleteEvent.submit();
        }
      }
    });
  }

  // Event listener for new event button
  const newEventBtn = document.getElementById("btn-new-event");
  if (newEventBtn) {
    newEventBtn.addEventListener("click", function (event) {
      showAddNewEventModal();
    });
  }
  
  // Event listener for form submission
  const formEventElement = document.getElementById("form-event");
  if (formEventElement) {
    formEventElement.addEventListener("submit", function(event) {
      // Update the description field with CKEditor content before submission
      const descriptionField = document.getElementById("event-description");
      if (editor && descriptionField) {
        descriptionField.value = editor.getData();
      }
    });
  }
  
  // Event listener for modal hidden event to clean up CKEditor
  const eventModal = document.getElementById("event-modal");
  if (eventModal) {
    eventModal.addEventListener("hidden.bs.modal", function () {
      destroyCKEditor();
    });
  }
});
