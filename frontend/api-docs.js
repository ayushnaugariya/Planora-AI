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
