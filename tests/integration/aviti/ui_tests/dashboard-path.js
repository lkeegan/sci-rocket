const fs = require("fs");
const path = require("path");

const dashboardPath = path.resolve(
  __dirname,
  "..",
  "output",
  "fastq_from_aviti_one_run",
  "sci-dash",
  "index.html"
);

module.exports = {
  dashboardPath,
  hasDashboard: fs.existsSync(dashboardPath),
};
