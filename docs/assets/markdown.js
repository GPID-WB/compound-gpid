function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function slugify(value) { return DocsSearch.slugify(value); }

function normalizePath(path) {
  const output = [];
  path.split("/").forEach((part) => {
    if (!part || part === ".") return;
    if (part === "..") output.pop(); else output.push(part);
  });
  return output.join("/");
}

function resolveDocLink(href) {
  if (/^(https?:|mailto:)/i.test(href)) {
    return { href, external: true };
  }
  if (href.startsWith("#")) {
    return activePage
      ? { href: `#page=${activePage}&section=${encodeURIComponent(href.slice(1))}` }
      : { href: "#home" };
  }
  const [path, fragment] = href.split("#", 2);
  if (/(?:^|\/)README\.md$/i.test(path)) return { href: "#home" };
  const activeFile = pageMap.get(activePage)?.file || "";
  const base = activeFile.includes("/") ? activeFile.slice(0, activeFile.lastIndexOf("/") + 1) : "";
  const target = normalizePath(`${base}${path}`);
  const page = fileMap.get(target);
  if (page) {
    const section = fragment ? `&section=${encodeURIComponent(fragment)}` : "";
    return { href: `#page=${page.id}${section}` };
  }
  if (/^[a-z0-9_./-]+(?:#[^\s]*)?$/i.test(href)) {
    const branch = document.body.dataset.channel || "dev";
    return { href: new URL(href, `https://github.com/GPID-WB/compound-gpid/blob/${branch}/docs/${activeFile}`).href, external: true };
  }
  return null;
}

function inlineMarkdown(value) {
  let html = escapeHtml(value);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  html = html.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]+&quot;)?\)/g, (_, label, href) => {
    const resolved = resolveDocLink(href.replace(/&amp;/g, "&"));
    if (!resolved) return `<span class="unresolved-link" title="See the source file for this reference">${label}</span>`;
    const external = resolved.external ? ' target="_blank" rel="noreferrer"' : "";
    return `<a href="${escapeHtml(resolved.href)}"${external}>${label}</a>`;
  });
  return html;
}

function renderTable(lines) {
  const cells = (line) => {
    const input = line.trim().replace(/^\||\|$/g, "");
    const output = [];
    let cell = "";
    let inCode = false;
    for (let index = 0; index < input.length; index += 1) {
      const character = input[index];
      if (character === "\\" && input[index + 1] === "|") { cell += "|"; index += 1; continue; }
      if (character === "`") inCode = !inCode;
      if (character === "|" && !inCode) { output.push(inlineMarkdown(cell.trim())); cell = ""; continue; }
      cell += character;
    }
    output.push(inlineMarkdown(cell.trim()));
    return output;
  };
  const header = cells(lines[0]);
  const rows = lines.slice(2).map(cells);
  return `<div class="table-wrap" role="region" aria-label="Scrollable table" tabindex="0"><table><thead><tr>${header.map((cell) => `<th scope="col">${cell}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function listLine(line) {
  const match = line.match(/^(\s*)([-*+]|\d+\.)\s+(.+)$/);
  return match && { indent: match[1].replace(/\t/g, "    ").length, ordered: /\d+\./.test(match[2]), text: match[3] };
}

function renderList(lines, start, indent) {
  const first = listLine(lines[start]);
  const tag = first.ordered ? "ol" : "ul";
  const items = [];
  let index = start;
  while (index < lines.length) {
    const item = listLine(lines[index]);
    if (!item || item.indent !== indent || item.ordered !== first.ordered) break;
    const body = [item.text];
    index += 1;
    while (index < lines.length) {
      const next = listLine(lines[index]);
      if (next && next.indent === indent && next.ordered === first.ordered) break;
      if (next && next.indent < indent) break;
      if (!lines[index].trim()) {
        const afterBlank = listLine(lines[index + 1] || "");
        if (afterBlank && afterBlank.indent === indent && afterBlank.ordered === first.ordered) { index += 1; break; }
        break;
      }
      const strip = Math.min(lines[index].match(/^\s*/)[0].length, indent + 3);
      body.push(lines[index].slice(strip));
      index += 1;
    }
    const checkbox = body[0].match(/^\[([ xX])\]\s+(.+)$/);
    if (checkbox) body[0] = checkbox[2];
    const prefix = checkbox ? `<span class="task-box" aria-hidden="true">${checkbox[1].trim() ? "✓" : ""}</span>` : "";
    items.push(`<li>${prefix}${markdownToHtml(body.join("\n"))}</li>`);
  }
  return { html: `<${tag}>${items.join("")}</${tag}>`, index };
}

function markdownToHtml(markdown, headings = new Map()) {
  const lines = markdown.replace(/^\uFEFF/, "").replace(/^---[\s\S]*?---\s*/, "").split("\n");
  const output = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index += 1; continue; }
    if (line.trim().startsWith("<!--")) {
      while (index < lines.length && !lines[index].includes("-->")) index += 1;
      index += 1;
      continue;
    }
    if (line.startsWith("```")) {
      const language = line.slice(3).trim();
      const code = [];
      index += 1;
      while (index < lines.length && !lines[index].startsWith("```")) code.push(lines[index++]);
      index += 1;
      output.push(`<pre><button class="copy-code" type="button" aria-label="Copy code">Copy</button><code class="language-${escapeHtml(language)}">${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }
    if (/^\|/.test(line) && /^\|?\s*:?-{3,}/.test(lines[index + 1] || "")) {
      const table = [line];
      index += 1;
      while (index < lines.length && /^\|/.test(lines[index])) table.push(lines[index++]);
      output.push(renderTable(table));
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      const text = heading[2];
      const base = slugify(text);
      const count = headings.get(base) || 0;
      headings.set(base, count + 1);
      const id = count ? `${base}-${count}` : base;
      output.push(`<h${level} id="${id}">${inlineMarkdown(text)}</h${level}>`);
      index += 1;
      continue;
    }
    if (/^([-*_])\1\1+\s*$/.test(line)) { output.push("<hr>"); index += 1; continue; }
    if (line.startsWith(">")) {
      const quote = [];
      while (index < lines.length && lines[index].startsWith(">")) quote.push(lines[index++].replace(/^>\s?/, ""));
      output.push(`<blockquote>${markdownToHtml(quote.join("\n"))}</blockquote>`);
      continue;
    }
    const list = listLine(line);
    if (list) {
      const rendered = renderList(lines, index, list.indent);
      output.push(rendered.html);
      index = rendered.index;
      continue;
    }
    const paragraph = [line];
    index += 1;
    while (index < lines.length && lines[index].trim()
      && !/^(#{1,6}\s|```|\||>|[-*_]{3,}\s*$)/.test(lines[index])
      && !listLine(lines[index])) paragraph.push(lines[index++]);
    output.push(`<p>${inlineMarkdown(paragraph.join(" "))}</p>`);
  }
  return output.join("\n");
}

