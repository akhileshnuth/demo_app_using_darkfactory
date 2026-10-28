const fs = require("node:fs");
const path = require("node:path");

const frontendDirectory = path.resolve(__dirname, "..");
const cssDirectory = path.join(frontendDirectory, "css");
const outputPath = path.join(frontendDirectory, "dist", "app.css");

function cssFiles() {
  return fs
    .readdirSync(cssDirectory, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".css"))
    .map((entry) => entry.name)
    .sort((left, right) => {
      if (left === "base.css") return -1;
      if (right === "base.css") return 1;
      return left.localeCompare(right);
    });
}

function readSources() {
  return cssFiles().map((fileName) => ({
    fileName,
    contents: fs.readFileSync(path.join(cssDirectory, fileName), "utf8"),
  }));
}

function validate(sources) {
  const errors = [];

  for (const { fileName, contents } of sources) {
    let depth = 0;
    for (const character of contents) {
      if (character === "{") depth += 1;
      if (character === "}") depth -= 1;
      if (depth < 0) break;
    }
    if (depth !== 0) errors.push(`${fileName}: unbalanced curly braces`);
  }

  return errors;
}

function lint() {
  const sources = readSources();
  const errors = validate(sources);
  if (errors.length > 0) {
    for (const error of errors) console.error(`CSS check failed: ${error}`);
    process.exitCode = 1;
    return;
  }
  console.log(`CSS check passed (${sources.length} file${sources.length === 1 ? "" : "s"})`);
}

function build() {
  const sources = readSources();
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(
    outputPath,
    sources.map(({ contents }) => contents).join("\n"),
    "utf8",
  );
  console.log(`CSS built: ${path.relative(process.cwd(), outputPath)}`);
}

const operation = process.argv[2];
if (operation === "lint") lint();
else if (operation === "build") build();
else {
  console.error("Usage: node scripts/build-css.js <build|lint>");
  process.exitCode = 1;
}
