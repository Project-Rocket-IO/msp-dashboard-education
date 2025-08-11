// Initializing variables
let heatmapCurrentFilter = "yearly";
let heatmapData = [];

const daysOfWeek = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
];

// ************************************ //
// *********** Topbar ***************** //
// ************************************ //

const openTicketsBoxNumber = document.getElementById("openTicketsBoxNumber");
const openTicketsBoxPercentage = document.getElementById(
  "openTicketsBoxPercentage"
);
const timePostedBoxNumber = document.getElementById("timePostedBoxNumber");
const timePostedBoxPercentage = document.getElementById(
  "timePostedBoxPercentage"
);
const closeTicketsBoxNumber = document.getElementById("closeTicketsBoxNumber");
const closeTicketsBoxPercentage = document.getElementById(
  "closeTicketsBoxPercentage"
);
const totalProjectsNumber = document.getElementById("totalProjectsNumber");
console.log(totalProjectsNumber)
const crtBoxPercentage = document.getElementById("crtBoxPercentage");
const selectedTopbarFilter = document.querySelector(".selected-topbar-filter");
const topbarFilterItems = document.querySelectorAll(".topbar-sort-item");

Array.from(topbarFilterItems).map((item) =>
  item.addEventListener("click", () => {
    selectedTopbarFilter.innerHTML = item?.innerHTML;
    updateTopBarBoxses(item.getAttribute("data-label"));
    counter(); // animation and formatting of numbers
  })
);

/**
 * Updates the values of the top bar boxes based on the selected filter
 * @param {string} value - The selected filter value, i.e. 'daily', 'weekly', etc.
 */
const updateTopBarBoxses = (value) => {
  const data = metricsData[value]; // value is whatever the sort by filter is selected, i.e. daily, weekly etc.
  openTicketsBoxNumber.setAttribute("data-target", data.open_tickets); // data.open_tickets;
  timePostedBoxNumber.setAttribute("data-target", data.labor_hours.toFixed());
  closeTicketsBoxNumber.setAttribute("data-target", data.closed_tickets);
  totalProjectsNumber.setAttribute("data-target", data.total_projects);

};

// Default topbar metrics
updateTopBarBoxses("yearly");

// Set the default selected filter
selectedTopbarFilter.innerHTML = topbarFilterItems[3]?.innerHTML;


// ************************************ //
// *********** Topbar END ************* //
// ************************************ //

// ************************************ //
// ***********Column chart DATA******** //
// ************************************ //

const getWeeklyColumnChartData = () => {
  const weeklyData = chartsData.weekly;
  const result = Array(7).fill(0);

  for (const entry of weeklyData) {
    const dayIndex = new Date(entry.date).getUTCDay();
    for (const hour in entry.hours) {
      result[dayIndex] += entry.hours[hour].tickets;
    }
  }

  const orderedDayIndices = getOrderedDayIndices();
  return orderedDayIndices.map((index) => result[index]);
};

const getMonthlyColumnChartData = () => {
  const monthlyData = chartsData.monthly;
  const result = Array(5).fill(0);

  index = 0;
  for (const entry of monthlyData) {
    result[Math.floor(index / 7)] += entry.count;
    index++;
  }

  return result;
};

/**
 * Returns an array of 12 integers representing the total number of tickets
 * grouped by month, for the current year.
 *
 * @returns {Array<number>}
 */
const getYearlyColumnChartData = () => {
  const yearlyData = chartsData.yearly;
  const result = Array(12).fill(0);

  for (const entry of yearlyData) {
    result[entry.month - 1] = entry.weeks.reduce((acc, item) => acc + item, 0);
  }

  // Reorder the result based on the current month
  const orderedMonthIndices = getOrderedMonthIndices();
  return orderedMonthIndices.map((index) => result[index]);
};

