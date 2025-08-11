
export function calculateStartEnd(dateRangeInput, timepicker1, timepicker2) {
  // Extract date range and times
  const dateRange = dateRangeInput.value.split("to").map(date => date.trim());
  let startDate = new Date(dateRange[0]);
  let endDate = dateRange[1] ? new Date(dateRange[1]) : null;

  // Handle invalid dates
  if (isNaN(startDate.getTime())) {
    console.error("Invalid start date");
    return { start: null, end: null };
  }

  // If there's an end date, check if it's valid and handle multi-day events
  if (endDate) {
    if (isNaN(endDate.getTime())) {
      console.error("Invalid end date");
      return { start: null, end: null };
    }
    //! Why are we adding an extra day in endDate?
    // endDate.setDate(endDate.getDate() + 1);
  } else {
    // Handle single day events with start and end times
    const startTime = timepicker1.value.trim();
    const endTime = timepicker2.value.trim();

    if (startTime) {
      startDate = new Date(`${dateRange[0]}T${startTime}`);
    }

    if (endTime) {
      endDate = new Date(`${dateRange[0]}T${endTime}`);
    }

    // Handle cases where end time is before start time
    if (endDate && endDate < startDate) {
      console.error("End time is before start time");
      return { start: null, end: null };
    }

    // Handle cases where end time is before start time or event duration is less than 1 minute
    // if (endDate && (endDate < startDate || (endDate - startDate) < 60000)) {
    //   console.error("End time is before start time or event duration is less than 1 minute");
    //   return { start: null, end: null };
    // }

  }

  return {
    start: startDate,
    end: endDate
  };
}

