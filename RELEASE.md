# Release Notes

## 0.13.0

- Add support for passing complex lists on the command line and converting from
  string to list using ast.literal_eval to safely evaluate the string
  expression.
- Add experimental ParsedDocstring class to help generalize the docstring
  parsing used in @docannotate.
- Add experimental terminal size querying routines to support better help string
  printing in the shell.
- Add additional functionality to metadata

## 0.12.3

- Fix valid_identifiers() on python 3 that was adding dict.keys() which is no
  longer supported.
- Fix negative numbers being misinterpreted as flags.
- Fix equals signs in --flag=name=value causing an exception due to incorrect
  splitting logic.

## 0.12.2

- Fix issue with bytes type that did not properly allow specifying hex strings
  during the conversion to being python 3 compliant.  (Issue #25)

## 0.12.1

- Add support for indicating contexts and stringable return values in
  docannotate. (Issue #22)

## 0.12.0

- Add support for @docannotate that pulls all annotation info directly from the
  docstring.
- Fix miscellaneous bugs and slight incompatibilities with previous typedargs
  embedded into CoreTools.

## 0.11.0

- Add support for lazy type loading. (Issue #15)
- Test for and fix compatibility with old embedded typedargs in coretools, to
  prepare for dropping embedded version.

## 0.10.0

- Port to modern code, fix all pylint errors and turn pylint on in CI
- Add support for short arguments and not passing True to a boolean flag

## 0.9.2

- Update unicode compatibility

## 0.9.1

- Remove unnecessary pyparsing dependency

## 0.9.0

- Initial release after being broken out of IOTile CoreTools
- Exception hierarchy renamed and IOTile specific wording removed
