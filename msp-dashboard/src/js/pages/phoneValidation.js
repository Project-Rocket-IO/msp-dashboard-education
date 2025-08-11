function initializeCleave(phoneInputField, itiInstance) {
  // Create Cleave instance
  const cleaveInstance = new Cleave(phoneInputField, {
    phone: true,
  });
}

// Function to initialize intlTelInput for phone number validation and formatting
function initializeIntlTelInput(phoneInputField) {
  const iti = intlTelInput(phoneInputField, {
    initialCountry: "us",
    utilsScript:
      "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
    autoHideDialCode: false,
    nationalMode: false, // Ensure the input includes the full international number
  });

  // Reformat number to E.164 format before form submission
  phoneInputField.form.addEventListener("submit", function (e) {
    const formattedNumber = iti.getNumber().replace(/\s|-/g, "");
    phoneInputField.value = formattedNumber; // Set the value in the input field
  });

  return iti;
}

const phoneInputFields = document.querySelectorAll("input[type='tel']");
phoneInputFields.forEach((phoneInputField) => {
  initializeIntlTelInput(phoneInputField);
  initializeCleave(phoneInputField);
});
