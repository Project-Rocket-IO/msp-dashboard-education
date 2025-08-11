/**
 * Toggles the validation state of a select element.
 *
 * @param {HTMLSelectElement} element - The select element to validate.
 * @param {HTMLElement} invalidFeedback - The element to display validation feedback.
 * @param {HTMLElement} div - The parent div element containing the select element.
 */

export function toggleSelectValidation(element, invalidFeedback, div) {
  if (!element.value) {
    invalidFeedback.style.display = "block";
    div.firstChild.style.borderColor = "#f06548";
    div.style.marginBottom = "2px";
  } else {
    invalidFeedback.style.display = "none";
    div.firstChild.style.borderColor = "#0ab39c";
  }
}

export function toggleDateValidation(element, invalidFeedback) {
  if (!element.value) {
    invalidFeedback.style.display = "block";
    element.style.borderColor = "#f06548";
    element.style.marginBottom = "2px";
  } else {
    invalidFeedback.style.display = "none";
    element.style.borderColor = "#0ab39c";
  }
}

export function togglePhoneValidation(element, invalidFeedback) {
  console.log("validating");
  const phone = element.value.trim();
  const phoneRegex =
    /^[\+]?[0-9]{0,3}\W?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/im;
  if (!phoneRegex.test(phone)) {
    phoneIsInvalid(element, invalidFeedback);
  } else {
    phoneIsValid(element, invalidFeedback);
  }
}

export function phoneIsValid(element, invalidFeedback) {
  invalidFeedback.style.display = "none";
  element.style.borderColor = "#0ab39c";
}
export function phoneIsInvalid(element, invalidFeedback) {
  invalidFeedback.style.display = "block";
  element.style.borderColor = "#f06548";
  element.style.marginBottom = "2px";
}

/**
 * Sets custom validity for select elements within div elements with class 'choices'.
 *
 * This function iterates over each 'choices' div element, checks if the select element is required,
 * and attaches an event listener to update error messages in real-time based on the select element's value.
 */
export function setCustomValidity(form) {
  // Get all top-level div elements with the class 'choices'
  const choiceDivs = form.querySelectorAll(
    'div.choices[data-type="select-multiple"], div.choices[data-type="select-one"]'
  );

  // Iterate over each 'choices' div element
  choiceDivs.forEach((div) => {
    // Remove extra bottom margin
    div.classList.add("mb-0");
    // Find the select element within the div
    const select = div.querySelector("select[data-choices][required]");

    // Check if the select element exists
    if (select) {
      // Get the next sibling element with the class 'invalid-feedback'
      const invalidFeedback = div.nextElementSibling;
      // Add Event listener for better UX (update error messages in real time)
      select.addEventListener("change", function () {
        // Call your function here
        toggleSelectValidation(this, invalidFeedback, div);
      });
      if (
        invalidFeedback &&
        invalidFeedback.classList.contains("invalid-feedback")
      ) {
        toggleSelectValidation(select, invalidFeedback, div);
      }
    } else {
      div.firstChild.style.border = '1px solid #0ab39c'
    }
  });
}

export function setCustomValidityDates(form) {
  const dateinputs = form.querySelectorAll(
    'input.flatpickr-input[data-provider="flatpickr"]'
  );
  // Iterate over each 'choices' div element
  dateinputs.forEach((input) => {
    // Remove extra bottom margin
    input.classList.add("mb-0");
    // Find the select element within the div
    if (input.hasAttribute("required")) {
      const invalidFeedback = input.nextElementSibling;
      // Add Event listener for better UX (update error messages in real time)
      input.addEventListener("change", function () {
        // Call your function here
        toggleDateValidation(this, invalidFeedback);
      });
      if (
        invalidFeedback &&
        invalidFeedback.classList.contains("invalid-feedback")
      ) {
        toggleDateValidation(input, invalidFeedback);
      }
    } else {
      input.style.border = '1px solid #0ab39c'
    }
  });
}

export function setCustomValidityPhones(form) {
  const phoneInputs = form.querySelectorAll('input[type="tel"]');

  // Iterate over each 'choices' div element
  phoneInputs.forEach((input) => {
    const invalidFeedback = input.parentElement.nextElementSibling;
    togglePhoneValidation(input, invalidFeedback);

    // Remove extra bottom margin
    input.classList.add("mb-0");
    // Find the select element within the div
    input.addEventListener("change", function () {
      // Call your function here
      togglePhoneValidation(this, invalidFeedback);
    });
    if (
      invalidFeedback &&
      invalidFeedback.classList.contains("invalid-feedback")
    ) {
      togglePhoneValidation(input, invalidFeedback);
    }
  });
}
