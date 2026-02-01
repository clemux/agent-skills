---
name: accessibility-testing
description: Use when fixing accessibility issues, verifying WCAG compliance, checking color contrast ratios, or running Lighthouse audits. Triggers on "accessibility", "a11y", "WCAG", "contrast ratio", "screen reader", "Lighthouse audit".
---

# Accessibility Testing

Run Lighthouse accessibility audits and verify WCAG color contrast compliance.

## Quick Reference

```bash
# Run Lighthouse accessibility audit (dev server must be running)
npx lighthouse http://localhost:9000 --preset=desktop --output=json --output-path=./report.json --chrome-flags="--headless --no-sandbox"

# Extract accessibility score (0-1, multiply by 100 for percentage)
jq '.categories.accessibility.score' ./report.json

# Check color contrast ratio
npx get-contrast "#foreground" "#background"
```

## WCAG Contrast Requirements

| Level | Normal Text | Large Text |
|-------|-------------|------------|
| AA    | 4.5:1       | 3:1        |
| AAA   | 7:1         | 4.5:1      |

Large text = 18pt+ regular or 14pt+ bold.

## Color Contrast Verification

```bash
# Check if colors pass WCAG
npx get-contrast "#6abf7b" "#141816"
# Output: Ratio: 7.98, Score: AAA

npx get-contrast "#6abf7b" "#fff"
# Output: Ratio: 2.25, Score: Fail
```

Always verify both light and dark mode combinations.

## Lighthouse Workflow

1. **Start dev server** (if not running)
2. **Run audit:**
   ```bash
   npx lighthouse http://localhost:9000 --preset=desktop --output=json --output-path=./report.json --chrome-flags="--headless --no-sandbox"
   ```
3. **Check score:**
   ```bash
   jq '.categories.accessibility.score' ./report.json
   ```
4. **Find failing audits:**
   ```bash
   jq '[.audits | to_entries[] | select(.value.score == 0) | {id: .key, title: .value.title}]' ./report.json
   ```
5. **Get details on specific audit:**
   ```bash
   jq '.audits["aria-allowed-attr"]' ./report.json
   ```

## Testing Dark Mode with Lighthouse

Lighthouse launches a fresh Chrome instance ignoring localStorage. To test dark mode:

1. Temporarily force dark mode in boot file:
   ```typescript
   // In src/boot/dark-mode.ts or equivalent
   Dark.set(true); // TEMP: force dark mode for Lighthouse
   ```
2. Run Lighthouse with different output path:
   ```bash
   npx lighthouse http://localhost:9000 --preset=desktop --output=json --output-path=./report_dark.json --chrome-flags="--headless --no-sandbox"
   ```
3. Remove the temporary line after testing

## Common Accessibility Issues

| Issue | Fix |
|-------|-----|
| `user-scalable=no` in viewport | Remove it, set `maximum-scale=5` |
| Button without accessible name | Add `aria-label` attribute |
| Low contrast text | Use darker/lighter colors (check with get-contrast) |
| ARIA role with invalid attributes | Add `role="presentation"` or remove conflicting attrs |
| `<hr>` in `<ul>/<ol>` with tabindex | Add `role="presentation"` and `:aria-orientation="null"` |

## Quasar-Specific Fixes

```vue
<!-- Button with icon needs aria-label -->
<q-btn
  icon="dark_mode"
  :aria-label="$t('theme.toggleDarkMode')"
/>

<!-- Separator in list needs presentation role -->
<q-separator role="presentation" :aria-orientation="null" />

<!-- Conditional contrast classes for theme support -->
<div :class="$q.dark.isActive ? 'text-grey-4' : 'text-grey-9'">
```

## Verification Checklist

- [ ] Run Lighthouse, score >= 95%
- [ ] Verify contrast with `get-contrast` for all text/background combinations
- [ ] Test both light and dark mode
- [ ] Run `pnpm lint` after changes
- [ ] Run tests to ensure no regressions