// Updated getSixMonthsColumnChartData with reordered last 6 months
const getSixMonthsColumnChartData = () => {
  const yearlyData = chartsData.yearly;
  const lastSixMonthsData = yearlyData.slice(-6);
  const result = Array(6).fill(0);

  for (let i = 0; i < lastSixMonthsData.length; i++) {
    result[i] = lastSixMonthsData[i].weeks.reduce((acc, item) => acc + item, 0);
  }

  // Reorder to ensure the current month is at the end for six months data
  const orderedMonthIndices = getOrderedMonthIndices().slice(-6);
  return orderedMonthIndices.map((index) => result[index % 6]);
};

// ************************************ //
// *********** Column chart
// ************************************ //

let tempColumnChartData = [];
let columnChartCurrentFilter = "1y";

/**
 * Returns an array of categories for the column chart, based on the current filter.
 *
 * @function getColumnChartCategories
 * @returns {string[]} An array of categories for the column chart.
 * @since 1.0.0
 */
const updateColumnChartData = () => {
  const tempWeeklyData = getWeeklyColumnChartData();
  const tempSixMonthsData = getSixMonthsColumnChartData();
  const tempYearlyData = getYearlyColumnChartData();
  const tempMonthlyData = getMonthlyColumnChartData();

  switch (columnChartCurrentFilter) {
    case "1w":
      tempColumnChartData = tempWeeklyData;
      break;
    case "1m":
      tempColumnChartData = tempMonthlyData;
      break;
    case "6m":
      tempColumnChartData = tempSixMonthsData;
      break;

    default:
      tempColumnChartData = tempYearlyData;
  }

  // Total tickets activity, how many tickets were worked on this timeframe
  let totalTicketsMonthlyActivity = document.querySelector("#totalTicketsMonthlyActivity");
  totalTicketsMonthlyActivity.setAttribute('data-target', barChartMetricsData[columnChartCurrentFilter].totalTickets);
  
  // Total hours activity, how many hours were worked on this timeframe
  let hoursCommittedMonthlyActivity = document.querySelector("#hoursCommittedMonthlyActivity");
  hoursCommittedMonthlyActivity.setAttribute('data-target', barChartMetricsData[columnChartCurrentFilter].hoursCommitted);

  // same as above, get it from "avgSessionDuration" in barChartMetricsData
  let avgSessionDuration = barChartMetricsData[columnChartCurrentFilter].avgSessionDuration // format: 3h 3m

  let avgSessionDurationHours = document.getElementById("avgSessionDurationHours");
  let avgSessionDurationMinutes = document.getElementById("avgSessionDurationMinutes");
  const durationParts = avgSessionDuration.split(" ");

  avgSessionDurationHours.setAttribute("data-target",  durationParts[0]);
  avgSessionDurationMinutes.setAttribute("data-target",  durationParts[1]);

  counter(); // animation and formatting of numbers


  return [
    {
      name: "Tickets Worked On:",
      data: tempColumnChartData,
    },
  ];
};



const columnChartFilterItem = document.querySelectorAll(
  ".columnchart-sort-item"
);



// Updated getColumnChartCategories function
const getColumnChartCategories = () => {
  switch (columnChartCurrentFilter) {
    case "1w":
      return getOrderedDaysOfWeek().map(
        (day) => day.charAt(0).toUpperCase() + day.slice(1)
      );
    case "1m":
      return ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"];
    case "6m":
      return getOrderedMonths().slice(-6); // Last 6 months in the correct order

    default:
      return getOrderedMonths(); // Full year with the current month at the end
  }
};

// unselected button's css:
// columnchart-sort-item btn btn-soft-secondary btn-sm

// selected button's css:
// columnchart-sort-item btn btn-soft-primary btn-sm

