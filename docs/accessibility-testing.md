# accessibility-testing

Historical accessibility checks for a Quasar project. Not installed by default.

The skill runs Lighthouse against `localhost:9000`, writes JSON reports into the working
directory, and includes a manual contrast check.

## Known limitations

- It mentions screen-reader testing but provides no screen-reader procedure.
- It assumes Quasar, `pnpm lint`, and a fixed local URL.
- Its dark-mode check temporarily edits source code.
- A Lighthouse score does not establish WCAG compliance.
