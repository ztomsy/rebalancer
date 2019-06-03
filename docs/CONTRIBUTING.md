
#Contributing


Some of the things that project need to help with:

- Add features from [Roadmap](../README.md#Roadmap)
- Improve performance of existing code (but not at the cost of readability)
- Help to write more tests! Feel free to check for edge cases, or for uncommon parameter
  combinations which may cause silent errors.


# Guidelines


## Seek early feedback

Before you start coding your contribution, it may be wise to
`raise an issue` on repository page to discuss whether the contribution is appropriate for the project.

## Code style

For this project is used `Pycharm Python Default IDE` as the
formatting standard, with all of the default settings. It would be much
appreciated if any PRs follow this standard because if not it will be formatted before merging.

# Testing

Any contributions must be accompanied by unit tests (written with `pytest`).
These are incredibly simple to write, just find the relevant test file (or create
a new one), and write a bunch of `assert` statements. The test should
cover core functionality, warnings/errors (check that they are raised as expected),
and limiting behaviour or edge cases.

# Documentation

Inline comments are great when needed, but don't go overboard. Docstring content
should follow [PEP257](https://stackoverflow.com/questions/2557110/what-to-put-in-a-python-module-docstring)
semantically and sphinx syntactically, such that sphinx can automatically document
the methods and their arguments.

Just remember it'd make things a lot simpler to have the person who
wrote the code explain it in their own words.