# Taxonomy

- [ ] link with https://www.eopugetsound.org/species/oregonia-gracilis ?
- [x] remove leading '...' from search suggestions

# Wikipedia

- [ ] some point to the wrong thing, barnacle Balanoidea is also part of the name for a snail
- [ ] when a page has multiple names, show them in order

# General

- [x] https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps
- [x] clean up versioned files
- [x] make search-data.js properly versioned
- [ ] add tests for javascript, run in the browser with a wrapper function?
- [ ] textwrap.dedent on all HTML output is expensive

# Verify
- [ ] n^2 spell check is expensive

# Sites

- [x] add search for site names, not dates


# Dive Log
- [ ] match pictures with approximate depth
- [ ] cache XML parsing results in database for next time

# HTML/CSS/JavaScript Improvements

## High Priority

### Security & Code Quality
- [x] **Fix eval() usage in game.js** - Replace `eval(onclick)` with proper event listeners (SECURITY RISK)
- [ ] **Update jQuery** - Currently using 3.6.0 from 2023; update to latest version for security patches
- [ ] **Add Content Security Policy** - Implement CSP headers to prevent XSS attacks

### Accessibility
- [ ] **Add semantic HTML5 elements** - Replace generic divs with `<main>`, `<nav>`, `<article>`, `<section>`, `<aside>`
- [ ] **Add ARIA labels** - Interactive cards/buttons need proper ARIA attributes
- [ ] **Implement focus indicators** - Add visible focus states for keyboard navigation
- [ ] **Add skip to content link** - Improve keyboard navigation
- [ ] **Improve alt text quality** - Include more context beyond species names
- [ ] **Fix color contrast** - Gray `.count` text (#808080) on black may fail WCAG AA

### HTML Structure
- [ ] **Standardize HTML structure** - Consistent footer placement across page types
- [ ] **Consistent lang attribute** - Add `lang="en"` to all pages
- [ ] **Consolidate inline scripts** - Move duplicate `flip()` function to external JS file

## Medium Priority

### Performance
- [ ] **Fix lazy loading inconsistency** - Apply threshold-based logic consistently
- [ ] **Add resource hints** - `<link rel="preconnect">` for external resources
- [ ] **Implement critical CSS inlining** - Inline above-the-fold CSS to reduce render-blocking
- [ ] **Minify CSS** - Minify stylesheet for production
- [ ] **Remove console.log statements** - Remove prefetch logging in production
- [ ] **Optimize search index** - `search-data.js` is 106KB; compress or load on-demand
- [ ] **Add service worker** - Implement offline support for static site
- [ ] **Code splitting** - Split JavaScript by page type instead of loading everything upfront

### CSS Improvements
- [ ] **Implement CSS custom properties** - Replace magic numbers (7000ms, 350px, 2.5rem) with CSS variables
- [ ] **Remove unused vendor prefixes** - `-webkit-backface-visibility` and `-webkit-transform` no longer needed
- [ ] **Clean up redundant rules** - Remove duplicate border rules
- [ ] **Add dark mode support** - Implement `prefers-color-scheme` media query
- [ ] **Fix font-family** - Either use web fonts properly or specify fallback stack

### JavaScript Enhancements
- [ ] **Refactor global variables** - Detective game uses many globals; use module pattern or classes
- [ ] **Improve error handling** - Show user-friendly messages for video/timeline loading errors
- [ ] **Optimize search algorithm** - O(n²) complexity; consider Fuse.js or more efficient fuzzy search
- [ ] **Improve random function** - Use standard `Math.floor(Math.random() * maximum)` pattern
- [ ] **Standardize quote style** - Consistent use of single or double quotes
- [ ] **Extract magic strings** - Classes like 'is-flipped', 'diving_prefetched_urls' should be constants

### SEO & Meta
- [ ] **Add Open Graph tags** - `og:image`, `og:description` for social media sharing
- [ ] **Add structured data** - JSON-LD for ImageObject, BreadcrumbList, etc.
- [ ] **Fix canonical URL consistency** - Ensure consistent canonical URLs across pages
- [ ] **Optimize sitemap** - 3.8MB sitemap.xml is large; consider splitting or compressing

## Low Priority

### UX Improvements
- [ ] **Make card flip timeout configurable** - 7-second auto-flip is arbitrary
- [ ] **Add loading indicators** - Visual feedback for timeline lazy loading
- [ ] **Improve search UX** - Add clear/reset button; Enter key should trigger search
- [ ] **Fix mobile navigation** - Prevent top navigation pills from overflowing on small screens
- [ ] **Add image captions on hover** - Show captions in regular view, not just Fancybox
- [ ] **Improve detective game feedback** - Add green border for correct answers (currently only red for wrong)
- [ ] **Use browser back button** - Search "Back" should use browser history instead of custom stack

### Code Cleanup
- [ ] **Remove commented code** - Clean up CSS comments like `/* text-justify: inter-word; */`
- [ ] **Dynamic copyright year** - Generate footer year dynamically instead of hardcoding
- [ ] **Add srcset for responsive images** - Better support for different screen sizes
- [ ] **Remove CSS Grid fallback** - Document browser support requirements (or add fallback if needed)
- [ ] **Consistent script loading** - Standardize use of `defer` attribute across all pages