// When the user changes the bar chart filter
Array.from(columnChartFilterItem).map((item) =>
  item.addEventListener("click", () => {
    columnChartCurrentFilter = item.getAttribute("data-label");

    // Update the selected button's CSS
    // Show selected filter for column chart
    Array.from(columnChartFilterItem).forEach((button) => {
      button.classList.remove("btn-soft-primary");
      button.classList.remove("btn-soft-secondary");
      button.classList.add("btn-soft-secondary");
    });
    item.classList.remove("btn-soft-secondary");
    item.classList.add("btn-soft-primary");

    // Update the chart data
    const updatedData = updateColumnChartData();
    columnChart.updateOptions({
      series: updatedData,
      xaxis: {
        categories: getColumnChartCategories(),
      },
    });
  })
);

let columnChartOptions = {
  series: updateColumnChartData(),
  chart: {
    type: "bar",
    height: 300,
    toolbar: { show: false },
    borderRadius: 12,
  },
  plotOptions: {
    bar: {
      columnWidth: "20%",
      colors: {
        borderRadius: 32,
        backgroundBarColors: ["#F2F4F6"],
      },
    },
  },
  dataLabels: {
    enabled: false,
    formatter: function (val) {
      return val + "%";
    },
    offsetY: -20,
    style: {
      fontSize: "12px",
    },
  },
  colors: ["#0ab39c"],
  legend: { show: false },
  xaxis: {
    categories: getColumnChartCategories(),
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: {
      style: {
        fontSize: "12px",
      },
    },
  },
  yaxis: { show: false },
  grid: {
    show: false,
  },
  tooltip: {
    y: {
      formatter: function (val) {
        return val;
      },
    },
  },
};

let columnChart = new ApexCharts(
  document.querySelector("#columnChart"),
  columnChartOptions
);
columnChart.render();

// ************************************ //
// *********** Column chart END ******* //
// ************************************ //

// ************************************ //
// *********** HEATMAP CHART ********** //
// ************************************ //

/**
 * Returns an Object that represents the labor data in a heatmap-friendly format.
 *
 * The returned object will have the following structure:
 * {
 *   "sunday": {
 *     "hours": [0, 0, 0, ... ]
 *   },
 *   "monday": {
 *     "hours": [0, 0, 0, ... ]
 *   },
 *   ...
 * }
 *
 * The values in the "hours" array represent the number of tickets
 * on which that many hours were worked on that day.
 *
 * The data is grouped by day of the week, with the day names being
 * the keys of the object.
 *
 * @returns {Object} The heatmap data in the specified format.
 */
function getWeeklyLabor() {
  const weeklyData = chartsData.weekly;
  const result = {};

  for (const entry of weeklyData) {
    const dayIndex = new Date(entry.date).getUTCDay();
    if (!result[daysOfWeek[dayIndex]]) {
      result[daysOfWeek[dayIndex]] = {
        hours: Array(18).fill(0),
      };
    }

    for (const hour in entry.hours) {
      result[daysOfWeek[dayIndex]].hours[hour - 1] += entry.hours[hour].tickets;
    }
  }

  return result;
}

/**
 * Gets the monthly labor data grouped by day of the week.
 *
 * The returned object will have the following structure:
 * {
 *   "sunday": {
 *     "counts": [0, 0, 0, 0, 0]
 *   },
 *   "monday": {
 *     "counts": [0, 0, 0, 0, 0]
 *   },
 *   ...
 * }
 *
 * The values in the "counts" array represent the number of tickets
 * which were worked on that day of the week. The index of the array represents
 * the week of the month. Hence, the array has 5 elements.
 *
 * The data is grouped by day of the week, with the day names being
 * the keys of the object.
 *
 * @returns {Object} The heatmap data in the specified format.
 */

function getMonthlyLabor() {
  const monthlyData = chartsData.monthly;
  const result = {};

  index = 0;
  for (const entry of monthlyData) {
    const dayIndex = new Date(entry.date).getUTCDay();
    if (!result[daysOfWeek[dayIndex]]) {
      result[daysOfWeek[dayIndex]] = {
        counts: Array(5).fill(0),
      };
    }
    result[daysOfWeek[dayIndex]].counts[Math.floor(index / 7)] = entry.count;
    index++;
  }

  // sorted Result
  sortedResult = {};
  for (const day in daysOfWeek) {
    sortedResult[daysOfWeek[day]] = result[daysOfWeek[day]];
  }

  return sortedResult;
}

