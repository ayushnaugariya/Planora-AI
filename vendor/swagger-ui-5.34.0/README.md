# Self-hosted Swagger UI 5.34.0

These are the existing API documentation UI assets, now served locally so the unchanged application CSP can remain self-only. They are not loaded by the product homepage/studio. No npm install or browser CDN is needed.

Source: `https://registry.npmjs.org/swagger-ui-dist/-/swagger-ui-dist-5.34.0.tgz`
Registry metadata: `https://registry.npmjs.org/swagger-ui-dist/5.34.0`

The npm tarball was checked against its registry SHA-512 integrity before selecting these files:

```text
sha512-H6tAIjr3XqE31PbkZl0OFya1ziRLDfTwh3J6OHdumPtPCLfjTnyLeagl/55kFNZcTOz9a9QI9WP0FXldwiGJag==
```

| File | SHA-256 |
| --- | --- |
| `LICENSE` | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `NOTICE` | `0d20d1adef18aee3f40dd258172155521ce702ac445cb5f7b7d60ed32dad2fb2` |
| `swagger-ui-bundle.js` | `3f6abf70480db7e07914df4c98a77385f22ea585eaf457a3e6415ba0eae2d167` |
| `swagger-ui.css` | `c3cfe8248c4b0b89673600fb829924eafbac6de4bc4b2b06f5f5243483074d0a` |

`LICENSE` (Apache-2.0), upstream `NOTICE` and `swagger-ui-bundle.js.LICENSE.txt` (bundled third-party notices; SHA-256 `e5a4792feaa5332dfba37f1d7adf84308b93b4f2d8da0569a9f48a3cb61c969b`) are retained. The upstream bundle is unmodified. Source maps and unused distribution files are not shipped.

Update policy: select an explicit upstream version, review upstream security/license changes, verify the tarball integrity, replace the selected files and record hashes, then run the strict-CSP/no-CDN browser regression. Pinning and transport/integrity checks are not a comprehensive dependency vulnerability assessment.

Files live outside the authored `frontend/` modules and are mounted narrowly at `/static/assets/vendor/swagger-ui-5.34.0/`. Existing application source-safety checks remain unchanged; the vendor bundle receives a separate syntax check and real strict-CSP/no-CDN browser test.
