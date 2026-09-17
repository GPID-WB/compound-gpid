/* Reading controls are separate from document fetching and Markdown parsing. */
(function (root) {
  "use strict";
  let observer, article, toc, headings = [], offset = 88;
  const labels = { "suite-cg": ["technical", "Technical (CG)"], "suite-cr": ["research", "Research (CR)"],
    "cap-skill-management": ["technical", "Technical (CG)"] };
  const identity = owner => labels[owner] || ["shared", "Shared"];

  /** Create a labelled presentation badge from declared canonical module ownership. */
  function badge(owner) {
    const [kind, label] = identity(owner), span = document.createElement("span");
    span.className = `suite-badge suite-${kind}`; span.textContent = label;
    return span;
  }

  /** Render only primary links; registration remains complete for references and redirects. */
  function buildNavigation(groups) {
    const navigation = document.querySelector("[data-navigation]"); navigation.replaceChildren();
    const appendLink = (parent, id, title) => {
      const link = document.createElement("a");
      link.href = id === "home" ? "#home" : `#page=${encodeURIComponent(id)}`;
      link.dataset.route = id; link.textContent = title.replace(/`/g, ""); parent.append(link);
    };
    appendLink(navigation, "home", "Overview");
    groups.forEach((group, index) => {
      const section = document.createElement("section"), button = document.createElement("button"), links = document.createElement("div");
      section.className = "nav-group"; section.dataset.group = group.title;
      button.type = "button"; button.dataset.navGroup = ""; button.textContent = group.title;
      button.setAttribute("aria-label", group.title);
      links.id = `nav-group-${index}`; links.hidden = true;
      button.setAttribute("aria-controls", links.id); button.setAttribute("aria-expanded", "false");
      button.addEventListener("click", () => { links.hidden = !links.hidden; button.setAttribute("aria-expanded", String(!links.hidden)); });
      group.pages.filter(DocsContract.sidebarVisible).forEach(page => appendLink(links, page.id, page.title));
      section.append(button, links); navigation.append(section);
    });
  }

  /** Expose the active group without collapsing a reader's other open groups. */
  function updateNavigation(page, pages) {
    document.querySelectorAll("[data-route]").forEach(link => {
      const active = link.dataset.route === (page || "home"); link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current");
    });
    const group = pages.find(config => config.id === page)?.group;
    document.querySelectorAll(".nav-group").forEach(section => {
      if (section.dataset.group !== group) return;
      section.querySelector("div").hidden = false; section.querySelector("button").setAttribute("aria-expanded", "true");
    });
    setNavigationOpen(false);
  }

  /** Open the mobile primary drawer; return keyboard focus when it closes. */
  function setNavigationOpen(opened) {
    const sidebar = document.querySelector(".sidebar"), button = document.querySelector("[data-menu-toggle]"), close = document.querySelector("[data-menu-close]");
    const mobile = window.matchMedia("(max-width: 820px)").matches, isOpen = opened && mobile;
    const returnFocus = sidebar.contains(document.activeElement) || document.activeElement === close;
    sidebar.classList.toggle("open", isOpen); sidebar.inert = mobile && !isOpen;
    sidebar.setAttribute("aria-hidden", String(mobile && !isOpen));
    button.setAttribute("aria-expanded", String(isOpen)); button.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
    close.hidden = !isOpen; document.querySelector("main").inert = isOpen;
    document.body.classList.toggle("navigation-open", isOpen);
    if (isOpen) sidebar.querySelector("a")?.focus();
    if (mobile && !isOpen && returnFocus) button.focus();
  }

  /** Measure actual sticky header geometry, including a composed development banner. */
  function measure() {
    const header = document.querySelector(".topbar");
    const banner = document.querySelector(".dev-preview-banner");
    const bannerHeight = banner ? banner.getBoundingClientRect().height : 0;
    document.documentElement.style.setProperty("--banner-height", `${bannerHeight}px`);
    offset = Math.max(0, header.getBoundingClientRect().bottom) + 16;
    document.documentElement.style.setProperty("--reading-offset", `${offset}px`);
  }

  /** Clear route-owned observers and controls before loading or displaying an error. */
  function clear() {
    observer?.disconnect(); observer = null; headings = [];
    toc = document.querySelector("[data-toc]"); toc.hidden = true;
    toc.querySelector("nav").replaceChildren();
    document.querySelector("[data-breadcrumb]").replaceChildren();
    document.querySelector("[data-next-steps]").replaceChildren();
  }

  function track() {
    if (!toc) return;
    const current = headings.filter(node => node.getBoundingClientRect().top <= offset + 24).at(-1) || headings[0];
    toc.querySelectorAll("a").forEach(link => {
      if (link.dataset.section === current?.id) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }

  /** Mount article-only TOC, breadcrumbs and deliberate next steps after a successful render. */
  function mount(config, pages) {
    article = document.querySelector("[data-document]"); measure();
    const crumb = document.querySelector("[data-breadcrumb]");
    const home = document.createElement("a"); home.href = "#home"; home.textContent = "Home";
    const group = document.createElement("span"); group.textContent = config.group;
    const current = document.createElement("span"); current.textContent = config.title;
    current.setAttribute("aria-current", "page");
    crumb.append(home, group, current, badge(config.ownerModule));
    headings = [...article.querySelectorAll("h2, h3")];
    if (headings.length >= 2) {
      const list = document.createElement("ol");
      headings.forEach(heading => {
        const item = document.createElement("li"), link = document.createElement("a");
        link.textContent = heading.textContent;
        link.href = `#page=${config.id}&section=${encodeURIComponent(heading.id)}`;
        link.dataset.section = heading.id;
        item.className = heading.tagName === "H3" ? "toc-subsection" : "";
        item.append(link); list.append(item);
      });
      toc.querySelector("nav").append(list); toc.hidden = false;
      toc.open = window.matchMedia("(min-width: 1200px)").matches;
      observer = new IntersectionObserver(track, { rootMargin: `-${offset}px 0px -60% 0px` });
      headings.forEach(heading => observer.observe(heading)); track();
    }
    article.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(heading => {
      heading.setAttribute("aria-label", heading.textContent);
      const link = document.createElement("a"); link.className = "heading-permalink";
      link.href = `#page=${config.id}&section=${encodeURIComponent(heading.id)}`;
      link.setAttribute("aria-label", `Link to ${heading.textContent}`); link.textContent = "#";
      heading.append(link);
    });
    const next = document.querySelector("[data-next-steps]");
    if (config.next?.length) {
      const title = document.createElement("h2"); title.textContent = "Next useful steps"; next.append(title);
      config.next.forEach(id => {
        const target = pages.find(page => page.id === id), link = document.createElement("a");
        link.href = `#page=${id}`; link.textContent = target.title; next.append(link);
      });
    }
  }

  /** Move within the current article without refetching, announcing the article, or adding history. */
  function move(section, parsed, config, focus = false) {
    article = document.querySelector("[data-document]"); measure();
    document.querySelector("[data-route-notice]")?.remove();
    const resolved = section && DocsContract.resolveSection(parsed.headings, section, config.sectionAliases);
    const target = resolved?.status === "resolved" && [...article.querySelectorAll("[id]")].find(node => node.id === resolved.id);
    if (section && !target) {
      const notice = document.createElement("p"); notice.dataset.routeNotice = ""; notice.setAttribute("role", "status");
      notice.textContent = resolved.status === "ambiguous" ? "This old section link is ambiguous. Select a heading on this page." : "This section is not available. Showing the page top.";
      article.prepend(notice);
    }
    const element = target || article;
    window.scrollTo({ top: Math.max(0, window.scrollY + element.getBoundingClientRect().top - offset), behavior: "instant" });
    if (focus) {
      element.setAttribute("tabindex", "-1"); element.focus({ preventScroll: true });
    }
    track();
  }

  /** Attach geometry and explicit-focus controls once, not once per route. */
  function init() {
    measure();
    new ResizeObserver(measure).observe(document.querySelector(".topbar"));
    const banner = document.querySelector(".dev-preview-banner");
    if (banner) new ResizeObserver(measure).observe(banner);
    window.addEventListener("scroll", track, { passive: true });
    window.addEventListener("resize", () => {
      measure();
      if (window.matchMedia("(min-width: 1200px)").matches) document.querySelector("[data-toc]").open = true;
    });
    document.querySelector(".skip-link").addEventListener("click", event => {
      event.preventDefault(); document.querySelector("#content").focus({ preventScroll: true });
    });
    const sidebar = document.querySelector(".sidebar"), close = document.querySelector("[data-menu-close]");
    document.querySelector("[data-menu-toggle]").addEventListener("click", () => setNavigationOpen(!sidebar.classList.contains("open")));
    close.addEventListener("click", () => setNavigationOpen(false));
    window.addEventListener("resize", () => setNavigationOpen(false));
    document.addEventListener("keydown", event => {
      if (!sidebar.classList.contains("open")) return;
      if (event.key === "Escape") setNavigationOpen(false);
      if (event.key !== "Tab") return;
      const controls = [...sidebar.querySelectorAll("a, button")].filter(node => node.getClientRects().length);
      const first = controls[0], last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); close.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); close.focus(); }
      else if (document.activeElement === close) { event.preventDefault(); (event.shiftKey ? last : first).focus(); }
    });
  }
  root.DocsReading = { badge, buildNavigation, updateNavigation, setNavigationOpen, clear, mount, move, init };
})(globalThis);