/**
 * Returns the labor data in a heatmap-friendly format for yearly heatmap.
 *
 * The heatmap is represented by week1 to week 5 on y axis, and 12 Months names on x-axis.
 * The return value is an object with weeks as keys (rows), each value will be an array of elements.
 *
 * @returns {Object} The heatmap data in the specified format.
 */
function getYearlyLabor() {
  const yearlyData = chartsData.yearly;

  // Initialize result with week-based arrays for each month
  const result = {
    Week1: [],
    Week2: [],
    Week3: [],
    Week4: [],
    Week5: [],
  };

  // Get the current month (0-based, so we add 1 for comparison)
  const currentMonth = new Date().getMonth() + 1;

  // Reorder yearlyData based on the current month
  const orderedYearlyData = [
    ...yearlyData.slice(currentMonth), // Months after the current month
    ...yearlyData.slice(0, currentMonth), // Months up to and including the current month
  ];

  // Populate the result structure by weeks, based on the ordered months
  for (const entry of orderedYearlyData) {
    for (let i = 0; i < entry.weeks.length; i++) {
      result[`Week${i + 1}`].push(entry.weeks[i]);
    }
  }

  return result;
}

const getTodayLabor = () => {
  const todayData = chartsData.daily;
  const ticketsArray = Array(18).fill(0);
  for (const entry of todayData) {
    for (const hour in entry.hours) {
      ticketsArray[hour - 1] = entry.hours[hour].tickets;
    }
  }

  return ticketsArray;
};

const getTodayData = () => {
  const daysOfWeek = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];
  const today = new Date();
  const todayName = daysOfWeek[today.getDay()];
  const updatedData = daysOfWeek.map((day) => ({
    name: day,
    data: day === todayName ? getTodayLabor() : Array(18).fill(0),
  }));
  return updatedData;
};

/**
 * Returns the categories for the heatmap chart, based on the current filter.
 * Categories are the x-axis labels.
 * @returns {string[]} An array of strings, representing the categories.
 * @example
 * getHeatMapCategories() // Daily filter: ["1h", "2h", ...]
 * getHeatMapCategories() // Weekly filter: ["Week 1", "Week 2", ...]
 * getHeatMapCategories() // Monthly filter: ["Week 1", "Week 2", ...]
 * getHeatMapCategories() // Yearly filter: ["Jan", "Feb", ...]
 */
const getHeatMapCategories = () => {
  switch (heatmapCurrentFilter) {
    case "daily":
    case "weekly":
      return Array.from({ length: 18 }, (_, i) => `${i + 1}h`);

    case "monthly":
      return ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"];

    case "yearly":
      return getOrderedMonths(); // Dynamic ordering of months

    default:
      return ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"];
  }
};

// Get daily heatmap data
const getDailyHeatmapData = () => {
  const tempDailyData = getTodayData();
  return tempDailyData.map((item) => ({
    ...item,
    data: item.data.map((val) => (val === 0 ? 0 : val)),
  }));
};

// Get weekly heatmap data with dynamic ordering
const getWeeklyHeatmapData = () => {
  const tempWeeklyData = [
    { name: "Monday", data: getWeeklyLabor()["monday"].hours },
    { name: "Tuesday", data: getWeeklyLabor()["tuesday"].hours },
    { name: "Wednesday", data: getWeeklyLabor()["wednesday"].hours },
    { name: "Thursday", data: getWeeklyLabor()["thursday"].hours },
    { name: "Friday", data: getWeeklyLabor()["friday"].hours },
    { name: "Saturday", data: getWeeklyLabor()["saturday"].hours },
    { name: "Sunday", data: getWeeklyLabor()["sunday"].hours },
  ];
  return reorderWeeklyData(tempWeeklyData).map((item) => ({
    ...item,
    data: item.data.map((val) => (val === 0 ? 0 : val)),
  }));
};

