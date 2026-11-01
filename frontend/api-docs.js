// Keep the Swagger bootstrap external: no inline scripts or relaxed CSP.
window.ui = SwaggerUIBundle({
  url: '/api/openapi.json',
  dom_id: '#swagger-ui',
  deepLinking: true,
  showExtensions: true,
  showCommonExtensions: true,
  // Do not send schemas to the public Swagger validator service.
  validatorUrl: null,
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
  layout: 'BaseLayout',
});

// Swagger renders icon-only expand buttons; give each one an accessible name from its operation.
function improveSwaggerAccessibility(root) {
  for (const button of root.querySelectorAll('button.expand-operation:not([aria-label])')) {
    const block = button.closest('.opblock');
    const method = block?.querySelector('.opblock-summary-method')?.textContent.trim() || '';
    const path = block?.querySelector('.opblock-summary-path')?.textContent.trim() || 'operation';
    button.setAttribute('aria-label', `Show details for ${method} ${path}`.trim());
  }
  // Swagger renders section headings (<h3> groups, <h4> Schemas) directly under the <h1>; expose them as level 2.
  const sectionHeadings = 'h3.opblock-tag:not([aria-level]), section.models > h4:not([aria-level])';
  for (const heading of root.querySelectorAll(sectionHeadings)) {
    heading.setAttribute('aria-level', '2');
  }
}
const docsRoot = document.getElementById('swagger-ui');
new MutationObserver(() => improveSwaggerAccessibility(docsRoot)).observe(
  docsRoot, { childList: true, subtree: true }
);
