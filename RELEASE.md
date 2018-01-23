# Release Notes

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