// Get monthly heatmap data with dynamic ordering
const getMonthlyHeatmapData = () => {
  const tempMonthlyData = [
    { name: "Sunday", data: getMonthlyLabor()?.sunday?.counts },
    { name: "Monday", data: getMonthlyLabor()?.monday?.counts },
    { name: "Tuesday", data: getMonthlyLabor()?.tuesday?.counts },
    { name: "Wednesday", data: getMonthlyLabor()?.wednesday?.counts },
    { name: "Thursday", data: getMonthlyLabor()?.thursday?.counts },
    { name: "Friday", data: getMonthlyLabor()?.friday?.counts },
    { name: "Saturday", data: getMonthlyLabor()?.saturday?.counts },
  ];
  return reorderMonthlyData(tempMonthlyData).map((item) => ({
    ...item,
    data: item.data.map((val) => (val === 0 ? 0 : val)),
  }));
};

// Get yearly heatmap data with dynamic ordering
const getYearlyHeatmapData = () => {
  let yearlyLabor = getYearlyLabor();
  const tempYearlyData = [
    { name: "Week 1", data: yearlyLabor.Week1 },
    { name: "Week 2", data: yearlyLabor.Week2 },
    { name: "Week 3", data: yearlyLabor.Week3 },
    { name: "Week 4", data: yearlyLabor.Week4 },
    { name: "Week 5", data: yearlyLabor.Week5 },
  ];
  return tempYearlyData.map((item) => ({
    ...item,
    data: item.data.map((val) => (val === 0 ? 0 : val)),
  }));
};

/**
 * Updates heatmap data based on selected filter.
 *
 * @function updateHeatmapData
 * @private
 * @since 1.0.0
 */
function updateHeatmapData() {
  switch (heatmapCurrentFilter) {
    case "daily":
      heatmapData = getDailyHeatmapData();
      break;
    case "weekly":
      heatmapData = getWeeklyHeatmapData();
      break;
    case "monthly":
      heatmapData = getMonthlyHeatmapData();
      break;
    case "yearly":
      heatmapData = getYearlyHeatmapData();
      break;
    default:
      heatmapData = getMonthlyHeatmapData();
      break;
  }
}


const filterItem = document.querySelectorAll(".heatmap-sort-item");
const selectedHeatMapFilterValue = document.querySelector(
  ".selected-heatmap-filter"
);

// when user changes the sort filter.
Array.from(filterItem).map((item) => {
  item.addEventListener("click", () => {
    heatmapCurrentFilter = item.getAttribute("data-label");
    selectedHeatMapFilterValue.innerHTML = item?.innerHTML;
    updateHeatmapData();
    heatmapChart.updateOptions({
      series: heatmapData,
      xaxis: {
        categories: getHeatMapCategories(),
      },
      legend: {
        show: true,
      },
      plotOptions: {
        heatmap: {
          colorScale: {
            ranges: getDynamicRanges(heatmapData),
          },
        },
      },
    });
  });
});

// Set the default selected filter for heatmap
selectedHeatMapFilterValue.innerHTML = filterItem[3]?.innerHTML;

// Set default heatmap data
updateHeatmapData();

/**
 * Generates dynamic color ranges for heatmap visualization based on the current filter.
 *
 * The function returns an array of range objects, each containing:
 * - `from`: The starting value of the range.
 * - `to`: The ending value of the range.
 * - `color`: The color associated with the range.
 * - `name`: A label representing the range.
 *
 * The ranges are defined for various time filters: daily, weekly, monthly, and yearly.
 * Additionally, a gray range is added for values equal to 0.
 *
 * @returns {Array<Object>} An array of range objects for the current heatmap filter.
 */
