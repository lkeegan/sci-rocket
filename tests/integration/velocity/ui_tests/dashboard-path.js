const fs = require("fs");
const path = require("path");

const dashboardPath = path.resolve(
  __dirname,
  "..",
  "output",
  "velocity",
  "sci-dash",
  "index.html"
);

module.exports = {
  dashboardPath,
  hasDashboard: fs.existsSync(dashboardPath),
};
