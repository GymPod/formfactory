// Global file selection logger
(function () {
  function serializeFiles(fileList) {
    if (!fileList) return [];
    try {
      return Array.prototype.map.call(fileList, function (f) {
        return {
          name: f && f.name || '',
          size: f && typeof f.size === 'number' ? f.size : null,
          type: f && f.type || '',
          lastModified: f && f.lastModified ? f.lastModified : null
        };
      });
    } catch (_) { return []; }
  }

  function logSelection(input) {
    try {
      var payload = {
        event: 'file_selection',
        page: window.location.pathname,
        input: {
          id: input.id || null,
          name: input.name || null,
          multiple: !!input.multiple,
          accept: input.getAttribute('accept') || null
        },
        files: serializeFiles(input.files),
        formAction: (input.form && input.form.getAttribute('action')) || null,
        ts: new Date().toISOString()
      };

      var body = JSON.stringify(payload);

      // Prefer sendBeacon for reliability on navigation
      if (navigator.sendBeacon) {
        var blob = new Blob([body], { type: 'application/json' });
        navigator.sendBeacon('/log/file-selection', blob);
      } else if (window.fetch) {
        fetch('/log/file-selection', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body,
          keepalive: true,
          credentials: 'same-origin'
        }).catch(function () { /* ignore */ });
      }
    } catch (_) { /* ignore */ }
  }

  function attach(root) {
    try {
      var inputs = (root || document).querySelectorAll('input[type="file"]');
      inputs.forEach(function (inp) {
        // Avoid duplicate listeners
        if (inp.__ff_logger_attached) return;
        inp.addEventListener('change', function () { logSelection(inp); }, true);
        inp.__ff_logger_attached = true;
      });
    } catch (_) { /* ignore */ }
  }

  // Initial attach
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { attach(document); }, { once: true });
  } else {
    attach(document);
  }

  // Observe dynamic additions
  try {
    var obs = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var m = mutations[i];
        if (m.type === 'childList' && (m.addedNodes && m.addedNodes.length)) {
          m.addedNodes.forEach(function (node) {
            if (node.nodeType === 1) { // element
              attach(node);
            }
          });
        }
      }
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
  } catch (_) { /* ignore */ }
})();