function getDynamicRanges() {
  const ranges = {
    daily: [
      {
        from: 1,
        to: 5,
        color: "#83D9CE",
        name: "1-5",
      },
      {
        from: 6,
        to: 20,
        color: "#108575",
        name: "6-20",
      },
      {
        from: 21,
        to: 30,
        color: "#F59680",
        name: "21-30",
      },
      {
        from: 31,
        to: Infinity,
        color: "#f56140",
        name: "31+",
      },
    ],
    weekly: [
      {
        from: 1,
        to: 20,
        color: "#83D9CE",
        name: "1-20",
      },
      {
        from: 21,
        to: 50,
        color: "#108575",
        name: "21-50",
      },
      {
        from: 51,
        to: 80,
        color: "#F59680",
        name: "51-80",
      },
      {
        from: 81,
        to: Infinity,
        color: "#f56140",
        name: "81+",
      },
    ],
    monthly: [
      {
        from: 1,
        to: 20,
        color: "#83D9CE",
        name: "1-20",
      },
      {
        from: 21,
        to: 50,
        color: "#108575",
        name: "21-50",
      },
      {
        from: 51,
        to: 80,
        color: "#F59680",
        name: "51-80",
      },
      {
        from: 81,
        to: Infinity,
        color: "#f56140",
        name: "81+",
      },
    ],
    yearly: [
      {
        from: 1,
        to: 50,
        color: "#83D9CE",
        name: "1-50",
      },
      {
        from: 51,
        to: 100,
        color: "#108575",
        name: "51-100",
      },
      {
        from: 101,
        to: 200,
        color: "#F59680",
        name: "101-200",
      },
      {
        from: 201,
        to: Infinity,
        color: "#f56140",
        name: "201+",
      },
    ],
  };

  // Add gray range for 0 values
  const grayRange = {
    from: 0,
    to: 0,
    color: "#808080",
    name: "0",
  };

  const dynamicRanges = ranges[heatmapCurrentFilter];
  dynamicRanges.unshift(grayRange);

  return dynamicRanges;
}
// Heatmap Charts Generatedata
function generateData(count, yrange) {
  var i = 0;
  var series = [];
  while (i < count) {
    var x = (i + 1).toString() + "h";
    var y =
      Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

    series.push({
      x: x,
      y: y,
    });
    i++;
  }
  return series;
}

let heatmapseriesdata = [
  {
    name: "Sat",
    data: generateData(18, {
      min: 0,
      max: 90,
    }),
  },
  {
    name: "Fri",
    data: generateData(18, {
      min: 0,
      max: 90,
    }),
  },
  {
    name: "Thu",
    data: generateData(18, {
      min: 0,
      max: 90,
    }),
  },
  {
    name: "Wed",
    data: generateData(18, {
      min: 0,
      max: 90,
    }),
  },
  {
    name: "Tue",
    data: generateData(18, {
      min: 0,
      max: 90,
    }),
  },
  {
    name: "Mon",
    data: generateData(18, {
      min: 0,
      max: 90,
    }),
  },
  {
    name: "Sun",
    data: generateData(18, {
      min: 0,
      max: 90,
    }),
  },
];

let heatmapChartOptions = {
  series: heatmapData,
  chart: {
    height: 350,
    type: "heatmap",
    width: "100%",
    toolbar: { show: false },
  },
  dataLabels: {
    enabled: false,
  },
  plotOptions: {
    heatmap: {
      colorScale: {
        // Use the dynamic ranges
        ranges: getDynamicRanges(heatmapData),
      },
    },
  },
  tooltip: {
    enabled: true,
  },
  xaxis: {
    type: "category",
    tooltip: {
      enabled: false,
    },
    categories: getHeatMapCategories(),
  },
};

let heatmapChart = new ApexCharts(
  document.querySelector("#heatMapChart"),
  heatmapChartOptions
);

heatmapChart.render();

// ************************************ //
// *********** HEATMAP END ********** //
// ************************************ //



document.addEventListener('DOMContentLoaded', function () {
  // Update column chart
  updateColumnChartData();
});
