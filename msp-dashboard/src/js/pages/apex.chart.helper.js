// ************************************ //
// ********* HELPER FUNCTIONS ******** //
// *********************************** //

// Helper function to get dynamically ordered days
const getOrderedDaysOfWeek = () => {
  const todayIndex = new Date().getDay();
  return [
    ...daysOfWeek.slice(todayIndex + 1),
    ...daysOfWeek.slice(0, todayIndex + 1),
  ];
};

// Helper function to get dynamically ordered months
const getOrderedMonths = () => {
  const today = new Date();
  const currentMonthIndex = today.getMonth();
  const months = [
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
  return [
    ...months.slice(currentMonthIndex + 1),
    ...months.slice(0, currentMonthIndex + 1),
  ];
};

// Helper function to get dynamically ordered day indices for weekly data
const getOrderedDayIndices = () => {
  const todayIndex = new Date().getDay();
  return [...Array(7).keys()]
    .slice(todayIndex + 1)
    .concat([...Array(7).keys()].slice(0, todayIndex + 1));
};

// Helper function to get dynamically ordered month indices for yearly and six-month data
const getOrderedMonthIndices = () => {
  const currentMonthIndex = new Date().getMonth();
  return [...Array(12).keys()]
    .slice(currentMonthIndex + 1)
    .concat([...Array(12).keys()].slice(0, currentMonthIndex + 1));
};

// Helper function to reorder weekly data based on the current day
const reorderWeeklyData = (weeklyData) => {
  const orderedDayIndices = getOrderedDayIndices(); // Use the helper for dynamic day ordering
  return orderedDayIndices.map((index) => weeklyData[index]);
};

// Helper function to reorder monthly data based on the current day
const reorderMonthlyData = (monthlyData) => {
  const orderedDayIndices = getOrderedDayIndices(); // Use the helper for dynamic day ordering
  return orderedDayIndices.map((index) => monthlyData[index]);
};

// Helper function to reorder yearly data based on the current month
const reorderYearlyData = (yearlyData) => {
  const orderedMonthIndices = getOrderedMonthIndices(); // Use the helper for dynamic month ordering
  return orderedMonthIndices.map((index) => yearlyData[index]);
};
