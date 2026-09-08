"use strict";

// Parses only standalone cg:auto markers outside fenced code blocks. This keeps
// documentation examples from being mistaken for generator-owned regions.
function findManagedMarkers(text) {
  const markers = [];
  let active = null;
  let fence = null;
  let lineStart = 0;

  while (lineStart < text.length) {
    const newline = text.indexOf("\n", lineStart);
    const lineEnd = newline === -1 ? text.length : newline;
    const line = text.slice(lineStart, lineEnd).replace(/\r$/, "");
    const fenceMatch = /^[ \t]*(```|~~~)/.exec(line);

    if (fence) {
      if (fenceMatch && fenceMatch[1] === fence) fence = null;
    } else if (fenceMatch) {
      fence = fenceMatch[1];
    } else {
      const open = /^[ \t]*<!--[ \t]*cg:auto:(?!end\b)([a-z0-9-]+)[ \t]*-->[ \t]*$/.exec(line);
      const close = /^[ \t]*<!--[ \t]*cg:auto:end[ \t]*-->[ \t]*$/.exec(line);
      if (open) {
        if (active) throw new Error(`nested cg:auto marker '${open[1]}' inside '${active.section}'`);
        active = {
          section: open[1],
          openIndex: lineStart,
          openEnd: lineEnd,
        };
      } else if (close) {
        if (!active) throw new Error("unbalanced cg:auto markers (closing marker without opening marker)");
        markers.push({ ...active, closeIndex: lineStart, closeEnd: lineEnd });
        active = null;
      }
    }

    if (newline === -1) break;
    lineStart = newline + 1;
  }

  if (active) throw new Error(`unbalanced cg:auto marker '${active.section}' (missing closing marker)`);
  return markers;
}

function replaceManagedInterior(text, section, content) {
  const marker = findManagedMarkers(text).find((entry) => entry.section === section);
  if (!marker) throw new Error(`missing cg:auto section '${section}'`);
  const lineEnding = text.includes("\r\n") ? "\r\n" : "\n";
  const normalizedContent = content.replace(/\n/g, lineEnding);
  return text.slice(0, marker.openEnd) + lineEnding + normalizedContent + text.slice(marker.closeIndex);
}

function normalizeManagedInteriors(text) {
  const markers = findManagedMarkers(text);
  let normalized = "";
  let cursor = 0;
  for (const marker of markers) {
    normalized += text.slice(cursor, marker.openEnd);
    normalized += "<!--cg:auto-interior-->";
    cursor = marker.closeIndex;
  }
  return normalized + text.slice(cursor);
}

module.exports = { findManagedMarkers, replaceManagedInterior, normalizeManagedInteriors };
