const PptxGenJS = require("pptxgenjs");
const path = require("node:path");

const OUTPUT_PATH = path.join(__dirname, "output.pptx");

const COLORS = {
  ink: "1E252B",
  paper: "F6F2EA",
  accent: "D94F36",
  support: "1D7872",
  muted: "646D73",
  white: "FFFFFF",
};

const FONTS = {
  display: "Aptos Display",
  body: "Aptos",
};

function addText(slide, text, options) {
  slide.addText(text, {
    margin: 0,
    fontFace: FONTS.body,
    color: COLORS.ink,
    breakLine: false,
    ...options,
  });
}

function addTitleSlide(pptx) {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.ink };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 0.22,
    h: 7.5,
    fill: { color: COLORS.accent },
    line: { color: COLORS.accent },
  });
  addText(slide, "Presentation title", {
    x: 0.9,
    y: 2.35,
    w: 11.3,
    h: 0.8,
    fontFace: FONTS.display,
    fontSize: 42,
    bold: true,
    color: COLORS.paper,
  });
  addText(slide, "One sentence that states the audience-facing promise", {
    x: 0.92,
    y: 3.4,
    w: 10.8,
    h: 0.5,
    fontSize: 20,
    color: "D6DCDF",
  });
  addText(slide, "Presenter  |  Date", {
    x: 0.92,
    y: 6.55,
    w: 5,
    h: 0.25,
    fontSize: 11,
    color: "A8B0B5",
  });
  slide.addNotes("Open with the audience's decision.\nState the promised outcome.");
}

function addEvidenceSlide(pptx) {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.paper };
  addText(slide, "Turn report evidence into an audience argument", {
    x: 0.72,
    y: 0.48,
    w: 11.8,
    h: 0.55,
    fontFace: FONTS.display,
    fontSize: 30,
    bold: true,
  });
  addText(slide, "The report preserves detail; the deck makes deliberate editorial choices.", {
    x: 0.74,
    y: 1.15,
    w: 10.8,
    h: 0.3,
    fontSize: 14,
    color: COLORS.muted,
  });

  const rows = [
    ["Artifact", "Responsibility"],
    ["deck-report.md", "Complete evidence, context, diagrams, and caveats"],
    ["build-deck.js", "Slide sequence, emphasis, layouts, and native objects"],
    ["output.pptx", "Editable audience-facing presentation"],
  ];
  slide.addTable(rows, {
    x: 0.75,
    y: 2.0,
    w: 7.2,
    h: 3.1,
    border: { pt: 1, color: "D8D2C8" },
    fill: { color: COLORS.white },
    color: COLORS.ink,
    fontFace: FONTS.body,
    fontSize: 16,
    margin: 0.12,
    rowH: 0.68,
    bold: false,
  });

  slide.addShape(pptx.ShapeType.roundRect, {
    x: 8.45,
    y: 2.0,
    w: 4.1,
    h: 3.1,
    rectRadius: 0.08,
    fill: { color: COLORS.support },
    line: { color: COLORS.support },
  });
  addText(slide, "Native output", {
    x: 8.85,
    y: 2.55,
    w: 3.3,
    h: 0.45,
    fontFace: FONTS.display,
    fontSize: 24,
    bold: true,
    color: COLORS.white,
    align: "center",
  });
  addText(slide, "Text, shapes, tables, charts, and notes remain independently editable.", {
    x: 8.95,
    y: 3.25,
    w: 3.1,
    h: 1.15,
    fontSize: 17,
    color: COLORS.white,
    align: "center",
    valign: "mid",
  });
  slide.addNotes("Preserve report nuance during compression.\nCall out why editability matters.");
}

async function buildDeck() {
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Presentation author";
  pptx.company = "Organization";
  pptx.subject = "Editable PowerPoint presentation";
  pptx.title = "Presentation title";
  addTitleSlide(pptx);
  addEvidenceSlide(pptx);

  await pptx.writeFile({ fileName: OUTPUT_PATH });
  console.log(`Wrote ${OUTPUT_PATH}`);
}

buildDeck().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
