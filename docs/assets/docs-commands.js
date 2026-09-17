/* Catalog facts are inert data. Reader filters never assert project activation. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DocsCommands = factory();
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";
  let cached, pending;
  const text = value => typeof value === "string" && value.length <= 20000;
  const texts = value => Array.isArray(value) && value.length <= 100 && value.every(text);
  const id = value => typeof value === "string" && /^(slash|shell):[a-z][a-z0-9-]*$/.test(value);
  const route = value => value && typeof value.page === "string" && /^[a-z][a-z0-9-]*$/.test(value.page) &&
    typeof value.section === "string" && /^[a-z0-9-]*$/.test(value.section);
  const suites = value => Array.isArray(value) && value.length > 0 && value.length <= 2 &&
    new Set(value).size === value.length && value.every(s => ["cg", "cr"].includes(s));

  /** Validate every displayed field, route and reference before mounting any row. */
  function validate(value) {
    if (value?.schemaVersion !== "compound-gpid-docs-commands-v1" || !text(value.generatorVersion) ||
      !/^[a-f0-9]{64}$/.test(value.sourceDigest) || !Array.isArray(value.commands) || !value.commands.length ||
      value.commands.length > 1000 || !Array.isArray(value.workflows) || value.workflows.length > 100) throw Error("Invalid command index");
    const ids = new Set();
    for (const row of value.commands) {
      if (!id(row.id) || ids.has(row.id) || !row.id.startsWith(row.kind + ":") ||
        ![row.name, row.summary, row.usage, row.ownerModule].every(text) || !suites(row.supportedSuites) || !route(row.route) ||
        ![row.examples, row.prerequisites, row.outputs, row.constraints, row.intents, row.supportedOS, row.supportedPlatforms].every(texts) ||
        !text(row.availability?.status) || !Array.isArray(row.relatedCommands) || row.relatedCommands.length > 100 ||
        !row.relatedCommands.every(r => id(r.id) && text(r.relation))) throw Error("Invalid command row");
      ids.add(row.id);
    }
    if (value.commands.some(row => row.relatedCommands.some(r => !ids.has(r.id)))) throw Error("Unknown related command");
    const workflows = new Set();
    for (const row of value.workflows) {
      if (typeof row.id !== "string" || !/^[a-z][a-z0-9-]*$/.test(row.id) || workflows.has(row.id) || ![row.title, row.summary].every(text) ||
        !suites(row.supportedSuites) || ![row.prerequisites, row.intents].every(texts) || !route(row.route) ||
        !Array.isArray(row.steps) || !row.steps.length || row.steps.length > 100 ||
        !row.steps.every((step, index) => step.order === index + 1 && ids.has(step.commandId) && text(step.purpose))) throw Error("Invalid workflow row");
      workflows.add(row.id);
    }
    return value;
  }

  /** Return matching complete records without collapsing kind IDs or repeated steps. */
  function select(value, suite, kind, query) {
    const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    return [...value.commands, ...value.workflows.map(row => ({ ...row, kind: "workflow" }))].filter(row =>
      (!suite || row.supportedSuites.includes(suite)) && (!kind || row.kind === kind) &&
      words.every(word => [row.id, row.name || row.title, row.summary, row.usage || "", ...row.intents].join(" ").toLowerCase().includes(word)));
  }

  function node(tag, content, className) {
    const element = document.createElement(tag);
    if (content !== undefined) element.textContent = content;
    if (className) element.className = className;
    return element;
  }
  function list(parent, title, values) {
    if (!values.length) return;
    parent.append(node("p", title, "command-fact-label"));
    const ul = node("ul"); values.forEach(value => ul.append(node("li", value))); parent.append(ul);
  }
  function link(row, label) {
    const a = node("a", label);
    a.href = `#page=${encodeURIComponent(row.route.page)}${row.route.section ? `&section=${encodeURIComponent(row.route.section)}` : ""}`;
    return a;
  }
  function invocation(usage) {
    const block = node("div", undefined, "code-block"), pre = node("pre"), code = node("code", usage);
    const copy = node("button", "Copy", "copy-code"), select = node("button", "Select code", "select-code"), status = node("p", "", "copy-status");
    copy.type = select.type = "button"; copy.setAttribute("aria-label", "Copy command"); select.hidden = true;
    status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
    pre.tabIndex = 0; pre.setAttribute("aria-label", "Command invocation"); pre.append(copy, code); block.append(pre, status, select); return block;
  }
  function card(row, catalog) {
    const details = node("details", undefined, "command-card"); details.dataset.commandId = row.kind === "workflow" ? `workflow:${row.id}` : row.id;
    details.append(node("summary", `${row.name || row.title} · ${row.kind} · ${row.supportedSuites.join(" / ").toUpperCase()}`), node("p", row.summary));
    list(details, "Prerequisites", row.prerequisites);
    if (row.kind === "workflow") {
      details.append(node("p", "Follow these steps in order. This recipe ID is not a command to run."));
      const ol = node("ol");
      row.steps.forEach(step => {
        const command = catalog.commands.find(c => c.id === step.commandId), li = node("li");
        li.append(node("code", command.usage), node("p", step.purpose)); ol.append(li);
      });
      details.append(ol);
    } else {
      details.append(node("p", row.kind === "slash" ? "AI chat invocation" : "Terminal invocation"));
      details.append(invocation(row.usage));
      list(details, "Examples", row.examples); list(details, "Outputs", row.outputs); list(details, "Constraints", row.constraints);
      details.append(node("p", `Owner: ${row.ownerModule}. Catalog availability: ${row.availability.status}. Host certification is recorded separately.`));
      list(details, "Declared platforms", row.supportedPlatforms); list(details, "Declared operating systems", row.supportedOS);
      if (row.relatedCommands.length) {
        details.append(node("p", "Related commands", "command-fact-label")); const ul = node("ul");
        row.relatedCommands.forEach(related => {
          const target = catalog.commands.find(c => c.id === related.id), li = node("li");
          li.append(link(target, `${target.name} (${target.kind}; ${related.relation})`)); ul.append(li);
        }); details.append(ul);
      }
    }
    details.append(link(row, "Read the guide")); return details;
  }

  /** Mount on the command hub only; index loading is lazy and bound to this channel. */
  function mount(documentView, config) {
    if (config.id !== "commands") return;
    const panel = node("section", undefined, "command-browser"); panel.setAttribute("aria-label", "Browse commands and workflows");
    panel.append(node("h2", "Browse commands and workflows"), node("p", "Filter the complete catalog. Suite choices here do not activate workflows in your project."));
    const filters = node("div", undefined, "command-filters");
    function filter(label, choices, name) {
      const wrapper = node("label", label), select = node("select"); select.dataset.commandFilter = name;
      choices.forEach(([value, title]) => { const option = node("option", title); option.value = value; select.append(option); });
      wrapper.append(select); filters.append(wrapper); return select;
    }
    const suite = filter("Suite", [["", "All suites"], ["cg", "Technical (CG)"], ["cr", "Research (CR)"]], "suite");
    const kind = filter("Invocation", [["", "All kinds"], ["slash", "AI chat"], ["shell", "Terminal"], ["workflow", "Workflow recipes"]], "kind");
    const label = node("label", "Find a command"), query = node("input"); query.type = "search"; query.dataset.commandFilter = "query"; label.append(query); filters.append(label);
    const status = node("p", "Loading command catalog…"); status.setAttribute("role", "status");
    const retry = node("button", "Retry command catalog"); retry.type = "button"; retry.hidden = true;
    const results = node("div"); results.dataset.commandResults = "";
    panel.append(filters, status, retry, results); documentView.querySelector("h1").after(panel);
    let revision = 0;
    async function render() {
      const request = ++revision; retry.hidden = true;
      try {
        await DocsIdentity.assertCurrent();
        if (!cached) {
          pending ||= DocsIdentity.read("assets/command-index.json").then(JSON.parse).then(validate).then(value => (cached = value)).finally(() => { pending = null; });
          await pending;
        }
        if (request !== revision || !panel.isConnected) return;
        const rows = select(cached, suite.value, kind.value, query.value);
        results.replaceChildren(...rows.map(row => card(row, cached)));
        status.textContent = `${rows.length} matching commands and workflows`;
        DocsTools.mount(results);
      } catch (error) {
        if (request !== revision || !panel.isConnected) return;
        results.replaceChildren(); status.textContent = error.buildChanged ? "The documentation build changed. Reload the full page to browse commands." : "Command catalog unavailable. Try again.";
        retry.hidden = !!error.buildChanged;
      }
    }
    filters.addEventListener("input", render); filters.addEventListener("change", render); retry.addEventListener("click", render); render();
  }
  return { validate, select, mount };
});
