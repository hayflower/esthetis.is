/* Esthetis — progressive enhancement only.
   The page is complete and navigable without this file. */
(function () {
  "use strict";

  /* Copy buttons appear only where the clipboard API can actually serve them. */
  if (navigator.clipboard && window.isSecureContext) {
    document.documentElement.classList.add("js-clipboard");

    document.addEventListener("click", function (event) {
      var button = event.target.closest(".copy[data-copy]");
      if (!button || button.dataset.done) return;

      navigator.clipboard.writeText(button.getAttribute("data-copy")).then(function () {
        var label = button.textContent;
        button.dataset.done = "1";
        button.textContent = "copied";
        setTimeout(function () {
          delete button.dataset.done;
          button.textContent = label;
        }, 1600);
      });
    });
  }

  /* Mark the section the reader is in, in the document index. */
  var links = [].slice.call(document.querySelectorAll(".index a[href^='#']"));
  if (!links.length || !window.IntersectionObserver) return;

  var byId = {};
  var sections = links.map(function (link) {
    var section = document.getElementById(link.hash.slice(1));
    if (section) byId[section.id] = link;
    return section;
  }).filter(Boolean);

  var visible = new Set();

  function render() {
    var current = sections.filter(function (s) { return visible.has(s.id); })[0];
    links.forEach(function (link) {
      if (current && byId[current.id] === link) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) visible.add(entry.target.id);
      else visible.delete(entry.target.id);
    });
    render();
  }, { rootMargin: "-10% 0px -70% 0px" });

  sections.forEach(function (section) { observer.observe(section); });
})();
